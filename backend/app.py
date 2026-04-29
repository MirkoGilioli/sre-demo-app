import os
import random
import time
import logging
import json
import yaml
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

# Load Configuration
def load_config():
    config_path = os.getenv("CONFIG_PATH", "config/config.yaml")
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        return {
            "firestore": {"database_id": "sre-demo", "collection_name": "agenda_events"},
            "opentelemetry": {"service_name": "agenda-backend", "service_namespace": "sre-demo"},
            "chaos": {"default_latency_ms": 0, "default_error_rate": 0.0}
        }

config = load_config()

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
    "service.name": config["opentelemetry"]["service_name"],
    "service.namespace": config["opentelemetry"]["service_namespace"],
})

tracer_provider = TracerProvider(resource=resource)
if os.getenv("K_SERVICE"): # Running on Cloud Run
    cloud_trace_exporter = CloudTraceSpanExporter()
    tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))

trace.set_tracer_provider(tracer_provider)
FlaskInstrumentor().instrument_app(app)

tracer = trace.get_tracer(__name__)

# Firestore Setup
DB_NAME = config["firestore"]["database_id"]
COLLECTION_NAME = config["firestore"]["collection_name"]

emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")
if emulator_host:
    logger.info(f"Connecting to Firestore Emulator at {emulator_host} with DB {DB_NAME}")
    db = firestore.Client(database=DB_NAME)
else:
    logger.info(f"Connecting to Firestore Cloud DB {DB_NAME}")
    db = firestore.Client(database=DB_NAME)

# Chaos State (Dynamic)
chaos_state = {
    "latency_ms": config["chaos"]["default_latency_ms"],
    "error_rate": config["chaos"]["default_error_rate"]
}

# Systemic Chaos (via Environment Variables)
BUGGY_VERSION = os.getenv("BUGGY_VERSION", "false").lower() == "true"
SLOW_DB = os.getenv("SLOW_DB", "false").lower() == "true"

def apply_db_latency():
    if SLOW_DB:
        logger.warning("SLOW_DB active: injecting 3s latency to Firestore call")
        time.sleep(3.0)

@app.before_request
def apply_chaos():
    # 1. Systemic Buggy Version (High error rate)
    if BUGGY_VERSION:
        if random.random() < 0.7: # 70% error rate for buggy version
            logger.error("BUGGY_VERSION active: injecting error")
            return jsonify({"error": "Internal Server Error (Buggy Build)"}), 500

    # 2. Dynamic Latency (Manual trigger)
    if chaos_state["latency_ms"] > 0:
        time.sleep(chaos_state["latency_ms"] / 1000.0)
    
    # 3. Dynamic Error (Manual trigger)
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
        # Pagination and filter parameters
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        with tracer.start_as_current_span("list_events_firestore"):
            apply_db_latency()
            
            # Use order_by to ensure consistent pagination results
            query = db.collection(COLLECTION_NAME).order_by("timestamp", direction=firestore.Query.DESCENDING)
            
            # Apply date filters if provided
            from datetime import datetime, timezone
            if start_date_str:
                try:
                    start_dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                    query = query.where("timestamp", ">=", start_dt)
                except ValueError:
                    pass
            
            if end_date_str:
                try:
                    end_dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                    query = query.where("timestamp", "<=", end_dt)
                except ValueError:
                    pass

            if offset > 0:
                query = query.offset(offset)
            
            query = query.limit(limit)
            
            docs = query.stream()
            events = []
            for doc in docs:
                event = doc.to_dict()
                event['id'] = doc.id
                if 'timestamp' in event and hasattr(event['timestamp'], 'timestamp'):
                    event['timestamp'] = {"seconds": int(event['timestamp'].timestamp())}
                events.append(event)
            return jsonify(events)
    except Exception as e:
        logger.exception("Failed to list events from Firestore")
        return jsonify({"error": "Firestore Error", "details": str(e)}), 500

@app.route('/api/events', methods=['POST'])
def create_event():
    try:
        data = request.get_json(silent=True)
        if not data or 'title' not in data:
            return jsonify({"error": "Missing title"}), 400
        
        with tracer.start_as_current_span("create_event_firestore"):
            apply_db_latency()
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            ts = now
            if data.get('timestamp'):
                try:
                    ts = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                except Exception:
                    pass

            event_data = {
                "title": data['title'],
                "description": data.get('description', ''),
                "timestamp": ts,
                "inserted_at": now
            }
            _, doc_ref = db.collection(COLLECTION_NAME).add(event_data)
            new_doc = doc_ref.get()
            new_event = new_doc.to_dict()
            new_event['id'] = new_doc.id
            if 'timestamp' in new_event and hasattr(new_event['timestamp'], 'timestamp'):
                new_event['timestamp'] = {"seconds": int(new_event['timestamp'].timestamp())}
            return jsonify(new_event), 201
    except Exception as e:
        logger.exception("Failed to create event in Firestore")
        return jsonify({"error": "Firestore Error", "details": str(e)}), 500

@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        with tracer.start_as_current_span("delete_event_firestore"):
            apply_db_latency()
            db.collection(COLLECTION_NAME).document(event_id).delete()
            return '', 204
    except Exception as e:
        logger.exception("Failed to delete event from Firestore")
        return jsonify({"error": "Firestore Error", "details": str(e)}), 500

# --- Chaos Engineering Endpoints ---

@app.route('/api/chaos/latency', methods=['POST'])
def set_latency():
    ms = request.args.get('ms', default=0, type=int)
    chaos_state["latency_ms"] = ms
    return jsonify({"status": f"Latency set to {ms}ms"}), 200

@app.route('/api/chaos/error', methods=['POST'])
def set_error_rate():
    rate = request.args.get('rate', default=0.0, type=float)
    chaos_state["error_rate"] = rate
    return jsonify({"status": f"Error rate set to {rate*100}%"}), 200

@app.route('/api/chaos/reset', methods=['POST'])
def reset_chaos():
    chaos_state["latency_ms"] = 0
    chaos_state["error_rate"] = 0.0
    return jsonify({"status": "Chaos state reset to normal"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
