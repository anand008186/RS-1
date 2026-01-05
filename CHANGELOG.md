# Changelog

All notable changes to RS-1 (Reliability Sentinel) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-04

### Added
- Initial release of RS-1 Reliability Sentinel
- Core signal detection:
  - Hallucination risk detection
  - Loop/degeneracy detection
  - Tool misuse detection
  - Cost anomaly detection
- Scoring engine with weighted aggregation
- Policy layer with threshold-based verdicts (PASS/WARN/FAIL)
- CLI interface for trace evaluation
- Python API for programmatic use
- Comprehensive test suite (68 tests, 89% coverage)
- Structured JSON output format
- Full type hints throughout codebase
- Documentation (README, CONTRIBUTING, CLAUDE.md)

### Design Principles
- Stateless evaluation (no memory between runs)
- Deterministic (same input → same output)
- No external dependencies in core logic
- Portable architecture (can be rewritten in Go)

### Technical Details
- Language: Python 3.10+
- Test coverage: 89%
- Signals: 4 core signals
- Output: Structured JSON (machine-readable)
- Integration time: <10 minutes

