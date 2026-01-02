"""
Tests for loop detection signal.
"""
from rs1.schemas.execution import (
    ExecutionTrace,
    Message,
    ToolCall,
    ToolResult,
    TokenUsage,
)
from rs1.signals.loop import detect_loop


def test_loop_positive_repeated_tool_calls():
    """Test detection of repeated identical tool calls."""
    trace = ExecutionTrace(
        trace_id="test-1",
        messages=[
            Message(
                role="assistant",
                content="Fetching data",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={"url": "http://example.com"},
                        call_id=f"call-{i}",
                    )
                    for i in range(5)  # Same call repeated 5 times
                ],
            ),
        ],
        token_usage=TokenUsage(500, 200, 700),
    )

    score = detect_loop(trace)
    assert score > 0.3, f"Expected high loop score for repeated calls, got {score}"


def test_loop_positive_similar_messages():
    """Test detection of repeated similar assistant messages."""
    trace = ExecutionTrace(
        trace_id="test-2",
        messages=[
            Message(role="assistant", content="I will process the data now"),
            Message(role="assistant", content="I will process the data now"),
            Message(role="assistant", content="I will process the data now"),
            Message(role="assistant", content="I will process the data now"),
        ],
        token_usage=TokenUsage(400, 200, 600),
    )

    score = detect_loop(trace)
    assert score > 0.5, f"Expected high loop score for similar messages, got {score}"


def test_loop_positive_excessive_messages():
    """Test detection of excessive message count."""
    # Create trace with many messages
    messages = [
        Message(role="user", content="Request") if i % 2 == 0 else Message(role="assistant", content=f"Response {i}")
        for i in range(60)  # 60 messages (above threshold)
    ]

    trace = ExecutionTrace(
        trace_id="test-3",
        messages=messages,
        token_usage=TokenUsage(5000, 3000, 8000),
    )

    score = detect_loop(trace)
    assert score > 0.0, f"Expected positive loop score for excessive messages, got {score}"


def test_loop_negative_clean_trace():
    """Test that normal traces don't trigger loop detection."""
    trace = ExecutionTrace(
        trace_id="test-4",
        messages=[
            Message(role="user", content="Please analyze this data"),
            Message(
                role="assistant",
                content="I'll analyze it",
                tool_calls=[
                    ToolCall(
                        tool_name="analyze",
                        arguments={"data": "input1"},
                        call_id="call-1",
                    )
                ],
            ),
            Message(
                role="tool",
                content="Result",
                tool_results=[
                    ToolResult(call_id="call-1", success=True, result="analysis")
                ],
            ),
            Message(role="assistant", content="Here are the results"),
        ],
        token_usage=TokenUsage(300, 150, 450),
    )

    score = detect_loop(trace)
    assert score < 0.3, f"Expected low loop score for clean trace, got {score}"


def test_loop_negative_varied_tool_calls():
    """Test that varied tool calls don't trigger loop detection."""
    trace = ExecutionTrace(
        trace_id="test-5",
        messages=[
            Message(
                role="assistant",
                content="Processing",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={"url": "http://example1.com"},
                        call_id="call-1",
                    ),
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={"url": "http://example2.com"},
                        call_id="call-2",
                    ),
                    ToolCall(
                        tool_name="process_data",
                        arguments={"data": "test"},
                        call_id="call-3",
                    ),
                ],
            ),
        ],
        token_usage=TokenUsage(200, 100, 300),
    )

    score = detect_loop(trace)
    assert score < 0.3, f"Expected low loop score for varied calls, got {score}"


def test_loop_empty_trace():
    """Test handling of empty trace."""
    trace = ExecutionTrace(
        trace_id="test-6",
        messages=[],
        token_usage=TokenUsage(0, 0, 0),
    )

    score = detect_loop(trace)
    assert score == 0.0, f"Expected zero score for empty trace, got {score}"


def test_loop_few_messages():
    """Test that traces with few messages don't trigger false positives."""
    trace = ExecutionTrace(
        trace_id="test-7",
        messages=[
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there"),
        ],
        token_usage=TokenUsage(50, 30, 80),
    )

    score = detect_loop(trace)
    assert score == 0.0, f"Expected zero score for minimal trace, got {score}"
