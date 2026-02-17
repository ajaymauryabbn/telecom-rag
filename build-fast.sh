#!/bin/bash
# Fast Docker Build Script with BuildKit Optimizations

set -e

echo "🚀 Building Docker Image with Optimizations"
echo "============================================"

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1

# Configuration
PROJECT_ID="telecom-rag"
SERVICE_NAME="telecom-rag-service"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo ""
echo "📋 Build Configuration:"
echo "   BuildKit: ENABLED (cache mounts, parallel builds)"
echo "   Image: $IMAGE"
echo ""

# Build with BuildKit and cache
echo "🔨 Building image..."
time docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t $IMAGE \
  -f Dockerfile.optimized \
  .

echo ""
echo "✅ Build Complete!"
echo ""
echo "📊 Next Steps:"
echo "   1. Push: docker push $IMAGE"
echo "   2. Deploy: ./deploy.sh"
echo ""
