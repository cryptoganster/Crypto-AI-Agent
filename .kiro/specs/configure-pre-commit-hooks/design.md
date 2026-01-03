# Design Document: Configure Pre-Commit Hooks

## Overview

Este documento describe el diseño para configurar pre-commit hooks en el proyecto, asegurando calidad de código consistente mediante validaciones automáticas antes de cada commit.

## Architecture

### High-Level Design

```
Developer Workflow:
┌─────────────────────────────────────────────────────────────┐
│  Developer makes changes                                     │
│  ↓                                                           │
│  git add <files>                                             │
│  ↓                                                           │
│  git commit -m "message"                                     │
│  ↓                                                           │
│  Pre-commit hooks execute automatically                      │
│  ├─ Black (format code)                                     │
│  ├─ isort (sort imports)                                    │
│  ├─ Flake8 (lint code)                                      │
│  ├─ MyPy (type check)                                       │
│  ├─ File validations (YAML, JSON, trailing whitespace)     │
│  └─ Security checks (detect secrets)                        │
│  ↓                                                           │
│  All hooks pass? → Commit succeeds                          │
│  Any hook fails? → Commit blocked, files auto-fixed        │
└─────────────────────────────────────────────────────────────┘
```

### Components

1. **`.pre-commit-config.yaml`**: Archivo de configuración principal
2. **Git hooks**: Scripts en `.git/hooks/` (gestionados por pre-commit)
3. **Tool configurations**: Configuraciones en `pyproject.toml`
4. **Documentation**: Instrucciones en README.md

## Configuration File Structure

### `.pre-commit-config.yaml`

```yaml
# Pre-commit configuration
# See https://pre-commit.com for more information

default_language_version:
  python: python3.11

repos:
  # Python code formatting
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11

  # Import sorting
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  # Python linting
  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [
          "--max-line-length=88",
          "--extend-ignore=E203,W503",
          "--exclude=.git,__pycache__,venv,.venv,build,dist"
        ]

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: ["--config-file=pyproject.toml"]
        exclude: ^tests/

  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      # Prevent large files
      - id: check-added-large-files
        args: ['--maxkb=500']
      
      # Check for merge conflicts
      - id: check-merge-conflict
      
      # Check YAML syntax
      - id: check-yaml
        exclude: ^\.kiro/
      
      # Check JSON syntax
      - id: check-json
      
      # Remove trailing whitespace
      - id: trailing-whitespace
        args: [--markdown-linebreak-ext=md]
      
      # Ensure files end with newline
      - id: end-of-file-fixer
      
      # Check for private keys
      - id: detect-private-key
      
      # Check Python syntax
      - id: check-ast
      
      # Check for debugger imports
      - id: debug-statements
      
      # Fix mixed line endings
      - id: mixed-line-ending
        args: ['--fix=lf']

  # Security - detect secrets
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package.lock.json

# Configuration for specific hooks
ci:
  autofix_commit_msg: |
    [pre-commit.ci] auto fixes from pre-commit hooks
    
    for more information, see https://pre-commit.ci
  autofix_prs: true
  autoupdate_branch: ''
  autoupdate_commit_msg: '[pre-commit.ci] pre-commit autoupdate'
  autoupdate_schedule: weekly
  skip: []
  submodules: false
```

## Tool Configurations

### Black Configuration (already in pyproject.toml)

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### isort Configuration (already in pyproject.toml)

```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["src"]
```

### Flake8 Configuration

Flake8 no soporta `pyproject.toml`, necesita `.flake8`:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    venv,
    .venv,
    build,
    dist,
    .eggs,
    *.egg-info
per-file-ignores =
    __init__.py:F401
```

### MyPy Configuration (already in pyproject.toml)

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
show_error_codes = true

[[tool.mypy.overrides]]
module = [
    "feedparser.*",
    "playwright.*",
    "trafilatura.*",
    "readability.*",
]
ignore_missing_imports = true
```

## Installation and Setup

### Step 1: Install Development Dependencies

```bash
# Install all dev dependencies including pre-commit
pip install -e ".[dev]"
```

### Step 2: Install Pre-commit Hooks

```bash
# Install git hooks
pre-commit install

# Install commit-msg hook (optional)
pre-commit install --hook-type commit-msg
```

### Step 3: Run Hooks Manually (Optional)

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Run on staged files only
pre-commit run
```

## Usage Patterns

### Normal Commit Flow

```bash
# Make changes
vim src/domain/aggregates/article.py

# Stage changes
git add src/domain/aggregates/article.py

# Commit (hooks run automatically)
git commit -m "feat(article): add new method"

# If hooks fail, they auto-fix files
# Review changes and commit again
git add src/domain/aggregates/article.py
git commit -m "feat(article): add new method"
```

### Bypass Hooks (Emergency Only)

```bash
# Skip hooks for urgent commits
git commit -m "hotfix: critical bug" --no-verify

# Remember to run hooks manually later
pre-commit run --all-files
```

### Update Hook Versions

```bash
# Update to latest versions
pre-commit autoupdate

# Review changes in .pre-commit-config.yaml
git diff .pre-commit-config.yaml

# Commit updates
git add .pre-commit-config.yaml
git commit -m "chore: update pre-commit hooks"
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Code Formatting Consistency

*For any* Python file in the repository, after running Black, the file should be formatted according to Black's rules and running Black again should produce no changes (idempotent).

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 2: Import Ordering Consistency

*For any* Python file with imports, after running isort, the imports should be ordered according to isort's rules and running isort again should produce no changes (idempotent).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 3: Linting Compliance

*For any* Python file that passes Flake8, the file should contain no linting errors according to the configured rules.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 4: Type Safety

*For any* Python file with type hints, MyPy should verify that all type annotations are correct and consistent.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

### Property 5: File Size Limit

*For any* file being committed, if the file size exceeds 500KB, the commit should be blocked.

**Validates: Requirements 6.1**

### Property 6: Merge Conflict Detection

*For any* file being committed, if the file contains unresolved merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`), the commit should be blocked.

**Validates: Requirements 6.2**

### Property 7: YAML Validity

*For any* YAML file being committed, the file should be valid YAML syntax.

**Validates: Requirements 6.3**

### Property 8: JSON Validity

*For any* JSON file being committed, the file should be valid JSON syntax.

**Validates: Requirements 6.4**

### Property 9: No Trailing Whitespace

*For any* file being committed, lines should not end with trailing whitespace (except in markdown where it's intentional).

**Validates: Requirements 6.5**

### Property 10: Secret Detection

*For any* file being committed, the file should not contain private keys, API tokens, or other secrets.

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 11: Hook Execution Performance

*For any* typical commit (modifying 1-5 files), all pre-commit hooks should complete execution in less than 10 seconds.

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 12: UTF-8 Encoding

*For any* Python file being committed, the file should be encoded in UTF-8.

**Validates: Requirements 12.1**

## Error Handling

### Common Errors and Solutions

#### Error: "pre-commit not found"

**Solution:**
```bash
# Activate virtualenv
source venv/bin/activate

# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

#### Error: "Black would reformat file"

**Solution:**
```bash
# Black auto-fixes files, just re-stage and commit
git add <file>
git commit -m "your message"
```

#### Error: "Flake8 found linting errors"

**Solution:**
```bash
# Fix errors manually or use autopep8
autopep8 --in-place --aggressive <file>

# Or review and fix manually
vim <file>

# Re-stage and commit
git add <file>
git commit -m "your message"
```

#### Error: "MyPy type checking failed"

**Solution:**
```bash
# Add type hints or fix type errors
vim <file>

# Or add type: ignore comment for specific lines
# my_var = some_function()  # type: ignore

# Re-stage and commit
git add <file>
git commit -m "your message"
```

#### Error: "Large file detected"

**Solution:**
```bash
# Remove large file or use Git LFS
git rm --cached <large-file>

# Or add to .gitignore
echo "<large-file>" >> .gitignore

# Commit without the large file
git commit -m "your message"
```

#### Error: "Secret detected"

**Solution:**
```bash
# Remove secret from file
vim <file>

# Or add to .secrets.baseline if false positive
detect-secrets scan --baseline .secrets.baseline

# Re-stage and commit
git add <file>
git commit -m "your message"
```

## Testing Strategy

### Manual Testing

1. **Test Black formatting:**
   ```bash
   # Create unformatted file
   echo "def foo( x,y ):return x+y" > test.py
   
   # Try to commit
   git add test.py
   git commit -m "test"
   
   # Verify Black reformats it
   cat test.py  # Should be formatted
   ```

2. **Test isort:**
   ```bash
   # Create file with unsorted imports
   cat > test.py << EOF
   import sys
   import os
   from typing import List
   import asyncio
   EOF
   
   # Try to commit
   git add test.py
   git commit -m "test"
   
   # Verify imports are sorted
   cat test.py
   ```

3. **Test Flake8:**
   ```bash
   # Create file with linting errors
   echo "x=1+2" > test.py
   
   # Try to commit
   git add test.py
   git commit -m "test"
   
   # Should fail with linting errors
   ```

4. **Test large file detection:**
   ```bash
   # Create large file
   dd if=/dev/zero of=large.bin bs=1024 count=600
   
   # Try to commit
   git add large.bin
   git commit -m "test"
   
   # Should fail with size error
   ```

### Automated Testing

Pre-commit hooks themselves are tested by:
1. Running on all files: `pre-commit run --all-files`
2. CI/CD integration (runs same hooks)
3. Regular updates: `pre-commit autoupdate`

## Documentation Updates

### README.md Section

Add this section to README.md:

```markdown
## Development Setup

### Prerequisites

- Python 3.11+
- Git 2.x

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/cryptoganster/Crypto-AI-Agent.git
   cd scraping-service
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   # Install all dependencies including dev tools
   pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. (Optional) Run hooks on all files:
   ```bash
   pre-commit run --all-files
   ```

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. The following checks run automatically before each commit:

- **Black**: Code formatting (auto-fixes)
- **isort**: Import sorting (auto-fixes)
- **Flake8**: Linting (manual fixes required)
- **MyPy**: Type checking (manual fixes required)
- **File validations**: YAML, JSON, trailing whitespace (auto-fixes)
- **Security**: Secret detection (manual fixes required)

#### Running Hooks Manually

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Run on staged files only
pre-commit run
```

#### Bypassing Hooks (Emergency Only)

```bash
# Skip hooks for urgent commits
git commit -m "hotfix: critical bug" --no-verify

# Remember to run hooks manually later
pre-commit run --all-files
```

#### Updating Hooks

```bash
# Update to latest versions
pre-commit autoupdate

# Commit the updates
git add .pre-commit-config.yaml
git commit -m "chore: update pre-commit hooks"
```

### Common Issues

**Issue: "pre-commit not found"**
- Solution: Activate your virtualenv: `source venv/bin/activate`

**Issue: "Black would reformat file"**
- Solution: Black auto-fixes files. Just re-stage and commit.

**Issue: "Flake8 linting errors"**
- Solution: Fix errors manually or use `autopep8 --in-place <file>`

**Issue: "MyPy type errors"**
- Solution: Add type hints or use `# type: ignore` for specific lines

**Issue: "Large file detected"**
- Solution: Remove file or use Git LFS for large files

**Issue: "Secret detected"**
- Solution: Remove secret or add to `.secrets.baseline` if false positive
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Pre-commit Checks

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pre-commit
          pip install -e ".[dev]"
      
      - name: Run pre-commit
        run: pre-commit run --all-files
```

## Performance Optimizations

1. **Caching**: Pre-commit caches tool installations in `~/.cache/pre-commit`
2. **Staged files only**: Hooks run only on staged files by default
3. **Parallel execution**: Some hooks can run in parallel
4. **Skip slow hooks**: MyPy can be skipped for quick commits with `SKIP=mypy git commit`

## Security Considerations

1. **Secret detection**: Prevents accidental commit of credentials
2. **Private key detection**: Blocks commits with private keys
3. **Baseline file**: `.secrets.baseline` tracks known false positives
4. **Regular updates**: Keep hooks updated for latest security checks

## Maintenance

### Regular Tasks

1. **Update hooks monthly**:
   ```bash
   pre-commit autoupdate
   ```

2. **Review and update baseline**:
   ```bash
   detect-secrets scan --baseline .secrets.baseline
   ```

3. **Clean cache periodically**:
   ```bash
   pre-commit clean
   pre-commit gc
   ```

## Benefits

1. ✅ **Consistent code style**: All code follows same formatting rules
2. ✅ **Early error detection**: Catch issues before they reach CI/CD
3. ✅ **Automated fixes**: Many issues auto-fixed (Black, isort, trailing whitespace)
4. ✅ **Security**: Prevent accidental secret commits
5. ✅ **Fast feedback**: Developers get immediate feedback
6. ✅ **Reduced CI failures**: Fewer failures in CI/CD pipeline
7. ✅ **Better code quality**: Enforces best practices automatically

## Limitations

1. ❌ **Not a replacement for tests**: Hooks don't run tests (too slow)
2. ❌ **Can be bypassed**: Developers can use `--no-verify`
3. ❌ **Requires discipline**: Team must install and maintain hooks
4. ❌ **Initial setup time**: First run downloads all tools
5. ❌ **May slow commits**: Adds 5-10 seconds to commit time

## References

- Pre-commit documentation: https://pre-commit.com
- Black documentation: https://black.readthedocs.io
- isort documentation: https://pycqa.github.io/isort/
- Flake8 documentation: https://flake8.pycqa.org
- MyPy documentation: https://mypy.readthedocs.io
- detect-secrets: https://github.com/Yelp/detect-secrets
