# 1. Custom Service for the Backend
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

# 2b. Availability SLO: 99% of requests successful (non-5xx)
resource "google_monitoring_slo" "availability_slo" {
  service      = google_monitoring_custom_service.backend_service.service_id
  slo_id       = "availability-slo"
  display_name = "99% - Successful Requests"

  goal                = 0.99
  rolling_period_days = 28

  request_based_sli {
    good_total_ratio {
      # "Good" are all requests that are NOT 5xx errors (2xx, 3xx, 4xx)
      good_service_filter = <<EOF
        resource.type="cloud_run_revision"
        resource.labels.service_name="agenda-backend"
        metric.type="run.googleapis.com/request_count"
        metric.labels.response_code_class="2xx"
EOF
      total_service_filter = <<EOF
        resource.type="cloud_run_revision"
        resource.labels.service_name="agenda-backend"
        metric.type="run.googleapis.com/request_count"
EOF
    }
  }

  depends_on = [google_monitoring_custom_service.backend_service]
}

# 3. Burn Rate Alert Policy - Latency
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

  documentation {
    content   = "The Latency SLO for the Agenda Backend is burning through its error budget! Check if someone triggered a Chaos event or if there is a real performance regression in Firestore."
    mime_type = "text/markdown"
  }
}

# 3b. Burn Rate Alert Policy - Availability
resource "google_monitoring_alert_policy" "availability_burn_rate_alert" {
  display_name = "High Burn Rate - Availability SLO"
  combiner     = "OR"
  conditions {
    display_name = "Availability Burn Rate > 1.0 (1h window)"
    condition_threshold {
      filter          = "select_slo_burn_rate(\"${google_monitoring_slo.availability_slo.name}\", \"1h\")"
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 1.0
      trigger {
        count = 1
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content   = "The Availability SLO for the Agenda Backend is failing! This usually means the '50% Error Rate' chaos button has been clicked or the backend is crashing."
    mime_type = "text/markdown"
  }
}
