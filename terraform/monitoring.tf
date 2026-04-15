# 1. Custom Service for the Backend
# Although Cloud Run services are auto-discovered, creating a custom service 
# entry allows for more granular SLO management in a demo.
resource "google_monitoring_custom_service" "backend_service" {
  service_id   = "agenda-backend-service"
  display_name = "Agenda Backend Service"
}

# 2. Latency SLO: 90% of requests < 500ms
resource "google_monitoring_slo" "latency_slo" {
  service      = google_monitoring_custom_service.backend_service.service_id
  slo_id       = "latency-slo"
  display_name = "90% - Latency < 500ms"

  goal                = 0.9
  rolling_period_days = 28

  request_based_sli {
    distribution_cut {
      distribution_filter = <<EOF
        resource.type="cloud_run_revision"
        resource.labels.service_name="agenda-backend"
        metric.type="run.googleapis.com/request_latencies"
EOF
      range {
        max = 500 # 500ms threshold
      }
    }
  }

  depends_on = [google_monitoring_custom_service.backend_service]
}

# 3. Burn Rate Alert Policy
# Triggers if the "Chaos" injection burns through the error budget too fast.
# In a demo, we want to see this trip quickly.
resource "google_monitoring_alert_policy" "burn_rate_alert" {
  display_name = "High Burn Rate - Latency SLO"
  combiner     = "OR"
  conditions {
    display_name = "Slo Burn Rate > 1.0 (1h window)"
    condition_threshold {
      filter          = "select_slo_burn_rate(\"${google_monitoring_slo.latency_slo.name}\", \"1h\")"
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 1.0
      trigger {
        count = 1
      }
    }
  }

  alert_strategy {
    auto_close = "1800s" # 30 minutes
  }

  notification_channels = [] # You can add email/slack channels here if needed

  # Documentation for the on-call engineer (or students)
  documentation {
    content   = "The Latency SLO for the Agenda Backend is burning through its error budget! Check if someone triggered a Chaos event or if there is a real performance regression in Firestore."
    mime_type = "text/markdown"
  }
}
