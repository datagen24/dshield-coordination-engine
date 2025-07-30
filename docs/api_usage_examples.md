# DShield Coordination Engine API Usage Examples

This document provides comprehensive usage examples for the DShield Coordination Engine API, covering common scenarios and practical implementations.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication Setup](#authentication-setup)
3. [Basic Coordination Analysis](#basic-coordination-analysis)
4. [Advanced Analysis Scenarios](#advanced-analysis-scenarios)
5. [Bulk Processing](#bulk-processing)
6. [Error Handling](#error-handling)
7. [Monitoring and Health Checks](#monitoring-and-health-checks)
8. [Integration Examples](#integration-examples)

## Quick Start

### Python Example

```python
import requests
import json
from datetime import datetime, timedelta

class DShieldAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

    def submit_analysis(self, attack_sessions, analysis_depth="standard"):
        """Submit attack sessions for coordination analysis."""
        url = f"{self.base_url}/analyze/coordination"
        payload = {
            "attack_sessions": attack_sessions,
            "analysis_depth": analysis_depth
        }

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def get_results(self, analysis_id):
        """Get analysis results by ID."""
        url = f"{self.base_url}/analyze/{analysis_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def wait_for_completion(self, analysis_id, timeout=300, poll_interval=5):
        """Wait for analysis completion with timeout."""
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_results(analysis_id)

            if status["status"] == "completed":
                return status
            elif status["status"] == "failed":
                raise Exception(f"Analysis failed: {status.get('error', 'Unknown error')}")

            time.sleep(poll_interval)

        raise TimeoutError(f"Analysis timed out after {timeout} seconds")

# Usage
api = DShieldAPI("http://localhost:8000", "your-api-key")

# Sample attack sessions
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

# Submit analysis and wait for results
try:
    result = api.submit_analysis(attack_sessions)
    analysis_id = result["analysis_id"]

    final_result = api.wait_for_completion(analysis_id)
    print(f"Coordination confidence: {final_result['coordination_confidence']}")
    print(f"Evidence: {json.dumps(final_result['evidence'], indent=2)}")

except Exception as e:
    print(f"Error: {e}")
```

### JavaScript Example

```javascript
class DShieldAPI {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json'
        };
    }

    async submitAnalysis(attackSessions, analysisDepth = 'standard') {
        const url = `${this.baseUrl}/analyze/coordination`;
        const payload = {
            attack_sessions: attackSessions,
            analysis_depth: analysisDepth
        };

        const response = await fetch(url, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async getResults(analysisId) {
        const url = `${this.baseUrl}/analyze/${analysisId}`;
        const response = await fetch(url, {
            method: 'GET',
            headers: this.headers
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async waitForCompletion(analysisId, timeout = 300000, pollInterval = 5000) {
        const startTime = Date.now();

        while (Date.now() - startTime < timeout) {
            const status = await this.getResults(analysisId);

            if (status.status === 'completed') {
                return status;
            } else if (status.status === 'failed') {
                throw new Error(`Analysis failed: ${status.error || 'Unknown error'}`);
            }

            await new Promise(resolve => setTimeout(resolve, pollInterval));
        }

        throw new Error(`Analysis timed out after ${timeout}ms`);
    }
}

// Usage
const api = new DShieldAPI('http://localhost:8000', 'your-api-key');

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

// Submit analysis and wait for results
async function runAnalysis() {
    try {
        const result = await api.submitAnalysis(attackSessions);
        const analysisId = result.analysis_id;

        const finalResult = await api.waitForCompletion(analysisId);
        console.log(`Coordination confidence: ${finalResult.coordination_confidence}`);
        console.log('Evidence:', JSON.stringify(finalResult.evidence, null, 2));

    } catch (error) {
        console.error('Error:', error);
    }
}

runAnalysis();
```

## Authentication Setup

### Environment Configuration

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
API_BASE_URL = os.getenv("DSHIELD_API_URL", "http://localhost:8000")
API_KEY = os.getenv("DSHIELD_API_KEY")

if not API_KEY:
    raise ValueError("DSHIELD_API_KEY environment variable is required")

# Initialize API client
api = DShieldAPI(API_BASE_URL, API_KEY)
```

### Configuration File

```yaml
# config/api_config.yaml
api:
  base_url: "http://localhost:8000"
  api_key: "your-api-key-here"
  timeout: 300
  retry_attempts: 3

analysis:
  default_depth: "standard"
  max_sessions: 1000
  poll_interval: 5
```

```python
import yaml

def load_config(config_path="config/api_config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()
api = DShieldAPI(
    config['api']['base_url'],
    config['api']['api_key']
)
```

## Basic Coordination Analysis

### Simple Analysis

```python
def analyze_simple_coordination(api, attack_sessions):
    """Perform simple coordination analysis."""

    # Submit analysis
    result = api.submit_analysis(attack_sessions, analysis_depth="minimal")
    analysis_id = result["analysis_id"]

    # Wait for completion
    final_result = api.wait_for_completion(analysis_id)

    # Interpret results
    confidence = final_result["coordination_confidence"]
    evidence = final_result["evidence"]

    print(f"Analysis ID: {analysis_id}")
    print(f"Coordination Confidence: {confidence:.2f}")

    if confidence > 0.7:
        print("HIGH COORDINATION DETECTED")
    elif confidence > 0.4:
        print("MODERATE COORDINATION DETECTED")
    else:
        print("LOW COORDINATION DETECTED")

    # Print evidence breakdown
    for metric, score in evidence.items():
        print(f"  {metric}: {score:.2f}")

    return final_result
```

### Batch Processing

```python
def process_attack_logs(api, log_file_path):
    """Process attack logs from file."""

    attack_sessions = []

    # Read and parse log file
    with open(log_file_path, 'r') as f:
        for line in f:
            # Parse log line (example format)
            session = parse_log_line(line)
            if session:
                attack_sessions.append(session)

    # Group sessions by time window
    from collections import defaultdict
    import datetime

    windowed_sessions = defaultdict(list)
    window_size = datetime.timedelta(minutes=30)

    for session in attack_sessions:
        timestamp = datetime.datetime.fromisoformat(session["timestamp"].replace('Z', '+00:00'))
        window_key = timestamp.replace(minute=timestamp.minute - timestamp.minute % 30, second=0, microsecond=0)
        windowed_sessions[window_key].append(session)

    # Analyze each time window
    results = []
    for window, sessions in windowed_sessions.items():
        if len(sessions) >= 2:  # Minimum sessions for analysis
            try:
                result = analyze_simple_coordination(api, sessions)
                result["window"] = window.isoformat()
                result["session_count"] = len(sessions)
                results.append(result)
            except Exception as e:
                print(f"Error analyzing window {window}: {e}")

    return results
```

## Advanced Analysis Scenarios

### Real-time Monitoring

```python
import asyncio
import aiohttp
from datetime import datetime, timedelta

class RealTimeMonitor:
    def __init__(self, api, callback_url=None):
        self.api = api
        self.callback_url = callback_url
        self.session_buffer = []
        self.last_analysis = None

    async def add_session(self, session):
        """Add new session to buffer and trigger analysis if needed."""
        self.session_buffer.append(session)

        # Check if we have enough sessions for analysis
        if len(self.session_buffer) >= 10:
            await self.analyze_buffer()

    async def analyze_buffer(self):
        """Analyze current buffer and clear it."""
        if len(self.session_buffer) < 2:
            return

        try:
            # Submit analysis with callback
            result = self.api.submit_analysis(
                self.session_buffer,
                analysis_depth="standard"
            )

            if self.callback_url:
                result["callback_url"] = self.callback_url

            self.last_analysis = result
            print(f"Analysis submitted: {result['analysis_id']}")

            # Clear buffer
            self.session_buffer = []

        except Exception as e:
            print(f"Error submitting analysis: {e}")

    async def periodic_analysis(self, interval_minutes=15):
        """Perform periodic analysis even with small buffers."""
        while True:
            await asyncio.sleep(interval_minutes * 60)

            if len(self.session_buffer) >= 2:
                await self.analyze_buffer()

# Usage
async def main():
    api = DShieldAPI("http://localhost:8000", "your-api-key")
    monitor = RealTimeMonitor(api, callback_url="https://example.com/webhook")

    # Start periodic analysis
    asyncio.create_task(monitor.periodic_analysis())

    # Simulate incoming sessions
    for i in range(20):
        session = {
            "source_ip": f"192.168.1.{100 + i}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": f"Attack payload {i}",
            "target_port": 80,
            "protocol": "HTTP"
        }

        await monitor.add_session(session)
        await asyncio.sleep(1)  # Simulate time between sessions

# Run the monitor
asyncio.run(main())
```

### Geographic Analysis

```python
def analyze_geographic_patterns(api, attack_sessions):
    """Analyze geographic patterns in attacks."""

    # Group by geographic regions
    from collections import defaultdict
    import geoip2.database

    # Load GeoIP database (you'll need to download this)
    reader = geoip2.database.Reader('GeoLite2-City.mmdb')

    geographic_groups = defaultdict(list)

    for session in attack_sessions:
        try:
            response = reader.city(session["source_ip"])
            country = response.country.name
            city = response.city.name

            geographic_groups[f"{country}/{city}"].append(session)
        except Exception as e:
            print(f"Error geocoding {session['source_ip']}: {e}")

    # Analyze each geographic group
    results = {}
    for location, sessions in geographic_groups.items():
        if len(sessions) >= 2:
            try:
                result = api.submit_analysis(sessions, analysis_depth="deep")
                analysis_id = result["analysis_id"]

                # Wait for completion
                final_result = api.wait_for_completion(analysis_id)
                results[location] = final_result

            except Exception as e:
                print(f"Error analyzing {location}: {e}")

    return results
```

## Bulk Processing

### Large Dataset Processing

```python
def process_large_dataset(api, dataset_path, batch_size=100):
    """Process large dataset in batches."""

    import json
    from itertools import islice

    def read_sessions_in_batches(file_path, batch_size):
        """Read sessions from file in batches."""
        with open(file_path, 'r') as f:
            while True:
                batch = list(islice(f, batch_size))
                if not batch:
                    break

                sessions = []
                for line in batch:
                    try:
                        session = json.loads(line.strip())
                        sessions.append(session)
                    except json.JSONDecodeError:
                        continue

                if sessions:
                    yield sessions

    results = []

    for batch_num, batch in enumerate(read_sessions_in_batches(dataset_path, batch_size)):
        print(f"Processing batch {batch_num + 1}")

        try:
            # Submit bulk analysis
            bulk_result = api.submit_bulk_analysis([batch])
            analysis_ids = bulk_result["analysis_ids"]

            # Wait for all analyses to complete
            batch_results = []
            for analysis_id in analysis_ids:
                try:
                    result = api.wait_for_completion(analysis_id)
                    batch_results.append(result)
                except Exception as e:
                    print(f"Error in analysis {analysis_id}: {e}")

            results.extend(batch_results)

        except Exception as e:
            print(f"Error processing batch {batch_num + 1}: {e}")

    return results
```

### Continuous Monitoring

```python
class ContinuousMonitor:
    def __init__(self, api, config):
        self.api = api
        self.config = config
        self.analysis_queue = []
        self.results_cache = {}

    def add_sessions(self, sessions):
        """Add sessions to monitoring queue."""
        self.analysis_queue.extend(sessions)

        # Check if we should trigger analysis
        if len(self.analysis_queue) >= self.config["batch_threshold"]:
            self.trigger_analysis()

    def trigger_analysis(self):
        """Trigger analysis of queued sessions."""
        if len(self.analysis_queue) < 2:
            return

        # Create batches
        batch_size = self.config["batch_size"]
        batches = [
            self.analysis_queue[i:i + batch_size]
            for i in range(0, len(self.analysis_queue), batch_size)
        ]

        try:
            # Submit bulk analysis
            result = self.api.submit_bulk_analysis(batches)
            analysis_ids = result["analysis_ids"]

            # Store for later retrieval
            for analysis_id in analysis_ids:
                self.results_cache[analysis_id] = {
                    "status": "queued",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Clear queue
            self.analysis_queue = []

        except Exception as e:
            print(f"Error triggering analysis: {e}")

    def get_pending_results(self):
        """Get results for pending analyses."""
        completed_results = []

        for analysis_id, cache_entry in self.results_cache.items():
            if cache_entry["status"] == "queued":
                try:
                    result = self.api.get_results(analysis_id)
                    if result["status"] == "completed":
                        completed_results.append(result)
                        cache_entry["status"] = "completed"
                        cache_entry["result"] = result
                except Exception as e:
                    print(f"Error getting results for {analysis_id}: {e}")

        return completed_results
```

## Error Handling

### Comprehensive Error Handling

```python
import requests
from typing import Optional, Dict, Any

class DShieldAPIError(Exception):
    """Base exception for DShield API errors."""
    pass

class RateLimitError(DShieldAPIError):
    """Raised when rate limit is exceeded."""
    pass

class AuthenticationError(DShieldAPIError):
    """Raised when authentication fails."""
    pass

class ValidationError(DShieldAPIError):
    """Raised when request validation fails."""
    pass

class DShieldAPIClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        self.timeout = timeout

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After", 60)
            raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
        elif response.status_code == 400:
            error_data = response.json()
            raise ValidationError(f"Validation error: {error_data.get('detail', 'Unknown error')}")
        elif response.status_code >= 500:
            raise DShieldAPIError(f"Server error: {response.status_code}")
        else:
            raise DShieldAPIError(f"Unexpected error: {response.status_code}")

    def submit_analysis(self, attack_sessions: list, analysis_depth: str = "standard") -> Dict[str, Any]:
        """Submit analysis with comprehensive error handling."""
        try:
            url = f"{self.base_url}/analyze/coordination"
            payload = {
                "attack_sessions": attack_sessions,
                "analysis_depth": analysis_depth
            }

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            return self._handle_response(response)

        except requests.exceptions.Timeout:
            raise DShieldAPIError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise DShieldAPIError("Connection error")
        except requests.exceptions.RequestException as e:
            raise DShieldAPIError(f"Request error: {e}")

    def get_results(self, analysis_id: str) -> Dict[str, Any]:
        """Get results with error handling."""
        try:
            url = f"{self.base_url}/analyze/{analysis_id}"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            return self._handle_response(response)

        except requests.exceptions.RequestException as e:
            raise DShieldAPIError(f"Error getting results: {e}")

# Usage with error handling
def safe_analysis(api_client, attack_sessions):
    """Perform analysis with comprehensive error handling."""
    try:
        # Submit analysis
        result = api_client.submit_analysis(attack_sessions)
        analysis_id = result["analysis_id"]

        # Wait for completion with retry logic
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                final_result = api_client.get_results(analysis_id)

                if final_result["status"] == "completed":
                    return final_result
                elif final_result["status"] == "failed":
                    raise DShieldAPIError(f"Analysis failed: {final_result.get('error', 'Unknown error')}")

                # Wait before retrying
                import time
                time.sleep(5)
                retry_count += 1

            except RateLimitError as e:
                print(f"Rate limited: {e}")
                time.sleep(60)  # Wait 1 minute
                retry_count += 1
            except Exception as e:
                print(f"Error getting results: {e}")
                retry_count += 1

        raise DShieldAPIError("Max retries exceeded")

    except AuthenticationError as e:
        print(f"Authentication error: {e}")
        # Handle authentication issues
    except ValidationError as e:
        print(f"Validation error: {e}")
        # Handle validation issues
    except RateLimitError as e:
        print(f"Rate limit error: {e}")
        # Handle rate limiting
    except DShieldAPIError as e:
        print(f"API error: {e}")
        # Handle general API errors
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Handle unexpected errors
```

## Monitoring and Health Checks

### Health Monitoring

```python
class HealthMonitor:
    def __init__(self, api_client):
        self.api_client = api_client

    def check_health(self) -> Dict[str, Any]:
        """Check API health status."""
        try:
            response = requests.get(
                f"{self.api_client.base_url}/health",
                headers=self.api_client.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def check_readiness(self) -> Dict[str, Any]:
        """Check service readiness."""
        try:
            response = requests.get(
                f"{self.api_client.base_url}/health/ready",
                headers=self.api_client.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"status": "not_ready", "error": str(e)}

    def monitor_continuously(self, interval: int = 60):
        """Continuously monitor API health."""
        import time

        while True:
            health = self.check_health()
            readiness = self.check_readiness()

            print(f"Health: {health['status']}")
            print(f"Readiness: {readiness['status']}")

            if health['status'] != 'healthy' or readiness['status'] != 'ready':
                print("WARNING: Service is not healthy!")

            time.sleep(interval)

# Usage
monitor = HealthMonitor(api_client)
monitor.monitor_continuously()
```

## Integration Examples

### Log Analysis Integration

```python
import re
from datetime import datetime

class LogAnalyzer:
    def __init__(self, api_client):
        self.api_client = api_client

    def parse_apache_log(self, log_line: str) -> Optional[Dict[str, Any]]:
        """Parse Apache log line into attack session."""
        # Apache log format: IP - - [timestamp] "request" status bytes
        pattern = r'(\S+) - - \[([^\]]+)\] "([^"]*)" (\d+) (\d+)'
        match = re.match(pattern, log_line)

        if match:
            ip, timestamp_str, request, status, bytes_sent = match.groups()

            # Parse timestamp
            try:
                timestamp = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
                timestamp_iso = timestamp.strftime('%Y-%m-%dT%H:%M:%S%z')
            except ValueError:
                return None

            # Extract port from request
            port_match = re.search(r':(\d+)', request)
            port = int(port_match.group(1)) if port_match else 80

            return {
                "source_ip": ip,
                "timestamp": timestamp_iso,
                "payload": request,
                "target_port": port,
                "protocol": "HTTP"
            }

        return None

    def analyze_log_file(self, log_file_path: str, batch_size: int = 100):
        """Analyze log file for coordination patterns."""
        sessions = []

        with open(log_file_path, 'r') as f:
            for line in f:
                session = self.parse_apache_log(line.strip())
                if session:
                    sessions.append(session)

                # Process in batches
                if len(sessions) >= batch_size:
                    try:
                        result = self.api_client.submit_analysis(sessions)
                        print(f"Submitted batch: {result['analysis_id']}")
                        sessions = []  # Clear for next batch
                    except Exception as e:
                        print(f"Error submitting batch: {e}")

        # Process remaining sessions
        if sessions:
            try:
                result = self.api_client.submit_analysis(sessions)
                print(f"Submitted final batch: {result['analysis_id']}")
            except Exception as e:
                print(f"Error submitting final batch: {e}")

# Usage
analyzer = LogAnalyzer(api_client)
analyzer.analyze_log_file("/var/log/apache2/access.log")
```

### SIEM Integration

```python
class SIEMIntegration:
    def __init__(self, api_client, siem_config):
        self.api_client = api_client
        self.siem_config = siem_config

    def process_siem_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process SIEM alert and submit for coordination analysis."""

        # Extract relevant information from alert
        sessions = []

        for event in alert_data.get("events", []):
            session = {
                "source_ip": event.get("source_ip"),
                "timestamp": event.get("timestamp"),
                "payload": event.get("payload", ""),
                "target_port": event.get("target_port"),
                "protocol": event.get("protocol", "UNKNOWN")
            }

            # Validate required fields
            if session["source_ip"] and session["timestamp"]:
                sessions.append(session)

        if len(sessions) >= 2:
            try:
                result = self.api_client.submit_analysis(sessions)

                # Add SIEM context to result
                result["siem_alert_id"] = alert_data.get("alert_id")
                result["siem_severity"] = alert_data.get("severity")
                result["siem_category"] = alert_data.get("category")

                return result

            except Exception as e:
                print(f"Error processing SIEM alert: {e}")
                return {"error": str(e)}

        return {"error": "Insufficient sessions for analysis"}

    def create_siem_alert(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create SIEM alert from coordination analysis result."""

        confidence = analysis_result.get("coordination_confidence", 0)
        evidence = analysis_result.get("evidence", {})

        # Determine alert severity based on confidence
        if confidence > 0.8:
            severity = "HIGH"
        elif confidence > 0.6:
            severity = "MEDIUM"
        elif confidence > 0.4:
            severity = "LOW"
        else:
            severity = "INFO"

        alert = {
            "alert_type": "COORDINATION_DETECTED",
            "severity": severity,
            "confidence": confidence,
            "evidence": evidence,
            "analysis_id": analysis_result.get("analysis_id"),
            "timestamp": datetime.utcnow().isoformat(),
            "description": f"Attack coordination detected with {confidence:.2f} confidence"
        }

        return alert

# Usage
siem_integration = SIEMIntegration(api_client, siem_config)

# Process SIEM alert
alert_data = {
    "alert_id": "ALERT-001",
    "severity": "HIGH",
    "category": "ATTACK",
    "events": [
        {
            "source_ip": "192.168.1.100",
            "timestamp": "2025-07-28T10:00:00Z",
            "payload": "Attack payload 1",
            "target_port": 80,
            "protocol": "HTTP"
        },
        {
            "source_ip": "192.168.1.101",
            "timestamp": "2025-07-28T10:05:00Z",
            "payload": "Attack payload 2",
            "target_port": 80,
            "protocol": "HTTP"
        }
    ]
}

result = siem_integration.process_siem_alert(alert_data)
if "analysis_id" in result:
    # Wait for completion and create SIEM alert
    final_result = api_client.wait_for_completion(result["analysis_id"])
    siem_alert = siem_integration.create_siem_alert(final_result)
    print(f"Created SIEM alert: {siem_alert}")
```

These examples demonstrate comprehensive usage of the DShield Coordination Engine API for various scenarios. Each example includes proper error handling, configuration management, and integration patterns that can be adapted for specific use cases.
