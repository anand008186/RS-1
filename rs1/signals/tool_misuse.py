"""
Tool misuse detection signal.

Detects improper or dangerous tool usage patterns.
"""
from rs1.schemas.execution import ExecutionTrace, ToolCall, ToolResult


def detect_tool_misuse(trace: ExecutionTrace) -> float:
    """
    Returns tool misuse risk score [0.0-1.0].

    Logic:
    - Detects high error rates in tool calls (many failed tool results)
    - Detects missing required arguments (empty or null arguments)
    - Detects suspicious tool call patterns (e.g., too many calls of same tool)
    - Higher score = higher misuse risk

    Args:
        trace: ExecutionTrace object to analyze

    Returns:
        float: Risk score from 0.0 (no risk) to 1.0 (high risk)
    """
    if not trace.messages:
        return 0.0

    risk_score = 0.0
    risk_factors = []

    tool_calls = trace.get_tool_calls()
    tool_results = trace.get_tool_results()

    # Early exit if no tools used
    if not tool_calls:
        return 0.0

    # Check 1: High error rate in tool results
    if tool_results:
        failed_results = [r for r in tool_results if not r.success]
        error_rate = len(failed_results) / len(tool_results)

        if error_rate > 0.3:  # More than 30% failures
            # Scale score based on error rate
            error_score = min(1.0, error_rate * 1.5)
            risk_factors.append(error_score)

    # Check 2: Tool calls with missing or empty arguments
    calls_with_bad_args = 0
    for call in tool_calls:
        # Check if arguments are empty or contain null/None values
        if not call.arguments:
            calls_with_bad_args += 1
        elif _has_empty_required_args(call.arguments):
            calls_with_bad_args += 1

    if calls_with_bad_args > 0:
        bad_args_ratio = calls_with_bad_args / len(tool_calls)
        if bad_args_ratio > 0.2:  # More than 20% have bad args
            risk_factors.append(bad_args_ratio)

    # Check 3: Excessive use of single tool (potential misuse pattern)
    tool_usage_counts = {}
    for call in tool_calls:
        tool_usage_counts[call.tool_name] = tool_usage_counts.get(call.tool_name, 0) + 1

    if tool_usage_counts:
        max_usage = max(tool_usage_counts.values())
        total_calls = len(tool_calls)

        # If single tool is >70% of all calls and used >5 times, suspicious
        if max_usage > 5 and (max_usage / total_calls) > 0.7:
            concentration_score = min(1.0, (max_usage / total_calls - 0.5) * 2)
            risk_factors.append(concentration_score * 0.5)  # Weight this lower

    # Check 4: Tool calls with arguments that look like error messages
    # (agent might be confused about tool usage)
    suspicious_arg_patterns = ["error", "failed", "undefined", "null", "none"]
    calls_with_suspicious_args = 0

    for call in tool_calls:
        arg_str = str(call.arguments).lower()
        if any(pattern in arg_str for pattern in suspicious_arg_patterns):
            calls_with_suspicious_args += 1

    if calls_with_suspicious_args > 0:
        suspicious_ratio = calls_with_suspicious_args / len(tool_calls)
        if suspicious_ratio > 0.3:  # More than 30%
            risk_factors.append(suspicious_ratio * 0.7)

    # Aggregate risk factors
    if risk_factors:
        # Average the risk factors
        risk_score = sum(risk_factors) / len(risk_factors)

    return min(1.0, max(0.0, risk_score))


def _has_empty_required_args(args: dict) -> bool:
    """
    Check if arguments contain empty/null values that might indicate misuse.

    Note: This is a heuristic. We don't know which args are actually required
    without tool schemas, so we check for obviously problematic patterns.
    """
    for key, value in args.items():
        # Check for None, empty string, or explicit "null"/"undefined"
        if value is None:
            return True
        if isinstance(value, str) and value.strip() in ["", "null", "undefined", "None"]:
            return True

    return False
