# pre-commit Git Hooks Integration Requirements

**Specification Version:** 1.0.0  
**Created:** 2025-12-30  
**Author:** Sisyphus AI Agent  
**Status:** Pivoted from Husky  
**Priority:** Must-Have  
**Last Updated:** 2025-12-30

> **NOTE:** This specification was pivoted from Husky (Node.js-based) to pre-commit (Python-native) because this is a pure Python project. See Session Summary ses_48f1.md for details.

---

## 1. Overview

### 1.1 Purpose
Implement Git hooks (pre-commit and pre-push) using pre-commit to enforce code quality checks, linting, and testing before commits and pushes. This ensures that no substandard code enters the repository and maintains consistent code quality across the codebase.

### 1.2 Scope
**In Scope:**
- Pre-commit hook for running linters (mypy, black, flake8)
- Pre-commit hook for running unit tests
- Pre-push hook for running integration tests
- pre-commit configuration and initialization
- Documentation for developers

**Out of Scope:**
- Post-commit or post-merge hooks
- CI/CD pipeline configuration (separate spec)
- Commit message validation (may be added later)

### 1.3 Definitions
| Term | Definition |
|------|------------|
| pre-commit | Git hooks framework that enables running scripts before commits/pushes |
| Pre-commit hook | Git hook that runs before a commit is created |
| Pre-push hook | Git hook that runs before changes are pushed to remote |
| Linting | Automated checking of source code for programmatic and stylistic errors |

### 1.4 References
- [pre-commit Documentation](https://pre-commit.com/)
- [Git Hooks Documentation](https://git-scm.com/docs/githooks)
- Project linting configuration in `pyproject.toml`

---

## 2. User Stories

| ID | User Story | Priority | Estimated Effort |
|----|------------|----------|------------------|
| US-001 | AS A developer I WANT TO run linting automatically before commits SO THAT I catch code quality issues early | Must-Have | 2 hours |
| US-002 | AS A developer I WANT TO run tests automatically before commits SO THAT I prevent breaking changes | Must-Have | 2 hours |
| US-003 | AS A developer I WANT TO run comprehensive tests before pushes SO THAT I ensure the codebase is stable before sharing | Must-Have | 2 hours |
| US-004 | AS A developer I WANT TO be able to skip hooks when necessary SO THAT I can make urgent fixes | Should-Have | 1 hour |

---

## 3. Functional Requirements

### 3.1 Core Requirements

#### REQ-001: Pre-commit Linting
**Priority:** Must-Have | **Risk:** Low

**Statement:**
```
WHEN a developer commits changes THE SYSTEM SHALL run mypy, black, and flake8 checks
```

**Rationale:**
Linting ensures code quality and consistency. Running these checks before commit prevents bad code from entering the repository.

**Acceptance Criteria:**
- [ ] mypy type checking runs on modified Python files
- [ ] black formatting check runs on modified Python files
- [ ] flake8 style check runs on modified Python files
- [ ] Commit is aborted if any check fails
- [ ] Error messages are clear and actionable
- [ ] Checks run only on staged files

**Dependencies:**
- None

---

#### REQ-002: Pre-commit Unit Tests
**Priority:** Must-Have | **Risk:** Medium

**Statement:**
```
WHEN a developer commits changes THE SYSTEM SHALL run unit tests on modified code
```

**Rationale:**
Running unit tests before commit catches regressions early and ensures that the changes don't break existing functionality.

**Acceptance Criteria:**
- [ ] Unit tests run on modified files and their dependencies
- [ ] Tests fail if any assertion fails
- [ ] Commit is aborted if tests fail
- [ ] Coverage report generated (optional, for information only)
- [ ] Test output shows clear pass/fail status

**Dependencies:**
- REQ-001 (linting must pass before tests run)

---

#### REQ-003: Pre-push Integration Tests
**Priority:** Must-Have | **Risk:** Medium

**Statement:**
```
WHEN a developer pushes changes THE SYSTEM SHALL run integration tests
```

**Rationale:**
Integration tests verify that the codebase works as a whole. Running them before push ensures that the remote repository always has stable code.

**Acceptance Criteria:**
- [ ] Integration tests run on the entire codebase
- [ ] Push is aborted if any integration test fails
- [ ] Test output shows clear pass/fail status
- [ ] Integration tests use the test database configuration

**Dependencies:**
- None

---

#### REQ-004: Hook Skipping Capability
**Priority:** Should-Have | **Risk:** Low

**Statement:**
```
WHERE a developer needs to skip hooks THE SYSTEM SHALL allow skipping with --no-verify flag
```

**Rationale:**
Sometimes developers need to make urgent fixes without running all checks.

**Acceptance Criteria:**
- [ ] `git commit --no-verify` skips pre-commit hooks
- [ ] `git push --no-verify` skips pre-push hooks
- [ ] Warning message displayed when skipping hooks
- [ ] Skipping is logged for audit purposes (optional)

**Dependencies:**
- None

---

#### REQ-005: pre-commit Initialization
**Priority:** Must-Have | **Risk:** Low

**Statement:**
```
WHEN the project is set up THE SYSTEM SHALL initialize pre-commit with proper configuration
```

**Rationale:**
Proper initialization ensures that Git hooks are created and managed correctly.

**Acceptance Criteria:**
- [ ] pre-commit is installed as a dev dependency
- [ ] `.pre-commit-config.yaml` is created with proper structure
- [ ] Git hooks are installed in `.git/hooks/`
- [ ] Configuration is committed to the repository

**Dependencies:**
- None

---

### 3.2 Performance Requirements

| ID | Requirement | Target | Measurement Method |
|----|-------------|--------|-------------------|
| NFR-PERF-001 | Pre-commit hook execution time | ≤ 30 seconds | Timer measurement |
| NFR-PERF-002 | Pre-push hook execution time | ≤ 5 minutes | Timer measurement |
| NFR-PERF-003 | Linting only on staged files | < 10 files/second | File processing rate |

### 3.3 Security Requirements

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR-SEC-001 | Hook scripts are executable | Unix file permissions (755) |
| NFR-SEC-002 | No sensitive data in logs | Filter environment variables |

---

## 4. Constraints & Assumptions

### 4.1 Constraints
| ID | Constraint | Impact |
|----|------------|--------|
| C-001 | Must use pip for pre-commit | Installation and scripts must use pip |
| C-002 | Must work on macOS and Linux | Scripts must be cross-platform compatible |
| C-003 | Must not block emergency fixes | --no-verify flag must work |

### 4.2 Assumptions
| ID | Assumption | Risk if Incorrect |
|----|------------|-------------------|
| A-001 | Python 3.11+ is installed | Cannot use pre-commit without Python |
| A-002 | pip is available | Installation requires pip |
| A-003 | Developer has commit access | Hooks only run on local development |

---

## 5. Dependencies

### 5.1 External Dependencies
| Dependency | Version | Purpose | Status |
|------------|---------|---------|--------|
| pre-commit | ^4.5.0 | Git hooks framework (Python native) | Ready |
| Python | >= 3.11 | Runtime for pre-commit and tools | Ready |
| pip | Latest | Package manager for pre-commit | Ready |
| mypy | Latest | Type checking | Ready |
| black | Latest | Code formatting | Ready |
| flake8 | Latest | Linting | Ready |
| pytest | Latest | Testing | Ready |

### 5.2 Internal Dependencies
| Depends On | Blocks | Status |
|------------|--------|--------|
| None | This feature | Ready |

---

## 6. Acceptance Criteria Summary

| ID | Requirement | Test Approach |
|----|-------------|---------------|
| REQ-001 | Pre-commit linting | Manual verification of hook execution |
| REQ-002 | Pre-commit unit tests | Manual verification of test execution |
| REQ-003 | Pre-push integration tests | Manual verification of test execution |
| REQ-004 | Hook skipping | Manual verification of --no-verify flag |
| REQ-005 | pre-commit initialization | Manual verification of configuration |

---

## 7. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.1.0 | 2025-12-30 | Sisyphus | Pivoted from Husky to pre-commit (Python native). Updated constraints and dependencies. |
| 1.0.0 | 2025-12-30 | Sisyphus | Initial requirements document |

---

## Appendix A: EARS Notation Quick Reference

### Basic Syntax
```
WHEN [condition] THE SYSTEM SHALL [behavior]
WHILE [state] THE SYSTEM SHALL [behavior]
THE SYSTEM SHALL [behavior]
WHERE [feature] THE SYSTEM SHALL [behavior]
THE SYSTEM SHALL NOT [behavior]
```

### Keywords (Required)
- **WHEN** - Event trigger
- **WHILE** - State condition
- **WHERE** - Feature condition
- **SHALL** - Mandatory behavior (never use "should" or "may")
- **NOT** - Prohibition

---

## Appendix B: Requirement Quality Checklist

- [x] Each requirement has a unique ID
- [x] Requirements use "SHALL" not "should" or "may"
- [x] Requirements are testable and measurable
- [x] Requirements are unambiguous
- [x] Requirements have clear acceptance criteria
- [x] Dependencies between requirements are documented
- [x] Requirements have defined priority and risk
