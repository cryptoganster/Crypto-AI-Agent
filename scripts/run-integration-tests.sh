#!/bin/bash
# Run integration tests for pre-push hook

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} Running integration tests..."

# Run pytest with integration marker
pytest tests/integration/ -v --tb=short -m integration

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}[PASS]${NC} All integration tests passed"
else
    echo -e "${RED}[FAIL]${NC} Integration tests failed"
fi

exit $EXIT_CODE
