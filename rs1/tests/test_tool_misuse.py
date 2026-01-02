"""
Tests for tool misuse detection signal.
"""
from rs1.schemas.execution import (
    ExecutionTrace,
    Message,
    ToolCall,
    ToolResult,
    TokenUsage,
)
from rs1.signals.tool_misuse import detect_tool_misuse


def test_tool_misuse_positive_high_error_rate():
    """Test detection of high error rate in tool results."""
    trace = ExecutionTrace(
        trace_id="test-1",
        messages=[
            Message(
                role="assistant",
                content="Calling tools",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={"url": f"http://example{i}.com"},
                        call_id=f"call-{i}",
                    )
                    for i in range(5)
                ],
            ),
            Message(
                role="tool",
                content="Results",
                tool_results=[
                    ToolResult(
                        call_id=f"call-{i}",
                        success=(i == 0),  # Only first succeeds, 80% failure rate
                        result="data" if i == 0 else None,
                        error=None if i == 0 else "Failed to fetch",
                    )
                    for i in range(5)
                ],
            ),
        ],
        token_usage=TokenUsage(300, 150, 450),
    )

    score = detect_tool_misuse(trace)
    assert score > 0.4, f"Expected high misuse score for error rate, got {score}"


def test_tool_misuse_positive_empty_arguments():
    """Test detection of tool calls with empty arguments."""
    trace = ExecutionTrace(
        trace_id="test-2",
        messages=[
            Message(
                role="assistant",
                content="Calling tools",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={},  # Empty args
                        call_id="call-1",
                    ),
                    ToolCall(
                        tool_name="process_data",
                        arguments={},  # Empty args
                        call_id="call-2",
                    ),
                    ToolCall(
                        tool_name="analyze",
                        arguments={"data": "test"},  # Valid
                        call_id="call-3",
                    ),
                ],
            ),
        ],
        token_usage=TokenUsage(200, 100, 300),
    )

    score = detect_tool_misuse(trace)
    assert score > 0.3, f"Expected moderate misuse score for empty args, got {score}"


def test_tool_misuse_positive_null_arguments():
    """Test detection of tool calls with null/None values."""
    trace = ExecutionTrace(
        trace_id="test-3",
        messages=[
            Message(
                role="assistant",
                content="Calling tools",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={"url": None},  # Null value
                        call_id="call-1",
                    ),
                    ToolCall(
                        tool_name="process_data",
                        arguments={"data": "null"},  # String "null"
                        call_id="call-2",
                    ),
                ],
            ),
        ],
        token_usage=TokenUsage(150, 80, 230),
    )

    score = detect_tool_misuse(trace)
    assert score > 0.0, f"Expected positive misuse score for null args, got {score}"


def test_tool_misuse_positive_excessive_single_tool():
    """Test detection of excessive use of single tool."""
    trace = ExecutionTrace(
        trace_id="test-4",
        messages=[
            Message(
                role="assistant",
                content="Fetching",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={"url": f"http://example{i}.com"},
                        call_id=f"call-{i}",
                    )
                    for i in range(10)  # Same tool 10 times
                ],
            ),
        ],
        token_usage=TokenUsage(500, 200, 700),
    )

    score = detect_tool_misuse(trace)
    assert score > 0.0, f"Expected positive misuse score for tool concentration, got {score}"


def test_tool_misuse_negative_clean_usage():
    """Test that proper tool usage doesn't trigger detection."""
    trace = ExecutionTrace(
        trace_id="test-5",
        messages=[
            Message(
                role="assistant",
                content="Processing request",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={"url": "http://example.com"},
                        call_id="call-1",
                    ),
                    ToolCall(
                        tool_name="process_data",
                        arguments={"data": "input"},
                        call_id="call-2",
                    ),
                ],
            ),
            Message(
                role="tool",
                content="Results",
                tool_results=[
                    ToolResult(call_id="call-1", success=True, result="data"),
                    ToolResult(call_id="call-2", success=True, result="processed"),
                ],
            ),
        ],
        token_usage=TokenUsage(250, 120, 370),
    )

    score = detect_tool_misuse(trace)
    assert score < 0.3, f"Expected low misuse score for clean usage, got {score}"


def test_tool_misuse_negative_no_tools():
    """Test that traces without tools get zero score."""
    trace = ExecutionTrace(
        trace_id="test-6",
        messages=[
            Message(role="user", content="What is 2+2?"),
            Message(role="assistant", content="The answer is 4"),
        ],
        token_usage=TokenUsage(50, 20, 70),
    )

    score = detect_tool_misuse(trace)
    assert score == 0.0, f"Expected zero score for no-tool trace, got {score}"


def test_tool_misuse_empty_trace():
    """Test handling of empty trace."""
    trace = ExecutionTrace(
        trace_id="test-7",
        messages=[],
        token_usage=TokenUsage(0, 0, 0),
    )

    score = detect_tool_misuse(trace)
    assert score == 0.0, f"Expected zero score for empty trace, got {score}"


def test_tool_misuse_acceptable_error_rate():
    """Test that low error rates don't trigger detection."""
    trace = ExecutionTrace(
        trace_id="test-8",
        messages=[
            Message(
                role="assistant",
                content="Calling tools",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={"url": f"http://example{i}.com"},
                        call_id=f"call-{i}",
                    )
                    for i in range(10)
                ],
            ),
            Message(
                role="tool",
                content="Results",
                tool_results=[
                    ToolResult(
                        call_id=f"call-{i}",
                        success=(i != 0),  # Only 1 failure out of 10 (10% error rate)
                        result="data" if i != 0 else None,
                        error="Failed" if i == 0 else None,
                    )
                    for i in range(10)
                ],
            ),
        ],
        token_usage=TokenUsage(600, 300, 900),
    )

    score = detect_tool_misuse(trace)
    # 10% error rate is low, but tool concentration may trigger
    assert score < 0.6, f"Expected moderate misuse score for acceptable error rate, got {score}"
