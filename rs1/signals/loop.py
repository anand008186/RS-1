"""
Loop detection signal.

Detects potential infinite loops or repetitive behavior.
"""
from typing import List, Tuple
from rs1.schemas.execution import ExecutionTrace, Message, ToolCall


def detect_loop(trace: ExecutionTrace) -> float:
    """
    Returns loop/repetition risk score [0.0-1.0].

    Logic:
    - Detects repeated identical tool calls with same arguments
    - Detects repeated similar assistant messages (content similarity)
    - Detects excessive message count for simple interactions
    - Higher score = higher loop risk

    Args:
        trace: ExecutionTrace object to analyze

    Returns:
        float: Risk score from 0.0 (no risk) to 1.0 (high risk)
    """
    if not trace.messages:
        return 0.0

    risk_score = 0.0
    risk_factors = []

    # Check 1: Repeated identical tool calls
    tool_calls = trace.get_tool_calls()
    if len(tool_calls) >= 3:
        # Create signatures for tool calls (tool_name + args)
        call_signatures = []
        for call in tool_calls:
            # Create a simple signature from tool name and sorted args
            signature = (call.tool_name, _dict_to_signature(call.arguments))
            call_signatures.append(signature)

        # Count repeated signatures
        signature_counts = {}
        for sig in call_signatures:
            signature_counts[sig] = signature_counts.get(sig, 0) + 1

        # If any signature repeats more than 3 times, it's suspicious
        max_repeats = max(signature_counts.values()) if signature_counts else 0
        if max_repeats >= 3:
            # Score increases with repetition count
            repeat_score = min(1.0, (max_repeats - 2) / 8.0)  # Maxes at 10 repeats
            risk_factors.append(repeat_score)

    # Check 2: Repeated similar assistant messages
    assistant_messages = trace.get_assistant_messages()
    if len(assistant_messages) >= 3:
        message_contents = [msg.content for msg in assistant_messages]
        similar_pairs = 0
        total_pairs = 0

        # Check consecutive messages for similarity
        for i in range(len(message_contents) - 1):
            total_pairs += 1
            if _simple_similarity(message_contents[i], message_contents[i + 1]) > 0.7:
                similar_pairs += 1

        if total_pairs > 0:
            similarity_ratio = similar_pairs / total_pairs
            if similarity_ratio > 0.5:  # More than half are similar
                risk_factors.append(similarity_ratio)

    # Check 3: Excessive message count (potential runaway)
    # TODO: This threshold may need tuning based on real-world data
    message_count = trace.get_total_messages()
    if message_count > 50:
        # Score increases logarithmically with message count
        excess_score = min(1.0, (message_count - 50) / 100.0)
        risk_factors.append(excess_score)

    # Aggregate risk factors
    if risk_factors:
        # Take the maximum risk factor as the overall score
        # (if any one factor is high, we have a loop problem)
        risk_score = max(risk_factors)

    return min(1.0, max(0.0, risk_score))


def _dict_to_signature(d: dict) -> str:
    """Convert dict to deterministic string signature."""
    if not d:
        return ""
    # Sort keys and create simple string representation
    items = sorted(d.items())
    return str(items)


def _simple_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple text similarity using character overlap.

    This is a basic implementation. For production, consider more
    sophisticated methods, but keeping it simple for determinism.
    """
    if not text1 or not text2:
        return 0.0

    # Normalize
    t1 = text1.lower().strip()
    t2 = text2.lower().strip()

    if t1 == t2:
        return 1.0

    # Simple character-based similarity
    # Convert to character sets and calculate Jaccard similarity
    set1 = set(t1)
    set2 = set(t2)

    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0
