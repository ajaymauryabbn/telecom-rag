#!/bin/bash
# Deploy to Cloud Run using Cloud Build (faster than local push)

set -e

# Add gcloud to PATH if local SDK exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/google-cloud-sdk/bin" ]; then
    export PATH="$SCRIPT_DIR/google-cloud-sdk/bin:$PATH"
fi

echo "🚀 Deploying to Cloud Run using Cloud Build"
echo "============================================="

# Configuration
PROJECT_ID="telecom-rag"
SERVICE_NAME="telecom-rag-service"
REGION="us-central1"

# Load environment variables (using source to handle values properly)
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "✅ Loaded environment variables from .env"
else
    echo "❌ Error: .env file not found!"
    exit 1
fi

echo ""
echo "📋 Deployment Configuration:"
echo "   Project: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Method: Cloud Build (builds in GCP)"
echo ""

echo "🔨 Building and deploying with Cloud Build..."
echo ""

# Deploy using Cloud Build (builds image in GCP, much faster)
gcloud run deploy $SERVICE_NAME \
  --source=. \
  --platform=managed \
  --region=$REGION \
  --project=$PROJECT_ID \
  --memory=4Gi \
  --cpu=2 \
  --timeout=300s \
  --min-instances=0 \
  --max-instances=10 \
  --allow-unauthenticated \
  --set-env-vars="LLM_PROVIDER=openai,EMBEDDING_PROVIDER=openai,ENABLE_RERANK=false,ENABLE_HYBRID=true,ENABLE_REDIS=false,OPENAI_API_KEY=${OPENAI_API_KEY},HF_TOKEN=${HF_TOKEN}"

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
echo "   3. Check logs: gcloud run services logs read $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
echo ""
echo "🎉 Deployment successful!"
