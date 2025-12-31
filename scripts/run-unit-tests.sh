#!/bin/bash
# Unit test script for pre-commit hook
# Runs pytest on tests/unit/ directory

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

# Timeout in seconds
TIMEOUT=20

# Main execution
main() {
    log_section "Running Unit Tests"

    if ! command -v pytest &> /dev/null; then
        log_warn "pytest not found. Skipping unit tests."
        exit 0
    fi

    # Check if unit tests directory exists
    if [ ! -d "tests/unit" ]; then
        log_info "No unit tests directory found. Skipping."
        exit 0
    fi

    log_info "Running unit tests with timeout of ${TIMEOUT}s..."

    # Run pytest with timeout (portable across Linux and macOS)
    if command -v timeout &> /dev/null; then
        # Linux/Unix with timeout command
        PYTEST_CMD="timeout $TIMEOUT pytest tests/unit/ -v --tb=short -m unit"
    else
        # macOS without timeout command - use Python signal or run without timeout
        log_warn "timeout command not available, running without timeout limit"
        PYTEST_CMD="pytest tests/unit/ -v --tb=short -m unit"
    fi

    # Run pytest
    if bash -c "$PYTEST_CMD" 2>&1; then
        log_section "Unit Tests Results"
        log_info "All unit tests passed!"
        exit 0
    else
        EXIT_CODE=$?
        log_section "Unit Tests Results"
        log_error "Unit tests failed!"
        if [ $EXIT_CODE -eq 124 ]; then
            log_error "Tests timed out after ${TIMEOUT} seconds"
        fi
        exit 1
    fi
}

main "$@"
