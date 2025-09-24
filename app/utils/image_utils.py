"""
Image processing utilities.
"""
import base64
import io
from typing import Tuple, Optional
import numpy as np
import cv2
from PIL import Image
import aiohttp
import aiofiles

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def base64_to_image(base64_str: str) -> np.ndarray:
    """Convert base64 string to numpy image array."""
    try:
        # Remove data URL prefix if present
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        
        # Decode base64
        img_bytes = base64.b64decode(base64_str)
        
        # Convert to numpy array
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        
        # Decode image
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image from base64")
        
        return image
        
    except Exception as e:
        logger.error(f"Failed to convert base64 to image: {e}")
        raise ValueError(f"Invalid base64 image data: {str(e)}")


def image_to_base64(image: np.ndarray, format: str = 'JPEG') -> str:
    """Convert numpy image array to base64 string."""
    try:
        # Encode image
        if format.upper() == 'PNG':
            success, buffer = cv2.imencode('.png', image)
        else:
            success, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        if not success:
            raise ValueError("Failed to encode image")
        
        # Convert to base64
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return img_base64
        
    except Exception as e:
        logger.error(f"Failed to convert image to base64: {e}")
        raise ValueError(f"Image encoding failed: {str(e)}")


async def download_image_from_url(url: str) -> np.ndarray:
    """Download image from URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download image: HTTP {response.status}")
                
                image_bytes = await response.read()
                
                # Check file size
                if len(image_bytes) > settings.max_image_size_mb * 1024 * 1024:
                    raise ValueError(f"Image too large: {len(image_bytes)} bytes")
                
                # Convert to numpy array
                img_array = np.frombuffer(image_bytes, dtype=np.uint8)
                image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                if image is None:
                    raise ValueError("Failed to decode downloaded image")
                
                return image
                
    except Exception as e:
        logger.error(f"Failed to download image from URL: {e}")
        raise ValueError(f"Image download failed: {str(e)}")


def validate_image_format(image_bytes: bytes) -> bool:
    """Validate image format."""
    try:
        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return image is not None
    except:
        return False


def resize_image(
    image: np.ndarray,
    max_width: int = 1920,
    max_height: int = 1920,
    maintain_aspect: bool = True
) -> np.ndarray:
    """Resize image to fit within max dimensions."""
    height, width = image.shape[:2]
    
    if width <= max_width and height <= max_height:
        return image
    
    if maintain_aspect:
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
    else:
        new_width = max_width
        new_height = max_height
    
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    return resized


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normalize image to 0-1 range."""
    return image.astype(np.float32) / 255.0


def denormalize_image(image: np.ndarray) -> np.ndarray:
    """Denormalize image from 0-1 to 0-255 range."""
    return (image * 255).astype(np.uint8)


def convert_color_space(
    image: np.ndarray,
    from_space: str = 'BGR',
    to_space: str = 'RGB'
) -> np.ndarray:
    """Convert image between color spaces."""
    conversion_map = {
        ('BGR', 'RGB'): cv2.COLOR_BGR2RGB,
        ('RGB', 'BGR'): cv2.COLOR_RGB2BGR,
        ('BGR', 'GRAY'): cv2.COLOR_BGR2GRAY,
        ('RGB', 'GRAY'): cv2.COLOR_RGB2GRAY,
        ('GRAY', 'BGR'): cv2.COLOR_GRAY2BGR,
        ('GRAY', 'RGB'): cv2.COLOR_GRAY2RGB,
        ('BGR', 'HSV'): cv2.COLOR_BGR2HSV,
        ('RGB', 'HSV'): cv2.COLOR_RGB2HSV,
        ('HSV', 'BGR'): cv2.COLOR_HSV2BGR,
        ('HSV', 'RGB'): cv2.COLOR_HSV2RGB,
    }
    
    key = (from_space.upper(), to_space.upper())
    if key in conversion_map:
        return cv2.cvtColor(image, conversion_map[key])
    
    return image


def crop_face_region(
    image: np.ndarray,
    bbox: list,
    padding: float = 0.2
) -> Tuple[np.ndarray, list]:
    """Crop face region with padding."""
    x, y, w, h = bbox
    height, width = image.shape[:2]
    
    # Add padding
    pad_w = int(w * padding)
    pad_h = int(h * padding)
    
    x1 = max(0, x - pad_w)
    y1 = max(0, y - pad_h)
    x2 = min(width, x + w + pad_w)
    y2 = min(height, y + h + pad_h)
    
    cropped = image[y1:y2, x1:x2]
    new_bbox = [x1, y1, x2 - x1, y2 - y1]
    
    return cropped, new_bbox


def draw_face_bbox(
    image: np.ndarray,
    bbox: list,
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2
) -> np.ndarray:
    """Draw bounding box on image."""
    x, y, w, h = bbox
    result = image.copy()
    cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
    return result


def draw_landmarks(
    image: np.ndarray,
    landmarks: list,
    color: Tuple[int, int, int] = (0, 255, 0),
    radius: int = 2
) -> np.ndarray:
    """Draw facial landmarks on image."""
    result = image.copy()
    for point in landmarks:
        x, y = int(point[0]), int(point[1])
        cv2.circle(result, (x, y), radius, color, -1)
    return result


def create_thumbnail(
    image: np.ndarray,
    size: Tuple[int, int] = (256, 256)
) -> np.ndarray:
    """Create thumbnail of image."""
    return cv2.resize(image, size, interpolation=cv2.INTER_AREA)


def calculate_image_hash(image: np.ndarray) -> str:
    """Calculate perceptual hash of image."""
    import hashlib
    
    # Resize to small size
    small = cv2.resize(image, (8, 8), interpolation=cv2.INTER_AREA)
    
    # Convert to grayscale
    if len(small.shape) == 3:
        small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    
    # Calculate hash
    avg = small.mean()
    diff = small > avg
    
    # Convert to hex string
    hash_str = ''.join(['1' if pixel else '0' for pixel in diff.flatten()])
    return hashlib.md5(hash_str.encode()).hexdigest()


async def save_image_async(
    image: np.ndarray,
    filepath: str,
    quality: int = 95
) -> None:
    """Save image asynchronously."""
    # Encode image
    if filepath.lower().endswith('.png'):
        success, buffer = cv2.imencode('.png', image)
    else:
        success, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    
    if not success:
        raise ValueError("Failed to encode image")
    
    # Save asynchronously
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(buffer.tobytes())


def get_image_stats(image: np.ndarray) -> dict:
    """Get image statistics."""
    if len(image.shape) == 2:
        gray = image
    else:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    return {
        'shape': image.shape,
        'dtype': str(image.dtype),
        'min': float(np.min(image)),
        'max': float(np.max(image)),
        'mean': float(np.mean(image)),
        'std': float(np.std(image)),
        'brightness': float(np.mean(gray)),
        'contrast': float(np.std(gray)),
    }
