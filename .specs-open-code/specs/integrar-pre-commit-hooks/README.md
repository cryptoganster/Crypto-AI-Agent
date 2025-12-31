# Pre-commit Git Hooks Integration

## Overview

This project uses **pre-commit** to automatically run code quality checks and tests before every commit and push. This ensures that all code meets the project's standards before being versioned.

## Hooks Configuration

### Pre-commit Hooks (Run on `git commit`)

| Hook | Purpose | Execution Time |
|------|---------|----------------|
| **mypy** | Static type checking | ~2-5s |
| **black** | Code formatting | ~1-2s |
| **isort** | Import sorting | ~1s |
| **flake8** | Style guide enforcement | ~1-2s |
| **unit-tests** | Run unit tests | ~5-10s |

### Pre-push Hooks (Run on `git push`)

| Hook | Purpose | Execution Time |
|------|---------|----------------|
| **integration-tests** | Run integration tests | ~1-2 minutes |

## Quick Start

### Initial Setup

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Initialize hooks (runs automatically on first clone)
pre-commit install
pre-commit install --hook-type pre-push
```

### Daily Development Workflow

```bash
# 1. Stage your changes
git add .

# 2. Commit (hooks run automatically)
git commit -m "Your commit message"

# 3. Push (integration tests run automatically)
git push origin main
```

## Skipping Hooks

In rare cases, you may need to bypass hooks (e.g., emergency fixes):

```bash
# Skip pre-commit hooks
git commit --no-verify -m "Emergency fix"

# Skip pre-push hooks
git push --no-verify origin main
```

> **Warning**: Use `--no-verify` sparingly. Hooks exist to maintain code quality.

## Troubleshooting

### Hooks Not Running

If hooks don't run:

```bash
# Reinstall hooks
pre-commit clean
pre-commit install
pre-commit install --hook-type pre-push
```

### Pre-existing Test Failures

Some unit tests may fail due to environment issues (e.g., pydantic architecture incompatibility between arm64 and x86_64). These are **not** caused by the hooks implementation.

### Slow Hook Execution

First run may be slow as pre-commit downloads environments. Subsequent runs use cached environments.

### Hook Fails with Import Error

Ensure you're in the correct Python environment:
```bash
source venv/bin/activate  # or your virtualenv
pip install -e ".[dev]"
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.pre-commit-config.yaml` | Hook definitions and settings |
| `scripts/run-unit-tests.sh` | Unit test execution script |
| `scripts/run-integration-tests.sh` | Integration test execution script |

## Best Practices

1. **Don't skip hooks** unless absolutely necessary
2. **Fix issues early** - hooks catch problems before they enter the codebase
3. **Run hooks manually** to check before committing:
   ```bash
   pre-commit run --all-files
   ```

## Support

If you encounter issues:
1. Check the error message from the hook
2. Review the troubleshooting section above
3. Ensure dependencies are installed: `pip install -e ".[dev]"`
