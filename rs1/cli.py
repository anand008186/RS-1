"""
Command-line interface for RS-1 evaluator.

Usage:
    python -m rs1.cli <trace_file.json>
    python -m rs1.cli --stdin

Output:
    - JSON report on stdout
    - Human-readable summary on stderr (if --verbose)
"""
import sys
import json
import argparse
from typing import Optional
from pathlib import Path

from rs1.schemas.execution import ExecutionTrace, Message, ToolCall, ToolResult, TokenUsage
from rs1.core.evaluator import evaluate_trace


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="RS-1: Reliability Sentinel - Agent Reliability Evaluator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "trace_file",
        nargs="?",
        help="Path to execution trace JSON file (use --stdin to read from stdin)",
    )

    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read execution trace from stdin instead of file",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print human-readable summary to stderr",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )

    args = parser.parse_args()

    # Validate input
    if not args.stdin and not args.trace_file:
        parser.print_help(sys.stderr)
        return 1

    try:
        # Load trace
        if args.stdin:
            trace = _load_trace_from_stdin()
        else:
            trace = _load_trace_from_file(args.trace_file)

        # Evaluate
        report = evaluate_trace(trace)

        # Output JSON to stdout
        report_dict = report.to_dict()
        if args.pretty:
            json.dump(report_dict, sys.stdout, indent=2)
        else:
            json.dump(report_dict, sys.stdout)
        sys.stdout.write("\n")

        # Optional human-readable summary to stderr
        if args.verbose:
            _print_summary(report, sys.stderr)

        # Exit code based on verdict
        if report.verdict.value == "FAIL":
            return 2
        elif report.verdict.value == "WARN":
            return 1
        else:
            return 0

    except Exception as e:
        # Error output to stderr
        print(f"Error: {e}", file=sys.stderr)
        return 3


def _load_trace_from_file(file_path: str) -> ExecutionTrace:
    """Load execution trace from JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Trace file not found: {file_path}")

    with open(path, "r") as f:
        data = json.load(f)

    return _parse_trace_dict(data)


def _load_trace_from_stdin() -> ExecutionTrace:
    """Load execution trace from stdin."""
    data = json.load(sys.stdin)
    return _parse_trace_dict(data)


def _parse_trace_dict(data: dict) -> ExecutionTrace:
    """
    Parse dictionary into ExecutionTrace object.

    This handles the conversion from JSON dict to typed dataclasses.
    """
    # Parse messages
    messages = []
    for msg_data in data.get("messages", []):
        # Parse tool calls
        tool_calls = []
        for call_data in msg_data.get("tool_calls", []):
            tool_calls.append(
                ToolCall(
                    tool_name=call_data["tool_name"],
                    arguments=call_data.get("arguments", {}),
                    timestamp=call_data.get("timestamp"),
                    call_id=call_data.get("call_id"),
                )
            )

        # Parse tool results
        tool_results = []
        for result_data in msg_data.get("tool_results", []):
            tool_results.append(
                ToolResult(
                    call_id=result_data.get("call_id"),
                    success=result_data.get("success", False),
                    result=result_data.get("result"),
                    error=result_data.get("error"),
                    timestamp=result_data.get("timestamp"),
                )
            )

        messages.append(
            Message(
                role=msg_data["role"],
                content=msg_data.get("content", ""),
                tool_calls=tool_calls,
                tool_results=tool_results,
                timestamp=msg_data.get("timestamp"),
            )
        )

    # Parse token usage
    token_data = data.get("token_usage", {})
    token_usage = TokenUsage(
        prompt_tokens=token_data.get("prompt_tokens", 0),
        completion_tokens=token_data.get("completion_tokens", 0),
        total_tokens=token_data.get("total_tokens", 0),
    )

    # Create trace
    trace = ExecutionTrace(
        trace_id=data["trace_id"],
        messages=messages,
        token_usage=token_usage,
        metadata=data.get("metadata", {}),
    )

    return trace


def _print_summary(report, output_file) -> None:
    """Print human-readable summary to specified file (typically stderr)."""
    output_file.write("\n" + "=" * 60 + "\n")
    output_file.write("RS-1 RELIABILITY EVALUATION SUMMARY\n")
    output_file.write("=" * 60 + "\n\n")

    output_file.write(f"Trace ID: {report.trace_id}\n")
    output_file.write(f"Verdict: {report.verdict.value}\n")
    output_file.write(f"Overall Score: {report.overall_score:.2f}\n\n")

    output_file.write("Signal Scores:\n")
    for signal in report.signal_scores:
        output_file.write(f"  {signal.signal_name:15s}: {signal.score:.2f}\n")
        if signal.details:
            output_file.write(f"    └─ {signal.details}\n")

    output_file.write(f"\nReasoning:\n  {report.reasoning}\n")

    output_file.write("\n" + "=" * 60 + "\n\n")


if __name__ == "__main__":
    sys.exit(main())
