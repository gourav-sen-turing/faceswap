# Face Quality Assessment Microservice

Enterprise-grade face quality assessment microservice using OpenCV, dlib, and deep learning models for comprehensive quality analysis including blur detection, pose estimation, lighting analysis, resolution assessment, and super-resolution enhancement.

## 🚀 Features

- **Comprehensive Quality Assessment**
  - Blur detection using Laplacian variance and gradient magnitude
  - Head pose estimation (yaw, pitch, roll)
  - Lighting analysis (brightness, contrast, histogram uniformity)
  - Resolution adequacy assessment
  - Overall quality scoring with configurable thresholds

- **Image Enhancement**
  - Super-resolution upscaling
  - Face-specific restoration
  - Automatic quality enhancement
  - Denoising and sharpening

- **Quality Decision Engine**
  - Accept: High-quality images ready for use
  - Enhance: Medium-quality images requiring enhancement
  - Reject: Low-quality images unsuitable for processing
  - Customizable threshold configuration

- **Enterprise Features**
  - RESTful API with FastAPI
  - JWT and API key authentication
  - Horizontal scaling with load balancing
  - GPU optimization
  - Prometheus metrics and Grafana dashboards
  - Health monitoring and readiness probes
  - Rate limiting and CORS support
  - Structured logging
  - Batch processing support

## 📋 Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.9+ (for local development)
- NVIDIA GPU with CUDA 12.1+ (optional, for GPU acceleration)
- 8GB+ RAM
- 10GB+ disk space

## 🔧 Installation

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd face_quality_service
```

2. **Configure environment**
```bash
cp .env.template .env
# Edit .env with your configuration
nano .env
```

3. **Build and run with Docker Compose**
```bash
# Quick start (uses MediaPipe - no dlib compilation issues)
docker-compose up -d

# Or use the build script
./scripts/build.sh mediapipe  # Fastest, most reliable
./scripts/build.sh gpu        # Full GPU with dlib
./scripts/build.sh cpu        # CPU-optimized

# Then start services
docker-compose up -d
```

4. **Verify deployment**
```bash
curl http://localhost/health
```

**Note:** If you encounter dlib build errors, see [DOCKER_BUILD_FIX.md](DOCKER_BUILD_FIX.md) for solutions. We provide 3 Dockerfiles:
- `Dockerfile.mediapipe` - Fast, reliable (default)
- `Dockerfile` - GPU with updated CMake
- `Dockerfile.cpu` - CPU optimized

### Option 2: Local Development

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Download models**
```bash
mkdir -p models
# Download dlib shape predictor
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
mv shape_predictor_68_face_landmarks.dat models/
```

4. **Run the service**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Documentation

### Base URL
- Local: `http://localhost:8000`
- With NGINX: `http://localhost/api/v1`

### Authentication

**API Key Authentication:**
```bash
curl -H "X-API-Key: your-api-key" http://localhost/api/v1/assess
```

**JWT Authentication:**
```bash
curl -H "Authorization: Bearer your-jwt-token" http://localhost/api/v1/assess
```

### Endpoints

#### 1. Assess Face Quality
```bash
POST /api/v1/assess
```

**Request:**
```json
{
  "image_base64": "base64_encoded_image",
  "return_enhanced": false,
  "custom_thresholds": {
    "accept": 0.75,
    "enhance": 0.50,
    "reject": 0.30
  }
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "status": "success",
  "assessment": {
    "overall_score": 0.85,
    "decision": "accept",
    "blur_metrics": {
      "laplacian_variance": 120.5,
      "gradient_magnitude": 45.2,
      "is_blurry": false,
      "blur_score": 0.95,
      "recommendation": "Sharp image, no action needed"
    },
    "pose_metrics": {
      "yaw": 5.2,
      "pitch": -3.1,
      "roll": 1.5,
      "is_frontal": true,
      "pose_score": 0.92,
      "recommendation": "Frontal pose, ideal for processing"
    },
    "lighting_metrics": {
      "brightness": 128.5,
      "contrast": 45.3,
      "histogram_uniformity": 5.2,
      "is_well_lit": true,
      "lighting_score": 0.88,
      "recommendation": "Good lighting conditions"
    },
    "resolution_metrics": {
      "width": 1920,
      "height": 1080,
      "face_width": 512,
      "face_height": 512,
      "is_adequate": true,
      "resolution_score": 1.0,
      "recommendation": "Excellent resolution"
    },
    "face_detection": {
      "bbox": [100, 150, 512, 512],
      "confidence": 0.95,
      "landmarks": [[x, y], ...]
    },
    "recommendations": ["Image quality is excellent"],
    "processing_time_ms": 45.2
  },
  "enhanced_image_base64": null,
  "metadata": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 2. Batch Assessment
```bash
POST /api/v1/assess/batch
```

**Request:**
```json
{
  "images": [
    {"image_base64": "..."},
    {"image_url": "https://..."}
  ],
  "parallel": true,
  "max_workers": 4
}
```

#### 3. Image Enhancement
```bash
POST /api/v1/enhance
```

**Request:**
```json
{
  "image_base64": "base64_encoded_image",
  "scale_factor": 4,
  "enhance_face": true,
  "denoise": true
}
```

#### 4. Upload File Assessment
```bash
POST /api/v1/assess/upload
```

**cURL Example:**
```bash
curl -X POST http://localhost/api/v1/assess/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@face.jpg" \
  -F "return_enhanced=false"
```

#### 5. Health Check
```bash
GET /health
```

#### 6. Metrics
```bash
GET /metrics
GET /api/v1/metrics
```

## 🔒 Security Configuration

### API Key Setup
```bash
# Generate secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in .env file
API_KEY=your-generated-api-key
SECRET_KEY=your-jwt-secret-key-min-32-chars
```

### JWT Token Generation
```python
from app.core.security import create_access_token
from datetime import timedelta

token = create_access_token(
    data={"username": "user@example.com"},
    expires_delta=timedelta(minutes=30)
)
```

## ⚙️ Configuration

### Quality Thresholds

Edit `.env` file to configure quality thresholds:

```bash
# Blur Detection
BLUR_THRESHOLD_MIN=100.0
BLUR_THRESHOLD_REJECT=50.0

# Pose Estimation (degrees)
POSE_YAW_MAX=30.0
POSE_PITCH_MAX=25.0
POSE_ROLL_MAX=20.0

# Lighting Analysis
LIGHTING_MIN=40.0
LIGHTING_MAX=220.0
LIGHTING_CONTRAST_MIN=30.0

# Resolution
RESOLUTION_MIN_WIDTH=224
RESOLUTION_MIN_HEIGHT=224

# Quality Scores
QUALITY_SCORE_ACCEPT=0.75
QUALITY_SCORE_ENHANCE=0.50
QUALITY_SCORE_REJECT=0.30
```

### GPU Configuration
```bash
GPU_ENABLED=true
CUDA_VISIBLE_DEVICES=0
GPU_MEMORY_FRACTION=0.8
ENABLE_MIXED_PRECISION=true
```

### Scaling Configuration
```bash
WORKERS=4
ASYNC_WORKERS=4
BATCH_SIZE=8
```

## 📊 Monitoring

### Prometheus Metrics
- Request count and duration
- Quality distribution (accept/enhance/reject)
- Processing time statistics
- Error rates

Access: `http://localhost:9090`

### Grafana Dashboards
- Service performance overview
- Quality metrics visualization
- Resource utilization
- Error tracking

Access: `http://localhost:3000`
- Username: admin
- Password: admin (change in production)

## 🚀 Deployment

### Production Deployment

1. **Update configuration**
```bash
# Set production values in .env
ENVIRONMENT=production
DEBUG=false
API_KEY=<secure-production-key>
SECRET_KEY=<secure-jwt-secret>
```

2. **Enable SSL/TLS**
```bash
# Configure SSL certificates in nginx/nginx.conf
# Uncomment HTTPS server block
```

3. **Deploy with Docker**
```bash
docker-compose up -d --scale face-quality-worker-1=3 --scale face-quality-worker-2=3
```

4. **Configure monitoring**
```bash
# Set up alerts in Prometheus
# Configure Grafana dashboards
```

### Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests:
```bash
kubectl apply -f k8s/
```

## 🧪 Testing

### Run tests
```bash
pytest tests/ -v --cov=app
```

### Load testing
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host http://localhost
```

## 📈 Performance

### Benchmarks
- Single image assessment: ~50-100ms (GPU)
- Single image assessment: ~200-500ms (CPU)
- Batch processing (8 images): ~300-600ms (GPU)
- Super-resolution enhancement: ~500-1000ms (GPU)

### Optimization Tips
1. Enable GPU acceleration
2. Use batch processing for multiple images
3. Enable result caching
4. Configure appropriate worker counts
5. Use NGINX load balancing

## 🐛 Troubleshooting

### Common Issues

**1. No face detected**
- Ensure image contains a clear face
- Check face detection confidence threshold
- Verify image quality and lighting

**2. GPU not available**
- Install NVIDIA drivers and CUDA
- Set GPU_ENABLED=true in .env
- Check Docker GPU configuration

**3. Model loading errors**
- Download required models to models/ directory
- Check model paths in configuration
- Verify disk space

**4. Authentication errors**
- Verify API key in request headers
- Check JWT token expiration
- Ensure security settings in .env

## 📝 API Examples

### Python Client
```python
import requests
import base64

# Load image
with open("face.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

# Assess quality
response = requests.post(
    "http://localhost/api/v1/assess",
    json={"image_base64": image_base64, "return_enhanced": True},
    headers={"X-API-Key": "your-api-key"}
)

result = response.json()
print(f"Quality Score: {result['assessment']['overall_score']}")
print(f"Decision: {result['assessment']['decision']}")
```

### JavaScript Client
```javascript
const fs = require('fs');
const axios = require('axios');

const imageBase64 = fs.readFileSync('face.jpg', 'base64');

axios.post('http://localhost/api/v1/assess', {
    image_base64: imageBase64,
    return_enhanced: true
}, {
    headers: {'X-API-Key': 'your-api-key'}
})
.then(response => {
    console.log('Quality Score:', response.data.assessment.overall_score);
    console.log('Decision:', response.data.assessment.decision);
})
.catch(error => console.error(error));
```

### cURL Examples
```bash
# Assess from file
curl -X POST http://localhost/api/v1/assess/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@face.jpg"

# Assess from URL
curl -X POST http://localhost/api/v1/assess \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/face.jpg"}'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- Documentation: `/docs` (Swagger UI)
- API Reference: `/redoc` (ReDoc)
- Issues: GitHub Issues
- Email: support@facequality.ai

## 🔄 Version History

### v1.0.0 (2024-01-01)
- Initial release
- Blur detection
- Pose estimation
- Lighting analysis
- Resolution assessment
- Super-resolution enhancement
- Enterprise security
- Monitoring and metrics

## 🙏 Acknowledgments

- OpenCV for computer vision
- dlib for face detection
- FastAPI for web framework
- PyTorch for deep learning
- RealESRGAN for super-resolution
