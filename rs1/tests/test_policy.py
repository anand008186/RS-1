"""
Tests for policy evaluation.
"""
from rs1.schemas.report import SignalScore, Verdict
from rs1.core.policy import (
    determine_verdict,
    get_policy_info,
    OVERALL_THRESHOLDS,
    CRITICAL_SIGNAL_THRESHOLDS,
)


def test_determine_verdict_pass():
    """Test PASS verdict for low scores."""
    signal_scores = [
        SignalScore("hallucination", 0.1),
        SignalScore("loop", 0.1),
        SignalScore("tool_misuse", 0.1),
        SignalScore("cost", 0.1),
    ]

    verdict, reasoning = determine_verdict(0.1, signal_scores)

    assert verdict == Verdict.PASS
    assert "reliable" in reasoning.lower()
    assert "0.10" in reasoning  # Score should be in reasoning


def test_determine_verdict_warn_overall():
    """Test WARN verdict for moderate overall score."""
    signal_scores = [
        SignalScore("hallucination", 0.4),
        SignalScore("loop", 0.4),
        SignalScore("tool_misuse", 0.4),
        SignalScore("cost", 0.4),
    ]

    verdict, reasoning = determine_verdict(0.45, signal_scores)

    assert verdict == Verdict.WARN
    assert "concerning" in reasoning.lower() or "warn" in reasoning.lower()


def test_determine_verdict_fail_overall():
    """Test FAIL verdict for high overall score."""
    signal_scores = [
        SignalScore("hallucination", 0.7),
        SignalScore("loop", 0.7),
        SignalScore("tool_misuse", 0.7),
        SignalScore("cost", 0.7),
    ]

    verdict, reasoning = determine_verdict(0.75, signal_scores)

    assert verdict == Verdict.FAIL
    assert "should not be trusted" in reasoning.lower() or "fail" in reasoning.lower()


def test_determine_verdict_fail_critical_hallucination():
    """Test FAIL verdict for critical hallucination even with low overall."""
    signal_scores = [
        SignalScore("hallucination", 0.9),  # Critical
        SignalScore("loop", 0.1),
        SignalScore("tool_misuse", 0.1),
        SignalScore("cost", 0.1),
    ]

    verdict, reasoning = determine_verdict(0.3, signal_scores)

    assert verdict == Verdict.FAIL
    assert "critical" in reasoning.lower()
    assert "hallucination" in reasoning.lower()


def test_determine_verdict_fail_critical_loop():
    """Test FAIL verdict for critical loop even with low overall."""
    signal_scores = [
        SignalScore("hallucination", 0.1),
        SignalScore("loop", 0.85),  # Critical
        SignalScore("tool_misuse", 0.1),
        SignalScore("cost", 0.1),
    ]

    verdict, reasoning = determine_verdict(0.3, signal_scores)

    assert verdict == Verdict.FAIL
    assert "critical" in reasoning.lower()
    assert "loop" in reasoning.lower()


def test_determine_verdict_warn_critical_tool_misuse():
    """Test WARN verdict for critical tool misuse."""
    signal_scores = [
        SignalScore("hallucination", 0.1),
        SignalScore("loop", 0.1),
        SignalScore("tool_misuse", 0.75),  # Critical for warn
        SignalScore("cost", 0.1),
    ]

    verdict, reasoning = determine_verdict(0.25, signal_scores)

    assert verdict == Verdict.WARN
    assert "tool_misuse" in reasoning.lower()


def test_determine_verdict_warn_critical_cost():
    """Test WARN verdict for critical cost."""
    signal_scores = [
        SignalScore("hallucination", 0.1),
        SignalScore("loop", 0.1),
        SignalScore("tool_misuse", 0.1),
        SignalScore("cost", 0.95),  # Critical for warn
    ]

    verdict, reasoning = determine_verdict(0.25, signal_scores)

    assert verdict == Verdict.WARN
    assert "cost" in reasoning.lower()


def test_determine_verdict_reasoning_includes_breakdown():
    """Test that reasoning includes signal breakdown."""
    signal_scores = [
        SignalScore("hallucination", 0.3),
        SignalScore("loop", 0.2),
        SignalScore("tool_misuse", 0.5),
        SignalScore("cost", 0.1),
    ]

    verdict, reasoning = determine_verdict(0.28, signal_scores)

    # Should include all signal names and scores
    assert "hallucination" in reasoning.lower()
    assert "loop" in reasoning.lower()
    assert "tool_misuse" in reasoning.lower()
    assert "cost" in reasoning.lower()


def test_determine_verdict_reasoning_includes_levels():
    """Test that reasoning includes score levels."""
    signal_scores = [
        SignalScore("hallucination", 0.9),  # Critical
        SignalScore("loop", 0.6),  # High
        SignalScore("tool_misuse", 0.4),  # Moderate
        SignalScore("cost", 0.1),  # Minimal
    ]

    verdict, reasoning = determine_verdict(0.55, signal_scores)

    # Should include level descriptions
    assert "critical" in reasoning.lower()


def test_get_policy_info():
    """Test policy information retrieval."""
    info = get_policy_info()

    assert isinstance(info, dict)
    assert "overall_thresholds" in info
    assert "critical_signal_thresholds" in info
    assert "description" in info

    # Check thresholds are present
    assert info["overall_thresholds"] == OVERALL_THRESHOLDS
    assert info["critical_signal_thresholds"] == CRITICAL_SIGNAL_THRESHOLDS


def test_thresholds_are_valid():
    """Test that thresholds are valid ranges."""
    # Overall thresholds
    assert 0.0 < OVERALL_THRESHOLDS["WARN"] < 1.0
    assert 0.0 < OVERALL_THRESHOLDS["FAIL"] < 1.0
    assert OVERALL_THRESHOLDS["WARN"] < OVERALL_THRESHOLDS["FAIL"]

    # Critical thresholds
    for threshold in CRITICAL_SIGNAL_THRESHOLDS.values():
        assert 0.0 < threshold <= 1.0


def test_determine_verdict_deterministic():
    """Test that verdict determination is deterministic."""
    signal_scores = [
        SignalScore("hallucination", 0.5),
        SignalScore("loop", 0.3),
        SignalScore("tool_misuse", 0.4),
        SignalScore("cost", 0.2),
    ]

    # Calculate multiple times
    verdict1, reasoning1 = determine_verdict(0.4, signal_scores)
    verdict2, reasoning2 = determine_verdict(0.4, signal_scores)
    verdict3, reasoning3 = determine_verdict(0.4, signal_scores)

    assert verdict1 == verdict2 == verdict3
    assert reasoning1 == reasoning2 == reasoning3


def test_determine_verdict_boundary_warn():
    """Test verdict at WARN boundary."""
    signal_scores = [
        SignalScore("hallucination", 0.4),
        SignalScore("loop", 0.4),
        SignalScore("tool_misuse", 0.4),
        SignalScore("cost", 0.4),
    ]

    # Exactly at WARN threshold
    verdict, _ = determine_verdict(OVERALL_THRESHOLDS["WARN"], signal_scores)
    assert verdict == Verdict.WARN


def test_determine_verdict_boundary_fail():
    """Test verdict at FAIL boundary."""
    signal_scores = [
        SignalScore("hallucination", 0.7),
        SignalScore("loop", 0.7),
        SignalScore("tool_misuse", 0.7),
        SignalScore("cost", 0.7),
    ]

    # Exactly at FAIL threshold
    verdict, _ = determine_verdict(OVERALL_THRESHOLDS["FAIL"], signal_scores)
    assert verdict == Verdict.FAIL


def test_determine_verdict_just_below_warn():
    """Test verdict just below WARN threshold."""
    signal_scores = [
        SignalScore("hallucination", 0.3),
        SignalScore("loop", 0.3),
        SignalScore("tool_misuse", 0.3),
        SignalScore("cost", 0.3),
    ]

    # Just below WARN threshold
    verdict, _ = determine_verdict(OVERALL_THRESHOLDS["WARN"] - 0.01, signal_scores)
    assert verdict == Verdict.PASS
