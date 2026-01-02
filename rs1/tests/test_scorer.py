"""
Tests for score aggregation.
"""
import pytest
from rs1.schemas.report import SignalScore
from rs1.core.scorer import (
    calculate_overall_score,
    get_weight_info,
    validate_weights,
    SIGNAL_WEIGHTS,
)


def test_calculate_overall_score_all_zeros():
    """Test score calculation with all zero scores."""
    signal_scores = [
        SignalScore("hallucination", 0.0),
        SignalScore("loop", 0.0),
        SignalScore("tool_misuse", 0.0),
        SignalScore("cost", 0.0),
    ]

    overall = calculate_overall_score(signal_scores)
    assert overall == 0.0


def test_calculate_overall_score_all_ones():
    """Test score calculation with all maximum scores."""
    signal_scores = [
        SignalScore("hallucination", 1.0),
        SignalScore("loop", 1.0),
        SignalScore("tool_misuse", 1.0),
        SignalScore("cost", 1.0),
    ]

    overall = calculate_overall_score(signal_scores)
    assert overall == 1.0


def test_calculate_overall_score_weighted():
    """Test that weights are applied correctly."""
    signal_scores = [
        SignalScore("hallucination", 1.0),  # weight 0.35
        SignalScore("loop", 0.0),  # weight 0.25
        SignalScore("tool_misuse", 0.0),  # weight 0.25
        SignalScore("cost", 0.0),  # weight 0.15
    ]

    overall = calculate_overall_score(signal_scores)
    # Should be weighted by hallucination's weight (0.35)
    assert overall == 0.35


def test_calculate_overall_score_mixed():
    """Test score calculation with mixed values."""
    signal_scores = [
        SignalScore("hallucination", 0.8),
        SignalScore("loop", 0.4),
        SignalScore("tool_misuse", 0.2),
        SignalScore("cost", 0.6),
    ]

    overall = calculate_overall_score(signal_scores)

    # Manual calculation
    expected = (
        0.8 * SIGNAL_WEIGHTS["hallucination"]
        + 0.4 * SIGNAL_WEIGHTS["loop"]
        + 0.2 * SIGNAL_WEIGHTS["tool_misuse"]
        + 0.6 * SIGNAL_WEIGHTS["cost"]
    )

    assert abs(overall - expected) < 0.001


def test_calculate_overall_score_subset():
    """Test score calculation with subset of signals."""
    signal_scores = [
        SignalScore("hallucination", 0.8),
        SignalScore("loop", 0.4),
    ]

    overall = calculate_overall_score(signal_scores)

    # Should normalize by sum of weights present
    total_weight = SIGNAL_WEIGHTS["hallucination"] + SIGNAL_WEIGHTS["loop"]
    expected = (
        0.8 * SIGNAL_WEIGHTS["hallucination"] + 0.4 * SIGNAL_WEIGHTS["loop"]
    ) / total_weight

    assert abs(overall - expected) < 0.001


def test_calculate_overall_score_empty():
    """Test that empty signal list raises error."""
    with pytest.raises(ValueError, match="no signal scores provided"):
        calculate_overall_score([])


def test_calculate_overall_score_unknown_signal():
    """Test that unknown signal raises error."""
    signal_scores = [
        SignalScore("hallucination", 0.5),
        SignalScore("unknown_signal", 0.8),
    ]

    with pytest.raises(ValueError, match="Unknown signal"):
        calculate_overall_score(signal_scores)


def test_calculate_overall_score_clamped():
    """Test that score is clamped to [0, 1]."""
    # This shouldn't happen in practice, but ensure clamping works
    signal_scores = [
        SignalScore("hallucination", 1.5),  # Invalid but should be clamped
    ]

    overall = calculate_overall_score(signal_scores)
    assert 0.0 <= overall <= 1.0


def test_get_weight_info():
    """Test weight information retrieval."""
    info = get_weight_info()

    assert isinstance(info, dict)
    assert "hallucination" in info
    assert "loop" in info
    assert "tool_misuse" in info
    assert "cost" in info

    # Check structure
    for signal_name, signal_info in info.items():
        assert "weight" in signal_info
        assert "description" in signal_info
        assert isinstance(signal_info["weight"], float)
        assert isinstance(signal_info["description"], str)


def test_validate_weights():
    """Test weight validation."""
    # Weights should sum to 1.0
    assert validate_weights() is True

    # Verify manually
    total = sum(SIGNAL_WEIGHTS.values())
    assert abs(total - 1.0) < 0.001


def test_signal_weights_all_present():
    """Test that all expected signals have weights."""
    expected_signals = {"hallucination", "loop", "tool_misuse", "cost"}
    actual_signals = set(SIGNAL_WEIGHTS.keys())

    assert actual_signals == expected_signals


def test_signal_weights_all_positive():
    """Test that all weights are positive."""
    for weight in SIGNAL_WEIGHTS.values():
        assert weight > 0.0


def test_calculate_overall_score_deterministic():
    """Test that calculation is deterministic."""
    signal_scores = [
        SignalScore("hallucination", 0.6),
        SignalScore("loop", 0.3),
        SignalScore("tool_misuse", 0.5),
        SignalScore("cost", 0.2),
    ]

    # Calculate multiple times
    result1 = calculate_overall_score(signal_scores)
    result2 = calculate_overall_score(signal_scores)
    result3 = calculate_overall_score(signal_scores)

    assert result1 == result2 == result3
