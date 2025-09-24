"""
Main FastAPI application entry point.
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api import routes

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'face_quality_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'face_quality_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"GPU Enabled: {settings.gpu_enabled}")
    logger.info(f"Debug Mode: {settings.debug}")
    
    # Initialize services
    try:
        from app.services.quality_assessor import FaceQualityAssessor
        from app.services.enhancement import ImageEnhancer
        
        # Warm up models
        assessor = FaceQualityAssessor()
        enhancer = ImageEnhancer()
        
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down service")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Enterprise Face Quality Assessment Microservice with Deep Learning",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins if settings.cors_origins != ["*"] else ["*"],
        allow_credentials=True,
        allow_methods=settings.cors_methods if settings.cors_methods != ["*"] else ["*"],
        allow_headers=settings.cors_headers if settings.cors_headers != ["*"] else ["*"],
    )

# GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header and metrics."""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Process-Time"] = str(process_time)
        
        # Update Prometheus metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(process_time)
        
        return response
    except Exception as e:
        logger.exception(f"Request processing error: {e}")
        raise


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle global exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc)
        }
    )


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Health check endpoint
@app.get("/health")
async def health():
    """Simple health check."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": time.time()
    }


@app.get("/ready")
async def readiness():
    """Readiness probe."""
    try:
        # Check if services are ready
        from app.api.routes import quality_assessor, image_enhancer
        
        if quality_assessor is None or image_enhancer is None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not ready", "reason": "Services not initialized"}
            )
        
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "reason": str(e)}
        )


# Include API routes
app.include_router(
    routes.router,
    prefix=settings.api_prefix,
    tags=["Face Quality Assessment"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "ready": "/ready",
            "metrics": "/metrics",
            "api": settings.api_prefix
        }
    }


def main():
    """Run the application."""
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.reload,
        workers=1 if settings.reload else settings.workers,
        log_level=settings.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()
