#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Exit codes
BACKEND_EXIT_CODE=0
FRONTEND_EXIT_CODE=0

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}   Running All Tests with Coverage${NC}"
echo -e "${BLUE}=================================${NC}\n"

# ========================================
# Backend Tests (Python)
# ========================================
echo -e "${YELLOW}>>> Running Backend Tests (Python/pytest)${NC}\n"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}Error: Backend directory not found at $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR" || exit 1

# Prefer python3.12 for the virtual environment if available. If an existing venv
# is present but not using Python 3.12, recreate it with python3.12 (or fallback
# to python3 when 3.12 isn't installed).
if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN=python3.12
else
    PYTHON_BIN=python3
fi

# Create or recreate venv to ensure it uses Python 3.12 when possible
if [ -d "venv" ]; then
    VENV_PY="$(pwd)/venv/bin/python"
    if [ -x "$VENV_PY" ]; then
        VENV_VER=$($VENV_PY -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "")
        if [ "$VENV_VER" != "3.12" ]; then
            echo -e "${YELLOW}Existing virtualenv uses Python $VENV_VER, recreating with $PYTHON_BIN...${NC}"
            rm -rf venv
            $PYTHON_BIN -m venv venv
            echo -e "${GREEN}Virtual environment (created with $PYTHON_BIN).${NC}\n"
        else
            echo -e "${GREEN}Virtual environment already uses Python 3.12.${NC}\n"
        fi
    else
        echo -e "${YELLOW}venv directory exists but no python binary found inside; recreating with $PYTHON_BIN...${NC}"
        rm -rf venv
        $PYTHON_BIN -m venv venv
        echo -e "${GREEN}Virtual environment created.${NC}\n"
    fi
else
    echo -e "${YELLOW}Virtual environment not found. Creating one with $PYTHON_BIN...${NC}"
    $PYTHON_BIN -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}\n"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if dependencies are installed
## If pytest or core backend deps (fastapi) are missing, install dependencies.
if ! python -c "import pytest, fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies (attempt full requirements)...${NC}"
    # Try full install first (may fail when compiling heavy packages like pandas)
    if pip install -q -r requirements.txt; then
        echo -e "${GREEN}Dependencies installed.${NC}\n"
    else
        echo -e "${YELLOW}Full install failed, attempting install without pandas...${NC}"
        # Try installing everything except pandas (pandas often requires heavy compilation)
        TMP_REQ=$(mktemp)
        grep -iEv '^\s*pandas\b' requirements.txt > "$TMP_REQ"
        if pip install -q -r "$TMP_REQ"; then
            echo -e "${GREEN}Dependencies installed (excluding pandas).${NC}\n"
        else
            echo -e "${YELLOW}Install without pandas also failed, installing only minimal test dependencies...${NC}"
            # Install minimal test deps so pytest can run without building C-extensions
            if pip install -q pytest pytest-asyncio pytest-cov httpx requests; then
                echo -e "${GREEN}Test dependencies installed.${NC}\n"
            else
                echo -e "${RED}Failed to install test dependencies. Backend tests cannot run.${NC}\n"
                BACKEND_EXIT_CODE=127
                # Skip trying to run pytest below
            fi
        fi
        rm -f "$TMP_REQ"
    fi
fi

# Run pytest with coverage
echo -e "${BLUE}Running backend tests...${NC}\n"
pytest
BACKEND_EXIT_CODE=$?

# Deactivate virtual environment
deactivate

if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ Backend tests passed!${NC}\n"
else
    echo -e "\n${RED}✗ Backend tests failed!${NC}\n"
fi

# ========================================
# Frontend Tests (JavaScript/Vitest)
# ========================================
echo -e "${YELLOW}>>> Running Frontend Tests (JavaScript/Vitest)${NC}\n"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}Error: Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

cd "$FRONTEND_DIR" || exit 1

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Node modules not found. Installing...${NC}"
    npm install
    echo -e "${GREEN}Node modules installed.${NC}\n"
fi

# Run vitest with coverage
echo -e "${BLUE}Running frontend tests...${NC}\n"
npm run test:coverage -- --run
FRONTEND_EXIT_CODE=$?

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ Frontend tests passed!${NC}\n"
else
    echo -e "\n${RED}✗ Frontend tests failed!${NC}\n"
fi

# ========================================
# Summary
# ========================================
cd "$SCRIPT_DIR" || exit 1

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}   Test Summary${NC}"
echo -e "${BLUE}=================================${NC}\n"

if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Backend Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Backend Tests: FAILED (exit code: $BACKEND_EXIT_CODE)${NC}"
fi

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Frontend Tests: FAILED (exit code: $FRONTEND_EXIT_CODE)${NC}"
fi

echo -e "\n${BLUE}=================================${NC}"
echo -e "${BLUE}   Coverage Reports${NC}"
echo -e "${BLUE}=================================${NC}\n"

echo -e "${YELLOW}Backend Coverage Report:${NC}"
echo -e "  HTML: ${BLUE}$BACKEND_DIR/htmlcov/index.html${NC}"

echo -e "\n${YELLOW}Frontend Coverage Report:${NC}"
echo -e "  HTML: ${BLUE}$FRONTEND_DIR/coverage/index.html${NC}"

# Overall exit code
if [ $BACKEND_EXIT_CODE -eq 0 ] && [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}=================================${NC}"
    echo -e "${GREEN}   All Tests Passed! ✓${NC}"
    echo -e "${GREEN}=================================${NC}\n"
    exit 0
else
    echo -e "\n${RED}=================================${NC}"
    echo -e "${RED}   Some Tests Failed! ✗${NC}"
    echo -e "${RED}=================================${NC}\n"
    exit 1
fi
