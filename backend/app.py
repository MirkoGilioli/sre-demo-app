import os
import random
import time
import logging
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import firestore

# OpenTelemetry Imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource

# Setup Logging
if os.getenv("K_SERVICE"): # Running on Cloud Run
    from google.cloud import logging as cloud_logging
    log_client = cloud_logging.Client()
    log_client.setup_logging()
else:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# OpenTelemetry Setup
resource = Resource.create({
    "service.name": "agenda-backend",
    "service.namespace": "sre-demo",
})

tracer_provider = TracerProvider(resource=resource)
# Only use CloudTraceSpanExporter if not in local dev or if explicitly enabled
if os.getenv("K_SERVICE"): # Running on Cloud Run
    cloud_trace_exporter = CloudTraceSpanExporter()
    tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))

trace.set_tracer_provider(tracer_provider)
FlaskInstrumentor().instrument_app(app)

tracer = trace.get_tracer(__name__)

# Firestore Setup
emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")
if emulator_host:
    logger.info(f"Connecting to Firestore Emulator at {emulator_host}")
db = firestore.Client()
COLLECTION_NAME = "agenda_events"

# Chaos State
chaos_state = {
    "latency_ms": 0,
    "error_rate": 0.0
}

@app.before_request
def apply_chaos():
    # Apply Latency Chaos
    if chaos_state["latency_ms"] > 0:
        time.sleep(chaos_state["latency_ms"] / 1000.0)
    
    # Apply Error Chaos
    if chaos_state["error_rate"] > 0:
        if random.random() < chaos_state["error_rate"]:
            logger.error("Chaos induced error triggered!")
            return jsonify({"error": "Internal Server Error (Chaos)"}), 500

@app.route('/healthz')
def healthz():
    return "OK", 200

# --- CRUD Endpoints ---

@app.route('/api/events', methods=['GET'])
def list_events():
    try:
        with tracer.start_as_current_span("list_events_firestore"):
            docs = db.collection(COLLECTION_NAME).stream()
            events = []
            for doc in docs:
                event = doc.to_dict()
                event['id'] = doc.id
                
                # Convert datetime to serializable format for frontend
                if 'timestamp' in event and hasattr(event['timestamp'], 'timestamp'):
                    event['timestamp'] = {
                        "seconds": int(event['timestamp'].timestamp())
                    }
                events.append(event)
            return jsonify(events)
    except Exception as e:
        logger.exception("Failed to list events from Firestore")
        # Return the actual error for easier debugging during the demo/setup
        return jsonify({"error": "Firestore Error", "details": str(e)}), 500

@app.route('/api/events', methods=['POST'])
def create_event():
    try:
        data = request.get_json(silent=True)
        if not data or 'title' not in data:
            logger.error(f"Invalid request data: {data}")
            return jsonify({"error": "Missing title"}), 400
        
        with tracer.start_as_current_span("create_event_firestore"):
            # Use provided timestamp or fallback to server timestamp
            ts = firestore.SERVER_TIMESTAMP
            if data.get('timestamp'):
                try:
                    # Expecting ISO format from frontend
                    from datetime import datetime
                    ts = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                except Exception as te:
                    logger.warning(f"Failed to parse provided timestamp {data.get('timestamp')}: {te}")

            event_data = {
                "title": data['title'],
                "description": data.get('description', ''),
                "timestamp": ts
            }
            logger.info(f"Adding event to Firestore: {data['title']}")
            
            # Create doc and get reference
            _, doc_ref = db.collection(COLLECTION_NAME).add(event_data)
            
            # Fetch the doc back to get the server timestamp
            new_doc = doc_ref.get()
            if not new_doc.exists:
                logger.error(f"Created document {doc_ref.id} but could not retrieve it immediately.")
                return jsonify({"id": doc_ref.id, "title": data['title'], "status": "created_but_not_fetched"}), 201

            new_event = new_doc.to_dict()
            new_event['id'] = new_doc.id
            
            # Convert datetime to serializable format
            if 'timestamp' in new_event and hasattr(new_event['timestamp'], 'timestamp'):
                new_event['timestamp'] = {
                    "seconds": int(new_event['timestamp'].timestamp())
                }
            
            logger.info(f"Successfully created and retrieved event: {new_event['id']}")
            return jsonify(new_event), 201
            
    except Exception as e:
        logger.exception("Failed to create event in Firestore")
        # Return the actual error for easier debugging during the demo/setup
        return jsonify({"error": "Firestore Error", "details": str(e)}), 500

@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    with tracer.start_as_current_span("delete_event_firestore"):
        db.collection(COLLECTION_NAME).document(event_id).delete()
        logger.info(f"Deleted event: {event_id}")
        return '', 204

# --- Chaos Engineering Endpoints ---

@app.route('/api/chaos/latency', methods=['POST'])
def set_latency():
    ms = request.args.get('ms', default=0, type=int)
    chaos_state["latency_ms"] = ms
    logger.warning(f"Chaos Latency set to {ms}ms")
    return jsonify({"status": f"Latency set to {ms}ms"}), 200

@app.route('/api/chaos/error', methods=['POST'])
def set_error_rate():
    rate = request.args.get('rate', default=0.0, type=float)
    chaos_state["error_rate"] = rate
    logger.warning(f"Chaos Error Rate set to {rate*100}%")
    return jsonify({"status": f"Error rate set to {rate*100}%"}), 200

@app.route('/api/chaos/reset', methods=['POST'])
def reset_chaos():
    chaos_state["latency_ms"] = 0
    chaos_state["error_rate"] = 0.0
    logger.info("Chaos state reset")
    return jsonify({"status": "Chaos state reset to normal"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
