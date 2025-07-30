# DShield Coordination Engine API Documentation

## Overview

The DShield Coordination Engine API provides RESTful endpoints for analyzing attack coordination patterns in cybersecurity research. This API enables researchers and security analysts to submit attack session data and receive detailed coordination analysis results.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.dshield.org`

## Authentication

All API endpoints require authentication using API keys. Include your API key in the request header:

```
X-API-Key: your-api-key-here
```

### API Key Management

- API keys are provided by your administrator
- Keys should be kept secure and not shared
- Rotate keys regularly for security
- Contact support if you need a new key

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Standard endpoints**: 100 requests per minute per API key
- **Bulk analysis**: 5 requests per hour per API key
- **Health checks**: No rate limiting

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages in JSON format:

```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-07-28T10:00:00Z"
}
```

### Common Status Codes

| Code | Description |
|------|-------------|
| 200 | Request successful |
| 201 | Resource created successfully |
| 202 | Request accepted for processing |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid API key |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

## Endpoints

### Health Monitoring

#### GET /health

Basic health check endpoint for service availability.

**Request:**
```bash
curl -X GET "http://localhost:8000/health" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "status": "healthy",
  "service": "dshield-coordination-engine",
  "version": "0.1.0",
  "timestamp": "2025-07-28T10:00:00Z"
}
```

#### GET /health/ready

Readiness check for Kubernetes deployments.

**Request:**
```bash
curl -X GET "http://localhost:8000/health/ready" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "status": "ready",
  "service": "dshield-coordination-engine",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy",
    "elasticsearch": "healthy",
    "llm_service": "healthy"
  }
}
```

#### GET /health/live

Liveness check for container health monitoring.

**Request:**
```bash
curl -X GET "http://localhost:8000/health/live" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "status": "alive",
  "service": "dshield-coordination-engine",
  "uptime": 3600
}
```

### Coordination Analysis

#### POST /analyze/coordination

Submit attack sessions for coordination analysis.

**Request:**
```bash
curl -X POST "http://localhost:8000/analyze/coordination" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "attack_sessions": [
      {
        "source_ip": "192.168.1.100",
        "timestamp": "2025-07-28T10:00:00Z",
        "payload": "GET /admin HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0",
        "target_port": 80,
        "protocol": "HTTP"
      },
      {
        "source_ip": "192.168.1.101",
        "timestamp": "2025-07-28T10:05:00Z",
        "payload": "GET /admin HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0",
        "target_port": 80,
        "protocol": "HTTP"
      }
    ],
    "analysis_depth": "standard",
    "callback_url": "https://example.com/webhook/analysis-complete"
  }'
```

**Response:**
```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "coordination_confidence": null,
  "evidence": null,
  "enrichment_applied": false
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| attack_sessions | Array | Yes | List of attack sessions (2-1000) |
| analysis_depth | String | No | Analysis depth: minimal, standard, deep |
| callback_url | String | No | Callback URL for async results |

**Attack Session Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| source_ip | String | Yes | Source IP address |
| timestamp | String | Yes | Attack timestamp (ISO 8601) |
| payload | String | Yes | Attack payload/signature |
| target_port | Integer | No | Target port (1-65535) |
| protocol | String | No | Network protocol |

#### GET /analyze/{analysis_id}

Retrieve coordination analysis results.

**Request:**
```bash
curl -X GET "http://localhost:8000/analyze/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "coordination_confidence": 0.75,
  "evidence": {
    "temporal_correlation": 0.8,
    "behavioral_similarity": 0.7,
    "infrastructure_clustering": 0.6,
    "geographic_proximity": 0.5,
    "payload_similarity": 0.9
  },
  "enrichment_applied": true
}
```

**Status Values:**

| Status | Description |
|--------|-------------|
| queued | Analysis is waiting to be processed |
| processing | Analysis is currently running |
| completed | Analysis finished successfully |
| failed | Analysis failed with error details |

**Evidence Breakdown:**

| Field | Description | Range |
|-------|-------------|-------|
| temporal_correlation | Timing pattern similarity | 0-1 |
| behavioral_similarity | Attack technique similarity | 0-1 |
| infrastructure_clustering | IP/ASN relationship strength | 0-1 |
| geographic_proximity | Geographic clustering score | 0-1 |
| payload_similarity | Attack signature similarity | 0-1 |

#### POST /analyze/bulk

Submit multiple batches for bulk coordination analysis.

**Request:**
```bash
curl -X POST "http://localhost:8000/analyze/bulk" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "session_batches": [
      [
        {
          "source_ip": "192.168.1.100",
          "timestamp": "2025-07-28T10:00:00Z",
          "payload": "GET /admin HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0"
        }
      ],
      [
        {
          "source_ip": "192.168.1.101",
          "timestamp": "2025-07-28T10:05:00Z",
          "payload": "GET /admin HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0"
        }
      ]
    ],
    "analysis_depth": "standard",
    "callback_url": "https://example.com/webhook/bulk-analysis-complete"
  }'
```

**Response:**
```json
{
  "analysis_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "660e8400-e29b-41d4-a716-446655440001"
  ],
  "status": "queued",
  "batch_count": 2
}
```

## Usage Examples

### Python Client

```python
import requests
import json

# API configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Submit coordination analysis
def submit_analysis(attack_sessions, analysis_depth="standard"):
    url = f"{API_BASE_URL}/analyze/coordination"
    payload = {
        "attack_sessions": attack_sessions,
        "analysis_depth": analysis_depth
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

# Get analysis results
def get_results(analysis_id):
    url = f"{API_BASE_URL}/analyze/{analysis_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# Example usage
attack_sessions = [
    {
        "source_ip": "192.168.1.100",
        "timestamp": "2025-07-28T10:00:00Z",
        "payload": "GET /admin HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0",
        "target_port": 80,
        "protocol": "HTTP"
    },
    {
        "source_ip": "192.168.1.101",
        "timestamp": "2025-07-28T10:05:00Z",
        "payload": "GET /admin HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0",
        "target_port": 80,
        "protocol": "HTTP"
    }
]

# Submit analysis
result = submit_analysis(attack_sessions)
analysis_id = result["analysis_id"]

# Poll for results
import time
while True:
    status = get_results(analysis_id)
    if status["status"] == "completed":
        print(f"Coordination confidence: {status['coordination_confidence']}")
        print(f"Evidence: {status['evidence']}")
        break
    elif status["status"] == "failed":
        print("Analysis failed")
        break
    time.sleep(5)  # Wait 5 seconds before polling again
```

### JavaScript Client

```javascript
// API configuration
const API_BASE_URL = 'http://localhost:8000';
const API_KEY = 'your-api-key-here';

const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
};

// Submit coordination analysis
async function submitAnalysis(attackSessions, analysisDepth = 'standard') {
    const url = `${API_BASE_URL}/analyze/coordination`;
    const payload = {
        attack_sessions: attackSessions,
        analysis_depth: analysisDepth
    };

    const response = await fetch(url, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

// Get analysis results
async function getResults(analysisId) {
    const url = `${API_BASE_URL}/analyze/${analysisId}`;
    const response = await fetch(url, {
        method: 'GET',
        headers: headers
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

// Example usage
const attackSessions = [
    {
        source_ip: '192.168.1.100',
        timestamp: '2025-07-28T10:00:00Z',
        payload: 'GET /admin HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0',
        target_port: 80,
        protocol: 'HTTP'
    },
    {
        source_ip: '192.168.1.101',
        timestamp: '2025-07-28T10:05:00Z',
        payload: 'GET /admin HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0',
        target_port: 80,
        protocol: 'HTTP'
    }
];

// Submit analysis and poll for results
async function runAnalysis() {
    try {
        const result = await submitAnalysis(attackSessions);
        const analysisId = result.analysis_id;

        // Poll for results
        while (true) {
            const status = await getResults(analysisId);

            if (status.status === 'completed') {
                console.log(`Coordination confidence: ${status.coordination_confidence}`);
                console.log(`Evidence:`, status.evidence);
                break;
            } else if (status.status === 'failed') {
                console.log('Analysis failed');
                break;
            }

            // Wait 5 seconds before polling again
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

runAnalysis();
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| API_HOST | API server host | 0.0.0.0 |
| API_PORT | API server port | 8000 |
| API_KEY | API key for authentication | your-api-key-here |
| ENABLE_SWAGGER_UI | Enable Swagger UI | true |
| ENABLE_REDOC | Enable ReDoc | true |
| DEBUG | Enable debug mode | false |

### Analysis Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| analysis_max_sessions | Maximum sessions per analysis | 1000 |
| analysis_timeout_seconds | Analysis timeout | 300 |
| analysis_confidence_threshold | Confidence threshold | 0.7 |
| analysis_temporal_window_seconds | Temporal window | 300 |
| analysis_batch_size | Batch processing size | 100 |

## Monitoring and Observability

### Health Checks

The API provides comprehensive health monitoring endpoints:

- `/health` - Basic availability check
- `/health/ready` - Kubernetes readiness probe
- `/health/live` - Container liveness probe

### Metrics

The API exposes Prometheus metrics at `/metrics`:

- Request counts and durations
- Error rates and types
- Analysis processing metrics
- Resource utilization

### Logging

Structured logging is enabled with the following fields:

- Request ID for tracing
- User/client identification
- Performance metrics
- Error details and stack traces

## Security Considerations

### API Key Security

- Store API keys securely
- Rotate keys regularly
- Use HTTPS in production
- Monitor for suspicious activity

### Input Validation

- All inputs are validated and sanitized
- IP addresses are validated for format
- Timestamps are validated for reasonable ranges
- Payloads are limited in size

### Rate Limiting

- Prevents abuse and DoS attacks
- Configurable per endpoint
- Headers indicate current limits

## Support and Documentation

### Additional Resources

- **Swagger UI**: `/docs` - Interactive API documentation
- **ReDoc**: `/redoc` - Alternative API documentation
- **OpenAPI JSON**: `/openapi.json` - Machine-readable schema

### Getting Help

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/datagen24/dshield-coordination-engine/issues)
- **Security**: [SECURITY.md](.github/SECURITY.md)

### API Versioning

The API follows semantic versioning. Current version: `0.1.0`

Breaking changes will be communicated in advance and may require:
- API version updates
- Client code modifications
- Migration procedures

## Changelog

### Version 0.1.0 (2025-07-28)

- Initial API release
- Coordination analysis endpoints
- Health monitoring endpoints
- Comprehensive documentation
- OpenAPI specification
- Authentication and rate limiting
