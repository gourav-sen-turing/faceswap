"""
Face quality assessment service using MediaPipe (no dlib compilation required).
Includes blur detection, pose estimation, lighting analysis, and resolution assessment.
"""
import time
import numpy as np
import cv2
from typing import Tuple, Optional, Dict, Any
from scipy.spatial import distance
from skimage import exposure
from skimage.filters import laplace
from skimage.measure import shannon_entropy

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import (
    QualityAssessment, QualityDecision, BlurMetrics, PoseMetrics,
    LightingMetrics, ResolutionMetrics, FaceDetection
)

logger = get_logger(__name__)


class FaceQualityAssessor:
    """Face quality assessment service using MediaPipe."""
    
    def __init__(self):
        """Initialize quality assessor with MediaPipe."""
        self.cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Initialize MediaPipe Face Detection and Face Mesh
        if MEDIAPIPE_AVAILABLE:
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_face_mesh = mp.solutions.face_mesh
            
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=settings.face_detection_confidence
            )
            
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=settings.face_detection_confidence
            )
            
            self.landmarks_available = True
            logger.info("MediaPipe face detection initialized successfully")
        else:
            self.face_detection = None
            self.face_mesh = None
            self.landmarks_available = False
            logger.warning("MediaPipe not available, using OpenCV Haar cascades only")
        
        logger.info("Face quality assessor initialized")
    
    def assess_quality(
        self,
        image: np.ndarray,
        custom_thresholds: Optional[Dict[str, float]] = None
    ) -> QualityAssessment:
        """
        Perform comprehensive face quality assessment.
        
        Args:
            image: Input image as numpy array
            custom_thresholds: Optional custom quality thresholds
            
        Returns:
            QualityAssessment with all metrics
        """
        start_time = time.time()
        
        # Detect face
        face_detection = self._detect_face(image)
        
        if face_detection is None:
            raise ValueError("No face detected in image")
        
        # Extract face region
        x, y, w, h = face_detection.bbox
        face_region = image[y:y+h, x:x+w]
        
        # Assess blur
        blur_metrics = self._assess_blur(face_region)
        
        # Assess pose
        pose_metrics = self._assess_pose(image, face_detection)
        
        # Assess lighting
        lighting_metrics = self._assess_lighting(face_region)
        
        # Assess resolution
        resolution_metrics = self._assess_resolution(image, face_detection)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            blur_metrics, pose_metrics, lighting_metrics, resolution_metrics
        )
        
        # Make decision
        decision = self._make_decision(overall_score, custom_thresholds)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            blur_metrics, pose_metrics, lighting_metrics, resolution_metrics
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return QualityAssessment(
            overall_score=overall_score,
            decision=decision,
            blur_metrics=blur_metrics,
            pose_metrics=pose_metrics,
            lighting_metrics=lighting_metrics,
            resolution_metrics=resolution_metrics,
            face_detection=face_detection,
            recommendations=recommendations,
            processing_time_ms=processing_time
        )
    
    def _detect_face(self, image: np.ndarray) -> Optional[FaceDetection]:
        """Detect face in image using MediaPipe or OpenCV."""
        
        # Try MediaPipe first (if available)
        if MEDIAPIPE_AVAILABLE and self.face_detection:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_image)
            
            if results.detections:
                detection = results.detections[0]
                bbox_rel = detection.location_data.relative_bounding_box
                
                h, w = image.shape[:2]
                x = int(bbox_rel.xmin * w)
                y = int(bbox_rel.ymin * h)
                width = int(bbox_rel.width * w)
                height = int(bbox_rel.height * h)
                
                # Ensure bbox is within image bounds
                x = max(0, x)
                y = max(0, y)
                width = min(width, w - x)
                height = min(height, h - y)
                
                # Get landmarks using Face Mesh
                landmarks = None
                if self.face_mesh:
                    mesh_results = self.face_mesh.process(rgb_image)
                    if mesh_results.multi_face_landmarks:
                        face_landmarks = mesh_results.multi_face_landmarks[0]
                        landmarks = []
                        for landmark in face_landmarks.landmark:
                            landmarks.append([
                                landmark.x * image.shape[1],
                                landmark.y * image.shape[0]
                            ])
                
                return FaceDetection(
                    bbox=[x, y, width, height],
                    confidence=detection.score[0],
                    landmarks=landmarks
                )
        
        # Fallback to Haar cascade
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        faces = self.cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(settings.min_face_size, settings.min_face_size)
        )
        
        if len(faces) > 0:
            x, y, w, h = faces[0]
            return FaceDetection(
                bbox=[int(x), int(y), int(w), int(h)],
                confidence=0.85,
                landmarks=None
            )
        
        return None
    
    def _assess_blur(self, face_region: np.ndarray) -> BlurMetrics:
        """Assess image blur using multiple methods."""
        gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY) if len(face_region.shape) == 3 else face_region
        
        # Laplacian variance method
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Gradient magnitude method
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag = np.mean(np.sqrt(sobelx**2 + sobely**2))
        
        # Normalize scores
        blur_score = min(laplacian_var / settings.blur_threshold_min, 1.0)
        is_blurry = laplacian_var < settings.blur_threshold_reject
        
        # Generate recommendation
        if laplacian_var >= settings.blur_threshold_min:
            recommendation = "Sharp image, no action needed"
        elif laplacian_var >= settings.blur_threshold_reject:
            recommendation = "Slightly blurry, consider enhancement"
        else:
            recommendation = "Too blurry, reject or apply strong enhancement"
        
        return BlurMetrics(
            laplacian_variance=float(laplacian_var),
            gradient_magnitude=float(gradient_mag),
            is_blurry=is_blurry,
            blur_score=float(blur_score),
            recommendation=recommendation
        )
    
    def _assess_pose(
        self,
        image: np.ndarray,
        face_detection: FaceDetection
    ) -> PoseMetrics:
        """Assess head pose using MediaPipe landmarks or geometric methods."""
        
        if face_detection.landmarks and len(face_detection.landmarks) >= 468:
            # MediaPipe has 468 landmarks, use key points for pose
            yaw, pitch, roll = self._estimate_pose_from_mediapipe(
                face_detection.landmarks, image.shape
            )
        else:
            # Fallback to geometric estimation
            yaw, pitch, roll = self._estimate_pose_geometric(
                face_detection.bbox, image.shape
            )
        
        # Check if pose is frontal
        is_frontal = (
            abs(yaw) <= settings.pose_yaw_max and
            abs(pitch) <= settings.pose_pitch_max and
            abs(roll) <= settings.pose_roll_max
        )
        
        # Calculate pose score
        yaw_score = 1.0 - min(abs(yaw) / settings.pose_yaw_max, 1.0)
        pitch_score = 1.0 - min(abs(pitch) / settings.pose_pitch_max, 1.0)
        roll_score = 1.0 - min(abs(roll) / settings.pose_roll_max, 1.0)
        pose_score = (yaw_score + pitch_score + roll_score) / 3.0
        
        # Generate recommendation
        if is_frontal:
            recommendation = "Frontal pose, ideal for processing"
        else:
            angles = []
            if abs(yaw) > settings.pose_yaw_max:
                angles.append(f"yaw ({yaw:.1f}°)")
            if abs(pitch) > settings.pose_pitch_max:
                angles.append(f"pitch ({pitch:.1f}°)")
            if abs(roll) > settings.pose_roll_max:
                angles.append(f"roll ({roll:.1f}°)")
            recommendation = f"Non-frontal pose detected: {', '.join(angles)}"
        
        return PoseMetrics(
            yaw=float(yaw),
            pitch=float(pitch),
            roll=float(roll),
            is_frontal=is_frontal,
            pose_score=float(pose_score),
            recommendation=recommendation
        )
    
    def _estimate_pose_from_mediapipe(
        self,
        landmarks: list,
        image_shape: Tuple[int, ...]
    ) -> Tuple[float, float, float]:
        """Estimate pose from MediaPipe landmarks."""
        # MediaPipe key landmark indices for pose estimation
        # Nose tip: 1, Chin: 152, Left eye: 33, Right eye: 263
        # Left mouth: 61, Right mouth: 291
        
        if len(landmarks) < 468:
            return 0.0, 0.0, 0.0
        
        # 3D model points
        model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye
            (225.0, 170.0, -135.0),      # Right eye
            (-150.0, -150.0, -125.0),    # Left mouth
            (150.0, -150.0, -125.0)      # Right mouth
        ], dtype=np.float64)
        
        # Get 2D image points from MediaPipe landmarks
        try:
            image_points = np.array([
                landmarks[1],    # Nose tip
                landmarks[152],  # Chin
                landmarks[33],   # Left eye
                landmarks[263],  # Right eye
                landmarks[61],   # Left mouth
                landmarks[291]   # Right mouth
            ], dtype=np.float64)
            
            # Camera matrix
            focal_length = image_shape[1]
            center = (image_shape[1] / 2, image_shape[0] / 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype=np.float64)
            
            dist_coeffs = np.zeros((4, 1))
            
            # Solve PnP
            success, rotation_vector, translation_vector = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if success:
                # Convert rotation vector to angles
                rotation_mat, _ = cv2.Rodrigues(rotation_vector)
                pose_mat = cv2.hconcat((rotation_mat, translation_vector))
                _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
                
                pitch, yaw, roll = euler_angles.flatten()[:3]
                return yaw, pitch, roll
        except Exception as e:
            logger.warning(f"Pose estimation from landmarks failed: {e}")
        
        return 0.0, 0.0, 0.0
    
    def _estimate_pose_geometric(
        self,
        bbox: list,
        image_shape: Tuple[int, ...]
    ) -> Tuple[float, float, float]:
        """Estimate pose from face bounding box geometry."""
        x, y, w, h = bbox
        
        # Calculate face center
        center_x = x + w / 2
        center_y = y + h / 2
        
        # Calculate relative position in image
        img_center_x = image_shape[1] / 2
        img_center_y = image_shape[0] / 2
        
        # Estimate yaw from horizontal position
        yaw = (center_x - img_center_x) / img_center_x * 30.0
        
        # Estimate pitch from vertical position
        pitch = (center_y - img_center_y) / img_center_y * 20.0
        
        # Estimate roll from aspect ratio
        aspect_ratio = w / h
        roll = (aspect_ratio - 1.0) * 15.0
        
        return yaw, pitch, roll
    
    def _assess_lighting(self, face_region: np.ndarray) -> LightingMetrics:
        """Assess lighting conditions."""
        gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY) if len(face_region.shape) == 3 else face_region
        
        # Calculate brightness
        brightness = np.mean(gray)
        
        # Calculate contrast
        contrast = np.std(gray)
        
        # Calculate histogram uniformity
        hist, _ = np.histogram(gray.flatten(), bins=256, range=[0, 256])
        hist_normalized = hist / hist.sum()
        histogram_uniformity = shannon_entropy(hist_normalized)
        
        # Check if well-lit
        is_well_lit = (
            settings.lighting_min <= brightness <= settings.lighting_max and
            contrast >= settings.lighting_contrast_min
        )
        
        # Calculate lighting score
        brightness_score = 1.0 - abs(brightness - 128) / 128
        contrast_score = min(contrast / 50.0, 1.0)
        lighting_score = (brightness_score + contrast_score) / 2.0
        
        # Generate recommendation
        if is_well_lit:
            recommendation = "Good lighting conditions"
        else:
            issues = []
            if brightness < settings.lighting_min:
                issues.append("underexposed")
            elif brightness > settings.lighting_max:
                issues.append("overexposed")
            if contrast < settings.lighting_contrast_min:
                issues.append("low contrast")
            recommendation = f"Poor lighting: {', '.join(issues)}"
        
        return LightingMetrics(
            brightness=float(brightness),
            contrast=float(contrast),
            histogram_uniformity=float(histogram_uniformity),
            is_well_lit=is_well_lit,
            lighting_score=float(lighting_score),
            recommendation=recommendation
        )
    
    def _assess_resolution(
        self,
        image: np.ndarray,
        face_detection: FaceDetection
    ) -> ResolutionMetrics:
        """Assess image and face resolution."""
        height, width = image.shape[:2]
        x, y, w, h = face_detection.bbox
        
        # Check if resolution is adequate
        is_adequate = (
            w >= settings.resolution_min_width and
            h >= settings.resolution_min_height
        )
        
        # Calculate resolution score
        width_score = min(w / settings.resolution_recommended_width, 1.0)
        height_score = min(h / settings.resolution_recommended_height, 1.0)
        resolution_score = (width_score + height_score) / 2.0
        
        # Generate recommendation
        if is_adequate:
            if w >= settings.resolution_recommended_width and h >= settings.resolution_recommended_height:
                recommendation = "Excellent resolution"
            else:
                recommendation = "Adequate resolution, enhancement recommended"
        else:
            recommendation = f"Low resolution ({w}x{h}), super-resolution required"
        
        return ResolutionMetrics(
            width=width,
            height=height,
            face_width=w,
            face_height=h,
            is_adequate=is_adequate,
            resolution_score=float(resolution_score),
            recommendation=recommendation
        )
    
    def _calculate_overall_score(
        self,
        blur: BlurMetrics,
        pose: PoseMetrics,
        lighting: LightingMetrics,
        resolution: ResolutionMetrics
    ) -> float:
        """Calculate overall quality score."""
        weights = {
            'blur': 0.3,
            'pose': 0.25,
            'lighting': 0.25,
            'resolution': 0.2
        }
        
        overall = (
            weights['blur'] * blur.blur_score +
            weights['pose'] * pose.pose_score +
            weights['lighting'] * lighting.lighting_score +
            weights['resolution'] * resolution.resolution_score
        )
        
        return float(overall)
    
    def _make_decision(
        self,
        overall_score: float,
        custom_thresholds: Optional[Dict[str, float]] = None
    ) -> QualityDecision:
        """Make quality decision based on score."""
        if custom_thresholds:
            accept_threshold = custom_thresholds.get('accept', settings.quality_score_accept)
            enhance_threshold = custom_thresholds.get('enhance', settings.quality_score_enhance)
        else:
            accept_threshold = settings.quality_score_accept
            enhance_threshold = settings.quality_score_enhance
        
        if overall_score >= accept_threshold:
            return QualityDecision.ACCEPT
        elif overall_score >= enhance_threshold:
            return QualityDecision.ENHANCE
        else:
            return QualityDecision.REJECT
    
    def _generate_recommendations(
        self,
        blur: BlurMetrics,
        pose: PoseMetrics,
        lighting: LightingMetrics,
        resolution: ResolutionMetrics
    ) -> list:
        """Generate improvement recommendations."""
        recommendations = []
        
        if blur.is_blurry:
            recommendations.append(blur.recommendation)
        
        if not pose.is_frontal:
            recommendations.append(pose.recommendation)
        
        if not lighting.is_well_lit:
            recommendations.append(lighting.recommendation)
        
        if not resolution.is_adequate:
            recommendations.append(resolution.recommendation)
        
        if not recommendations:
            recommendations.append("Image quality is excellent, no improvements needed")
        
        return recommendations
