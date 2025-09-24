# Enterprise Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Production Deployment](#production-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Security Hardening](#security-hardening)
7. [Monitoring Setup](#monitoring-setup)
8. [Backup and Recovery](#backup-and-recovery)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Hardware Requirements
- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 8GB minimum (16GB+ recommended)
- **GPU**: NVIDIA GPU with 6GB+ VRAM (optional but recommended)
- **Storage**: 20GB+ SSD

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker Runtime (for GPU support)
- Python 3.9-3.11
- CUDA 12.1+ (for GPU)

## Quick Start

### 1. Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd face_quality_service

# Copy environment template
cp .env.template .env

# Generate secure keys
python -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env

# Create necessary directories
mkdir -p logs uploads results cache models
```

### 2. Download Models
```bash
# Download dlib face landmark predictor
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
mv shape_predictor_68_face_landmarks.dat models/

# Optional: Download super-resolution models
# wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
# mv RealESRGAN_x4plus.pth models/
```

### 3. Deploy Services
```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f face-quality-api
```

### 4. Verify Deployment
```bash
# Health check
curl http://localhost/health

# Test API
curl -X POST http://localhost/api/v1/assess \
  -H "X-API-Key: $(grep API_KEY .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/face.jpg"}'
```

## Production Deployment

### 1. Environment Configuration

**Edit `.env` for production:**
```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security
API_KEY=<use-generated-secure-key>
SECRET_KEY=<use-generated-secure-key>
ENABLE_API_KEY_AUTH=true
ENABLE_JWT_AUTH=true

# Database
MONGO_USERNAME=admin
MONGO_PASSWORD=<secure-password>
REDIS_PASSWORD=<secure-password>

# Performance
WORKERS=8
ASYNC_WORKERS=8
BATCH_SIZE=16

# GPU
GPU_ENABLED=true
CUDA_VISIBLE_DEVICES=0,1  # Multiple GPUs

# Rate Limiting
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=5000
```

### 2. SSL/TLS Configuration

**Generate SSL certificates:**
```bash
# Self-signed (for testing)
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem

# Production: Use Let's Encrypt
certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

**Update nginx.conf:**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... rest of configuration
}
```

### 3. Database Setup

**MongoDB Initialization:**
```bash
# Connect to MongoDB
docker-compose exec mongodb mongosh -u admin -p <password>

# Create database and user
use face_quality_db
db.createUser({
  user: "facequalityuser",
  pwd: "<secure-password>",
  roles: [{role: "readWrite", db: "face_quality_db"}]
})

# Create indexes
db.assessments.createIndex({"timestamp": -1})
db.assessments.createIndex({"decision": 1})
```

**Redis Configuration:**
```bash
# Update Redis password in docker-compose.yml
redis:
  command: redis-server --requirepass <secure-password> --appendonly yes
```

### 4. Horizontal Scaling

**Scale workers:**
```bash
# Scale to 5 instances of each worker
docker-compose up -d --scale face-quality-worker-1=5 --scale face-quality-worker-2=5

# Verify
docker-compose ps
```

**Load balancer configuration:**
```bash
# Update nginx upstream
upstream face_quality_backend {
    least_conn;
    server face-quality-api:8000 weight=5 max_fails=3 fail_timeout=30s;
    server face-quality-worker-1:8000 weight=3 max_fails=3 fail_timeout=30s;
    server face-quality-worker-2:8000 weight=3 max_fails=3 fail_timeout=30s;
    keepalive 64;
}
```

## Kubernetes Deployment

### 1. Create Namespace
```bash
kubectl create namespace face-quality
```

### 2. Create Secrets
```bash
# Create secret for API keys
kubectl create secret generic face-quality-secrets \
  --from-literal=api-key=<your-api-key> \
  --from-literal=secret-key=<your-secret-key> \
  --from-literal=mongo-password=<mongo-password> \
  --from-literal=redis-password=<redis-password> \
  -n face-quality

# Create TLS secret
kubectl create secret tls face-quality-tls \
  --cert=nginx/ssl/cert.pem \
  --key=nginx/ssl/key.pem \
  -n face-quality
```

### 3. Deploy ConfigMap
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: face-quality-config
  namespace: face-quality
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  WORKERS: "4"
  GPU_ENABLED: "true"
```

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Deploy Application
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: face-quality-api
  namespace: face-quality
spec:
  replicas: 3
  selector:
    matchLabels:
      app: face-quality-api
  template:
    metadata:
      labels:
        app: face-quality-api
    spec:
      containers:
      - name: api
        image: face-quality-assessment:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: face-quality-secrets
              key: api-key
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: 1
          limits:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: 1
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

```bash
kubectl apply -f k8s/deployment.yaml
```

### 5. Create Service
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: face-quality-service
  namespace: face-quality
spec:
  type: LoadBalancer
  selector:
    app: face-quality-api
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
```

```bash
kubectl apply -f k8s/service.yaml
```

### 6. Configure Ingress
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: face-quality-ingress
  namespace: face-quality
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.your-domain.com
    secretName: face-quality-tls
  rules:
  - host: api.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: face-quality-service
            port:
              number: 80
```

```bash
kubectl apply -f k8s/ingress.yaml
```

## Cloud Deployment

### AWS Deployment

**1. ECR Setup:**
```bash
# Create ECR repository
aws ecr create-repository --repository-name face-quality-assessment

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t face-quality-assessment .
docker tag face-quality-assessment:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/face-quality-assessment:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/face-quality-assessment:latest
```

**2. ECS/EKS Deployment:**
```bash
# ECS Task Definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create ECS Service
aws ecs create-service --cluster face-quality-cluster \
  --service-name face-quality-service \
  --task-definition face-quality-task \
  --desired-count 3 \
  --launch-type FARGATE
```

### GCP Deployment

**1. Container Registry:**
```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push
docker build -t gcr.io/project-id/face-quality-assessment .
docker push gcr.io/project-id/face-quality-assessment
```

**2. GKE Deployment:**
```bash
# Create GKE cluster
gcloud container clusters create face-quality-cluster \
  --machine-type n1-standard-4 \
  --num-nodes 3 \
  --accelerator type=nvidia-tesla-t4,count=1

# Deploy
kubectl apply -f k8s/
```

### Azure Deployment

**1. Container Registry:**
```bash
# Create ACR
az acr create --resource-group face-quality-rg --name facequalityacr --sku Premium

# Login
az acr login --name facequalityacr

# Build and push
docker build -t facequalityacr.azurecr.io/face-quality-assessment .
docker push facequalityacr.azurecr.io/face-quality-assessment
```

**2. AKS Deployment:**
```bash
# Create AKS cluster
az aks create --resource-group face-quality-rg \
  --name face-quality-cluster \
  --node-count 3 \
  --node-vm-size Standard_NC6s_v3 \
  --enable-cluster-autoscaler

# Deploy
kubectl apply -f k8s/
```

## Security Hardening

### 1. Network Security
```bash
# Configure firewall rules
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 27017/tcp  # MongoDB
ufw deny 6379/tcp   # Redis
ufw enable
```

### 2. API Security
```bash
# Rotate API keys regularly
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env
API_KEY=<new-key>

# Restart services
docker-compose restart
```

### 3. Database Security
```bash
# Enable MongoDB authentication
# Enable Redis password
# Use encrypted connections
# Regular backups
```

### 4. Container Security
```bash
# Scan images for vulnerabilities
docker scan face-quality-assessment:latest

# Use minimal base images
# Run as non-root user
# Limit container capabilities
```

## Monitoring Setup

### 1. Prometheus Configuration
```bash
# Access Prometheus
open http://localhost:9090

# Create alerts
# Edit prometheus/alerts.yml
```

### 2. Grafana Dashboards
```bash
# Access Grafana
open http://localhost:3000

# Import dashboards
# Configure data sources
# Set up alerts
```

### 3. Application Logging
```bash
# Centralized logging with ELK
docker-compose -f docker-compose.elk.yml up -d

# View logs
open http://localhost:5601  # Kibana
```

### 4. Alerting
```bash
# Configure Slack webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Configure email alerts
# Set up PagerDuty integration
```

## Backup and Recovery

### 1. Database Backup
```bash
# MongoDB backup
docker-compose exec mongodb mongodump --out /backup

# Copy backup
docker cp mongodb:/backup ./backups/mongodb-$(date +%Y%m%d)

# Automated backups
0 2 * * * /path/to/backup-script.sh
```

### 2. Redis Backup
```bash
# Redis backup
docker-compose exec redis redis-cli BGSAVE

# Copy RDB file
docker cp redis:/data/dump.rdb ./backups/redis-$(date +%Y%m%d).rdb
```

### 3. Model Backup
```bash
# Backup models
tar -czf models-backup-$(date +%Y%m%d).tar.gz models/

# Upload to S3
aws s3 cp models-backup-$(date +%Y%m%d).tar.gz s3://backups/
```

### 4. Disaster Recovery
```bash
# Restore MongoDB
docker-compose exec mongodb mongorestore /backup

# Restore Redis
docker cp backups/redis-latest.rdb redis:/data/dump.rdb
docker-compose restart redis

# Restore models
tar -xzf models-backup-latest.tar.gz
```

## Troubleshooting

### Common Issues

**1. Service Won't Start**
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

**2. GPU Not Detected**
```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Reinstall NVIDIA Docker
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

**3. High Memory Usage**
```bash
# Limit container memory
docker-compose.yml:
  services:
    face-quality-api:
      deploy:
        resources:
          limits:
            memory: 8G

# Clear cache
docker-compose exec face-quality-api python -c "import shutil; shutil.rmtree('/app/cache')"
```

**4. Slow Performance**
```bash
# Check system resources
htop
nvidia-smi

# Optimize workers
WORKERS=8
BATCH_SIZE=16

# Enable caching
ENABLE_RESULT_CACHING=true
```

### Support Contacts
- Technical Support: support@facequality.ai
- Documentation: https://docs.facequality.ai
- GitHub Issues: https://github.com/facequality/issues
