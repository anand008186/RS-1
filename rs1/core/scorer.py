"""
Score aggregation module.

Combines individual signal scores into an overall reliability score.
"""
from typing import List
from rs1.schemas.report import SignalScore


# Signal weights for linear aggregation
# These are fixed and transparent - no learning or adaptation
# Total must sum to 1.0 for normalized scoring
SIGNAL_WEIGHTS = {
    "hallucination": 0.35,  # Highest weight - critical reliability issue
    "loop": 0.25,  # High weight - indicates stuck/broken behavior
    "tool_misuse": 0.25,  # High weight - incorrect tool usage
    "cost": 0.15,  # Lower weight - efficiency concern, not reliability
}


def calculate_overall_score(signal_scores: List[SignalScore]) -> float:
    """
    Calculate overall reliability score using linear weighted aggregation.

    Formula:
        overall_score = Σ(signal_score × signal_weight)

    Where:
        - signal_score is the individual signal's risk score [0.0-1.0]
        - signal_weight is the predetermined weight for that signal
        - Higher overall_score = higher reliability risk

    Args:
        signal_scores: List of SignalScore objects

    Returns:
        float: Overall reliability score [0.0-1.0]

    Raises:
        ValueError: If signal_scores is empty or contains unknown signals
    """
    if not signal_scores:
        raise ValueError("Cannot calculate score: no signal scores provided")

    # Validate all signals are recognized
    for score in signal_scores:
        if score.signal_name not in SIGNAL_WEIGHTS:
            raise ValueError(f"Unknown signal: {score.signal_name}")

    # Calculate weighted sum
    weighted_sum = 0.0
    total_weight = 0.0

    for score in signal_scores:
        weight = SIGNAL_WEIGHTS.get(score.signal_name, 0.0)
        weighted_sum += score.score * weight
        total_weight += weight

    # Normalize by total weight used
    # (in case not all signals are present)
    if total_weight > 0:
        overall_score = weighted_sum / total_weight
    else:
        overall_score = 0.0

    # Ensure score is in valid range
    return min(1.0, max(0.0, overall_score))


def get_weight_info() -> dict:
    """
    Get information about signal weights for transparency.

    Returns:
        dict: Signal names mapped to their weights and descriptions
    """
    return {
        "hallucination": {
            "weight": SIGNAL_WEIGHTS["hallucination"],
            "description": "Critical reliability issue - agent producing ungrounded outputs",
        },
        "loop": {
            "weight": SIGNAL_WEIGHTS["loop"],
            "description": "Agent stuck in repetitive behavior or runaway execution",
        },
        "tool_misuse": {
            "weight": SIGNAL_WEIGHTS["tool_misuse"],
            "description": "Incorrect or dangerous tool usage patterns",
        },
        "cost": {
            "weight": SIGNAL_WEIGHTS["cost"],
            "description": "Efficiency concern - excessive token/resource usage",
        },
    }


def validate_weights() -> bool:
    """
    Validate that weights are properly configured.

    Returns:
        bool: True if weights are valid, False otherwise
    """
    total = sum(SIGNAL_WEIGHTS.values())
    # Allow small floating point error
    return abs(total - 1.0) < 0.001
