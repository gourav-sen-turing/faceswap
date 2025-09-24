# Multi-stage GPU-optimized Dockerfile for Face Quality Assessment Service
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04 AS builder

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:$PATH \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-dev \
    python3-pip \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    pkg-config \
    libopencv-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libboost-all-dev \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libatlas-base-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Upgrade CMake to version 3.20+ to fix dlib compatibility
RUN wget -q https://github.com/Kitware/CMake/releases/download/v3.27.7/cmake-3.27.7-linux-x86_64.sh \
    && chmod +x cmake-3.27.7-linux-x86_64.sh \
    && ./cmake-3.27.7-linux-x86_64.sh --skip-license --prefix=/usr/local \
    && rm cmake-3.27.7-linux-x86_64.sh \
    && cmake --version

# Set working directory for builder
WORKDIR /build

# Copy requirements
COPY requirements.txt .

# Install Python dependencies with proper build order
RUN pip3 install --upgrade pip setuptools wheel && \
    # Install numpy first (required by many packages)
    pip3 install numpy==1.24.3 && \
    # Install dlib with proper build flags
    pip3 install dlib==19.24.2 --verbose && \
    # Install remaining dependencies
    pip3 install --no-cache-dir -r requirements.txt

# Runtime stage
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:$PATH \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    libopencv-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libopenblas0 \
    liblapack3 \
    libx11-6 \
    libgtk-3-0 \
    libavcodec58 \
    libavformat58 \
    libswscale5 \
    libatlas-base-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/logs /app/cache /app/uploads /app/results /app/models && \
    chown -R appuser:appuser /app

# Download pre-trained models
RUN python3 -c "import cv2; cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')" || true

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
