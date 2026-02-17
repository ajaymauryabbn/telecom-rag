#!/bin/bash
# Complete Deployment Workflow with OrbStack

set -e

echo "🚀 Telecom RAG - Complete Deployment Workflow"
echo "=============================================="
echo ""

# Check OrbStack status
CURRENT_CONTEXT=$(docker context show)
if [ "$CURRENT_CONTEXT" != "orbstack" ]; then
    echo "⚠️  Switching to OrbStack for better performance..."
    docker context use orbstack
fi

echo "✅ Using OrbStack (faster builds & pushes)"
echo ""

# Configuration
PROJECT_ID="telecom-rag"
SERVICE_NAME="telecom-rag-service"
REGION="us-central1"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

# Menu
echo "Select deployment method:"
echo "  1) Build locally + Push to GCR + Deploy (slower, ~45 min total)"
echo "  2) Cloud Build from source (faster, ~15-20 min total) ⭐ RECOMMENDED"
echo "  3) Build locally only (for testing)"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "📦 Option 1: Local Build + Push + Deploy"
        echo "========================================="
        
        # Build
        echo ""
        echo "🔨 Step 1/3: Building with OrbStack..."
        ./build-orbstack.sh
        
        # Push
        echo ""
        echo "📤 Step 2/3: Pushing to GCR..."
        START_PUSH=$(date +%s)
        docker push $IMAGE
        END_PUSH=$(date +%s)
        PUSH_TIME=$((END_PUSH - START_PUSH))
        echo "✅ Push completed in ${PUSH_TIME}s"
        
        # Deploy
        echo ""
        echo "🚀 Step 3/3: Deploying to Cloud Run..."
        ./deploy.sh
        ;;
        
    2)
        echo ""
        echo "☁️  Option 2: Cloud Build Deployment (Recommended)"
        echo "=================================================="
        echo ""
        echo "This builds the image in GCP (faster & more reliable)"
        echo ""
        ./deploy-cloudbuild.sh
        ;;
        
    3)
        echo ""
        echo "🔨 Option 3: Local Build Only"
        echo "=============================="
        ./build-orbstack.sh
        echo ""
        echo "💡 To test locally:"
        echo "   docker run -p 8501:8501 --env-file .env $IMAGE"
        ;;
        
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "🎉 Done!"
