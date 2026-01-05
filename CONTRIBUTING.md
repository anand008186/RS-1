# Contributing to RS-1

Thank you for your interest in contributing to RS-1 (Reliability Sentinel)!

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/anand008186/RS-1.git
   cd RS-1
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run tests**
   ```bash
   pytest
   ```

## Contribution Guidelines

### Code Requirements

- ✅ **Type hints** on all functions
- ✅ **Docstrings** on all modules and functions
- ✅ **No external dependencies** in core logic (only standard library)
- ✅ **Deterministic** (no time, random, network calls)
- ✅ **Stateless** (no memory between evaluations)

### Testing Requirements

All contributions must include:

1. **Positive tests**: Should detect the issue
2. **Negative tests**: Should not false-positive
3. **Edge case tests**: Empty traces, boundary conditions

Run tests with:
```bash
pytest --cov=rs1 --cov-report=html
```

### Adding a New Signal

1. Create signal file in `rs1/signals/`
2. Implement function: `ExecutionTrace → float`
3. Add weight to `rs1/core/scorer.py`
4. Register in `rs1/core/evaluator.py`
5. Add tests in `rs1/tests/`

### Code Style

- Follow PEP 8
- Use type hints
- Write clear docstrings
- Keep functions focused and small
- Prefer explicit over clever

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Write tests first (TDD)
   - Ensure all tests pass
   - Update documentation if needed
4. **Commit your changes**
   ```bash
   git commit -m "Add: description of changes"
   ```
5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Open a Pull Request**

### Review Criteria

All PRs must:

- ✅ Pass all existing tests
- ✅ Include new tests for new features
- ✅ Maintain test coverage ≥85%
- ✅ Follow code style guidelines
- ✅ Update documentation if needed
- ✅ Not introduce new external dependencies (unless approved)

### Architecture Constraints

**Must Be:**
- Stateless: No memory between evaluations
- Deterministic: Same input → same output, always
- Explicit: No hidden state or side effects
- Portable: Can be rewritten in Go later

**Must Not Be:**
- A web service or API
- An async pipeline
- ML/learning-based
- Dependent on external services

## Questions?

For questions or clarifications:
- Open an issue with the `question` label
- Check existing issues and discussions
- Review the `CLAUDE.md` file for detailed architecture guidelines


