# Property-Based Tests

**Parent:** `../../AGENTS.md`

## OVERVIEW

49 Hypothesis-based tests validating domain invariants, value objects, aggregates.

## WHERE TO LOOK

| Test Type | Location | Notes |
|-----------|----------|-------|
| Article tests | `test_article_*.py` | Invariants, factories |
| Value objects | `test_*_vo_properties.py` | Type safety |
| Services | `test_*_service_properties.py` | Business logic |
| Events | `test_*_event*.py` | Event sourcing |

## CONVENTIONS

- **Strategies**: Use `conftest.py` fixtures for domain object generation
- **Settings**: `@settings(max_examples=100)` for coverage
- **Language**: Tests in Spanish
