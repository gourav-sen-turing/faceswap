# API Examples

Complete examples for integrating with the Face Quality Assessment API.

## Table of Contents
1. [Python Examples](#python-examples)
2. [JavaScript Examples](#javascript-examples)
3. [cURL Examples](#curl-examples)
4. [Java Examples](#java-examples)
5. [Go Examples](#go-examples)

## Python Examples

### Basic Quality Assessment

```python
import requests
import base64
import json

# Configuration
API_URL = "http://localhost/api/v1"
API_KEY = "your-api-key"

def assess_face_quality(image_path):
    """Assess face quality from local image."""
    
    # Read and encode image
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Prepare request
    payload = {
        "image_base64": image_base64,
        "return_enhanced": False
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Make request
    response = requests.post(
        f"{API_URL}/assess",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        assessment = result['assessment']
        
        print(f"Overall Score: {assessment['overall_score']:.3f}")
        print(f"Decision: {assessment['decision']}")
        print(f"Processing Time: {assessment['processing_time_ms']:.2f}ms")
        
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

# Usage
result = assess_face_quality("face.jpg")
```

### Batch Processing

```python
import requests
import base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def assess_batch(image_paths):
    """Process multiple images in batch."""
    
    images = []
    for path in image_paths:
        with open(path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        images.append({"image_base64": image_base64})
    
    payload = {
        "images": images,
        "parallel": True,
        "max_workers": 4
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_URL}/assess/batch",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Batch ID: {result['batch_id']}")
        print(f"Total: {result['total_images']}")
        print(f"Successful: {result['successful']}")
        print(f"Failed: {result['failed']}")
        
        for i, res in enumerate(result['results']):
            if res['status'] == 'success':
                score = res['assessment']['overall_score']
                decision = res['assessment']['decision']
                print(f"Image {i+1}: Score={score:.3f}, Decision={decision}")
        
        return result
    else:
        print(f"Error: {response.status_code}")
        return None

# Usage
image_paths = list(Path("images").glob("*.jpg"))
results = assess_batch(image_paths)
```

### Image Enhancement

```python
def enhance_image(image_path, output_path):
    """Enhance image quality."""
    
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {
        "image_base64": image_base64,
        "scale_factor": 4,
        "enhance_face": True,
        "denoise": True
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_URL}/enhance",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        
        # Decode and save enhanced image
        enhanced_data = base64.b64decode(result['enhanced_image_base64'])
        with open(output_path, "wb") as f:
            f.write(enhanced_data)
        
        print(f"Original: {result['original_size']}")
        print(f"Enhanced: {result['enhanced_size']}")
        print(f"Saved to: {output_path}")
        
        return result
    else:
        print(f"Error: {response.status_code}")
        return None

# Usage
enhance_image("face.jpg", "face_enhanced.jpg")
```

### Async Client

```python
import aiohttp
import asyncio
import base64

async def assess_async(session, image_path):
    """Async quality assessment."""
    
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {"image_base64": image_base64}
    headers = {"X-API-Key": API_KEY}
    
    async with session.post(
        f"{API_URL}/assess",
        json=payload,
        headers=headers
    ) as response:
        return await response.json()

async def assess_multiple_async(image_paths):
    """Process multiple images asynchronously."""
    
    async with aiohttp.ClientSession() as session:
        tasks = [assess_async(session, path) for path in image_paths]
        results = await asyncio.gather(*tasks)
        return results

# Usage
image_paths = ["face1.jpg", "face2.jpg", "face3.jpg"]
results = asyncio.run(assess_multiple_async(image_paths))
```

## JavaScript Examples

### Node.js Client

```javascript
const axios = require('axios');
const fs = require('fs');

const API_URL = 'http://localhost/api/v1';
const API_KEY = 'your-api-key';

async function assessFaceQuality(imagePath) {
    try {
        // Read and encode image
        const imageBuffer = fs.readFileSync(imagePath);
        const imageBase64 = imageBuffer.toString('base64');
        
        // Make request
        const response = await axios.post(
            `${API_URL}/assess`,
            {
                image_base64: imageBase64,
                return_enhanced: false
            },
            {
                headers: {
                    'X-API-Key': API_KEY,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        const { assessment } = response.data;
        console.log(`Overall Score: ${assessment.overall_score.toFixed(3)}`);
        console.log(`Decision: ${assessment.decision}`);
        console.log(`Processing Time: ${assessment.processing_time_ms.toFixed(2)}ms`);
        
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        return null;
    }
}

// Usage
assessFaceQuality('face.jpg');
```

### Browser Client

```javascript
// Upload and assess
async function assessImageFromFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('return_enhanced', 'false');
    
    try {
        const response = await fetch('/api/v1/assess/upload', {
            method: 'POST',
            headers: {
                'X-API-Key': 'your-api-key'
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            console.log('Quality Score:', result.assessment.overall_score);
            console.log('Decision:', result.assessment.decision);
            return result;
        } else {
            console.error('Error:', result);
            return null;
        }
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

// Usage with file input
document.getElementById('fileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        const result = await assessImageFromFile(file);
        // Display results
    }
});
```

### React Component

```jsx
import React, { useState } from 'react';
import axios from 'axios';

function FaceQualityAssessment() {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    
    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;
        
        setLoading(true);
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await axios.post(
                '/api/v1/assess/upload',
                formData,
                {
                    headers: {
                        'X-API-Key': process.env.REACT_APP_API_KEY
                    }
                }
            );
            
            setResult(response.data);
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div>
            <input type="file" onChange={handleFileUpload} accept="image/*" />
            
            {loading && <p>Processing...</p>}
            
            {result && (
                <div>
                    <h3>Quality Assessment Results</h3>
                    <p>Overall Score: {result.assessment.overall_score.toFixed(3)}</p>
                    <p>Decision: {result.assessment.decision}</p>
                    <p>Processing Time: {result.assessment.processing_time_ms.toFixed(2)}ms</p>
                    
                    <h4>Recommendations:</h4>
                    <ul>
                        {result.assessment.recommendations.map((rec, i) => (
                            <li key={i}>{rec}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

export default FaceQualityAssessment;
```

## cURL Examples

### Basic Assessment

```bash
# From base64
curl -X POST http://localhost/api/v1/assess \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "'"$(base64 -w 0 face.jpg)"'",
    "return_enhanced": false
  }'

# From URL
curl -X POST http://localhost/api/v1/assess \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/face.jpg"
  }'

# From file upload
curl -X POST http://localhost/api/v1/assess/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@face.jpg" \
  -F "return_enhanced=false"
```

### Custom Thresholds

```bash
curl -X POST http://localhost/api/v1/assess \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "'"$(base64 -w 0 face.jpg)"'",
    "custom_thresholds": {
      "accept": 0.8,
      "enhance": 0.6,
      "reject": 0.4
    }
  }'
```

### Enhancement

```bash
curl -X POST http://localhost/api/v1/enhance \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "'"$(base64 -w 0 face.jpg)"'",
    "scale_factor": 4,
    "enhance_face": true,
    "denoise": true
  }' | jq -r '.enhanced_image_base64' | base64 -d > enhanced.jpg
```

## Java Examples

```java
import java.io.*;
import java.net.http.*;
import java.util.Base64;
import org.json.*;

public class FaceQualityClient {
    private static final String API_URL = "http://localhost/api/v1";
    private static final String API_KEY = "your-api-key";
    
    public static JSONObject assessFaceQuality(String imagePath) throws Exception {
        // Read and encode image
        byte[] imageBytes = Files.readAllBytes(Paths.get(imagePath));
        String imageBase64 = Base64.getEncoder().encodeToString(imageBytes);
        
        // Prepare request
        JSONObject payload = new JSONObject();
        payload.put("image_base64", imageBase64);
        payload.put("return_enhanced", false);
        
        // Make request
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_URL + "/assess"))
            .header("X-API-Key", API_KEY)
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
            .build();
        
        HttpResponse<String> response = client.send(
            request,
            HttpResponse.BodyHandlers.ofString()
        );
        
        if (response.statusCode() == 200) {
            JSONObject result = new JSONObject(response.body());
            JSONObject assessment = result.getJSONObject("assessment");
            
            System.out.println("Overall Score: " + assessment.getDouble("overall_score"));
            System.out.println("Decision: " + assessment.getString("decision"));
            
            return result;
        } else {
            throw new Exception("API Error: " + response.statusCode());
        }
    }
    
    public static void main(String[] args) {
        try {
            assessFaceQuality("face.jpg");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

## Go Examples

```go
package main

import (
    "bytes"
    "encoding/base64"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "net/http"
)

const (
    APIURL = "http://localhost/api/v1"
    APIKey = "your-api-key"
)

type AssessmentRequest struct {
    ImageBase64    string `json:"image_base64"`
    ReturnEnhanced bool   `json:"return_enhanced"`
}

type AssessmentResponse struct {
    RequestID  string     `json:"request_id"`
    Status     string     `json:"status"`
    Assessment Assessment `json:"assessment"`
}

type Assessment struct {
    OverallScore     float64 `json:"overall_score"`
    Decision         string  `json:"decision"`
    ProcessingTimeMs float64 `json:"processing_time_ms"`
}

func assessFaceQuality(imagePath string) (*AssessmentResponse, error) {
    // Read and encode image
    imageBytes, err := ioutil.ReadFile(imagePath)
    if err != nil {
        return nil, err
    }
    imageBase64 := base64.StdEncoding.EncodeToString(imageBytes)
    
    // Prepare request
    payload := AssessmentRequest{
        ImageBase64:    imageBase64,
        ReturnEnhanced: false,
    }
    
    payloadBytes, err := json.Marshal(payload)
    if err != nil {
        return nil, err
    }
    
    // Make request
    req, err := http.NewRequest(
        "POST",
        APIURL+"/assess",
        bytes.NewBuffer(payloadBytes),
    )
    if err != nil {
        return nil, err
    }
    
    req.Header.Set("X-API-Key", APIKey)
    req.Header.Set("Content-Type", "application/json")
    
    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    body, err := ioutil.ReadAll(resp.Body)
    if err != nil {
        return nil, err
    }
    
    var result AssessmentResponse
    err = json.Unmarshal(body, &result)
    if err != nil {
        return nil, err
    }
    
    fmt.Printf("Overall Score: %.3f\n", result.Assessment.OverallScore)
    fmt.Printf("Decision: %s\n", result.Assessment.Decision)
    
    return &result, nil
}

func main() {
    result, err := assessFaceQuality("face.jpg")
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
    fmt.Printf("Result: %+v\n", result)
}
```

## Error Handling

### Python Error Handling

```python
from requests.exceptions import RequestException, Timeout

def assess_with_retry(image_path, max_retries=3):
    """Assess with retry logic."""
    
    for attempt in range(max_retries):
        try:
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            response = requests.post(
                f"{API_URL}/assess",
                json={"image_base64": image_base64},
                headers={"X-API-Key": API_KEY},
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except Timeout:
            print(f"Timeout on attempt {attempt + 1}")
            if attempt == max_retries - 1:
                raise
        except RequestException as e:
            print(f"Request failed: {e}")
            if attempt == max_retries - 1:
                raise
        
        time.sleep(2 ** attempt)  # Exponential backoff
```

## Rate Limiting

### Python Rate Limiter

```python
import time
from functools import wraps

class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            self.calls = [c for c in self.calls if c > now - self.period]
            
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                time.sleep(sleep_time)
            
            self.calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper

# Usage
@RateLimiter(max_calls=60, period=60)  # 60 calls per minute
def assess_rate_limited(image_path):
    return assess_face_quality(image_path)
```
