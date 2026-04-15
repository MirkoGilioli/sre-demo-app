# Scenario 3: Dependency Degradation

## Concept
Applications don't exist in a vacuum. Often, a "slow" application is actually caused by a "slow" dependency (like a database or an external API).

## The Incident
1.  Update the backend service to simulate a slow database:
    ```bash
    gcloud run deploy agenda-backend --update-env-vars SLOW_DB=true
    ```
2.  Add a few events in the UI. You will notice every action takes 3+ seconds to complete.

## The Impact
-   The **Latency SLO** will immediately fail (since our threshold is 500ms).
-   User experience is poor, but the app isn't "crashing".

## The Lesson
-   **Distributed Tracing**: Open **Cloud Trace** in the GCP Console.
-   Find a slow trace. Show students how to expand the spans.
-   Point out that the root span (`POST /api/events`) is slow, but specifically the inner span **`create_event_firestore`** is where all the time is being spent.
-   This proves the issue is in the **Database Layer**, not the application logic or network—saving SREs hours of debugging!
