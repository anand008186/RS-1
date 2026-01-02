# RS-1 (Reliability Sentinel) — Claude Code Instructions

## Project Overview

**What**: Infrastructure-grade agent reliability evaluator for Sentient ecosystem  
**Type**: Critical infrastructure component, NOT a demo or UI app  
**Purpose**: Evaluate agent execution traces for reliability issues and provide deterministic scores

## Input/Output Contract

```
ExecutionTrace (JSON) → RS-1 Evaluator → ReliabilityReport (JSON)
```

**Critical**: This must be stateless, deterministic, and auditable.

---

## Technology Stack

**Language**: Python 3.10+
- Type hints required on all functions
- Standard library preferred
- Dataclasses/Pydantic for schemas only

**Forbidden Dependencies**:
- ❌ LangChain, LangGraph, AutoGen
- ❌ FastAPI, Flask, Django (no web servers)
- ❌ async/await (unless explicitly required)
- ❌ Heavy frameworks of any kind

**Allowed**:
- ✅ Standard library
- ✅ pydantic (schemas only)
- ✅ pytest (testing)

---

## Architecture Constraints

### Must Be
- **Stateless**: No memory between evaluations
- **Deterministic**: Same input always produces same output
- **Explicit**: No hidden state, side effects, or global variables
- **Portable**: Can be rewritten in Go later

### Must Not Be
- A web service or API
- An async pipeline
- ML/learning-based (no model weights, no training)
- Dependent on external services during evaluation

---

## Project Structure

```
rs1/
├── core/
│   ├── evaluator.py     # Main orchestrator
│   ├── scorer.py        # Score aggregation
│   └── policy.py        # Threshold rules
├── signals/
│   ├── hallucination.py # Detects hallucinated data
│   ├── loop.py          # Detects infinite loops
│   ├── tool_misuse.py   # Detects improper tool use
│   └── cost.py          # Tracks token/cost metrics
├── schemas/
│   ├── execution.py     # ExecutionTrace schema
│   └── report.py        # ReliabilityReport schema
├── tests/
│   └── test_*.py
├── cli.py
└── README.md
```

**Do not deviate from this structure without explicit approval.**

---

## Signal Implementation Rules

Each signal in `signals/` must:

1. **Accept only**: `ExecutionTrace` object
2. **Return**: Primitive type (`float`, `bool`, or `int`)
3. **Be independent**: No dependencies on other signals
4. **Be deterministic**: No LLM calls, no random numbers, no timestamps
5. **Be explainable**: Logic documented in comments

### Example Signal Structure

```python
from schemas.execution import ExecutionTrace

def detect_hallucination(trace: ExecutionTrace) -> float:
    """
    Returns hallucination risk score [0.0-1.0].
    
    Logic:
    - Checks for tool calls with no corresponding results
    - Measures response coherence with context
    """
    # Implementation here
    return score
```

### What Signals Should NOT Do
- Make network requests
- Call LLMs or external APIs
- Use randomness or current time
- Depend on filesystem state
- Share state with other signals

---

## Scoring & Policy Rules

### Scoring (`scorer.py`)
- Transparent, linear aggregation
- No learned weights or adaptive thresholds
- Formula must be documented and auditable

### Policy (`policy.py`)
- Rule-based thresholds only
- No ML-based decisions
- Output: PASS, WARN, FAIL + reasoning

---

## Output Contract

### JSON Output
- Must conform to `ReliabilityReport` schema exactly
- No extra fields, no logs mixed in
- Valid JSON always, even on errors

### Human Output (Optional)
- CLI may print separate human-readable summary
- Keep this separate from JSON output
- Use stderr for logs, stdout for JSON

---

## Testing Requirements

Every signal needs minimum:
- **1 positive test**: Should detect the issue
- **1 negative test**: Should not false-positive
- **Deterministic assertions**: No mocks of time/random

Example:
```python
def test_hallucination_positive():
    trace = create_trace_with_hallucination()
    score = detect_hallucination(trace)
    assert score > 0.7  # High risk detected

def test_hallucination_negative():
    trace = create_clean_trace()
    score = detect_hallucination(trace)
    assert score < 0.3  # Low risk, no false positive
```

---

## Development Guidelines

### When Implementing
1. Start simple, add complexity only when needed
2. Document WHY, not just WHAT
3. Prefer explicit over clever
4. Leave TODOs for unclear requirements

### When Uncertain
1. Ask via TODO comment in code
2. Choose simplest correct implementation
3. Favor false negatives over false positives (v1)
4. Do NOT invent requirements

### Code Quality
- Every function has type hints
- Every module has docstring
- Complex logic has inline comments
- No dead code or commented-out blocks

---

## Anti-Patterns (Never Do)

- ❌ Add web server or REST API
- ❌ Add dashboard or frontend
- ❌ Introduce config files without approval
- ❌ Use global state or singletons
- ❌ Make network calls in core logic
- ❌ Premature optimization
- ❌ Abstract patterns without clear wins

---

## Working with Claude Code

### Good Task Examples
- "Implement the hallucination signal"
- "Add tests for loop detection"
- "Create ExecutionTrace schema based on spec"
- "Fix scorer to use linear aggregation"

### Bad Task Examples
- "Make it better" (too vague)
- "Add AI to detect issues" (violates determinism)
- "Build a dashboard" (out of scope)

### When You Complete a Task
1. Ensure all tests pass
2. Verify type hints present
3. Check no forbidden patterns introduced
4. Leave code cleaner than you found it

---

## Context for Other Agents

RS-1 is foundational reliability infrastructure. Your code will be:
- Used by other agents in production
- Expected to be deterministic and bug-free
- Potentially rewritten in Go for performance
- Audited by human engineers

**Build for correctness and clarity, not cleverness.**

---

## Quick Reference

**Primary Goal**: Deterministic reliability evaluation  
**Primary Output**: JSON ReliabilityReport  
**Primary Constraint**: No external dependencies in core logic  
**Primary Rule**: Same input = same output, always