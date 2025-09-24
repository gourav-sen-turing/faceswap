#!/usr/bin/env python3
"""
API Testing Script for Face Quality Assessment Service
"""
import requests
import base64
import json
import sys
import os
from pathlib import Path
import numpy as np
import cv2


def create_test_image():
    """Create a simple test image with a face-like pattern."""
    # Create image
    image = np.ones((400, 400, 3), dtype=np.uint8) * 200
    
    # Draw face
    cv2.circle(image, (200, 200), 100, (180, 180, 180), -1)
    cv2.circle(image, (170, 180), 15, (50, 50, 50), -1)
    cv2.circle(image, (230, 180), 15, (50, 50, 50), -1)
    cv2.ellipse(image, (200, 220), (40, 20), 0, 0, 180, (50, 50, 50), 2)
    
    # Encode
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')


def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent.parent / '.env'
    env_vars = {}
    
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    return env_vars


def test_health(base_url):
    """Test health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_assessment(base_url, api_key):
    """Test quality assessment endpoint."""
    print("\n=== Testing Quality Assessment ===")
    
    # Create test image
    image_base64 = create_test_image()
    
    payload = {
        "image_base64": image_base64,
        "return_enhanced": False
    }
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/assess",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nRequest ID: {data.get('request_id')}")
            print(f"Status: {data.get('status')}")
            
            if 'assessment' in data:
                assessment = data['assessment']
                print(f"\nQuality Assessment:")
                print(f"  Overall Score: {assessment.get('overall_score'):.3f}")
                print(f"  Decision: {assessment.get('decision')}")
                print(f"  Processing Time: {assessment.get('processing_time_ms'):.2f}ms")
                
                if 'blur_metrics' in assessment:
                    print(f"\n  Blur Metrics:")
                    print(f"    Laplacian Variance: {assessment['blur_metrics'].get('laplacian_variance'):.2f}")
                    print(f"    Is Blurry: {assessment['blur_metrics'].get('is_blurry')}")
                
                if 'pose_metrics' in assessment:
                    print(f"\n  Pose Metrics:")
                    print(f"    Yaw: {assessment['pose_metrics'].get('yaw'):.2f}°")
                    print(f"    Pitch: {assessment['pose_metrics'].get('pitch'):.2f}°")
                    print(f"    Roll: {assessment['pose_metrics'].get('roll'):.2f}°")
                    print(f"    Is Frontal: {assessment['pose_metrics'].get('is_frontal')}")
                
                if 'lighting_metrics' in assessment:
                    print(f"\n  Lighting Metrics:")
                    print(f"    Brightness: {assessment['lighting_metrics'].get('brightness'):.2f}")
                    print(f"    Contrast: {assessment['lighting_metrics'].get('contrast'):.2f}")
                    print(f"    Is Well Lit: {assessment['lighting_metrics'].get('is_well_lit')}")
                
                if 'recommendations' in assessment:
                    print(f"\n  Recommendations:")
                    for rec in assessment['recommendations']:
                        print(f"    - {rec}")
            
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_metrics(base_url, api_key):
    """Test metrics endpoint."""
    print("\n=== Testing Metrics Endpoint ===")
    
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(
            f"{base_url}/api/v1/metrics",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nService Metrics:")
            print(f"  Total Requests: {data.get('total_requests')}")
            print(f"  Successful Requests: {data.get('successful_requests')}")
            print(f"  Failed Requests: {data.get('failed_requests')}")
            print(f"  Avg Processing Time: {data.get('average_processing_time_ms'):.2f}ms")
            print(f"  Quality Distribution: {data.get('quality_distribution')}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_enhancement(base_url, api_key):
    """Test image enhancement endpoint."""
    print("\n=== Testing Image Enhancement ===")
    
    # Create test image
    image_base64 = create_test_image()
    
    payload = {
        "image_base64": image_base64,
        "scale_factor": 2,
        "enhance_face": True,
        "denoise": True
    }
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/enhance",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nEnhancement Results:")
            print(f"  Request ID: {data.get('request_id')}")
            print(f"  Original Size: {data.get('original_size')}")
            print(f"  Enhanced Size: {data.get('enhanced_size')}")
            print(f"  Processing Time: {data.get('processing_time_ms'):.2f}ms")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main test execution."""
    print("=" * 60)
    print("Face Quality Assessment Service - API Test Suite")
    print("=" * 60)
    
    # Load configuration
    env_vars = load_env()
    base_url = os.getenv('BASE_URL', 'http://localhost')
    api_key = env_vars.get('API_KEY', 'your-api-key')
    
    print(f"\nConfiguration:")
    print(f"  Base URL: {base_url}")
    print(f"  API Key: {api_key[:10]}..." if len(api_key) > 10 else f"  API Key: {api_key}")
    
    # Run tests
    results = []
    
    results.append(("Health Check", test_health(base_url)))
    results.append(("Quality Assessment", test_assessment(base_url, api_key)))
    results.append(("Metrics", test_metrics(base_url, api_key)))
    results.append(("Enhancement", test_enhancement(base_url, api_key)))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<40} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Exit code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
