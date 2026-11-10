#!/bin/bash
set -euo pipefail

TIMEOUT=${EXECUTION_TIMEOUT:-300}
MEMORY_LIMIT=${MEMORY_LIMIT:-512m}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

cleanup() {
    log "Cleaning up workspace..."
    rm -rf /app/workspace/* 2>/dev/null || true
}

trap cleanup EXIT

validate_input() {
    if [[ -z "${TASK_ID:-}" ]]; then
        log "Warning: TASK_ID not set"
    fi
    
    if [[ -z "${CODE_PATH:-}" ]] && [[ -z "${1:-}" ]]; then
        log "No code path or command specified"
        exit 1
    fi
}

run_syntax_check() {
    local file_path="$1"
    local extension="${file_path##*.}"
    
    log "Running syntax check for: $file_path"
    
    case "$extension" in
        py)
            python -m py_compile "$file_path"
            flake8 --max-line-length=120 "$file_path" || true
            ;;
        js|ts)
            eslint "$file_path" || true
            ;;
        *)
            log "No syntax checker for extension: $extension"
            ;;
    esac
}

run_security_scan() {
    local file_path="$1"
    local extension="${file_path##*.}"
    
    log "Running security scan for: $file_path"
    
    case "$extension" in
        py)
            bandit -r "$file_path" -f json || true
            ;;
        *)
            log "No security scanner for extension: $extension"
            ;;
    esac
}

run_tests() {
    local test_path="${1:-.}"
    
    log "Running tests in: $test_path"
    
    if [[ -f "pytest.ini" ]] || [[ -f "setup.py" ]] || [[ -f "pyproject.toml" ]]; then
        timeout "$TIMEOUT" pytest "$test_path" \
            --tb=short \
            --cov=. \
            --cov-report=json \
            --cov-report=term \
            -v || true
    elif [[ -f "package.json" ]]; then
        timeout "$TIMEOUT" npm test || true
    else
        log "No test framework detected"
    fi
}

execute_command() {
    local cmd="$*"
    log "Executing command: $cmd"
    timeout "$TIMEOUT" bash -c "$cmd"
}

main() {
    log "Sandbox starting in ${SANDBOX_MODE:-development} mode"
    log "Timeout: ${TIMEOUT}s, Memory limit: ${MEMORY_LIMIT}"
    
    validate_input "$@"
    
    case "${ACTION:-execute}" in
        syntax)
            run_syntax_check "${CODE_PATH:-$1}"
            ;;
        security)
            run_security_scan "${CODE_PATH:-$1}"
            ;;
        test)
            run_tests "${TEST_PATH:-.}"
            ;;
        full)
            run_syntax_check "${CODE_PATH:-$1}"
            run_security_scan "${CODE_PATH:-$1}"
            run_tests "${TEST_PATH:-.}"
            ;;
        execute)
            execute_command "$@"
            ;;
        *)
            log "Unknown action: ${ACTION}"
            exit 1
            ;;
    esac
    
    log "Sandbox execution completed"
}

main "$@"
