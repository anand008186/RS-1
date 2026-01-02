"""
Reliability report schema for RS-1 output.

Defines the output format for the evaluator.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class Verdict(str, Enum):
    """Overall reliability verdict."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class SignalScore:
    """Score for an individual reliability signal."""

    signal_name: str
    score: float  # 0.0 to 1.0, where 1.0 = high risk
    details: Optional[str] = None


@dataclass
class ReliabilityReport:
    """
    Complete reliability evaluation report.

    This is the main output of the RS-1 evaluator.
    Must be serializable to valid JSON.
    """

    trace_id: str
    verdict: Verdict
    overall_score: float  # 0.0 to 1.0, where 1.0 = high risk
    signal_scores: List[SignalScore]
    reasoning: str
    metadata: Dict[str, any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert report to dictionary for JSON serialization."""
        return {
            "trace_id": self.trace_id,
            "verdict": self.verdict.value,
            "overall_score": self.overall_score,
            "signal_scores": [
                {
                    "signal_name": s.signal_name,
                    "score": s.score,
                    "details": s.details,
                }
                for s in self.signal_scores
            ],
            "reasoning": self.reasoning,
            "metadata": self.metadata,
        }
