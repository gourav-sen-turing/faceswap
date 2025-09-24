#!/bin/bash

# Face Quality Assessment Service Setup Script

set -e

echo "========================================="
echo "Face Quality Assessment Service Setup"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    log_info "Docker is installed: $(docker --version)"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    log_info "Docker Compose is installed: $(docker-compose --version)"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_warn "Python 3 is not installed. Some features may not work."
    else
        log_info "Python is installed: $(python3 --version)"
    fi
}

# Create directories
create_directories() {
    log_info "Creating necessary directories..."
    mkdir -p logs uploads results cache models
    mkdir -p nginx/ssl
    mkdir -p prometheus grafana/provisioning/{dashboards,datasources}
    log_info "Directories created successfully"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    if [ -f .env ]; then
        log_warn ".env file already exists. Skipping..."
    else
        log_info "Creating .env from template..."
        cp .env.template .env
        
        # Generate secure keys
        if command -v python3 &> /dev/null; then
            log_info "Generating secure API keys..."
            API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
            SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
            
            # Update .env file
            sed -i "s/your-super-secret-api-key-change-this/$API_KEY/" .env
            sed -i "s/your-jwt-secret-key-min-32-chars-change-this/$SECRET_KEY/" .env
            
            log_info "API keys generated successfully"
        else
            log_warn "Python not available. Please manually update API keys in .env"
        fi
    fi
}

# Download models
download_models() {
    log_info "Downloading required models..."
    
    # Download dlib shape predictor
    if [ ! -f models/shape_predictor_68_face_landmarks.dat ]; then
        log_info "Downloading dlib shape predictor..."
        wget -q --show-progress http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2 -P models/
        bunzip2 models/shape_predictor_68_face_landmarks.dat.bz2
        log_info "Shape predictor downloaded successfully"
    else
        log_info "Shape predictor already exists"
    fi
    
    # Optional: Download super-resolution models
    # if [ ! -f models/RealESRGAN_x4plus.pth ]; then
    #     log_info "Downloading RealESRGAN model..."
    #     wget -q --show-progress https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth -P models/
    #     log_info "RealESRGAN model downloaded successfully"
    # fi
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    docker-compose build
    log_info "Docker images built successfully"
}

# Start services
start_services() {
    log_info "Starting services..."
    docker-compose up -d
    log_info "Services started successfully"
}

# Wait for services
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost/health > /dev/null 2>&1; then
            log_info "Services are ready!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    log_error "Services did not start within expected time"
    return 1
}

# Print summary
print_summary() {
    echo ""
    echo "========================================="
    echo "Setup completed successfully!"
    echo "========================================="
    echo ""
    echo "Service URLs:"
    echo "  - API:        http://localhost/api/v1"
    echo "  - Docs:       http://localhost/docs"
    echo "  - Health:     http://localhost/health"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana:    http://localhost:3000"
    echo ""
    echo "Configuration:"
    echo "  - API Key: Check .env file"
    echo "  - Logs:    ./logs/"
    echo "  - Models:  ./models/"
    echo ""
    echo "Next steps:"
    echo "  1. Review and update .env file"
    echo "  2. Test the API: curl http://localhost/health"
    echo "  3. View documentation: open http://localhost/docs"
    echo ""
}

# Main execution
main() {
    check_prerequisites
    create_directories
    setup_environment
    download_models
    build_images
    start_services
    
    if wait_for_services; then
        print_summary
    else
        log_error "Setup completed with errors. Check logs: docker-compose logs"
        exit 1
    fi
}

# Run main
main
