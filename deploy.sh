#!/bin/bash
# Telecom RAG - Cloud Run Deployment Script
# This script deploys the telecom-rag application to Google Cloud Run

set -e  # Exit on error

# Add gcloud to PATH if local SDK exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/google-cloud-sdk/bin" ]; then
    export PATH="$SCRIPT_DIR/google-cloud-sdk/bin:$PATH"
fi

echo "🚀 Starting Telecom RAG Deployment to Cloud Run"
echo "================================================"

# Configuration
PROJECT_ID="telecom-rag"
SERVICE_NAME="telecom-rag-service"
REGION="us-central1"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

# Load environment variables from .env (using source to handle values properly)
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "✅ Loaded environment variables from .env"
else
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Verify required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not set in .env"
    exit 1
fi

echo ""
echo "📋 Deployment Configuration:"
echo "   Project: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Image: $IMAGE"
echo ""

# Wait for Docker image to be available
echo "⏳ Checking if Docker image is available..."
if gcloud container images describe $IMAGE --project=$PROJECT_ID &>/dev/null; then
    echo "✅ Docker image found in GCR"
else
    echo "⚠️  Docker image not found. Waiting for push to complete..."
    echo "   Please ensure 'docker push $IMAGE' is running"
    
    # Wait up to 10 minutes for image
    for i in {1..60}; do
        sleep 10
        if gcloud container images describe $IMAGE --project=$PROJECT_ID &>/dev/null; then
            echo "✅ Docker image now available!"
            break
        fi
        echo "   Still waiting... ($((i*10))s elapsed)"
    done
fi

echo ""
echo "🚀 Deploying to Cloud Run..."
echo ""

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE \
  --platform=managed \
  --region=$REGION \
  --project=$PROJECT_ID \
  --memory=4Gi \
  --cpu=2 \
  --timeout=300s \
  --min-instances=0 \
  --max-instances=10 \
  --allow-unauthenticated \
  --set-env-vars="LLM_PROVIDER=openai,EMBEDDING_PROVIDER=openai,ENABLE_RERANK=false,ENABLE_HYBRID=true,ENABLE_REDIS=false,OPENAI_API_KEY=${OPENAI_API_KEY},HF_TOKEN=${HF_TOKEN}" \
  --quiet

echo ""
echo "✅ Deployment Complete!"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format='value(status.url)')

echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "📊 Next Steps:"
echo "   1. Visit $SERVICE_URL to test the application"
echo "   2. Try a sample query: 'What is HARQ in 5G?'"
echo "   3. Check logs: gcloud run services logs read $SERVICE_NAME --region=$REGION"
echo ""
echo "🎉 Deployment successful!"
