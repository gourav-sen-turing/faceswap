"""
API routes for face quality assessment service.
"""
import time
import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import JSONResponse
import numpy as np

from app.core.config import settings
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.models.schemas import (
    AssessmentRequest, AssessmentResponse, BatchAssessmentRequest,
    BatchAssessmentResponse, EnhancementRequest, EnhancementResponse,
    HealthStatus, MetricsResponse, ErrorResponse
)
from app.services.quality_assessor import FaceQualityAssessor
from app.services.enhancement import ImageEnhancer
from app.utils.image_utils import (
    base64_to_image, image_to_base64, download_image_from_url
)

logger = get_logger(__name__)

# Initialize router
router = APIRouter()

# Initialize services (singleton pattern)
quality_assessor = None
image_enhancer = None

# Metrics storage
metrics = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'total_processing_time': 0.0,
    'quality_distribution': {'accept': 0, 'enhance': 0, 'reject': 0}
}

# Service start time
service_start_time = time.time()


def get_quality_assessor() -> FaceQualityAssessor:
    """Get quality assessor instance."""
    global quality_assessor
    if quality_assessor is None:
        quality_assessor = FaceQualityAssessor()
    return quality_assessor


def get_image_enhancer() -> ImageEnhancer:
    """Get image enhancer instance."""
    global image_enhancer
    if image_enhancer is None:
        image_enhancer = ImageEnhancer()
    return image_enhancer


@router.post("/assess", response_model=AssessmentResponse)
async def assess_face_quality(
    request: AssessmentRequest,
    user: dict = Depends(get_current_user)
):
    """
    Assess face quality from base64 image or URL.
    
    Args:
        request: Assessment request with image data
        user: Authenticated user
        
    Returns:
        Quality assessment results
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"Processing quality assessment request: {request_id}")
        
        # Update metrics
        metrics['total_requests'] += 1
        
        # Get image from source
        if request.image_base64:
            image = base64_to_image(request.image_base64)
        elif request.image_url:
            image = await download_image_from_url(request.image_url)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either image_base64 or image_url must be provided"
            )
        
        # Assess quality
        assessor = get_quality_assessor()
        assessment = assessor.assess_quality(image, request.custom_thresholds)
        
        # Update quality distribution
        metrics['quality_distribution'][assessment.decision.value] += 1
        
        # Enhance image if needed and requested
        enhanced_image_base64 = None
        if request.return_enhanced and assessment.decision.value in ['enhance', 'reject']:
            enhancer = get_image_enhancer()
            if settings.enable_auto_enhancement:
                enhanced_image = enhancer.auto_enhance(image)
                enhanced_image_base64 = image_to_base64(enhanced_image)
        
        # Update metrics
        processing_time = (time.time() - start_time) * 1000
        metrics['successful_requests'] += 1
        metrics['total_processing_time'] += processing_time
        
        logger.info(
            f"Assessment completed: {request_id}",
            score=assessment.overall_score,
            decision=assessment.decision.value,
            processing_time_ms=processing_time
        )
        
        return AssessmentResponse(
            request_id=request_id,
            status="success",
            assessment=assessment,
            enhanced_image_base64=enhanced_image_base64,
            metadata={
                'user': user.get('token_data', {}).get('username', 'api-key-user'),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
    except ValueError as e:
        metrics['failed_requests'] += 1
        logger.error(f"Validation error in request {request_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        metrics['failed_requests'] += 1
        logger.exception(f"Error processing request {request_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.post("/assess/batch", response_model=BatchAssessmentResponse)
async def assess_batch(
    request: BatchAssessmentRequest,
    user: dict = Depends(get_current_user)
):
    """
    Assess quality of multiple images in batch.
    
    Args:
        request: Batch assessment request
        user: Authenticated user
        
    Returns:
        Batch assessment results
    """
    batch_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"Processing batch assessment: {batch_id}, images: {len(request.images)}")
        
        results = []
        successful = 0
        failed = 0
        
        # Process images
        for img_request in request.images:
            try:
                # Create individual assessment
                response = await assess_face_quality(img_request, user)
                results.append(response)
                successful += 1
            except Exception as e:
                logger.error(f"Failed to process image in batch {batch_id}: {e}")
                failed += 1
                # Add error response
                error_response = AssessmentResponse(
                    request_id=str(uuid.uuid4()),
                    status="failed",
                    assessment=None,
                    metadata={'error': str(e)}
                )
                results.append(error_response)
        
        total_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"Batch assessment completed: {batch_id}",
            total=len(request.images),
            successful=successful,
            failed=failed,
            processing_time_ms=total_time
        )
        
        return BatchAssessmentResponse(
            batch_id=batch_id,
            total_images=len(request.images),
            successful=successful,
            failed=failed,
            results=results,
            total_processing_time_ms=total_time
        )
        
    except Exception as e:
        logger.exception(f"Error processing batch {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing failed: {str(e)}"
        )


@router.post("/enhance", response_model=EnhancementResponse)
async def enhance_image(
    request: EnhancementRequest,
    user: dict = Depends(get_current_user)
):
    """
    Enhance image quality using super-resolution and restoration.
    
    Args:
        request: Enhancement request
        user: Authenticated user
        
    Returns:
        Enhanced image
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"Processing enhancement request: {request_id}")
        
        # Convert base64 to image
        image = base64_to_image(request.image_base64)
        original_size = [image.shape[1], image.shape[0]]
        
        # Enhance image
        enhancer = get_image_enhancer()
        enhanced_image = enhancer.enhance_image(
            image,
            scale_factor=request.scale_factor,
            enhance_face=request.enhance_face,
            denoise=request.denoise
        )
        
        enhanced_size = [enhanced_image.shape[1], enhanced_image.shape[0]]
        
        # Convert back to base64
        enhanced_base64 = image_to_base64(enhanced_image)
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"Enhancement completed: {request_id}",
            original_size=original_size,
            enhanced_size=enhanced_size,
            processing_time_ms=processing_time
        )
        
        return EnhancementResponse(
            request_id=request_id,
            enhanced_image_base64=enhanced_base64,
            original_size=original_size,
            enhanced_size=enhanced_size,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.exception(f"Error enhancing image {request_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhancement failed: {str(e)}"
        )


@router.post("/assess/upload")
async def assess_uploaded_file(
    file: UploadFile = File(...),
    return_enhanced: bool = False,
    user: dict = Depends(get_current_user)
):
    """
    Assess face quality from uploaded file.
    
    Args:
        file: Uploaded image file
        return_enhanced: Whether to return enhanced image
        user: Authenticated user
        
    Returns:
        Quality assessment results
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Read file
        contents = await file.read()
        
        # Convert to numpy array
        img_array = np.frombuffer(contents, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )
        
        # Convert to base64
        image_base64 = image_to_base64(image)
        
        # Create assessment request
        assessment_request = AssessmentRequest(
            image_base64=image_base64,
            return_enhanced=return_enhanced
        )
        
        # Process assessment
        return await assess_face_quality(assessment_request, user)
        
    except Exception as e:
        logger.exception(f"Error processing uploaded file {request_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing failed: {str(e)}"
        )


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    import torch
    
    uptime = time.time() - service_start_time
    
    # Check if models are loaded
    models_loaded = quality_assessor is not None and image_enhancer is not None
    
    # Check GPU availability
    gpu_available = torch.cuda.is_available() if settings.gpu_enabled else False
    
    return HealthStatus(
        status="healthy" if models_loaded else "degraded",
        version=settings.app_version,
        gpu_available=gpu_available,
        models_loaded=models_loaded,
        uptime_seconds=uptime
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(user: dict = Depends(get_current_user)):
    """
    Get service metrics.
    
    Args:
        user: Authenticated user
        
    Returns:
        Service metrics
    """
    avg_processing_time = (
        metrics['total_processing_time'] / metrics['successful_requests']
        if metrics['successful_requests'] > 0 else 0.0
    )
    
    return MetricsResponse(
        total_requests=metrics['total_requests'],
        successful_requests=metrics['successful_requests'],
        failed_requests=metrics['failed_requests'],
        average_processing_time_ms=avg_processing_time,
        quality_distribution=metrics['quality_distribution']
    )


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }
