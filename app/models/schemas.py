"""
Pydantic models for request/response schemas.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class QualityDecision(str, Enum):
    """Quality assessment decision."""
    ACCEPT = "accept"
    ENHANCE = "enhance"
    REJECT = "reject"


class BlurMetrics(BaseModel):
    """Blur detection metrics."""
    laplacian_variance: float = Field(..., description="Laplacian variance score")
    gradient_magnitude: float = Field(..., description="Gradient magnitude")
    is_blurry: bool = Field(..., description="Whether image is blurry")
    blur_score: float = Field(..., ge=0, le=1, description="Normalized blur score (0-1)")
    recommendation: str = Field(..., description="Blur-based recommendation")


class PoseMetrics(BaseModel):
    """Head pose estimation metrics."""
    yaw: float = Field(..., description="Yaw angle in degrees")
    pitch: float = Field(..., description="Pitch angle in degrees")
    roll: float = Field(..., description="Roll angle in degrees")
    is_frontal: bool = Field(..., description="Whether pose is frontal")
    pose_score: float = Field(..., ge=0, le=1, description="Normalized pose score (0-1)")
    recommendation: str = Field(..., description="Pose-based recommendation")


class LightingMetrics(BaseModel):
    """Lighting analysis metrics."""
    brightness: float = Field(..., description="Average brightness (0-255)")
    contrast: float = Field(..., description="Contrast value")
    histogram_uniformity: float = Field(..., description="Histogram uniformity")
    is_well_lit: bool = Field(..., description="Whether lighting is adequate")
    lighting_score: float = Field(..., ge=0, le=1, description="Normalized lighting score (0-1)")
    recommendation: str = Field(..., description="Lighting-based recommendation")


class ResolutionMetrics(BaseModel):
    """Resolution adequacy metrics."""
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    face_width: int = Field(..., description="Face region width")
    face_height: int = Field(..., description="Face region height")
    is_adequate: bool = Field(..., description="Whether resolution is adequate")
    resolution_score: float = Field(..., ge=0, le=1, description="Normalized resolution score (0-1)")
    recommendation: str = Field(..., description="Resolution-based recommendation")


class FaceDetection(BaseModel):
    """Face detection results."""
    bbox: List[int] = Field(..., description="Bounding box [x, y, w, h]")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    landmarks: Optional[List[List[float]]] = Field(None, description="Facial landmarks")


class QualityAssessment(BaseModel):
    """Complete quality assessment results."""
    overall_score: float = Field(..., ge=0, le=1, description="Overall quality score (0-1)")
    decision: QualityDecision = Field(..., description="Quality decision")
    blur_metrics: BlurMetrics = Field(..., description="Blur detection results")
    pose_metrics: PoseMetrics = Field(..., description="Pose estimation results")
    lighting_metrics: LightingMetrics = Field(..., description="Lighting analysis results")
    resolution_metrics: ResolutionMetrics = Field(..., description="Resolution assessment results")
    face_detection: FaceDetection = Field(..., description="Face detection results")
    recommendations: List[str] = Field(..., description="Improvement recommendations")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class AssessmentRequest(BaseModel):
    """Face quality assessment request."""
    image_base64: Optional[str] = Field(None, description="Base64 encoded image")
    image_url: Optional[str] = Field(None, description="Image URL")
    return_enhanced: bool = Field(False, description="Return enhanced image if needed")
    custom_thresholds: Optional[Dict[str, float]] = Field(None, description="Custom quality thresholds")
    
    @field_validator("image_base64", "image_url")
    @classmethod
    def validate_image_source(cls, v, info):
        """Ensure at least one image source is provided."""
        if not v and not info.data.get("image_url") and not info.data.get("image_base64"):
            raise ValueError("Either image_base64 or image_url must be provided")
        return v


class AssessmentResponse(BaseModel):
    """Face quality assessment response."""
    request_id: str = Field(..., description="Unique request identifier")
    status: str = Field(..., description="Processing status")
    assessment: QualityAssessment = Field(..., description="Quality assessment results")
    enhanced_image_base64: Optional[str] = Field(None, description="Enhanced image if requested")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")


class BatchAssessmentRequest(BaseModel):
    """Batch face quality assessment request."""
    images: List[AssessmentRequest] = Field(..., description="List of images to assess")
    parallel: bool = Field(True, description="Process in parallel")
    max_workers: int = Field(4, description="Maximum parallel workers")


class BatchAssessmentResponse(BaseModel):
    """Batch face quality assessment response."""
    batch_id: str = Field(..., description="Unique batch identifier")
    total_images: int = Field(..., description="Total number of images")
    successful: int = Field(..., description="Successfully processed images")
    failed: int = Field(..., description="Failed processing count")
    results: List[AssessmentResponse] = Field(..., description="Individual assessment results")
    total_processing_time_ms: float = Field(..., description="Total processing time")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Batch timestamp")


class EnhancementRequest(BaseModel):
    """Image enhancement request."""
    image_base64: str = Field(..., description="Base64 encoded image")
    scale_factor: int = Field(4, ge=1, le=8, description="Super-resolution scale factor")
    enhance_face: bool = Field(True, description="Apply face-specific enhancement")
    denoise: bool = Field(True, description="Apply denoising")


class EnhancementResponse(BaseModel):
    """Image enhancement response."""
    request_id: str = Field(..., description="Unique request identifier")
    enhanced_image_base64: str = Field(..., description="Enhanced image")
    original_size: List[int] = Field(..., description="Original image size [width, height]")
    enhanced_size: List[int] = Field(..., description="Enhanced image size [width, height]")
    processing_time_ms: float = Field(..., description="Processing time")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")


class HealthStatus(BaseModel):
    """Health check status."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    gpu_available: bool = Field(..., description="GPU availability")
    models_loaded: bool = Field(..., description="Models loaded status")
    uptime_seconds: float = Field(..., description="Service uptime")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")


class MetricsResponse(BaseModel):
    """Metrics response."""
    total_requests: int = Field(..., description="Total requests processed")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")
    average_processing_time_ms: float = Field(..., description="Average processing time")
    quality_distribution: Dict[str, int] = Field(..., description="Quality decision distribution")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class TokenRequest(BaseModel):
    """Token generation request."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    scopes: List[str] = Field(default_factory=list, description="Requested scopes")


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
