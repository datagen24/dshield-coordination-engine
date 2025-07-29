# DShield Coordination Engine

AI-powered attack coordination detection service for cybersecurity research and analysis.

## Overview

The DShield Coordination Engine is a server-side service designed to analyze attack patterns from honeypot data and distinguish between coordinated campaigns and coincidental timing. This addresses critical academic and operational needs for evidence-based attribution in cybersecurity research.

## Features

- **Temporal Correlation Analysis**: Detect timing patterns with statistical significance testing
- **Behavioral Clustering**: Group attacks by TTP similarity with confidence scores
- **Infrastructure Relationship Mapping**: Analyze IP/ASN relationships, geographic clustering
- **Coordination Confidence Scoring**: Provide 0-1 confidence score with evidence breakdown
- **RESTful API**: OpenAPI 3.0 specification with authentication and rate limiting
- **dshield-mcp Integration**: MCP tool for coordination analysis queries
- **Academic Credibility**: Reproducible analysis with documented methodology

## Architecture

The system is built using:
- **FastAPI**: RESTful API service
- **LangGraph**: Multi-agent analysis orchestration
- **Local LLM**: Ollama-based inference for pattern analysis
- **PostgreSQL**: Analysis results storage
- **Redis**: Caching and task queues
- **Docker**: Containerized deployment

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- 16GB+ RAM (32GB recommended)
- GPU support for LLM inference (optional)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/datagen24/dshield-coordination-engine.git
   cd dshield-coordination-engine
   ```

2. **Install dependencies**
   ```bash
   pip install uv
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

5. **Run tests**
   ```bash
   pytest
   ```

### API Usage

```python
import requests

# Submit coordination analysis
response = requests.post(
    "http://localhost:8000/analyze/coordination",
    json={
        "attack_sessions": [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "example attack payload"
            }
        ],
        "analysis_depth": "standard"
    },
    headers={"Authorization": "Bearer your-api-key"}
)

analysis_id = response.json()["analysis_id"]

# Get results
results = requests.get(
    f"http://localhost:8000/analyze/{analysis_id}",
    headers={"Authorization": "Bearer your-api-key"}
)

print(f"Coordination confidence: {results.json()['coordination_confidence']}")
```

## Development

### Project Structure

```
dshield-coordination-engine/
├── services/           # Core services
│   ├── api/           # FastAPI coordination service
│   ├── workflow/      # LangGraph workflow engine
│   ├── workers/       # Celery background tasks
│   └── llm/          # LLM service wrapper
├── agents/            # LangGraph agent definitions
├── tools/             # External tool integrations
├── tests/             # Test suite
├── docker/            # Container definitions
├── docs/              # Documentation
└── scripts/           # Development utilities
```

### Code Quality

We maintain high code quality standards:

- **Type Hints**: All functions include type annotations
- **Testing**: >90% code coverage required
- **Security**: Automated security scanning with Bandit, Safety, and Semgrep
- **Linting**: Ruff for code formatting and linting
- **Documentation**: Comprehensive API and code documentation

### Contributing

1. Create a feature branch from `main`
2. Make your changes with tests
3. Run the full test suite: `pytest`
4. Run security checks: `bandit -r . && safety check`
5. Submit a pull request

## Security

This project follows strict security guidelines:

- **Authentication**: JWT-based API authentication
- **Input Validation**: Comprehensive input sanitization
- **Secrets Management**: 1Password CLI integration
- **Container Security**: Non-root users, minimal base images
- **Vulnerability Scanning**: Automated security testing in CI/CD

## Performance

- **Analysis Latency**: < 5 minutes for 1000 attack sessions
- **Concurrent Analysis**: Handle 10+ simultaneous requests
- **Resource Efficiency**: <16GB RAM, <8GB GPU memory per analysis
- **Scalability**: Horizontal scaling with container orchestration

## Academic Use

The coordination engine is designed for academic research:

- **Reproducible Analysis**: Deterministic algorithms with documented methods
- **Confidence Scoring**: Statistical basis for coordination claims
- **Evidence Chain**: Clear audit trail of analysis decisions
- **Validation Framework**: Test against known coordinated/independent attacks

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/datagen24/dshield-coordination-engine/issues)
- **Security**: [SECURITY.md](.github/SECURITY.md)

## Related Projects

- [dshield-mcp](https://github.com/datagen24/dsheild-mcp): Model Context Protocol server for cybersecurity analysis
- [DShield](https://dshield.org): Distributed intrusion detection system
