"""Prompt engineering for cybersecurity coordination analysis.

This module contains specialized prompts for LLM-based coordination analysis,
optimized for cybersecurity pattern recognition and threat attribution.
"""

from typing import Any

# Base prompt template for coordination analysis
COORDINATION_ANALYSIS_PROMPT = """
You are a cybersecurity analyst specializing in attack coordination detection.

Given the following attack session data, analyze whether these represent:
1. Coordinated campaign (multiple attackers working together)
2. Coincidental timing (independent attackers)
3. Single attacker using multiple sources

Evidence to consider:
- Temporal patterns and synchronization
- Behavioral similarities in TTPs (Tactics, Techniques, Procedures)
- Infrastructure relationships (IP/ASN clustering)
- Geographic distribution patterns
- Payload and attack vector similarities

Provide your analysis in the following JSON format:
{{
    "coordination_confidence": 0.75,
    "evidence_breakdown": {{
        "temporal_correlation": 0.8,
        "behavioral_similarity": 0.7,
        "infrastructure_clustering": 0.6,
        "geographic_proximity": 0.5,
        "payload_similarity": 0.9
    }},
    "reasoning": "Detailed explanation of your assessment",
    "key_factors": ["factor1", "factor2", "factor3"],
    "assessment": "coordinated|coincidental|single_attacker"
}}

Attack Sessions:
{attack_sessions}

Analysis Context:
{context}

Instructions:
{instructions}
"""

# Specialized prompts for different analysis types
TEMPORAL_ANALYSIS_PROMPT = """
You are analyzing temporal patterns in cybersecurity attacks.

Examine the timing patterns in these attack sessions to determine if they show:
- Synchronized timing (coordinated)
- Random timing (coincidental)
- Systematic timing (single attacker)

Consider:
- Time intervals between attacks
- Time-of-day patterns
- Day-of-week patterns
- Burst vs. distributed patterns

Provide analysis in JSON format with temporal correlation score (0-1).
"""

BEHAVIORAL_ANALYSIS_PROMPT = """
You are analyzing behavioral patterns in cybersecurity attacks.

Examine the attack techniques, tactics, and procedures (TTPs) to determine:
- Similarity in attack methods
- Consistency in payload patterns
- Common tools or scripts used
- Attack sophistication level

Consider:
- Attack vector similarities
- Payload structure patterns
- User agent consistency
- Target selection patterns

Provide analysis in JSON format with behavioral similarity score (0-1).
"""

INFRASTRUCTURE_ANALYSIS_PROMPT = """
You are analyzing infrastructure relationships in cybersecurity attacks.

Examine the source infrastructure to determine:
- IP address clustering patterns
- ASN (Autonomous System) relationships
- Geographic clustering vs. dispersion
- Infrastructure sharing indicators

Consider:
- IP address ranges and subnets
- ASN ownership patterns
- Geographic proximity
- Infrastructure reuse patterns

Provide analysis in JSON format with infrastructure clustering score (0-1).
"""

# Prompt for confidence scoring
CONFIDENCE_SCORING_PROMPT = """
You are a cybersecurity analyst evaluating coordination confidence.

Based on the following evidence scores, calculate an overall coordination confidence:

Evidence Breakdown:
- Temporal Correlation: {temporal_score}
- Behavioral Similarity: {behavioral_score}
- Infrastructure Clustering: {infrastructure_score}
- Geographic Proximity: {geographic_score}
- Payload Similarity: {payload_score}

Weighting Factors:
- High temporal correlation with behavioral similarity = strong coordination indicator
- Infrastructure clustering with geographic proximity = moderate coordination indicator
- High payload similarity alone = weak coordination indicator
- Low scores across all categories = likely coincidental

Provide:
- Overall confidence score (0-1)
- Reasoning for the score
- Key factors that influenced the assessment
"""

# Prompt for evidence synthesis
EVIDENCE_SYNTHESIS_PROMPT = """
You are synthesizing evidence for cybersecurity coordination analysis.

Combine the following analysis results into a comprehensive assessment:

Temporal Analysis: {temporal_analysis}
Behavioral Analysis: {behavioral_analysis}
Infrastructure Analysis: {infrastructure_analysis}

Synthesis Guidelines:
- Look for corroborating evidence across multiple dimensions
- Consider the strength and reliability of each evidence type
- Weight recent or high-confidence findings more heavily
- Identify conflicting evidence and resolve contradictions

Provide a synthesized assessment with:
- Overall coordination confidence
- Evidence breakdown
- Key supporting factors
- Confidence level in the assessment
"""


def format_attack_sessions(sessions: list[dict[str, Any]]) -> str:
    """Format attack sessions for prompt inclusion.

    Args:
        sessions: List of attack session dictionaries

    Returns:
        Formatted string representation of sessions
    """
    formatted_sessions = []

    for i, session in enumerate(sessions, 1):
        session_text = f"Session {i}:\n"
        session_text += f"  Source IP: {session.get('source_ip', 'Unknown')}\n"
        session_text += f"  Timestamp: {session.get('timestamp', 'Unknown')}\n"
        session_text += f"  Target Port: {session.get('target_port', 'Unknown')}\n"
        session_text += f"  Protocol: {session.get('protocol', 'Unknown')}\n"

        # Truncate payload if too long
        payload = session.get("payload", "")
        if len(payload) > 500:
            payload = payload[:500] + "... [truncated]"
        session_text += f"  Payload: {payload}\n"

        formatted_sessions.append(session_text)

    return "\n".join(formatted_sessions)


def create_coordination_prompt(
    sessions: list[dict[str, Any]],
    analysis_type: str = "comprehensive",
    context: dict[str, Any] = None,
    instructions: str = None,
) -> str:
    """Create a coordination analysis prompt.

    Args:
        sessions: List of attack session data
        analysis_type: Type of analysis to perform
        context: Additional context for analysis
        instructions: Custom instructions

    Returns:
        Formatted prompt string
    """
    # Select appropriate prompt template
    if analysis_type == "temporal":
        base_prompt = TEMPORAL_ANALYSIS_PROMPT
    elif analysis_type == "behavioral":
        base_prompt = BEHAVIORAL_ANALYSIS_PROMPT
    elif analysis_type == "infrastructure":
        base_prompt = INFRASTRUCTURE_ANALYSIS_PROMPT
    else:
        base_prompt = COORDINATION_ANALYSIS_PROMPT

    # Format sessions
    formatted_sessions = format_attack_sessions(sessions)

    # Format context
    context_text = ""
    if context:
        context_text = "\n".join([f"{k}: {v}" for k, v in context.items()])

    # Format instructions
    instructions_text = (
        instructions or "Analyze the attack sessions for coordination patterns."
    )

    # Create the prompt
    prompt = base_prompt.format(
        attack_sessions=formatted_sessions,
        context=context_text,
        instructions=instructions_text,
    )

    return prompt


def create_confidence_prompt(evidence_scores: dict[str, float]) -> str:
    """Create a confidence scoring prompt.

    Args:
        evidence_scores: Dictionary of evidence scores

    Returns:
        Formatted confidence scoring prompt
    """
    return CONFIDENCE_SCORING_PROMPT.format(
        temporal_score=evidence_scores.get("temporal_correlation", 0.0),
        behavioral_score=evidence_scores.get("behavioral_similarity", 0.0),
        infrastructure_score=evidence_scores.get("infrastructure_clustering", 0.0),
        geographic_score=evidence_scores.get("geographic_proximity", 0.0),
        payload_score=evidence_scores.get("payload_similarity", 0.0),
    )


def create_synthesis_prompt(
    temporal_analysis: str, behavioral_analysis: str, infrastructure_analysis: str
) -> str:
    """Create an evidence synthesis prompt.

    Args:
        temporal_analysis: Results from temporal analysis
        behavioral_analysis: Results from behavioral analysis
        infrastructure_analysis: Results from infrastructure analysis

    Returns:
        Formatted synthesis prompt
    """
    return EVIDENCE_SYNTHESIS_PROMPT.format(
        temporal_analysis=temporal_analysis,
        behavioral_analysis=behavioral_analysis,
        infrastructure_analysis=infrastructure_analysis,
    )
