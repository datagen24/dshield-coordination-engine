# DShield Coordination Engine - Development Guidelines

## Document Information
- **Version**: 1.0
- **Date**: July 28, 2025
- **Project**: DShield Coordination Engine
- **Scope**: Development standards and security requirements

## Development Environment Setup

### Required Tools
```bash
# Core development tools
python 3.11+
docker & docker-compose
git
pre-commit
uv (Python package manager)

# Security tools
bandit (security linting)
safety (dependency vulnerability scanning)
semgrep (static analysis)

# Testing tools
pytest
pytest-cov
pytest-asyncio
```

### Repository Structure Standards
```
dshield-coordination-engine/
├── .github/
│   ├── workflows/           # CI/CD pipelines
│   └── SECURITY.md         # Security policy
├── services/
│   ├── api/                # FastAPI coordination service
│   ├── workflow/           # LangGraph workflow engine
│   ├── workers/            # Celery background tasks
│   └── llm/               # LLM service wrapper
├── agents/                 # LangGraph agent definitions
├── tools/                  # External tool integrations
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── security/          # Security tests
├── docker/                # Container definitions
├── docs/                  # Documentation
├── scripts/               # Development utilities
├── requirements/          # Dependency files
│   ├── base.txt
│   ├── dev.txt
│   └── security.txt
└── pyproject.toml         # Project configuration
```

## Security Requirements

### Code Security Standards

#### Input Validation
```python
# REQUIRED: Validate all external inputs
from pydantic import BaseModel, validator
from typing import List, Dict

class AttackSession(BaseModel):
    source_ip: str
    timestamp: datetime
    payload: str

    @validator('source_ip')
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address format')

    @validator('payload')
    def validate_payload_size(cls, v):
        if len(v) > 10000:  # 10KB limit
            raise ValueError('Payload too large')
        return v
```

#### Authentication & Authorization
```python
# REQUIRED: JWT token validation for all API endpoints
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

def verify_token(token: str = Depends(security)):
    try:
        payload = jwt.decode(
            token.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
```

#### Secrets Management
```python
# REQUIRED: Use environment variables or vault for secrets
import os
from functools import lru_cache

@lru_cache()
def get_settings():
    return Settings(
        database_url=os.getenv("DATABASE_URL"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        # NEVER hardcode secrets in source code
    )
```

### Container Security

#### Dockerfile Security Standards
```dockerfile
# REQUIRED: Non-root user, minimal base image
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 coordinator && \
    mkdir -p /app && \
    chown coordinator:coordinator /app

# Install security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Switch to non-root user
USER coordinator
WORKDIR /app

# Install dependencies as non-root
COPY --chown=coordinator:coordinator requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=coordinator:coordinator . .

# Security settings
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Run as non-root
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dependency Security
```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Bandit Security Scan
        run: bandit -r . -f json -o bandit-report.json
      - name: Run Safety Check
        run: safety check --json --output safety-report.json
      - name: Run Semgrep
        run: semgrep --config=auto --json --output=semgrep-report.json .
```

## Code Quality Standards

### Python Style Guide
```python
# REQUIRED: Follow PEP 8 with these additions

# Type hints for all functions
def analyze_coordination(
    attack_sessions: List[AttackSession],
    confidence_threshold: float = 0.7
) -> CoordinationResult:
    """Analyze attack sessions for coordination patterns.

    Args:
        attack_sessions: List of attack session data
        confidence_threshold: Minimum confidence for positive detection

    Returns:
        CoordinationResult with confidence score and evidence

    Raises:
        ValidationError: If input data is invalid
    """
    pass

# Error handling with specific exceptions
class CoordinationAnalysisError(Exception):
    """Base exception for coordination analysis errors."""
    pass

class InsufficientDataError(CoordinationAnalysisError):
    """Raised when insufficient data for analysis."""
    pass

# Logging with structured format
import logging
import structlog

logger = structlog.get_logger(__name__)

def process_analysis(session_id: str):
    logger.info(
        "Starting coordination analysis",
        session_id=session_id,
        analysis_type="temporal_correlation"
    )
```

### Testing Requirements

#### Unit Testing Standards
```python
# REQUIRED: >90% code coverage
import pytest
from unittest.mock import Mock, patch

class TestCoordinationAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return CoordinationAnalyzer(
            llm_client=Mock(),
            confidence_threshold=0.7
        )

    @pytest.fixture
    def sample_sessions(self):
        return [
            AttackSession(
                source_ip="192.168.1.1",
                timestamp=datetime.now(),
                payload="test payload"
            )
        ]

    def test_coordination_detection_positive(self, analyzer, sample_sessions):
        """Test coordination detection with coordinated attacks."""
        with patch.object(analyzer.pattern_analyzer, 'analyze') as mock_analyze:
            mock_analyze.return_value = {"coordination_score": 0.9}

            result = analyzer.analyze_coordination(sample_sessions)

            assert result.coordination_confidence > 0.7
            assert result.is_coordinated is True

    def test_coordination_detection_negative(self, analyzer, sample_sessions):
        """Test coordination detection with random attacks."""
        with patch.object(analyzer.pattern_analyzer, 'analyze') as mock_analyze:
            mock_analyze.return_value = {"coordination_score": 0.3}

            result = analyzer.analyze_coordination(sample_sessions)

            assert result.coordination_confidence < 0.7
            assert result.is_coordinated is False
```

#### Integration Testing
```python
# REQUIRED: Test all service interactions
import pytest_asyncio
from httpx import AsyncClient

@pytest_asyncio.async_test
async def test_coordination_api_integration():
    """Test full API workflow."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Submit analysis request
        response = await client.post(
            "/analyze/coordination",
            json={"attack_sessions": test_sessions},
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        analysis_id = response.json()["analysis_id"]

        # Poll for results
        for _ in range(30):  # 30 second timeout
            result_response = await client.get(
                f"/analyze/{analysis_id}",
                headers={"Authorization": f"Bearer {test_token}"}
            )

            if result_response.json()["status"] == "completed":
                break
            await asyncio.sleep(1)

        assert result_response.json()["status"] == "completed"
        assert "coordination_confidence" in result_response.json()
```

### Performance Requirements

#### Response Time Standards
```python
# REQUIRED: Performance monitoring
import time
from functools import wraps

def performance_monitor(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()

        logger.info(
            "Function performance",
            function=func.__name__,
            duration=end_time - start_time,
            args_count=len(args)
        )

        # Alert if exceeds threshold
        if end_time - start_time > 300:  # 5 minutes
            logger.warning(
                "Performance threshold exceeded",
                function=func.__name__,
                duration=end_time - start_time
            )

        return result
    return wrapper

@performance_monitor
async def analyze_coordination(sessions: List[AttackSession]):
    # Implementation
    pass
```

#### Resource Usage Monitoring
```python
# REQUIRED: Memory and CPU monitoring
import psutil
import asyncio

class ResourceMonitor:
    def __init__(self):
        self.max_memory_mb = 16000  # 16GB limit
        self.max_cpu_percent = 80

    async def monitor_resources(self):
        while True:
            memory_usage = psutil.virtual_memory().used / 1024 / 1024
            cpu_usage = psutil.cpu_percent()

            if memory_usage > self.max_memory_mb:
                logger.warning(
                    "Memory usage exceeded threshold",
                    current_mb=memory_usage,
                    threshold_mb=self.max_memory_mb
                )

            if cpu_usage > self.max_cpu_percent:
                logger.warning(
                    "CPU usage exceeded threshold",
                    current_percent=cpu_usage,
                    threshold_percent=self.max_cpu_percent
                )

            await asyncio.sleep(30)  # Check every 30 seconds
```

## CI/CD Pipeline Requirements

### GitHub Actions Workflow
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run security checks
        run: |
          bandit -r . -f json
          safety check
          semgrep --config=auto .

      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          docker build -t coordination-api:${{ github.sha }} -f docker/Dockerfile.api .
          docker build -t coordination-worker:${{ github.sha }} -f docker/Dockerfile.worker .

      - name: Run container security scan
        run: |
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy image coordination-api:${{ github.sha }}

  deploy:
    needs: [test, build]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to staging
        run: |
          # Deployment logic here
          echo "Deploying to staging environment"
```

## Documentation Requirements

### API Documentation
```python
# REQUIRED: OpenAPI documentation
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="DShield Coordination Engine API",
    description="AI-powered attack coordination detection service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

class CoordinationRequest(BaseModel):
    """Request model for coordination analysis."""
    attack_sessions: List[AttackSession]
    analysis_depth: str = "standard"

    class Config:
        schema_extra = {
            "example": {
                "attack_sessions": [
                    {
                        "source_ip": "192.168.1.1",
                        "timestamp": "2025-07-28T10:00:00Z",
                        "payload": "example attack payload"
                    }
                ],
                "analysis_depth": "standard"
            }
        }

@app.post(
    "/analyze/coordination",
    response_model=CoordinationResponse,
    summary="Analyze attack coordination patterns",
    description="Submit attack session data for coordination analysis"
)
async def analyze_coordination(request: CoordinationRequest):
    """Analyze attack sessions for coordination patterns."""
    pass
```

### Code Documentation
```python
# REQUIRED: Comprehensive docstrings
def calculate_temporal_correlation(
    sessions: List[AttackSession],
    time_window_seconds: int = 300
) -> float:
    """Calculate temporal correlation between attack sessions.

    Analyzes timing patterns to determine if attacks show coordination
    based on synchronization within specified time windows.

    Args:
        sessions: List of attack session objects with timestamps
        time_window_seconds: Maximum time difference for correlation (default: 5 minutes)

    Returns:
        Correlation coefficient between 0.0 (no correlation) and 1.0 (perfect correlation)

    Raises:
        InsufficientDataError: If fewer than 2 sessions provided
        ValidationError: If session timestamps are invalid

    Example:
        >>> sessions = [session1, session2, session3]
        >>> correlation = calculate_temporal_correlation(sessions, 300)
        >>> print(f"Temporal correlation: {correlation:.2f}")
        Temporal correlation: 0.85

    References:
        - Statistical correlation analysis methodology
        - Academic paper: "Coordinated Attack Detection in Honeypot Networks"
    """
    pass
```

## Review & Approval Process

### Code Review Requirements
- [ ] Security review for all authentication/authorization code
- [ ] Performance review for analysis algorithms
- [ ] Architecture review for new service components
- [ ] Documentation review for API changes

### Pre-merge Checklist
- [ ] All tests passing (unit, integration, security)
- [ ] Code coverage >90%
- [ ] Security scan clean (bandit, safety, semgrep)
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Peer review approved

### Deployment Approval
- [ ] Security team approval for production deployment
- [ ] Performance testing completed
- [ ] Monitoring and alerting configured
- [ ] Rollback plan documented
- [ ] Change management approval

---

**Document Status**: Active Development Guidelines
**Last Updated**: July 28, 2025
**Next Review**: August 28, 2025
