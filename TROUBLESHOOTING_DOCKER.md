# Docker Build Troubleshooting Guide

## 🔴 Common Issue: dlib CMake Compatibility Error

### Error Message:
```
CMake Error at /tmp/pip-install-juhll_mu/dlib_571ddaea8a5e4c8f8ce96d4a8ed4123d/dlib/external/pybind11/CMakeLists.txt:8 (cmake_minimum_required):
Compatibility with CMake < 3.5 has been removed from CMake.
```

### Root Cause:
dlib requires compilation with CMake, but system CMake version conflicts with pybind11 requirements.

---

## ✅ SOLUTION 1: Quick Fix (Recommended - 5 minutes)

Use the pre-configured fixed Dockerfile that uses MediaPipe instead of dlib.

### Steps:

```bash
# 1. Run the automated fix script
chmod +x scripts/fix_docker_build.sh
./scripts/fix_docker_build.sh

# 2. Start services
docker-compose up -d

# 3. Verify
curl http://localhost/health
```

**Done!** This solution:
- ✅ Uses MediaPipe (no compilation needed)
- ✅ Faster builds (2-3 min vs 10-15 min)
- ✅ Better face detection (468 landmarks)
- ✅ All features maintained

---

## ✅ SOLUTION 2: Manual Fix

### Option A: Use Dockerfile.fixed (MediaPipe)

```bash
# 1. Update docker-compose.yml
sed -i 's/dockerfile: Dockerfile$/dockerfile: Dockerfile.fixed/' docker-compose.yml

# 2. Use fixed requirements
cp requirements-fixed.txt requirements.txt

# 3. Switch to MediaPipe
cp app/services/quality_assessor_mediapipe.py app/services/quality_assessor.py

# 4. Build
docker-compose build --no-cache
docker-compose up -d
```

### Option B: Upgrade CMake in Dockerfile

If you specifically need dlib:

```dockerfile
# Add to Dockerfile before pip install
RUN wget -q https://github.com/Kitware/CMake/releases/download/v3.27.7/cmake-3.27.7-linux-x86_64.sh && \
    chmod +x cmake-3.27.7-linux-x86_64.sh && \
    ./cmake-3.27.7-linux-x86_64.sh --skip-license --prefix=/usr/local && \
    rm cmake-3.27.7-linux-x86_64.sh
```

Then rebuild:
```bash
docker-compose build --no-cache
```

### Option C: Use Pre-compiled dlib Wheel

```bash
# Update requirements.txt
sed -i 's/dlib==19.24.2/dlib-binary==19.24.2/' requirements.txt

# Rebuild
docker-compose build --no-cache
```

---

## 🐛 Other Common Issues

### Issue 1: "No module named 'mediapipe'"

**Cause:** MediaPipe not installed

**Fix:**
```bash
# Verify requirements-fixed.txt is being used
docker-compose build --no-cache

# Or manually install
docker-compose exec face-quality-api pip install mediapipe==0.10.8
```

### Issue 2: Build Timeout

**Cause:** Long compilation time

**Fix:**
```bash
# Use Dockerfile.fixed (no compilation)
docker build -f Dockerfile.fixed -t face-quality-assessment .

# Or increase timeout
export COMPOSE_HTTP_TIMEOUT=300
docker-compose build
```

### Issue 3: Out of Memory During Build

**Cause:** Insufficient Docker memory

**Fix:**
```bash
# Increase Docker memory (Docker Desktop)
# Settings > Resources > Memory > 8GB+

# Or use multi-stage build
docker build -f Dockerfile -t face-quality-assessment .
```

### Issue 4: "Error loading shared library"

**Cause:** Missing runtime dependencies

**Fix:**
```bash
# Install missing libraries in Dockerfile
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1
```

### Issue 5: Face Detection Not Working

**Cause:** Wrong quality assessor version

**Fix:**
```bash
# Ensure MediaPipe version is active
docker-compose exec face-quality-api python -c "
from app.services.quality_assessor import FaceQualityAssessor
assessor = FaceQualityAssessor()
print('Face detection initialized successfully')
"
```

### Issue 6: GPU Not Detected

**Cause:** NVIDIA Docker runtime not configured

**Fix:**
```bash
# Install NVIDIA Docker runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Test
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## 🔍 Debugging Steps

### Step 1: Check Build Logs
```bash
docker-compose build --no-cache 2>&1 | tee build.log
cat build.log | grep -i error
```

### Step 2: Test Specific Package
```bash
# Test MediaPipe installation
docker run --rm python:3.10-slim bash -c "
    pip install mediapipe==0.10.8 && 
    python -c 'import mediapipe; print(mediapipe.__version__)'
"
```

### Step 3: Verify System Dependencies
```bash
docker run --rm -it face-quality-assessment:latest bash
# Inside container:
python -c "import cv2, numpy, mediapipe; print('All imports OK')"
```

### Step 4: Check Docker Resources
```bash
docker system df
docker system prune -a  # Clean up if needed
```

---

## 📋 Verification Checklist

After fixing, verify:

- [ ] Docker build completes without errors
- [ ] Services start successfully: `docker-compose ps`
- [ ] Health check passes: `curl http://localhost/health`
- [ ] Face detection works: `python scripts/test_api.py`
- [ ] API responds: `curl http://localhost/docs`

---

## 🎯 Quick Commands Reference

### Build Commands
```bash
# Use fixed Dockerfile (recommended)
docker-compose build --no-cache

# Build specific service
docker-compose build face-quality-api

# Build with verbose output
docker-compose build --no-cache --progress=plain

# Build CPU version
docker build -f Dockerfile.cpu -t face-quality:cpu .
```

### Debug Commands
```bash
# Check logs
docker-compose logs -f face-quality-api

# Enter container
docker-compose exec face-quality-api bash

# Test imports
docker-compose exec face-quality-api python -c "import mediapipe, cv2"

# Check installed packages
docker-compose exec face-quality-api pip list
```

### Cleanup Commands
```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi face-quality-assessment:latest

# Full cleanup
docker system prune -a
docker volume prune
```

---

## 🆘 Still Having Issues?

### Collect Debug Information

```bash
# 1. System info
docker version
docker-compose version
uname -a

# 2. Build log
docker-compose build --no-cache 2>&1 | tee debug_build.log

# 3. Runtime log
docker-compose logs > debug_runtime.log

# 4. Package versions
docker-compose exec face-quality-api pip freeze > debug_packages.txt
```

### Contact Support

Send the following information to support@facequality.ai:

1. Error message (full text)
2. Build logs (`debug_build.log`)
3. Runtime logs (`debug_runtime.log`)
4. System information
5. Dockerfile being used

---

## ✅ Success Indicators

You'll know it's working when:

```bash
# 1. Build succeeds
docker-compose build
# ✓ No errors, completes in 2-5 minutes

# 2. Services start
docker-compose up -d
docker-compose ps
# ✓ All services show "Up" status

# 3. Health check passes
curl http://localhost/health
# ✓ Returns {"status":"healthy",...}

# 4. Face detection works
curl -X POST http://localhost/api/v1/assess/upload \
  -H "X-API-Key: your-key" \
  -F "file=@test.jpg"
# ✓ Returns quality assessment results
```

---

## 📚 Additional Resources

- **DOCKER_BUILD_FIX.md** - Detailed fix guide
- **README.md** - Main documentation
- **DEPLOYMENT.md** - Production deployment
- **scripts/fix_docker_build.sh** - Automated fix script

---

## 🎉 Fixed!

Once resolved, you'll have:
- ✅ Fast builds (2-3 minutes)
- ✅ Reliable deployment
- ✅ Better face detection (MediaPipe)
- ✅ All quality assessment features
- ✅ Production-ready service

**Happy Deploying!** 🚀
