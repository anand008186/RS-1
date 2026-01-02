"""
Policy evaluation module.

Applies threshold-based rules to determine verdict and generate reasoning.
"""
from typing import List, Tuple
from rs1.schemas.report import Verdict, SignalScore


# Threshold configuration for overall score
# These are rule-based, not learned - explicitly defined for transparency
OVERALL_THRESHOLDS = {
    "FAIL": 0.7,  # Overall score >= 0.7 = FAIL
    "WARN": 0.4,  # Overall score >= 0.4 = WARN
    # Overall score < 0.4 = PASS
}

# Individual signal thresholds for specific concerns
# Even if overall score is low, certain critical signals can trigger warnings
CRITICAL_SIGNAL_THRESHOLDS = {
    "hallucination": 0.8,  # Very high hallucination = auto FAIL
    "loop": 0.8,  # Definite loop detected = auto FAIL
    "tool_misuse": 0.7,  # Severe tool misuse = auto WARN
    "cost": 0.9,  # Extreme cost = auto WARN (not FAIL, just efficiency)
}


def determine_verdict(
    overall_score: float, signal_scores: List[SignalScore]
) -> Tuple[Verdict, str]:
    """
    Determine verdict and generate reasoning based on scores and policy rules.

    Logic:
    1. Check for critical individual signal thresholds
    2. Apply overall score thresholds
    3. Generate human-readable reasoning

    Args:
        overall_score: Overall reliability score [0.0-1.0]
        signal_scores: List of individual signal scores

    Returns:
        Tuple of (Verdict, reasoning string)
    """
    # Check critical individual signals first
    critical_issues = []

    for score in signal_scores:
        signal_name = score.signal_name
        if signal_name in CRITICAL_SIGNAL_THRESHOLDS:
            threshold = CRITICAL_SIGNAL_THRESHOLDS[signal_name]
            if score.score >= threshold:
                critical_issues.append((signal_name, score.score))

    # Determine verdict based on critical issues
    has_critical_fail = any(
        name in ["hallucination", "loop"] for name, _ in critical_issues
    )
    has_critical_warn = any(
        name in ["tool_misuse", "cost"] for name, _ in critical_issues
    )

    # Apply rules
    if has_critical_fail:
        verdict = Verdict.FAIL
    elif overall_score >= OVERALL_THRESHOLDS["FAIL"]:
        verdict = Verdict.FAIL
    elif has_critical_warn or overall_score >= OVERALL_THRESHOLDS["WARN"]:
        verdict = Verdict.WARN
    else:
        verdict = Verdict.PASS

    # Generate reasoning
    reasoning = _generate_reasoning(verdict, overall_score, signal_scores, critical_issues)

    return verdict, reasoning


def _generate_reasoning(
    verdict: Verdict,
    overall_score: float,
    signal_scores: List[SignalScore],
    critical_issues: List[Tuple[str, float]],
) -> str:
    """
    Generate human-readable reasoning for the verdict.

    Args:
        verdict: The determined verdict
        overall_score: Overall reliability score
        signal_scores: List of signal scores
        critical_issues: List of (signal_name, score) for critical issues

    Returns:
        str: Human-readable reasoning
    """
    reasoning_parts = []

    # Start with verdict and overall score
    reasoning_parts.append(
        f"Overall reliability score: {overall_score:.2f} (0.0=good, 1.0=bad)."
    )

    # Add critical issues if any
    if critical_issues:
        critical_names = [name for name, _ in critical_issues]
        reasoning_parts.append(
            f"Critical issues detected: {', '.join(critical_names)}."
        )

    # Add signal breakdown
    signal_details = []
    for score in signal_scores:
        level = _get_score_level(score.score)
        signal_details.append(f"{score.signal_name}: {score.score:.2f} ({level})")

    reasoning_parts.append(f"Signal breakdown: {'; '.join(signal_details)}.")

    # Add verdict-specific guidance
    if verdict == Verdict.FAIL:
        reasoning_parts.append(
            "This execution shows significant reliability issues and should not be trusted."
        )
    elif verdict == Verdict.WARN:
        reasoning_parts.append(
            "This execution shows some concerning patterns that warrant review."
        )
    else:
        reasoning_parts.append(
            "This execution appears reliable with no major concerns."
        )

    return " ".join(reasoning_parts)


def _get_score_level(score: float) -> str:
    """
    Get human-readable level for a score.

    Args:
        score: Risk score [0.0-1.0]

    Returns:
        str: Level description
    """
    if score >= 0.8:
        return "critical"
    elif score >= 0.6:
        return "high"
    elif score >= 0.4:
        return "moderate"
    elif score >= 0.2:
        return "low"
    else:
        return "minimal"


def get_policy_info() -> dict:
    """
    Get information about policy thresholds for transparency.

    Returns:
        dict: Policy configuration details
    """
    return {
        "overall_thresholds": OVERALL_THRESHOLDS,
        "critical_signal_thresholds": CRITICAL_SIGNAL_THRESHOLDS,
        "description": (
            "Policy applies rule-based thresholds to determine verdict. "
            "Critical signals can override overall score. "
            "No ML or adaptive thresholds used."
        ),
    }
