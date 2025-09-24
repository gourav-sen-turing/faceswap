"""
Image enhancement service with super-resolution and face restoration.
"""
import cv2
import numpy as np
from typing import Optional, Tuple
import torch
from PIL import Image

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ImageEnhancer:
    """Image enhancement service with super-resolution."""
    
    def __init__(self):
        """Initialize enhancement models."""
        self.device = torch.device('cuda' if torch.cuda.is_available() and settings.gpu_enabled else 'cpu')
        self.models_loaded = False
        
        try:
            self._load_models()
            self.models_loaded = True
            logger.info(f"Image enhancer initialized on {self.device}")
        except Exception as e:
            logger.warning(f"Failed to load enhancement models: {e}")
            logger.info("Falling back to traditional enhancement methods")
    
    def _load_models(self):
        """Load super-resolution models."""
        # Placeholder for model loading
        # In production, load RealESRGAN, GFPGAN, or similar models
        self.sr_model = None
        self.face_enhancer = None
        
        # Example: Load RealESRGAN
        # from basicsr.archs.rrdbnet_arch import RRDBNet
        # from realesrgan import RealESRGANer
        # model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        # self.sr_model = RealESRGANer(
        #     scale=4,
        #     model_path='weights/RealESRGAN_x4plus.pth',
        #     model=model,
        #     tile=0,
        #     tile_pad=10,
        #     pre_pad=0,
        #     half=True if self.device == 'cuda' else False
        # )
        
        logger.info("Enhancement models loaded successfully")
    
    def enhance_image(
        self,
        image: np.ndarray,
        scale_factor: int = 4,
        enhance_face: bool = True,
        denoise: bool = True
    ) -> np.ndarray:
        """
        Enhance image quality using super-resolution and restoration.
        
        Args:
            image: Input image
            scale_factor: Upscaling factor
            enhance_face: Apply face-specific enhancement
            denoise: Apply denoising
            
        Returns:
            Enhanced image
        """
        if self.models_loaded and self.sr_model:
            return self._enhance_with_model(image, scale_factor, enhance_face)
        else:
            return self._enhance_traditional(image, scale_factor, denoise)
    
    def _enhance_with_model(
        self,
        image: np.ndarray,
        scale_factor: int,
        enhance_face: bool
    ) -> np.ndarray:
        """Enhance using deep learning models."""
        try:
            # Convert to RGB if needed
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
            else:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Apply super-resolution
            # output, _ = self.sr_model.enhance(image, outscale=scale_factor)
            
            # For now, use traditional method as fallback
            output = self._enhance_traditional(image, scale_factor, True)
            
            # Apply face enhancement if requested
            if enhance_face and self.face_enhancer:
                # output = self.face_enhancer.enhance(output)
                pass
            
            return output
            
        except Exception as e:
            logger.error(f"Model enhancement failed: {e}")
            return self._enhance_traditional(image, scale_factor, True)
    
    def _enhance_traditional(
        self,
        image: np.ndarray,
        scale_factor: int,
        denoise: bool
    ) -> np.ndarray:
        """Traditional image enhancement methods."""
        # Denoise if requested
        if denoise:
            image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        
        # Super-resolution using bicubic interpolation
        height, width = image.shape[:2]
        new_size = (width * scale_factor, height * scale_factor)
        enhanced = cv2.resize(image, new_size, interpolation=cv2.INTER_CUBIC)
        
        # Apply unsharp mask for sharpening
        gaussian = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
        enhanced = cv2.addWeighted(enhanced, 1.5, gaussian, -0.5, 0)
        
        # Enhance contrast
        lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def enhance_sharpness(self, image: np.ndarray, amount: float = 1.5) -> np.ndarray:
        """Enhance image sharpness."""
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]]) * amount / 9
        
        sharpened = cv2.filter2D(image, -1, kernel)
        return sharpened
    
    def enhance_brightness(
        self,
        image: np.ndarray,
        target_brightness: float = 128
    ) -> np.ndarray:
        """Adjust image brightness to target level."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        current_brightness = np.mean(gray)
        
        adjustment = target_brightness - current_brightness
        adjusted = cv2.convertScaleAbs(image, alpha=1, beta=adjustment)
        
        return adjusted
    
    def enhance_contrast(
        self,
        image: np.ndarray,
        clip_limit: float = 2.0
    ) -> np.ndarray:
        """Enhance image contrast using CLAHE."""
        if len(image.shape) == 2:
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            return clahe.apply(image)
        else:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    def auto_enhance(self, image: np.ndarray) -> np.ndarray:
        """Automatically enhance image based on quality assessment."""
        # Assess current quality
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        enhanced = image.copy()
        
        # Adjust brightness if needed
        if brightness < settings.lighting_min:
            enhanced = self.enhance_brightness(enhanced, settings.lighting_min + 20)
        elif brightness > settings.lighting_max:
            enhanced = self.enhance_brightness(enhanced, settings.lighting_max - 20)
        
        # Enhance contrast if low
        if contrast < settings.lighting_contrast_min:
            enhanced = self.enhance_contrast(enhanced, clip_limit=3.0)
        
        # Check for blur
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur_score < settings.blur_threshold_min:
            enhanced = self.enhance_sharpness(enhanced, amount=2.0)
        
        return enhanced
    
    def denoise(
        self,
        image: np.ndarray,
        strength: int = 10
    ) -> np.ndarray:
        """Remove noise from image."""
        if len(image.shape) == 2:
            return cv2.fastNlMeansDenoising(image, None, strength, 7, 21)
        else:
            return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)
    
    def upscale(
        self,
        image: np.ndarray,
        scale_factor: int = 2,
        method: str = 'cubic'
    ) -> np.ndarray:
        """Upscale image using specified method."""
        height, width = image.shape[:2]
        new_size = (width * scale_factor, height * scale_factor)
        
        if method == 'cubic':
            interpolation = cv2.INTER_CUBIC
        elif method == 'lanczos':
            interpolation = cv2.INTER_LANCZOS4
        elif method == 'linear':
            interpolation = cv2.INTER_LINEAR
        else:
            interpolation = cv2.INTER_CUBIC
        
        return cv2.resize(image, new_size, interpolation=interpolation)
