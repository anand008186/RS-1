# RS-1: Reliability Sentinel

Infrastructure-grade agent reliability evaluator for the Sentient ecosystem.

## Overview

RS-1 is a deterministic, stateless evaluation system that analyzes agent execution traces for reliability issues. It provides transparent scoring and rule-based verdicts without external dependencies or ML models.

**Type**: Critical infrastructure component
**Language**: Python 3.10+
**Design**: Stateless, deterministic, auditable

## Quick Start

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Evaluate a trace from file
python -m rs1.cli trace.json

# Evaluate from stdin
cat trace.json | python -m rs1.cli --stdin

# With verbose output
python -m rs1.cli trace.json --verbose

# Pretty-print JSON output
python -m rs1.cli trace.json --pretty
```

### Python API

```python
from rs1.core.evaluator import evaluate_trace
from rs1.schemas.execution import ExecutionTrace

# Load your trace
trace = ExecutionTrace(
    trace_id="example-1",
    messages=[...],
    token_usage=TokenUsage(...)
)

# Evaluate
report = evaluate_trace(trace)

# Access results
print(f"Verdict: {report.verdict}")
print(f"Score: {report.overall_score}")
print(f"Reasoning: {report.reasoning}")
```

## Input/Output Contract

### Input: ExecutionTrace

```json
{
  "trace_id": "unique-identifier",
  "messages": [
    {
      "role": "user|assistant|system|tool",
      "content": "message text",
      "tool_calls": [...],
      "tool_results": [...],
      "timestamp": "ISO-8601"
    }
  ],
  "token_usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  },
  "metadata": {}
}
```

### Output: ReliabilityReport

```json
{
  "trace_id": "unique-identifier",
  "verdict": "PASS|WARN|FAIL",
  "overall_score": 0.35,
  "signal_scores": [
    {
      "signal_name": "hallucination",
      "score": 0.2,
      "details": "No significant hallucination detected"
    }
  ],
  "reasoning": "Overall reliability score: 0.35...",
  "metadata": {
    "total_messages": 10,
    "total_tool_calls": 3,
    "total_tokens": 1500
  }
}
```

## Architecture

### Reliability Signals

RS-1 evaluates four independent signals:

1. **Hallucination** (35% weight)
   - Detects tool calls without results
   - Detects claims about tool use without actual calls
   - Detects orphaned tool results

2. **Loop Detection** (25% weight)
   - Detects repeated identical tool calls
   - Detects similar repeated messages
   - Detects excessive message counts

3. **Tool Misuse** (25% weight)
   - Tracks tool call error rates
   - Detects missing/empty arguments
   - Detects suspicious argument patterns

4. **Cost** (15% weight)
   - Tracks token usage efficiency
   - Detects excessive resource consumption
   - Monitors completion-to-prompt ratios

### Scoring

Overall score is calculated using **linear weighted aggregation**:

```
overall_score = Σ(signal_score × signal_weight)
```

Where:
- All scores are in range [0.0, 1.0]
- Higher score = higher risk
- Weights are fixed and transparent
- No ML or adaptive thresholds

### Policy Rules

Verdicts are determined by **rule-based thresholds**:

- **PASS**: overall_score < 0.4 and no critical signals
- **WARN**: overall_score >= 0.4 or critical tool_misuse/cost
- **FAIL**: overall_score >= 0.7 or critical hallucination/loop

Critical thresholds:
- Hallucination >= 0.8 → FAIL
- Loop >= 0.8 → FAIL
- Tool misuse >= 0.7 → WARN
- Cost >= 0.9 → WARN

## Project Structure

```
rs1/
├── core/
│   ├── evaluator.py     # Main orchestrator
│   ├── scorer.py        # Score aggregation
│   └── policy.py        # Threshold rules
├── signals/
│   ├── hallucination.py # Hallucination detection
│   ├── loop.py          # Loop detection
│   ├── tool_misuse.py   # Tool misuse detection
│   └── cost.py          # Cost tracking
├── schemas/
│   ├── execution.py     # ExecutionTrace schema
│   └── report.py        # ReliabilityReport schema
├── tests/
│   └── test_*.py        # Test suite
├── cli.py               # Command-line interface
└── README.md
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rs1 --cov-report=html

# Run specific test file
pytest rs1/tests/test_hallucination.py

# Run with verbose output
pytest -v
```

### Test Coverage

All signals have:
- ✅ Positive tests (should detect issue)
- ✅ Negative tests (should not false-positive)
- ✅ Edge case tests (empty traces, boundary conditions)

## Design Principles

### Must Be
- **Stateless**: No memory between evaluations
- **Deterministic**: Same input → same output, always
- **Explicit**: No hidden state or side effects
- **Portable**: Can be rewritten in Go later

### Must Not Be
- A web service or API
- An async pipeline
- ML/learning-based
- Dependent on external services

## Exit Codes

When using the CLI:

- `0`: PASS verdict
- `1`: WARN verdict
- `2`: FAIL verdict
- `3`: Error during evaluation

## Development

### Adding a New Signal

1. Create signal file in `rs1/signals/`
2. Implement function: `ExecutionTrace → float`
3. Add weight to `rs1/core/scorer.py`
4. Register in `rs1/core/evaluator.py`
5. Add tests in `rs1/tests/`

### Code Requirements

- ✅ Type hints on all functions
- ✅ Docstrings on all modules
- ✅ No external dependencies in core logic
- ✅ Deterministic (no time, random, network calls)

## API Reference

### evaluate_trace(trace: ExecutionTrace) → ReliabilityReport

Main entry point for evaluation.

**Args:**
- `trace`: ExecutionTrace object to evaluate

**Returns:**
- ReliabilityReport with verdict, scores, and reasoning

**Raises:**
- `ValueError`: If trace is invalid

### Signal Functions

All signal functions follow this contract:

```python
def detect_signal(trace: ExecutionTrace) -> float:
    """
    Returns risk score [0.0-1.0].

    Args:
        trace: ExecutionTrace to analyze

    Returns:
        float: Risk score where 1.0 = high risk
    """
```

## Troubleshooting

### "Cannot evaluate: trace_id is required"

Ensure your ExecutionTrace has a non-empty `trace_id` field.

### "Unknown signal: X"

You've added a signal without registering it in the scorer weights.

### Tests failing

Ensure you're using Python 3.10+ and have installed test dependencies:

```bash
pip install pytest
```

## License

Copyright 2026 Sentient. All rights reserved.

## Contributing

This is infrastructure code. Changes require:

1. Approval from architecture team
2. Full test coverage
3. No new external dependencies (unless critical)
4. Backward compatibility with existing traces

## Support

For issues or questions:
- File a bug report with example trace
- Include full error output
- Specify Python version and OS

## Roadmap

- [x] Core signal implementation
- [x] Linear aggregation scorer
- [x] Rule-based policy
- [x] CLI interface
- [x] Comprehensive tests
- [ ] Go implementation (future)
- [ ] Performance benchmarks (future)
- [ ] Signal tuning based on production data (future)
