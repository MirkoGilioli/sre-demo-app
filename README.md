# SRE Demo: Personal Agenda

This application is designed for Google SRE principles training. It features built-in "Chaos" mechanisms to demonstrate SLIs, SLOs, and Error Budgets.

## Architecture
- **Frontend**: Static SPA (HTML/JS) served by Nginx on Cloud Run.
- **Backend**: Flask API on Cloud Run, instrumented with OpenTelemetry.
- **Database**: Google Cloud Firestore.

## Features for SRE Training
- **SLI/SLO Demonstrations**:
  - **Availability**: Use the "50% Error Rate" button to burn through your error budget.
  - **Latency**: Use the "Inject 2s Latency" button to demonstrate SLI drops and the impact on user experience.
- **Observability**:
  - **OpenTelemetry**: Integrated with Cloud Trace for distributed tracing.
  - **Structured Logging**: View backend errors and chaos triggers in Logs Explorer.
- **Infrastructure as Code**: Terraform setup included for repeatable deployments.

## Quick Start
### Local Development (with Docker Compose)
To run the full stack locally (including a Firestore emulator):
1.  **Start Services**:
    ```bash
    docker-compose up --build
    ```
2.  **Access App**:
    - Frontend: [http://localhost:8082](http://localhost:8082)
    - Backend: [http://localhost:8081](http://localhost:8081)
3.  **Configure Local Backend**: In the Frontend UI, set the Backend URL to `http://localhost:8081/` and click Save.

### Cloud Deployment (GCP)
1.  **Configure GCP**: Ensure you have a project ID and `gcloud` is authenticated.
2.  **Infrastructure**:
    ```bash
    cd terraform
    terraform init
    terraform apply -var="project_id=YOUR_PROJECT_ID"
    ```
### CI/CD Pipeline (Cloud Build)
The project now includes a complete CI/CD pipeline defined in `cloudbuild.yaml`.

#### 1. Manual Trigger
To manually trigger the full build and deployment from your local machine using the custom Service Account:
```bash
# Obtain the email from terraform outputs first
CB_SA_EMAIL=$(terraform -chdir=terraform output -raw cloudbuild_sa_email)

gcloud builds submit --config cloudbuild.yaml --service-account="projects/$PROJECT_ID/serviceAccounts/$CB_SA_EMAIL" .
```

#### 2. Automatic GitHub Trigger
To set up a fully automated pipeline:
1.  Go to the **Cloud Build Console -> Triggers**.
2.  Connect your GitHub repository.
3.  Create a Trigger that points to the `main` branch.
4.  Choose **Cloud Build configuration file (yaml)** and select `cloudbuild.yaml`.
5.  Every `git push` will now automatically build and deploy your SRE demo app!

#### 3. Required Permissions
Ensure the Cloud Build Service Account has the following roles:
- `Cloud Run Admin`
- `Service Account User`
- `Artifact Registry Writer`
4.  **Use**: Visit the `Frontend URL` provided at the end of the deployment script.

## Generating Traffic Load (Locust)
You can use Locust to generate a steady stream of traffic. This is essential for populating your monitoring dashboards and demonstrating the impact of your Chaos events.

### 1. Installation
Install Locust locally via pip:
```bash
pip install locust
```

### 2. Running Locust
From the project root, run:
```bash
locust -f locust/locustfile.py
```

3. Open **http://localhost:8089** in your browser.
4. **Host**: 
   - Local: `http://localhost:8081`
   - Cloud: `https://your-backend-url.run.app`
5. **Users**: Start with 5-10 users and a spawn rate of 1.

### 3. Demo Workflow
1. Start Locust and generate traffic.
2. Observe your **Latency SLO Dashboard** in the GCP Console.
3. In the application UI, click **"Inject 2s Latency"**.
4. Observe how Locust immediately reports failures or high latency, which then propagates to your **Error Budget** and triggers the **Burn Rate Alert**.
