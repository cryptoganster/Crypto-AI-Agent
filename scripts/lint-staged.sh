#!/bin/bash
# Linting script for pre-commit hook
# Runs mypy, black, isort, and flake8 on staged Python files

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Get list of staged Python files
get_staged_files() {
    git diff --cached --name-only --diff-filter=d | grep -E '\.pyi?$' || true
}

# Main execution
main() {
    log_section "Running Linting Checks"

    # Get staged Python files
    STAGED_FILES=$(get_staged_files)

    if [ -z "$STAGED_FILES" ]; then
        log_info "No Python files staged for commit. Skipping linting."
        exit 0
    fi

    # Convert to array
    readarray -t FILE_ARRAY <<< "$STAGED_FILES"
    FILE_COUNT=${#FILE_ARRAY[@]}

    log_info "Found $FILE_COUNT Python file(s) to check"

    # Track overall status
    LINTING_FAILED=0

    # Run mypy
    log_section "Running mypy type checking..."
    if command -v mypy &> /dev/null; then
        if mypy "${FILE_ARRAY[@]}" 2>&1; then
            log_info "mypy: PASSED"
        else
            log_error "mypy: FAILED"
            LINTING_FAILED=1
        fi
    else
        log_warn "mypy not found. Skipping."
    fi

    # Run black
    log_section "Running black formatting check..."
    if command -v black &> /dev/null; then
        if black --check "${FILE_ARRAY[@]}" 2>&1; then
            log_info "black: PASSED"
        else
            log_error "black: FAILED"
            log_info "Run 'black ${FILE_ARRAY[@]}' to auto-format"
            LINTING_FAILED=1
        fi
    else
        log_warn "black not found. Skipping."
    fi

    # Run isort
    log_section "Running isort import order check..."
    if command -v isort &> /dev/null; then
        if isort --check-only "${FILE_ARRAY[@]}" 2>&1; then
            log_info "isort: PASSED"
        else
            log_error "isort: FAILED"
            log_info "Run 'isort ${FILE_ARRAY[@]}' to auto-fix"
            LINTING_FAILED=1
        fi
    else
        log_warn "isort not found. Skipping."
    fi

    # Run flake8
    log_section "Running flake8 style check..."
    if command -v flake8 &> /dev/null; then
        if flake8 "${FILE_ARRAY[@]}" 2>&1; then
            log_info "flake8: PASSED"
        else
            log_error "flake8: FAILED"
            LINTING_FAILED=1
        fi
    else
        log_warn "flake8 not found. Skipping."
    fi

    # Final result
    log_section "Linting Results"
    if [ $LINTING_FAILED -eq 1 ]; then
        log_error "Linting failed! Please fix the errors above before committing."
        exit 1
    else
        log_info "All linting checks passed!"
        exit 0
    fi
}

main "$@"
