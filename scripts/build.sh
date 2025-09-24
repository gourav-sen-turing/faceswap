#!/bin/bash

# Docker Build Script for Face Quality Assessment Service
# Handles multiple build options and troubleshooting

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${BLUE}=========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}=========================================${NC}\n"
}

# Parse arguments
BUILD_TYPE="${1:-mediapipe}"
IMAGE_TAG="${2:-latest}"

log_section "Face Quality Assessment - Docker Build"

echo "Build Type: $BUILD_TYPE"
echo "Image Tag: $IMAGE_TAG"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
fi

log_info "Docker version: $(docker --version)"

# Check available memory
if command -v free &> /dev/null; then
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    log_info "Available RAM: ${TOTAL_MEM}GB"
    
    if [ "$TOTAL_MEM" -lt 4 ]; then
        log_warn "Less than 4GB RAM detected. Build might be slow or fail."
        log_warn "Consider using 'mediapipe' build type for easier compilation."
    fi
fi

# Set Dockerfile based on build type
case "$BUILD_TYPE" in
    mediapipe)
        DOCKERFILE="Dockerfile.mediapipe"
        log_info "Using MediaPipe (no dlib compilation, fastest)"
        ;;
    gpu|dlib)
        DOCKERFILE="Dockerfile"
        log_info "Using dlib with GPU support (requires CMake 3.5+)"
        ;;
    cpu)
        DOCKERFILE="Dockerfile.cpu"
        log_info "Using CPU-optimized build"
        ;;
    *)
        log_error "Unknown build type: $BUILD_TYPE"
        echo "Usage: $0 [mediapipe|gpu|cpu] [image-tag]"
        echo ""
        echo "Build types:"
        echo "  mediapipe - Fast build, uses MediaPipe (recommended)"
        echo "  gpu       - Full GPU support with dlib"
        echo "  cpu       - CPU-optimized build"
        exit 1
        ;;
esac

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    log_error "Dockerfile not found: $DOCKERFILE"
    exit 1
fi

log_info "Using Dockerfile: $DOCKERFILE"

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1

log_section "Starting Docker Build"

# Build command
BUILD_CMD="docker build -f $DOCKERFILE -t face-quality-assessment:$IMAGE_TAG ."

log_info "Build command: $BUILD_CMD"
echo ""

# Execute build
if $BUILD_CMD; then
    log_section "Build Successful!"
    
    # Show image info
    log_info "Image details:"
    docker images face-quality-assessment:$IMAGE_TAG --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    echo ""
    log_info "Next steps:"
    echo "  1. Run: docker run -p 8000:8000 face-quality-assessment:$IMAGE_TAG"
    echo "  2. Or: docker-compose up -d"
    echo "  3. Test: curl http://localhost:8000/health"
    
else
    log_section "Build Failed!"
    
    log_error "Build failed. Troubleshooting tips:"
    echo ""
    echo "1. Check Docker resources:"
    echo "   - Ensure at least 4GB RAM available"
    echo "   - Ensure at least 10GB disk space"
    echo ""
    echo "2. Try alternative build:"
    echo "   ./scripts/build.sh mediapipe    # Fastest, most reliable"
    echo ""
    echo "3. Clean Docker cache:"
    echo "   docker system prune -a"
    echo ""
    echo "4. Check detailed logs:"
    echo "   docker build --progress=plain -f $DOCKERFILE -t face-quality-assessment:$IMAGE_TAG ."
    echo ""
    echo "5. See DOCKER_BUILD_FIX.md for more solutions"
    
    exit 1
fi

log_section "Build Complete"

# Optional: Test the image
read -p "Do you want to test the image now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Starting test container..."
    
    # Stop any existing container
    docker stop face-quality-test 2>/dev/null || true
    docker rm face-quality-test 2>/dev/null || true
    
    # Run test container
    docker run -d --name face-quality-test -p 8000:8000 face-quality-assessment:$IMAGE_TAG
    
    log_info "Waiting for service to start..."
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_info "✓ Health check passed!"
        log_info "Service is running at http://localhost:8000"
        log_info "API docs at http://localhost:8000/docs"
        echo ""
        log_info "To stop test container: docker stop face-quality-test"
    else
        log_error "✗ Health check failed"
        log_info "Check logs: docker logs face-quality-test"
    fi
fi

exit 0
