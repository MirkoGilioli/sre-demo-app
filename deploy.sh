#!/bin/bash
set -e

# Configuration (Change these to your project settings)
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
REPO_NAME="sre-demo-images"
REPO_PATH="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME"

echo "Using Project: $PROJECT_ID in Region: $REGION"

# 1. Build & Push Backend
echo "--- Building & Pushing Backend Image ---"
cd backend
gcloud builds submit --tag "$REPO_PATH/agenda-backend:latest" .
cd ..

# 2. Build & Push Frontend
echo "--- Building & Pushing Frontend Image ---"
cd frontend
gcloud builds submit --tag "$REPO_PATH/agenda-frontend:latest" .
cd ..

# 3. Deploy Backend to Cloud Run
echo "--- Deploying Backend Service ---"
gcloud run deploy agenda-backend \
  --image "$REPO_PATH/agenda-backend:latest" \
  --region "$REGION" \
  --service-account "sre-demo-backend-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --allow-unauthenticated

BACKEND_URL=$(gcloud run services describe agenda-backend --region "$REGION" --format 'value(status.url)')
echo "Backend URL: $BACKEND_URL"

# 4. Deploy Frontend to Cloud Run
echo "--- Deploying Frontend Service ---"
gcloud run deploy agenda-frontend \
  --image "$REPO_PATH/agenda-frontend:latest" \
  --region "$REGION" \
  --allow-unauthenticated

FRONTEND_URL=$(gcloud run services describe agenda-frontend --region "$REGION" --format 'value(status.url)')

echo "--- DEPLOYMENT COMPLETE ---"
echo "Frontend URL: $FRONTEND_URL"
echo "Backend URL: $BACKEND_URL"
echo ""
echo "INSTRUCTIONS:"
echo "1. Visit the Frontend URL."
echo "2. Paste the Backend URL into the Configuration field and click Save."
echo "3. Use the Chaos Control buttons to break the app for your SRE demo!"
