"""
Execution trace schema for agent interactions.

Defines the input format for RS-1 evaluator.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ToolCall:
    """Represents a single tool invocation by the agent."""

    tool_name: str
    arguments: Dict[str, Any]
    timestamp: Optional[str] = None  # ISO format timestamp
    call_id: Optional[str] = None


@dataclass
class ToolResult:
    """Represents the result of a tool invocation."""

    call_id: Optional[str]
    success: bool
    result: Any
    error: Optional[str] = None
    timestamp: Optional[str] = None  # ISO format timestamp


@dataclass
class Message:
    """Represents a message in the agent conversation."""

    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)
    timestamp: Optional[str] = None  # ISO format timestamp


@dataclass
class TokenUsage:
    """Token usage metrics for the execution."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ExecutionTrace:
    """
    Complete execution trace of an agent interaction.

    This is the main input to the RS-1 evaluator.
    Contains all messages, tool calls, and metadata from an agent execution.
    """

    trace_id: str
    messages: List[Message]
    token_usage: TokenUsage
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_tool_calls(self) -> List[ToolCall]:
        """Extract all tool calls from the trace."""
        calls = []
        for message in self.messages:
            calls.extend(message.tool_calls)
        return calls

    def get_tool_results(self) -> List[ToolResult]:
        """Extract all tool results from the trace."""
        results = []
        for message in self.messages:
            results.extend(message.tool_results)
        return results

    def get_assistant_messages(self) -> List[Message]:
        """Extract all assistant messages."""
        return [msg for msg in self.messages if msg.role == 'assistant']

    def get_total_messages(self) -> int:
        """Get total number of messages in trace."""
        return len(self.messages)
