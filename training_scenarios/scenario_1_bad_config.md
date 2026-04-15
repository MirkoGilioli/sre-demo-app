# Scenario 1: The Bad Config Push

## Concept
In SRE, we treat **Configuration as Code**. A small, one-line change in a configuration file can be just as destructive as a bug in the source code.

## The Incident
1.  Open `backend/config/config.yaml`.
2.  Change `default_error_rate: 0.0` to `0.5`.
3.  Commit and push this change to GitHub (triggering the CI/CD pipeline).

## The Impact
-   The new deployment will automatically have a 50% error rate for all users immediately upon startup.
-   The **Availability SLO** dashboard will show a massive drop.
-   The **Burn Rate Alert** will fire within minutes.

## The Lesson
-   **Validation**: Discuss why we need "Config Validation" tests in our CI/CD pipeline.
-   **Rollback**: Demonstrate how to quickly fix this by reverting the git commit and pushing again.
