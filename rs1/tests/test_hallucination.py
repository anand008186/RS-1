"""
Tests for hallucination detection signal.
"""
from rs1.schemas.execution import (
    ExecutionTrace,
    Message,
    ToolCall,
    ToolResult,
    TokenUsage,
)
from rs1.signals.hallucination import detect_hallucination


def test_hallucination_positive_orphaned_calls():
    """Test detection of tool calls without corresponding results."""
    trace = ExecutionTrace(
        trace_id="test-1",
        messages=[
            Message(
                role="assistant",
                content="I'll call the tool",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={"url": "http://example.com"},
                        call_id="call-1",
                    ),
                    ToolCall(
                        tool_name="process_data",
                        arguments={"data": "test"},
                        call_id="call-2",
                    ),
                ],
            ),
            # Only one result, missing result for call-2
            Message(
                role="tool",
                content="Result",
                tool_results=[
                    ToolResult(
                        call_id="call-1",
                        success=True,
                        result="data",
                    )
                ],
            ),
        ],
        token_usage=TokenUsage(100, 50, 150),
    )

    score = detect_hallucination(trace)
    assert score > 0.1, f"Expected positive hallucination score, got {score}"


def test_hallucination_positive_orphaned_results():
    """Test detection of results without corresponding calls."""
    trace = ExecutionTrace(
        trace_id="test-2",
        messages=[
            Message(
                role="assistant",
                content="Calling tool",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={"url": "http://example.com"},
                        call_id="call-1",
                    ),
                ],
            ),
            # Results reference non-existent calls
            Message(
                role="tool",
                content="Results",
                tool_results=[
                    ToolResult(call_id="call-1", success=True, result="data"),
                    ToolResult(
                        call_id="call-99", success=True, result="phantom"
                    ),  # Hallucinated
                ],
            ),
        ],
        token_usage=TokenUsage(100, 50, 150),
    )

    score = detect_hallucination(trace)
    assert score > 0.2, f"Expected positive hallucination score, got {score}"


def test_hallucination_positive_claimed_without_calls():
    """Test detection of claims about tool use without actual tool calls."""
    trace = ExecutionTrace(
        trace_id="test-3",
        messages=[
            Message(
                role="assistant",
                content="I called the fetch_data tool and got results",
                tool_calls=[],  # No actual tool calls
            ),
        ],
        token_usage=TokenUsage(50, 30, 80),
    )

    score = detect_hallucination(trace)
    assert score > 0.2, f"Expected moderate hallucination score, got {score}"


def test_hallucination_negative_clean_trace():
    """Test that clean traces don't trigger hallucination detection."""
    trace = ExecutionTrace(
        trace_id="test-4",
        messages=[
            Message(
                role="user",
                content="Please fetch some data",
            ),
            Message(
                role="assistant",
                content="I'll fetch that for you",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch_data",
                        arguments={"url": "http://example.com"},
                        call_id="call-1",
                    ),
                ],
            ),
            Message(
                role="tool",
                content="Success",
                tool_results=[
                    ToolResult(
                        call_id="call-1",
                        success=True,
                        result="data retrieved",
                    )
                ],
            ),
            Message(
                role="assistant",
                content="Here's the data I retrieved",
            ),
        ],
        token_usage=TokenUsage(200, 100, 300),
    )

    score = detect_hallucination(trace)
    assert score < 0.3, f"Expected low hallucination score for clean trace, got {score}"


def test_hallucination_negative_no_tools():
    """Test that traces without tool use get zero score."""
    trace = ExecutionTrace(
        trace_id="test-5",
        messages=[
            Message(role="user", content="What is 2+2?"),
            Message(role="assistant", content="The answer is 4"),
        ],
        token_usage=TokenUsage(50, 20, 70),
    )

    score = detect_hallucination(trace)
    assert score == 0.0, f"Expected zero score for no-tool trace, got {score}"


def test_hallucination_empty_trace():
    """Test handling of empty trace."""
    trace = ExecutionTrace(
        trace_id="test-6",
        messages=[],
        token_usage=TokenUsage(0, 0, 0),
    )

    score = detect_hallucination(trace)
    assert score == 0.0, f"Expected zero score for empty trace, got {score}"
