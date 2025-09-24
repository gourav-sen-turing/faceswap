"""
Application configuration management using Pydantic Settings.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    environment: str = Field(default="production", description="Environment")
    app_name: str = Field(default="Face Quality Assessment Service", description="App name")
    app_version: str = Field(default="1.0.0", description="App version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    workers: int = Field(default=4, description="Number of workers")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    
    # Security
    api_key: str = Field(default="change-this-api-key", description="API key")
    secret_key: str = Field(default="change-this-secret-key-min-32-chars", description="JWT secret")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiry")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiry")
    
    # Authentication
    enable_api_key_auth: bool = Field(default=True, description="Enable API key auth")
    enable_jwt_auth: bool = Field(default=True, description="Enable JWT auth")
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    
    # Database
    mongodb_url: str = Field(default="mongodb://localhost:27017", description="MongoDB URL")
    mongodb_db_name: str = Field(default="face_quality_db", description="MongoDB database name")
    mongo_username: str = Field(default="admin", description="MongoDB username")
    mongo_password: str = Field(default="password", description="MongoDB password")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_max_connections: int = Field(default=50, description="Redis max connections")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    # GPU Configuration
    gpu_enabled: bool = Field(default=True, description="Enable GPU")
    cuda_visible_devices: str = Field(default="0", description="CUDA devices")
    gpu_memory_fraction: float = Field(default=0.8, description="GPU memory fraction")
    enable_mixed_precision: bool = Field(default=True, description="Enable mixed precision")
    
    # Quality Thresholds - Blur Detection
    blur_threshold_min: float = Field(default=100.0, description="Min blur threshold")
    blur_threshold_reject: float = Field(default=50.0, description="Reject blur threshold")
    
    # Quality Thresholds - Pose Estimation
    pose_yaw_max: float = Field(default=30.0, description="Max yaw angle")
    pose_pitch_max: float = Field(default=25.0, description="Max pitch angle")
    pose_roll_max: float = Field(default=20.0, description="Max roll angle")
    
    # Quality Thresholds - Lighting
    lighting_min: float = Field(default=40.0, description="Min lighting level")
    lighting_max: float = Field(default=220.0, description="Max lighting level")
    lighting_contrast_min: float = Field(default=30.0, description="Min contrast")
    
    # Quality Thresholds - Resolution
    resolution_min_width: int = Field(default=224, description="Min width")
    resolution_min_height: int = Field(default=224, description="Min height")
    resolution_recommended_width: int = Field(default=512, description="Recommended width")
    resolution_recommended_height: int = Field(default=512, description="Recommended height")
    
    # Face Detection
    face_detection_confidence: float = Field(default=0.7, description="Detection confidence")
    min_face_size: int = Field(default=50, description="Min face size")
    max_faces: int = Field(default=10, description="Max faces to detect")
    
    # Quality Scores
    quality_score_accept: float = Field(default=0.75, description="Accept threshold")
    quality_score_enhance: float = Field(default=0.50, description="Enhance threshold")
    quality_score_reject: float = Field(default=0.30, description="Reject threshold")
    
    # Super Resolution
    enable_super_resolution: bool = Field(default=True, description="Enable SR")
    sr_scale_factor: int = Field(default=4, description="SR scale factor")
    sr_model: str = Field(default="RealESRGAN", description="SR model name")
    
    # Image Processing
    max_image_size_mb: int = Field(default=10, description="Max image size MB")
    allowed_image_formats: str = Field(default="jpg,jpeg,png,bmp,webp", description="Allowed formats")
    upload_dir: str = Field(default="./uploads", description="Upload directory")
    results_dir: str = Field(default="./results", description="Results directory")
    cache_dir: str = Field(default="./cache", description="Cache directory")
    
    # Models
    models_dir: str = Field(default="./models", description="Models directory")
    face_detector_model: str = Field(default="dlib", description="Face detector model")
    landmark_model: str = Field(default="shape_predictor_68_face_landmarks.dat", description="Landmark model")
    sr_model_path: str = Field(default="./models/RealESRGAN_x4plus.pth", description="SR model path")
    
    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format")
    log_file: str = Field(default="./logs/app.log", description="Log file")
    log_max_size: str = Field(default="100MB", description="Max log size")
    log_backup_count: int = Field(default=10, description="Log backup count")
    enable_structured_logging: bool = Field(default=True, description="Structured logging")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable metrics")
    metrics_port: int = Field(default=9090, description="Metrics port")
    health_check_interval: int = Field(default=30, description="Health check interval")
    
    # Rate Limiting
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    rate_limit_per_hour: int = Field(default=1000, description="Rate limit per hour")
    
    # CORS
    enable_cors: bool = Field(default=True, description="Enable CORS")
    cors_origins: str = Field(default="*", description="CORS origins")
    cors_methods: str = Field(default="GET,POST,PUT,DELETE", description="CORS methods")
    cors_headers: str = Field(default="*", description="CORS headers")
    
    # Performance
    async_workers: int = Field(default=4, description="Async workers")
    batch_size: int = Field(default=8, description="Batch size")
    queue_max_size: int = Field(default=1000, description="Queue max size")
    request_timeout: int = Field(default=300, description="Request timeout")
    
    # Storage
    storage_type: str = Field(default="local", description="Storage type")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret key")
    aws_region: str = Field(default="us-east-1", description="AWS region")
    s3_bucket_name: Optional[str] = Field(default=None, description="S3 bucket")
    
    # Notifications
    enable_notifications: bool = Field(default=False, description="Enable notifications")
    webhook_url: Optional[str] = Field(default=None, description="Webhook URL")
    slack_webhook_url: Optional[str] = Field(default=None, description="Slack webhook")
    
    # Feature Flags
    enable_batch_processing: bool = Field(default=True, description="Enable batch processing")
    enable_async_processing: bool = Field(default=True, description="Enable async processing")
    enable_result_caching: bool = Field(default=True, description="Enable result caching")
    enable_auto_enhancement: bool = Field(default=True, description="Enable auto enhancement")
    
    # Development
    reload: bool = Field(default=False, description="Auto reload")
    testing: bool = Field(default=False, description="Testing mode")
    mock_gpu: bool = Field(default=False, description="Mock GPU")
    
    @field_validator("allowed_image_formats")
    @classmethod
    def parse_formats(cls, v: str) -> List[str]:
        """Parse comma-separated formats."""
        if isinstance(v, str):
            return [fmt.strip().lower() for fmt in v.split(",")]
        return v
    
    @field_validator("cors_origins", "cors_methods", "cors_headers")
    @classmethod
    def parse_cors(cls, v: str) -> List[str]:
        """Parse CORS settings."""
        if isinstance(v, str) and v != "*":
            return [item.strip() for item in v.split(",")]
        return [v] if isinstance(v, str) else v
    
    @property
    def allowed_formats_list(self) -> List[str]:
        """Get allowed image formats as list."""
        if isinstance(self.allowed_image_formats, str):
            return [fmt.strip().lower() for fmt in self.allowed_image_formats.split(",")]
        return self.allowed_image_formats


# Global settings instance
settings = Settings()
