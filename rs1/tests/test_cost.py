"""
Tests for cost tracking signal.
"""
from rs1.schemas.execution import (
    ExecutionTrace,
    Message,
    ToolCall,
    ToolResult,
    TokenUsage,
)
from rs1.signals.cost import detect_excessive_cost, get_token_usage_summary


def test_cost_positive_excessive_tokens():
    """Test detection of excessive token usage."""
    trace = ExecutionTrace(
        trace_id="test-1",
        messages=[
            Message(role="user", content="Request"),
            Message(role="assistant", content="Response"),
        ],
        token_usage=TokenUsage(
            prompt_tokens=50000,
            completion_tokens=60000,
            total_tokens=110000,  # Exceeds excessive threshold
        ),
    )

    score = detect_excessive_cost(trace)
    assert score > 0.7, f"Expected high cost score for excessive tokens, got {score}"


def test_cost_positive_high_tokens():
    """Test detection of high token usage."""
    trace = ExecutionTrace(
        trace_id="test-2",
        messages=[
            Message(role="user", content="Request"),
            Message(role="assistant", content="Response"),
        ],
        token_usage=TokenUsage(
            prompt_tokens=30000,
            completion_tokens=30000,
            total_tokens=60000,  # High but not excessive
        ),
    )

    score = detect_excessive_cost(trace)
    assert 0.3 < score < 0.8, f"Expected moderate cost score for high tokens, got {score}"


def test_cost_positive_inefficient_usage():
    """Test detection of inefficient token usage (high tokens per message)."""
    trace = ExecutionTrace(
        trace_id="test-3",
        messages=[
            Message(role="user", content="Request"),
            Message(role="assistant", content="Response"),
        ],
        token_usage=TokenUsage(
            prompt_tokens=1000,
            completion_tokens=14000,  # Very high completion relative to messages
            total_tokens=15000,
        ),
    )

    score = detect_excessive_cost(trace)
    assert score > 0.3, f"Expected moderate cost score for inefficient usage, got {score}"


def test_cost_positive_high_completion_ratio():
    """Test detection of high completion to prompt ratio."""
    trace = ExecutionTrace(
        trace_id="test-4",
        messages=[
            Message(role="user", content="Request"),
            Message(role="assistant", content="Very verbose response"),
        ],
        token_usage=TokenUsage(
            prompt_tokens=1000,
            completion_tokens=5000,  # 5x completion ratio
            total_tokens=6000,
        ),
    )

    score = detect_excessive_cost(trace)
    # Should get some score due to high completion ratio
    assert score > 0.0, f"Expected positive cost score for high completion ratio, got {score}"


def test_cost_negative_normal_usage():
    """Test that normal token usage doesn't trigger detection."""
    trace = ExecutionTrace(
        trace_id="test-5",
        messages=[
            Message(role="user", content="What is 2+2?"),
            Message(role="assistant", content="The answer is 4"),
        ],
        token_usage=TokenUsage(
            prompt_tokens=30,
            completion_tokens=20,
            total_tokens=50,
        ),
    )

    score = detect_excessive_cost(trace)
    assert score == 0.0, f"Expected zero cost score for normal usage, got {score}"


def test_cost_negative_moderate_usage():
    """Test that moderate token usage doesn't trigger high scores."""
    trace = ExecutionTrace(
        trace_id="test-6",
        messages=[
            Message(role="user", content="Request"),
            Message(role="assistant", content="Response"),
            Message(role="user", content="Follow-up"),
            Message(role="assistant", content="Final response"),
        ],
        token_usage=TokenUsage(
            prompt_tokens=2000,
            completion_tokens=1500,
            total_tokens=3500,
        ),
    )

    score = detect_excessive_cost(trace)
    assert score < 0.3, f"Expected low cost score for moderate usage, got {score}"


def test_cost_zero_tokens_with_messages():
    """Test handling of zero tokens with messages (data quality issue)."""
    trace = ExecutionTrace(
        trace_id="test-7",
        messages=[
            Message(role="user", content="Request"),
            Message(role="assistant", content="Response"),
        ],
        token_usage=TokenUsage(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        ),
    )

    score = detect_excessive_cost(trace)
    assert score > 0.0, f"Expected positive cost score for missing token data, got {score}"


def test_cost_empty_trace():
    """Test handling of empty trace."""
    trace = ExecutionTrace(
        trace_id="test-8",
        messages=[],
        token_usage=TokenUsage(0, 0, 0),
    )

    score = detect_excessive_cost(trace)
    assert score == 0.0, f"Expected zero score for empty trace, got {score}"


def test_get_token_usage_summary():
    """Test token usage summary generation."""
    trace = ExecutionTrace(
        trace_id="test-9",
        messages=[
            Message(role="user", content="Request"),
            Message(role="assistant", content="Response"),
        ],
        token_usage=TokenUsage(
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
        ),
    )

    summary = get_token_usage_summary(trace)

    assert summary["total_tokens"] == 1500
    assert summary["prompt_tokens"] == 1000
    assert summary["completion_tokens"] == 500
    assert summary["tokens_per_message"] == 750.0  # 1500 / 2 messages
    assert summary["completion_ratio"] == 0.5  # 500 / 1000


def test_get_token_usage_summary_no_usage():
    """Test summary generation with no token usage."""
    trace = ExecutionTrace(
        trace_id="test-10",
        messages=[],
        token_usage=None,
    )

    summary = get_token_usage_summary(trace)

    assert summary["total_tokens"] == 0
    assert summary["prompt_tokens"] == 0
    assert summary["completion_tokens"] == 0
