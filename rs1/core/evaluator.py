"""
Main evaluator orchestrator.

Coordinates signal detection, scoring, and policy evaluation to produce
reliability reports.
"""
from typing import List
from rs1.schemas.execution import ExecutionTrace
from rs1.schemas.report import ReliabilityReport, SignalScore
from rs1.signals.hallucination import detect_hallucination
from rs1.signals.loop import detect_loop
from rs1.signals.tool_misuse import detect_tool_misuse
from rs1.signals.cost import detect_excessive_cost
from rs1.core.scorer import calculate_overall_score
from rs1.core.policy import determine_verdict


def evaluate_trace(trace: ExecutionTrace) -> ReliabilityReport:
    """
    Evaluate an execution trace for reliability issues.

    This is the main entry point for RS-1 evaluation.
    Stateless and deterministic - same input always produces same output.

    Args:
        trace: ExecutionTrace object to evaluate

    Returns:
        ReliabilityReport: Complete evaluation report

    Raises:
        ValueError: If trace is invalid or evaluation fails
    """
    if not trace:
        raise ValueError("Cannot evaluate: trace is None")

    if not trace.trace_id:
        raise ValueError("Cannot evaluate: trace_id is required")

    # Run all signal detectors
    signal_scores = _run_all_signals(trace)

    # Calculate overall score using linear aggregation
    overall_score = calculate_overall_score(signal_scores)

    # Determine verdict based on policy rules
    verdict, reasoning = determine_verdict(overall_score, signal_scores)

    # Build report
    report = ReliabilityReport(
        trace_id=trace.trace_id,
        verdict=verdict,
        overall_score=overall_score,
        signal_scores=signal_scores,
        reasoning=reasoning,
        metadata={
            "total_messages": trace.get_total_messages(),
            "total_tool_calls": len(trace.get_tool_calls()),
            "total_tokens": trace.token_usage.total_tokens if trace.token_usage else 0,
        },
    )

    return report


def _run_all_signals(trace: ExecutionTrace) -> List[SignalScore]:
    """
    Run all reliability signals on the trace.

    Each signal is independent and deterministic.
    No signal should depend on or communicate with other signals.

    Args:
        trace: ExecutionTrace to analyze

    Returns:
        List[SignalScore]: Scores from all signals
    """
    signal_scores = []

    # Hallucination detection
    hallucination_score = detect_hallucination(trace)
    signal_scores.append(
        SignalScore(
            signal_name="hallucination",
            score=hallucination_score,
            details=_get_hallucination_details(hallucination_score),
        )
    )

    # Loop detection
    loop_score = detect_loop(trace)
    signal_scores.append(
        SignalScore(
            signal_name="loop",
            score=loop_score,
            details=_get_loop_details(loop_score),
        )
    )

    # Tool misuse detection
    tool_misuse_score = detect_tool_misuse(trace)
    signal_scores.append(
        SignalScore(
            signal_name="tool_misuse",
            score=tool_misuse_score,
            details=_get_tool_misuse_details(tool_misuse_score),
        )
    )

    # Cost tracking
    cost_score = detect_excessive_cost(trace)
    signal_scores.append(
        SignalScore(
            signal_name="cost",
            score=cost_score,
            details=_get_cost_details(cost_score, trace),
        )
    )

    return signal_scores


def _get_hallucination_details(score: float) -> str:
    """Generate human-readable details for hallucination score."""
    if score >= 0.7:
        return "High risk of hallucinated outputs detected"
    elif score >= 0.4:
        return "Moderate hallucination indicators found"
    elif score >= 0.2:
        return "Some minor hallucination patterns detected"
    else:
        return "No significant hallucination detected"


def _get_loop_details(score: float) -> str:
    """Generate human-readable details for loop score."""
    if score >= 0.7:
        return "Strong evidence of looping or repetitive behavior"
    elif score >= 0.4:
        return "Moderate repetition patterns detected"
    elif score >= 0.2:
        return "Minor repetition observed"
    else:
        return "No concerning repetition detected"


def _get_tool_misuse_details(score: float) -> str:
    """Generate human-readable details for tool misuse score."""
    if score >= 0.7:
        return "Severe tool misuse patterns detected"
    elif score >= 0.4:
        return "Moderate tool usage issues found"
    elif score >= 0.2:
        return "Minor tool usage concerns"
    else:
        return "Tool usage appears appropriate"


def _get_cost_details(score: float, trace: ExecutionTrace) -> str:
    """Generate human-readable details for cost score."""
    total_tokens = trace.token_usage.total_tokens if trace.token_usage else 0

    if score >= 0.7:
        return f"Excessive resource usage detected ({total_tokens} tokens)"
    elif score >= 0.4:
        return f"High resource usage ({total_tokens} tokens)"
    elif score >= 0.2:
        return f"Moderate resource usage ({total_tokens} tokens)"
    else:
        return f"Resource usage within normal range ({total_tokens} tokens)"
