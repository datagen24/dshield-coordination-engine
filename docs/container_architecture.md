# DShield Coordination Engine - Container Architecture

## Service Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        MCP[dshield-mcp<br/>Local Analyst Tool]
        WEB[Web Dashboard]
        API_CLIENT[API Clients]
    end
    
    subgraph "Load Balancer"
        LB[nginx/traefik]
    end
    
    subgraph "Application Layer"
        API[Coordination API<br/>FastAPI/Flask]
        WORKFLOW[LangGraph Workflow Engine]
        QUEUE[Task Queue<br/>Celery/RQ]
    end
    
    subgraph "Analysis Services"
        PATTERN[Pattern Analysis Service]
        TOOLS[Tool Coordination Service]
        CONFIDENCE[Confidence Scoring Service]
        ENRICHER[ES Enrichment Service]
    end
    
    subgraph "Infrastructure Services"
        LLM[Local LLM Service<br/>ollama/vllm]
        REDIS[Redis<br/>Cache/Queue]
        POSTGRES[PostgreSQL<br/>Analysis Results]
    end
    
    subgraph "External Systems"
        ES[(Elasticsearch<br/>Attack Data)]
        BGP[BGP APIs]
        INTEL[Threat Intel APIs]
    end
    
    MCP --> LB
    WEB --> LB
    API_CLIENT --> LB
    LB --> API
    API --> WORKFLOW
    API --> QUEUE
    WORKFLOW --> PATTERN
    WORKFLOW --> TOOLS
    WORKFLOW --> CONFIDENCE
    WORKFLOW --> ENRICHER
    PATTERN --> LLM
    CONFIDENCE --> LLM
    TOOLS --> BGP
    TOOLS --> INTEL
    ENRICHER --> ES
    QUEUE --> REDIS
    API --> POSTGRES
    PATTERN --> REDIS
```

## Container Definitions

### docker-compose.yml
```yaml
version: '3.8'

services:
  # API Gateway & Web Interface
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - coordination-api

  # Main Coordination API
  coordination-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/coordination
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - LLM_SERVICE_URL=http://llm-service:8000
    depends_on:
      - postgres
      - redis
      - llm-service
    volumes:
      - ./config:/app/config
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  # LangGraph Workflow Engine
  workflow-engine:
    build:
      context: .
      dockerfile: Dockerfile.workflow
    environment:
      - REDIS_URL=redis://redis:6379
      - LLM_SERVICE_URL=http://llm-service:8000
    depends_on:
      - redis
      - llm-service
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 4G
          cpus: '2.0'

  # Local LLM Service
  llm-service:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    environment:
      - OLLAMA_MODELS=llama3.1:8b,mistral:7b
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '4.0'
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Background Task Processing
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - CELERY_BROKER_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:pass@postgres:5432/coordination
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 4
      resources:
        limits:
          memory: 3G
          cpus: '1.5'

  # Cache & Message Queue
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  # Analysis Results Storage
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=coordination
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  # Monitoring & Observability
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  ollama-data:
  redis-data:
  postgres-data:
  grafana-data:
```

## API Interface Design

### FastAPI Service
```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid

app = FastAPI(title="DShield Coordination Engine")

class CoordinationRequest(BaseModel):
    attack_sessions: List[Dict]
    analysis_depth: str = "standard"  # standard, deep, minimal
    callback_url: Optional[str] = None

class CoordinationResponse(BaseModel):
    analysis_id: str
    status: str  # queued, processing, completed, failed
    coordination_confidence: Optional[float] = None
    evidence: Optional[Dict] = None
    enrichment_applied: bool = False

@app.post("/analyze/coordination")
async def analyze_coordination(
    request: CoordinationRequest,
    background_tasks: BackgroundTasks
):
    analysis_id = str(uuid.uuid4())
    
    # Queue analysis task
    background_tasks.add_task(
        process_coordination_analysis,
        analysis_id,
        request.attack_sessions,
        request.analysis_depth
    )
    
    return CoordinationResponse(
        analysis_id=analysis_id,
        status="queued"
    )

@app.get("/analyze/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    # Return analysis results from database
    pass

@app.post("/analyze/bulk")
async def bulk_analysis(session_batches: List[List[Dict]]):
    # Process multiple batches for continuous monitoring
    pass
```

## Integration with dshield-mcp

### Local MCP Client Integration
```python
# In dshield-mcp
import requests
from typing import List, Dict

class CoordinationEngineClient:
    def __init__(self, engine_url: str, api_key: str):
        self.engine_url = engine_url
        self.api_key = api_key
    
    def analyze_coordination(self, attack_sessions: List[Dict]) -> Dict:
        response = requests.post(
            f"{self.engine_url}/analyze/coordination",
            json={"attack_sessions": attack_sessions},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
    
    def get_results(self, analysis_id: str) -> Dict:
        response = requests.get(
            f"{self.engine_url}/analyze/{analysis_id}",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()

# MCP Tool Integration
@mcp_tool("analyze_attack_coordination")
def analyze_coordination_mcp(attack_data: str) -> str:
    client = CoordinationEngineClient(
        engine_url=os.getenv("COORDINATION_ENGINE_URL"),
        api_key=os.getenv("COORDINATION_API_KEY")
    )
    
    sessions = parse_attack_data(attack_data)
    result = client.analyze_coordination(sessions)
    
    return f"Analysis queued with ID: {result['analysis_id']}"
```

## Deployment Considerations

### Security
```dockerfile
# Dockerfile.api - Security hardened
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 coordinator
USER coordinator

# Install dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Copy application
COPY --chown=coordinator:coordinator . /app
WORKDIR /app

# Security settings
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Resource Scaling
```yaml
# Kubernetes deployment example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coordination-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: coordination-api
  template:
    spec:
      containers:
      - name: api
        image: dshield/coordination-api:latest
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
```

## Operational Benefits

### Centralized Analysis
- **Shared Intelligence**: All analysts benefit from coordination detection
- **Consistent Results**: Standardized analysis across team
- **Resource Efficiency**: Single GPU server vs multiple local setups

### Scalability
- **Horizontal Scaling**: Add workers for increased throughput  
- **Load Distribution**: Balance analysis across multiple containers
- **Resource Optimization**: Dedicated hardware for ML workloads

### Monitoring & Observability
- **Analysis Metrics**: Track coordination detection accuracy
- **Performance Monitoring**: API response times, queue lengths
- **Resource Usage**: GPU utilization, memory consumption
- **Error Tracking**: Failed analyses, tool integration issues

This architecture gives you production-grade coordination detection while keeping your local MCP tool lightweight and focused on analyst interaction.
