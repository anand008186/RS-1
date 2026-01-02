"""
Cost tracking signal.

Tracks token usage and cost efficiency metrics.
"""
from rs1.schemas.execution import ExecutionTrace


# TODO: These thresholds should be configurable or passed as parameters
# For now, using reasonable defaults based on typical agent tasks
NORMAL_TOKEN_THRESHOLD = 10000  # Tokens
HIGH_TOKEN_THRESHOLD = 50000  # Tokens
EXCESSIVE_TOKEN_THRESHOLD = 100000  # Tokens


def detect_excessive_cost(trace: ExecutionTrace) -> float:
    """
    Returns cost/efficiency risk score [0.0-1.0].

    Logic:
    - Checks total token usage against thresholds
    - Checks tokens-per-message ratio (efficiency)
    - Checks for unusually high completion-to-prompt ratio
    - Higher score = higher cost concern

    Args:
        trace: ExecutionTrace object to analyze

    Returns:
        float: Risk score from 0.0 (no risk) to 1.0 (high risk)
    """
    if not trace.messages or not trace.token_usage:
        return 0.0

    risk_score = 0.0
    risk_factors = []

    total_tokens = trace.token_usage.total_tokens
    prompt_tokens = trace.token_usage.prompt_tokens
    completion_tokens = trace.token_usage.completion_tokens
    message_count = trace.get_total_messages()

    # Check 1: Absolute token usage
    if total_tokens > NORMAL_TOKEN_THRESHOLD:
        if total_tokens > EXCESSIVE_TOKEN_THRESHOLD:
            # Very high usage
            token_score = 1.0
        elif total_tokens > HIGH_TOKEN_THRESHOLD:
            # High usage - scale between 0.5 and 1.0
            excess = total_tokens - HIGH_TOKEN_THRESHOLD
            range_size = EXCESSIVE_TOKEN_THRESHOLD - HIGH_TOKEN_THRESHOLD
            token_score = 0.5 + (excess / range_size) * 0.5
        else:
            # Moderate usage - scale between 0.0 and 0.5
            excess = total_tokens - NORMAL_TOKEN_THRESHOLD
            range_size = HIGH_TOKEN_THRESHOLD - NORMAL_TOKEN_THRESHOLD
            token_score = (excess / range_size) * 0.5

        risk_factors.append(min(1.0, token_score))

    # Check 2: Token efficiency (tokens per message)
    if message_count > 0:
        tokens_per_message = total_tokens / message_count

        # TODO: Threshold tuning needed based on real data
        # Assuming ~500 tokens per message is normal for agent interactions
        if tokens_per_message > 1000:
            # Inefficient token usage
            efficiency_score = min(1.0, (tokens_per_message - 1000) / 2000)
            risk_factors.append(efficiency_score * 0.7)  # Weight this moderate

    # Check 3: Completion to prompt ratio
    # A very high ratio might indicate the agent is being overly verbose
    if prompt_tokens > 0:
        completion_ratio = completion_tokens / prompt_tokens

        # TODO: Typical ratio is ~0.3-0.5 for agent tasks
        # If completion is 2x+ the prompt, might be concerning
        if completion_ratio > 2.0:
            ratio_score = min(1.0, (completion_ratio - 2.0) / 3.0)
            risk_factors.append(ratio_score * 0.5)  # Weight this lower

    # Check 4: Zero token usage (data quality issue)
    if total_tokens == 0 and message_count > 0:
        # This is suspicious - we have messages but no token count
        # Could indicate incomplete data
        risk_factors.append(0.3)  # Moderate concern

    # Aggregate risk factors
    if risk_factors:
        # Take maximum risk factor (cost is concerning if ANY metric is high)
        risk_score = max(risk_factors)

    return min(1.0, max(0.0, risk_score))


def get_token_usage_summary(trace: ExecutionTrace) -> dict:
    """
    Get detailed token usage summary for reporting.

    Returns:
        dict: Token usage metrics and analysis
    """
    if not trace.token_usage:
        return {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "tokens_per_message": 0,
            "completion_ratio": 0,
        }

    message_count = trace.get_total_messages()
    tokens_per_message = (
        trace.token_usage.total_tokens / message_count if message_count > 0 else 0
    )
    completion_ratio = (
        trace.token_usage.completion_tokens / trace.token_usage.prompt_tokens
        if trace.token_usage.prompt_tokens > 0
        else 0
    )

    return {
        "total_tokens": trace.token_usage.total_tokens,
        "prompt_tokens": trace.token_usage.prompt_tokens,
        "completion_tokens": trace.token_usage.completion_tokens,
        "tokens_per_message": round(tokens_per_message, 2),
        "completion_ratio": round(completion_ratio, 2),
    }
