# Face Quality Assessment Service - Complete Setup Instructions

## 📋 Table of Contents
1. [System Requirements](#system-requirements)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 20 GB SSD
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows 10/11

### Recommended for Production
- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **GPU**: NVIDIA GPU with 6+ GB VRAM (Tesla T4, V100, A100)
- **Storage**: 50+ GB NVMe SSD
- **OS**: Ubuntu 22.04 LTS

### Software Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.9-3.11 (for local development)
- Git
- NVIDIA Docker Runtime (for GPU support)
- CUDA 12.1+ (for GPU)

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd face_quality_service

# 2. Run automated setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Verify installation
curl http://localhost/health
```

### Option 2: Manual Setup

```bash
# 1. Clone and enter directory
git clone <repository-url>
cd face_quality_service

# 2. Create environment file
cp .env.template .env

# 3. Generate secure API keys
python3 -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))" >> .env
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env

# 4. Create directories
mkdir -p logs uploads results cache models nginx/ssl

# 5. Download models
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
mv shape_predictor_68_face_landmarks.dat models/

# 6. Build and start services
docker-compose up -d

# 7. Wait for services to be ready (30-60 seconds)
sleep 30

# 8. Verify
curl http://localhost/health
```

### Option 3: Using Makefile

```bash
# 1. Clone repository
git clone <repository-url>
cd face_quality_service

# 2. Initialize environment
make init-env

# 3. Download models
make download-models

# 4. Setup and start
make setup
make start

# 5. Verify
make health
```

## Detailed Setup

### Step 1: Install Docker

#### Ubuntu/Debian
```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up stable repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
sudo docker run hello-world
```

#### macOS
```bash
# Install using Homebrew
brew install --cask docker

# Or download from https://www.docker.com/products/docker-desktop
```

#### Windows
Download and install Docker Desktop from https://www.docker.com/products/docker-desktop

### Step 2: Install NVIDIA Docker (For GPU Support)

```bash
# Add NVIDIA Docker repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install NVIDIA Docker
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart Docker
sudo systemctl restart docker

# Test GPU support
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Step 3: Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd face_quality_service

# Copy environment template
cp .env.template .env

# Edit configuration
nano .env
```

### Step 4: Configure Environment Variables

Edit `.env` file with your settings:

```bash
# Required Configuration
ENVIRONMENT=production
API_KEY=<generate-secure-key>
SECRET_KEY=<generate-secure-key>

# Optional: Generate keys
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# GPU Configuration
GPU_ENABLED=true
CUDA_VISIBLE_DEVICES=0

# Database Configuration
MONGO_USERNAME=admin
MONGO_PASSWORD=<secure-password>
REDIS_PASSWORD=<secure-password>

# Performance Tuning
WORKERS=4
BATCH_SIZE=8
```

### Step 5: Download Models

```bash
# Create models directory
mkdir -p models

# Download dlib face landmark predictor (required)
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
mv shape_predictor_68_face_landmarks.dat models/

# Optional: Download super-resolution models
# wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
# mv RealESRGAN_x4plus.pth models/
```

### Step 6: Build and Deploy

```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 7: Verify Installation

```bash
# Health check
curl http://localhost/health

# Test API
curl -X POST http://localhost/api/v1/assess \
  -H "X-API-Key: $(grep API_KEY .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/face.jpg"}'

# Check Prometheus
curl http://localhost:9090

# Check Grafana
curl http://localhost:3000
```

## Configuration

### Quality Thresholds

Customize quality thresholds in `.env`:

```bash
# Blur Detection (Laplacian variance)
BLUR_THRESHOLD_MIN=100.0      # Below this is blurry
BLUR_THRESHOLD_REJECT=50.0    # Below this is rejected

# Pose Estimation (degrees)
POSE_YAW_MAX=30.0             # Maximum yaw angle
POSE_PITCH_MAX=25.0           # Maximum pitch angle
POSE_ROLL_MAX=20.0            # Maximum roll angle

# Lighting (0-255 scale)
LIGHTING_MIN=40.0             # Minimum brightness
LIGHTING_MAX=220.0            # Maximum brightness
LIGHTING_CONTRAST_MIN=30.0    # Minimum contrast

# Resolution (pixels)
RESOLUTION_MIN_WIDTH=224
RESOLUTION_MIN_HEIGHT=224
RESOLUTION_RECOMMENDED_WIDTH=512
RESOLUTION_RECOMMENDED_HEIGHT=512

# Quality Scores (0-1 scale)
QUALITY_SCORE_ACCEPT=0.75     # Accept if score >= this
QUALITY_SCORE_ENHANCE=0.50    # Enhance if score >= this
QUALITY_SCORE_REJECT=0.30     # Reject if score < this
```

### Scaling Configuration

```bash
# Horizontal Scaling
docker-compose up -d --scale face-quality-worker-1=5 --scale face-quality-worker-2=5

# Or edit docker-compose.yml:
services:
  face-quality-worker-1:
    deploy:
      replicas: 5
```

### SSL/TLS Configuration

```bash
# Generate self-signed certificate
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem

# For production, use Let's Encrypt
certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# Update nginx.conf to enable HTTPS
```

## Testing

### API Testing

```bash
# Using provided test script
python3 scripts/test_api.py

# Or using Makefile
make test

# Manual testing
curl -X POST http://localhost/api/v1/assess/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@test_image.jpg"
```

### Unit Tests

```bash
# Run pytest
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html

# Using Makefile
make test-unit
make test-coverage
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host http://localhost
```

### Performance Benchmarking

```bash
# Using Makefile
make benchmark

# Or manually
for i in {1..100}; do
  curl -s -w "Time: %{time_total}s\n" -o /dev/null \
    -X POST http://localhost/api/v1/assess \
    -H "X-API-Key: your-api-key" \
    -H "Content-Type: application/json" \
    -d '{"image_base64":"test"}'
done
```

## Production Deployment

### Pre-Production Checklist

- [ ] Update `.env` with production values
- [ ] Generate secure API keys and secrets
- [ ] Configure SSL/TLS certificates
- [ ] Set up database authentication
- [ ] Enable rate limiting
- [ ] Configure monitoring and alerting
- [ ] Set up backup procedures
- [ ] Review security settings
- [ ] Load test the system
- [ ] Prepare rollback plan

### Deployment Steps

```bash
# 1. Update configuration
nano .env

# 2. Pull latest images
docker-compose pull

# 3. Build production images
docker-compose build --no-cache

# 4. Stop current services
docker-compose down

# 5. Start with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 6. Verify deployment
curl https://your-domain.com/health

# 7. Monitor logs
docker-compose logs -f
```

### Kubernetes Deployment

```bash
# 1. Create namespace
kubectl create namespace face-quality

# 2. Create secrets
kubectl create secret generic face-quality-secrets \
  --from-literal=api-key=your-api-key \
  --from-literal=secret-key=your-secret-key \
  -n face-quality

# 3. Apply configurations
kubectl apply -f k8s/

# 4. Verify deployment
kubectl get pods -n face-quality

# 5. Expose service
kubectl port-forward svc/face-quality-service 8000:80 -n face-quality
```

### Monitoring Setup

```bash
# Access Prometheus
http://localhost:9090

# Access Grafana
http://localhost:3000
Username: admin
Password: admin (change immediately)

# Import dashboards
# Navigate to Dashboards -> Import
# Upload dashboards from grafana/dashboards/
```

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

```bash
# Check logs
docker-compose logs -f

# Check disk space
df -h

# Check memory
free -m

# Restart services
docker-compose restart
```

#### 2. GPU Not Detected

```bash
# Verify NVIDIA driver
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Reinstall NVIDIA Docker
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

#### 3. Out of Memory

```bash
# Limit container memory in docker-compose.yml
services:
  face-quality-api:
    deploy:
      resources:
        limits:
          memory: 8G

# Clear cache
rm -rf cache/*
docker system prune -a
```

#### 4. Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000

# Kill process or change port in .env
API_PORT=8001
```

#### 5. Model Download Fails

```bash
# Manual download
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
mv shape_predictor_68_face_landmarks.dat models/

# Or use alternative mirror
```

#### 6. Authentication Errors

```bash
# Verify API key in .env
grep API_KEY .env

# Test with correct key
curl -H "X-API-Key: $(grep API_KEY .env | cut -d= -f2)" http://localhost/api/v1/metrics
```

### Getting Help

- **Documentation**: Check README.md and DEPLOYMENT.md
- **Logs**: `docker-compose logs -f face-quality-api`
- **GitHub Issues**: Open an issue with logs and configuration
- **Email Support**: support@facequality.ai

### Debug Mode

```bash
# Enable debug mode in .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart

# View detailed logs
docker-compose logs -f
```

## Maintenance

### Backup

```bash
# Using Makefile
make backup

# Manual backup
mkdir -p backups
docker-compose exec -T mongodb mongodump --out /backup
docker cp $(docker-compose ps -q mongodb):/backup ./backups/mongodb-$(date +%Y%m%d)
tar -czf backups/models-$(date +%Y%m%d).tar.gz models/
```

### Updates

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d

# Or using Makefile
make update
```

### Monitoring

```bash
# Check service status
docker-compose ps

# View resource usage
docker stats

# Check API metrics
curl http://localhost/api/v1/metrics

# View Prometheus metrics
curl http://localhost/metrics
```

## Next Steps

After successful setup:

1. **Review Configuration**: Ensure all settings match your requirements
2. **Test API**: Run comprehensive tests using provided scripts
3. **Set Up Monitoring**: Configure Grafana dashboards and alerts
4. **Security Audit**: Review security settings and authentication
5. **Load Testing**: Perform load testing to determine capacity
6. **Documentation**: Review API documentation at `/docs`
7. **Integration**: Integrate with your application using provided examples

## Support

For additional help:
- 📖 Documentation: Check all `.md` files in the repository
- 🐛 Issues: https://github.com/facequality/assessment/issues
- 📧 Email: support@facequality.ai
- 💬 Community: Join our Discord/Slack channel

---

**Congratulations!** Your Face Quality Assessment Service is now ready for use. 🎉
