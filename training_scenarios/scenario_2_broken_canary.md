# Scenario 2: The Broken Canary

## Concept
One of the most powerful SRE tools is the **Canary Release**. By deploying a new version to only a small fraction of users, we limit the **Blast Radius** of any potential bugs.

## The Incident
1.  Trigger a new deployment using the `gcloud` command, but inject a bug via environment variables:
    ```bash
    gcloud run deploy agenda-backend \
      --image [YOUR_IMAGE_PATH] \
      --set-env-vars BUGGY_VERSION=true \
      --no-traffic
    ```
    *Note: `--no-traffic` ensures the new buggy version receives 0% traffic initially.*
2.  Go to the **Cloud Run Console -> agenda-backend -> Networking**.
3.  Click **"Manage Traffic"**.
4.  Direct **10%** of traffic to the new revision and **90%** to the current healthy one.

## The Impact
-   Only 1 out of 10 requests will fail.
-   The **Availability SLO** will dip slightly (e.g., from 100% to 93%).
-   The system remains "mostly" functional, giving SREs time to detect the issue without a total outage.

## The Lesson
-   **MTTR (Mean Time to Recovery)**: Show how clicking "100% traffic" back to the old revision "fixes" the incident in seconds without a new build.
-   **Observability**: Explain that detecting a 7% failure rate is harder than detecting a 100% failure rate, highlighting the need for high-fidelity monitoring.
