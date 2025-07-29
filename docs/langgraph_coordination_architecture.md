# LangGraph Architecture for Attack Coordination Detection

## Core Agent Architecture

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Optional
import asyncio

class CoordinationAnalysisState(TypedDict):
    """Shared state across all agents"""
    attack_sessions: List[Dict]
    correlation_results: Dict
    enrichment_data: Dict
    coordination_confidence: float
    analysis_plan: Dict
    tool_results: Dict
    final_assessment: Dict
```

## Agent Definitions

### 1. **Orchestrator Agent**
**Purpose**: Entry point, manages workflow, determines analysis strategy
```python
class OrchestratorAgent:
    def analyze_initial_data(self, state: CoordinationAnalysisState):
        # Examine attack session data from Elasticsearch
        # Determine complexity and required analysis depth
        # Route to appropriate analysis path
        
    def should_deep_analyze(self, sessions) -> bool:
        # Quick heuristics: timing windows, source diversity, etc.
        # Returns True if coordination is possible
```

### 2. **Pattern Analyzer Agent**
**Purpose**: Core behavioral and temporal analysis
```python
class PatternAnalyzerAgent:
    def temporal_analysis(self, state):
        # Analyze timing patterns, intervals, synchronization
        # Statistical clustering of attack timings
        
    def behavioral_clustering(self, state):
        # TTP similarity analysis
        # Attack vector patterns
        # Payload similarities
        
    def infrastructure_mapping(self, state):
        # IP relationships, ASN analysis
        # Geolocation clustering vs dispersion
```

### 3. **Tool Coordinator Agent** 
**Purpose**: Orchestrates external tools based on analysis needs
```python
class ToolCoordinatorAgent:
    async def execute_analysis_plan(self, state):
        tools_needed = self.determine_tools(state)
        results = await asyncio.gather(*[
            self.bgp_lookup(ips) if 'bgp' in tools_needed else None,
            self.threat_intel_lookup(indicators) if 'threat_intel' in tools_needed else None,
            self.geolocation_analysis(ips) if 'geo' in tools_needed else None,
        ])
        return self.synthesize_results(results)
```

### 4. **Confidence Scorer Agent**
**Purpose**: Generates evidence-based confidence scores
```python
class ConfidenceScorerAgent:
    def calculate_coordination_score(self, state):
        evidence_factors = {
            'temporal_synchronization': 0.0,  # 0-1 score
            'behavioral_similarity': 0.0,
            'infrastructure_clustering': 0.0,
            'geographic_dispersion': 0.0,
            'threat_intel_correlation': 0.0
        }
        
        # Weight and combine factors
        # Return structured confidence assessment
```

### 5. **Elasticsearch Enricher Agent**
**Purpose**: Updates ES with analysis results
```python
class ElasticsearchEnricherAgent:
    def enrich_attack_sessions(self, state):
        # Add coordination metadata to each session
        # Include confidence scores, cluster IDs
        # Update campaign attribution fields
```

## Workflow Definition

```python
def create_coordination_analysis_workflow():
    workflow = StateGraph(CoordinationAnalysisState)
    
    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("pattern_analyzer", pattern_analyzer_node)
    workflow.add_node("tool_coordinator", tool_coordinator_node)
    workflow.add_node("confidence_scorer", confidence_scorer_node)
    workflow.add_node("elasticsearch_enricher", elasticsearch_enricher_node)
    
    # Define flow
    workflow.set_entry_point("orchestrator")
    
    workflow.add_conditional_edges(
        "orchestrator",
        lambda state: "pattern_analyzer" if state.get("needs_analysis") else "confidence_scorer"
    )
    
    workflow.add_edge("pattern_analyzer", "tool_coordinator")
    workflow.add_edge("tool_coordinator", "confidence_scorer")
    workflow.add_edge("confidence_scorer", "elasticsearch_enricher")
    workflow.add_edge("elasticsearch_enricher", END)
    
    return workflow.compile()
```

## Tool Integration Layer

### BGP Tool Integration
```python
class BGPAnalysisTool:
    async def analyze_ip_relationships(self, ips: List[str]):
        # Check ASN clustering, routing relationships
        # Return infrastructure correlation data
        
class ThreatIntelTool:
    async def lookup_indicators(self, iocs: List[str]):
        # Query multiple threat intel sources
        # Return attribution hints, campaign links
```

## Local LLM Integration

### Model Selection for Issue #80
```python
# Recommended models for coordination analysis:
MODELS = {
    "primary": "llama-3.1-8b-instruct",  # Good reasoning, efficient
    "fallback": "mistral-7b-instruct",   # Faster for simple decisions
    "specialist": "code-llama-13b"       # For technical pattern analysis
}
```

### Prompt Engineering for Cybersecurity
```python
COORDINATION_ANALYSIS_PROMPT = """
You are a cybersecurity analyst specializing in attack coordination detection.

Given attack session data, analyze whether these represent:
1. Coordinated campaign (multiple attackers working together)
2. Coincidental timing (independent attackers)
3. Single attacker using multiple sources

Evidence to consider:
- Temporal patterns and synchronization
- Behavioral similarities in TTPs
- Infrastructure relationships
- Geographic distribution patterns

Provide confidence score (0-1) and reasoning.
"""
```

## Implementation Phases

### Phase 1: Core Framework (2-3 weeks)
- Set up LangGraph workflow
- Implement basic agents
- Create Elasticsearch integration
- Simple temporal correlation

### Phase 2: Advanced Pattern Analysis (3-4 weeks)
- Behavioral clustering algorithms
- Infrastructure relationship mapping
- Statistical correlation analysis
- Confidence scoring system

### Phase 3: Tool Integration (2-3 weeks)
- BGP lookup integration
- Threat intelligence APIs
- Geolocation analysis
- Results synthesis

### Phase 4: Production Optimization (2 weeks)
- Performance tuning
- Error handling
- Monitoring and logging
- Academic validation testing

## Key Advantages Over Deer-Flow

1. **Purpose-Built**: Designed specifically for cybersecurity coordination detection
2. **Security-First**: No third-party dependencies with security concerns
3. **Performance**: Optimized for real-time analysis vs research reports
4. **Integration**: Native Elasticsearch and security tool support
5. **Maintainability**: Focused codebase, easier to audit and secure
6. **Scalability**: Can handle high-volume honeypot data streams

## Academic Credibility Features

- **Reproducible Analysis**: Deterministic algorithms with documented methods
- **Confidence Scoring**: Statistical basis for coordination claims
- **Evidence Chain**: Clear audit trail of analysis decisions
- **Validation Framework**: Test against known coordinated/independent attacks
- **Metrics**: Precision/recall for coordination detection accuracy

## Resource Requirements

- **Development**: 8-12 weeks for full implementation
- **Hardware**: 16GB RAM minimum, 32GB recommended
- **Storage**: ~5GB for models, minimal for framework
- **Skills**: Python, LangGraph, Elasticsearch, cybersecurity analysis

This architecture directly addresses your Issue #80 requirements while providing a foundation for future threat attribution work in separate issues.
