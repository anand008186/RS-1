"""
Hallucination detection signal.

Detects potential hallucinated responses from the agent.
"""
from rs1.schemas.execution import ExecutionTrace


def detect_hallucination(trace: ExecutionTrace) -> float:
    """
    Returns hallucination risk score [0.0-1.0].

    Logic:
    - Checks for tool calls with no corresponding results (orphaned calls)
    - Checks for tool results referenced in responses that don't exist
    - Checks for assistant messages that claim tool use without actual tool calls
    - Higher score = higher hallucination risk

    Args:
        trace: ExecutionTrace object to analyze

    Returns:
        float: Risk score from 0.0 (no risk) to 1.0 (high risk)
    """
    if not trace.messages:
        return 0.0

    risk_score = 0.0
    risk_count = 0
    max_risks = 0

    # Get all tool calls and results
    all_tool_calls = trace.get_tool_calls()
    all_tool_results = trace.get_tool_results()

    # Create mapping of call_ids to results
    result_call_ids = {r.call_id for r in all_tool_results if r.call_id is not None}
    call_ids = {c.call_id for c in all_tool_calls if c.call_id is not None}

    # Check 1: Tool calls without results (orphaned calls)
    if call_ids:
        max_risks += 1
        orphaned_calls = call_ids - result_call_ids
        if orphaned_calls:
            risk_count += 1
            # Severity based on percentage of orphaned calls
            orphan_ratio = len(orphaned_calls) / len(call_ids)
            risk_score += orphan_ratio

    # Check 2: Results without corresponding calls
    if result_call_ids:
        max_risks += 1
        orphaned_results = result_call_ids - call_ids
        if orphaned_results:
            risk_count += 1
            # This is a strong indicator of hallucination
            orphan_ratio = len(orphaned_results) / len(result_call_ids)
            risk_score += orphan_ratio * 1.5  # Weight this higher

    # Check 3: Assistant messages claiming tool use without actual tool calls
    assistant_messages = trace.get_assistant_messages()
    if assistant_messages:
        max_risks += 1
        tool_claim_keywords = [
            "called",
            "using the tool",
            "tool call",
            "executed",
            "ran the",
            "invoked",
        ]
        for msg in assistant_messages:
            content_lower = msg.content.lower()
            # Check if message claims tool use
            claims_tool_use = any(keyword in content_lower for keyword in tool_claim_keywords)
            # But has no actual tool calls
            has_tool_calls = len(msg.tool_calls) > 0

            if claims_tool_use and not has_tool_calls:
                risk_count += 1
                risk_score += 0.5  # Moderate risk
                break  # Only count once

    # Normalize score
    if max_risks > 0:
        normalized_score = risk_score / max_risks
        # Clamp to [0.0, 1.0]
        return min(1.0, max(0.0, normalized_score))

    return 0.0
