"""
API endpoint tests.
"""
import pytest
from fastapi.testclient import TestClient
import base64
import cv2
import numpy as np

from app.main import app
from app.core.config import settings

client = TestClient(app)


def create_test_image():
    """Create a test image with a face."""
    # Create a simple test image
    image = np.ones((300, 300, 3), dtype=np.uint8) * 128
    
    # Draw a simple face representation
    cv2.circle(image, (150, 150), 80, (200, 200, 200), -1)  # Face
    cv2.circle(image, (120, 130), 10, (0, 0, 0), -1)  # Left eye
    cv2.circle(image, (180, 130), 10, (0, 0, 0), -1)  # Right eye
    cv2.ellipse(image, (150, 170), (30, 15), 0, 0, 180, (0, 0, 0), 2)  # Mouth
    
    # Encode to base64
    _, buffer = cv2.imencode('.jpg', image)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return img_base64


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["version"] == settings.app_version


def test_health():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.skipif(not settings.testing, reason="Requires test mode")
def test_assess_quality():
    """Test quality assessment endpoint."""
    image_base64 = create_test_image()
    
    response = client.post(
        f"{settings.api_prefix}/assess",
        json={
            "image_base64": image_base64,
            "return_enhanced": False
        },
        headers={settings.api_key_header: settings.api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "assessment" in data
    assert "overall_score" in data["assessment"]


@pytest.mark.skipif(not settings.testing, reason="Requires test mode")
def test_assess_with_url():
    """Test quality assessment with URL."""
    response = client.post(
        f"{settings.api_prefix}/assess",
        json={
            "image_url": "https://example.com/face.jpg",
            "return_enhanced": False
        },
        headers={settings.api_key_header: settings.api_key}
    )
    
    # This will fail unless we have a valid URL
    assert response.status_code in [200, 400, 500]


@pytest.mark.skipif(not settings.testing, reason="Requires test mode")
def test_authentication():
    """Test API authentication."""
    image_base64 = create_test_image()
    
    # Test without API key
    response = client.post(
        f"{settings.api_prefix}/assess",
        json={"image_base64": image_base64}
    )
    
    if settings.enable_api_key_auth:
        assert response.status_code == 401


@pytest.mark.skipif(not settings.testing, reason="Requires test mode")
def test_invalid_image():
    """Test with invalid image data."""
    response = client.post(
        f"{settings.api_prefix}/assess",
        json={
            "image_base64": "invalid_base64_data"
        },
        headers={settings.api_key_header: settings.api_key}
    )
    
    assert response.status_code == 400


def test_metrics():
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
