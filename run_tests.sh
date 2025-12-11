#!/bin/bash

# Script to run all backend service tests
# Usage: ./run_tests.sh [options]
#   -v, --verbose    : Verbose output
#   -c, --coverage   : Generate coverage report
#   -h, --html       : Generate HTML coverage report
#   -s, --service    : Run tests for specific service only

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default options
VERBOSE=""
COVERAGE=""
HTML_REPORT=""
SERVICE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=backend/services --cov-report=term"
            shift
            ;;
        -h|--html)
            COVERAGE="--cov=backend/services --cov-report=html"
            HTML_REPORT="true"
            shift
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./run_tests.sh [-v|--verbose] [-c|--coverage] [-h|--html] [-s|--service SERVICE_NAME]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Internet of Emotions - Test Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# List of all services in logical testing order:
# 1. Infrastructure/Support Services (cache, cleanup)
# 2. Data Collection Services (post_fetcher, url_extractor)
# 3. Core Analysis Services (ml_analyzer, collective_analyzer, cross_country_detector)
# 4. Aggregation Services (country_aggregation)
# 5. Query/Stats Services (scheduler, search_service, stats_service)
# 6. API Gateway (entry point - tested last)
SERVICES=(
    "cache_service"         # 1. Infrastructure - caching layer
    "db_cleanup"            # 2. Infrastructure - database maintenance
    "post_fetcher"          # 3. Data Collection - Reddit posts
    "url_extractor"         # 4. Data Collection - URL content extraction
    "ml_analyzer"           # 5. Core Analysis - emotion detection (4 models)
    "collective_analyzer"   # 6. Core Analysis - collective vs personal
    "cross_country_detector" # 7. Core Analysis - cross-country detection
    "country_aggregation"   # 8. Aggregation - country-level consensus
    "scheduler"             # 9. Scheduling - smart prioritization
    "search_service"        # 10. Query - full-text search
    "stats_service"         # 11. Query - statistics & streaming
    "api_gateway"           # 12. Gateway - entry point (depends on all)
)

# If specific service requested
if [ -n "$SERVICE" ]; then
    echo -e "${GREEN}Running tests for: $SERVICE${NC}"
    echo ""
    cd "backend/services/$SERVICE"
    pytest test_app.py $VERBOSE $COVERAGE
    cd ../../..
    
    if [ -n "$HTML_REPORT" ]; then
        echo ""
        echo -e "${GREEN}Coverage report generated at: backend/services/$SERVICE/htmlcov/index.html${NC}"
    fi
    exit 0
fi

# Run tests for all services
echo -e "${GREEN}Running tests for all services...${NC}"
echo ""

FAILED_SERVICES=()
PASSED_SERVICES=()

for service in "${SERVICES[@]}"; do
    echo -e "${BLUE}Testing: $service${NC}"
    
    if cd "backend/services/$service" 2>/dev/null; then
        if pytest test_app.py $VERBOSE 2>&1 | tee test_output.log; then
            PASSED_SERVICES+=("$service")
            echo -e "${GREEN}✓ $service: PASSED${NC}"
        else
            FAILED_SERVICES+=("$service")
            echo -e "${RED}✗ $service: FAILED${NC}"
        fi
        rm -f test_output.log
        cd ../../..
    else
        echo -e "${RED}✗ $service: NOT FOUND${NC}"
        FAILED_SERVICES+=("$service")
    fi
    echo ""
done

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Total Services: ${#SERVICES[@]}"
echo -e "${GREEN}Passed: ${#PASSED_SERVICES[@]}${NC}"
echo -e "${RED}Failed: ${#FAILED_SERVICES[@]}${NC}"
echo ""

if [ ${#PASSED_SERVICES[@]} -gt 0 ]; then
    echo -e "${GREEN}Passed Services:${NC}"
    for service in "${PASSED_SERVICES[@]}"; do
        echo -e "  ✓ $service"
    done
    echo ""
fi

if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
    echo -e "${RED}Failed Services:${NC}"
    for service in "${FAILED_SERVICES[@]}"; do
        echo -e "  ✗ $service"
    done
    echo ""
    exit 1
fi

echo -e "${GREEN}All tests passed!${NC}"

# Run coverage for all services if requested
if [ -n "$COVERAGE" ]; then
    echo ""
    echo -e "${BLUE}Generating overall coverage report...${NC}"
    pytest backend/services/*/test_app.py $COVERAGE
    
    if [ -n "$HTML_REPORT" ]; then
        echo ""
        echo -e "${GREEN}HTML coverage report generated at: htmlcov/index.html${NC}"
        echo -e "${GREEN}Open with: open htmlcov/index.html${NC}"
    fi
fi
