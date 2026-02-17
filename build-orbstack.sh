#!/bin/bash
# OrbStack-Optimized Build Script for Telecom RAG

set -e

echo "🚀 Building with OrbStack (Optimized)"
echo "======================================"

# Verify OrbStack is active
CURRENT_CONTEXT=$(docker context show)
if [ "$CURRENT_CONTEXT" != "orbstack" ]; then
    echo "⚠️  Switching to OrbStack context..."
    docker context use orbstack
fi

# OrbStack-specific optimizations
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
export COMPOSE_DOCKER_CLI_BUILD=1

# Configuration
PROJECT_ID="telecom-rag"
SERVICE_NAME="telecom-rag-service"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo ""
echo "📋 Build Configuration:"
echo "   Context: $(docker context show)"
echo "   BuildKit: ENABLED"
echo "   Image: $IMAGE"
echo "   Dockerfile: Dockerfile.optimized"
echo ""

# Check if optimized Dockerfile exists
if [ ! -f "Dockerfile.optimized" ]; then
    echo "⚠️  Dockerfile.optimized not found, using standard Dockerfile"
    DOCKERFILE="Dockerfile"
else
    DOCKERFILE="Dockerfile.optimized"
fi

echo "🔨 Building image with OrbStack..."
echo ""

# Build with timing
START_TIME=$(date +%s)

docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --progress=plain \
  -t $IMAGE \
  -f $DOCKERFILE \
  .

END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))

echo ""
echo "✅ Build Complete!"
echo ""
echo "📊 Build Statistics:"
echo "   Time: ${BUILD_TIME}s ($(($BUILD_TIME / 60))m $(($BUILD_TIME % 60))s)"
docker images $IMAGE --format "   Size: {{.Size}}"
echo ""
echo "💡 Next Steps:"
echo "   1. Test locally: docker run -p 8501:8501 --env-file .env $IMAGE"
echo "   2. Push to GCR: docker push $IMAGE"
echo "   3. Deploy: ./deploy.sh"
echo ""
