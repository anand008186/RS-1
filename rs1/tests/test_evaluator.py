"""
Tests for main evaluator orchestrator.
"""
import pytest
from rs1.schemas.execution import (
    ExecutionTrace,
    Message,
    ToolCall,
    ToolResult,
    TokenUsage,
)
from rs1.schemas.report import Verdict
from rs1.core.evaluator import evaluate_trace


def test_evaluate_trace_basic():
    """Test basic trace evaluation."""
    trace = ExecutionTrace(
        trace_id="test-1",
        messages=[
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there"),
        ],
        token_usage=TokenUsage(50, 30, 80),
    )

    report = evaluate_trace(trace)

    assert report.trace_id == "test-1"
    assert report.verdict in [Verdict.PASS, Verdict.WARN, Verdict.FAIL]
    assert 0.0 <= report.overall_score <= 1.0
    assert len(report.signal_scores) == 4  # 4 signals
    assert report.reasoning


def test_evaluate_trace_clean_execution():
    """Test evaluation of clean execution."""
    trace = ExecutionTrace(
        trace_id="test-2",
        messages=[
            Message(role="user", content="Please analyze this"),
            Message(
                role="assistant",
                content="I'll analyze it",
                tool_calls=[
                    ToolCall(
                        tool_name="analyze",
                        arguments={"data": "input"},
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
        token_usage=TokenUsage(200, 100, 300),
    )

    report = evaluate_trace(trace)

    assert report.verdict == Verdict.PASS
    assert report.overall_score < 0.4  # Should be low risk
    assert all(s.score < 0.5 for s in report.signal_scores)


def test_evaluate_trace_with_hallucination():
    """Test evaluation of trace with hallucination."""
    trace = ExecutionTrace(
        trace_id="test-3",
        messages=[
            Message(
                role="assistant",
                content="I called tools",
                tool_calls=[
                    ToolCall(
                        tool_name="fetch",
                        arguments={"url": "test"},
                        call_id="call-1",
                    )
                ],
            ),
            # Missing result - hallucination
            Message(role="assistant", content="Got results from call-99"),
        ],
        token_usage=TokenUsage(100, 50, 150),
    )

    report = evaluate_trace(trace)

    # Should detect hallucination
    hallucination_score = next(
        s for s in report.signal_scores if s.signal_name == "hallucination"
    )
    assert hallucination_score.score > 0.3


def test_evaluate_trace_with_loop():
    """Test evaluation of trace with loop."""
    trace = ExecutionTrace(
        trace_id="test-4",
        messages=[
            Message(role="assistant", content="Processing") for _ in range(70)
        ],  # Excessive messages
        token_usage=TokenUsage(7000, 3000, 10000),
    )

    report = evaluate_trace(trace)

    # Should detect loop
    loop_score = next(s for s in report.signal_scores if s.signal_name == "loop")
    assert loop_score.score > 0.0


def test_evaluate_trace_missing_trace_id():
    """Test that evaluation fails without trace_id."""
    trace = ExecutionTrace(
        trace_id="",
        messages=[Message(role="user", content="Test")],
        token_usage=TokenUsage(50, 30, 80),
    )

    with pytest.raises(ValueError, match="trace_id is required"):
        evaluate_trace(trace)


def test_evaluate_trace_none():
    """Test that evaluation fails with None trace."""
    with pytest.raises(ValueError, match="trace is None"):
        evaluate_trace(None)


def test_evaluate_trace_signal_scores_present():
    """Test that all signal scores are present in report."""
    trace = ExecutionTrace(
        trace_id="test-5",
        messages=[Message(role="user", content="Test")],
        token_usage=TokenUsage(50, 30, 80),
    )

    report = evaluate_trace(trace)

    signal_names = {s.signal_name for s in report.signal_scores}
    expected_signals = {"hallucination", "loop", "tool_misuse", "cost"}

    assert signal_names == expected_signals


def test_evaluate_trace_metadata():
    """Test that metadata is populated in report."""
    trace = ExecutionTrace(
        trace_id="test-6",
        messages=[
            Message(role="user", content="Test"),
            Message(
                role="assistant",
                content="Response",
                tool_calls=[
                    ToolCall(tool_name="test", arguments={}, call_id="call-1")
                ],
            ),
        ],
        token_usage=TokenUsage(100, 50, 150),
    )

    report = evaluate_trace(trace)

    assert "total_messages" in report.metadata
    assert "total_tool_calls" in report.metadata
    assert "total_tokens" in report.metadata
    assert report.metadata["total_messages"] == 2
    assert report.metadata["total_tool_calls"] == 1
    assert report.metadata["total_tokens"] == 150


def test_evaluate_trace_report_to_dict():
    """Test that report can be converted to dict."""
    trace = ExecutionTrace(
        trace_id="test-7",
        messages=[Message(role="user", content="Test")],
        token_usage=TokenUsage(50, 30, 80),
    )

    report = evaluate_trace(trace)
    report_dict = report.to_dict()

    assert isinstance(report_dict, dict)
    assert "trace_id" in report_dict
    assert "verdict" in report_dict
    assert "overall_score" in report_dict
    assert "signal_scores" in report_dict
    assert "reasoning" in report_dict
    assert isinstance(report_dict["signal_scores"], list)
