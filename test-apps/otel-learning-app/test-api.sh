#!/bin/bash

# OTEL Learning App - Quick Test Script
# Run this to quickly test all the endpoints and generate traces

echo "🚀 Starting OTEL Learning App Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

# Function to print section
print_section() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo "Command: $method $endpoint"
    
    if [ -z "$data" ]; then
        curl -s -X $method "$BASE_URL$endpoint" | jq .
    else
        curl -s -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" | jq .
    fi
    
    echo ""
}

# ============================================================================
# AUTO-INSTRUMENTED TRACES
# ============================================================================

print_section "AUTO-INSTRUMENTED ENDPOINTS (FastAPI Middleware)"

test_endpoint "GET" "/health" "" "1. Health Check"

test_endpoint "GET" "/products" "" "2. List Products"

test_endpoint "GET" "/products/1" "" "3. Get Product by ID"

test_endpoint "GET" "/metrics" "" "4. Application Metrics"

# ============================================================================
# MANUAL-INSTRUMENTED TRACES
# ============================================================================

print_section "MANUAL-INSTRUMENTED ENDPOINTS (Explicit Spans)"

# Create an order
ORDER_DATA='{
  "customer_email": "john@example.com",
  "items": [
    {"product_id": 1, "quantity": 1},
    {"product_id": 2, "quantity": 2}
  ]
}'

echo -e "${YELLOW}Testing: 5. Create Order (Manual Instrumentation)${NC}"
echo "Command: POST /orders"
ORDER_RESPONSE=$(curl -s -X POST "$BASE_URL/orders" \
  -H "Content-Type: application/json" \
  -d "$ORDER_DATA")

echo "$ORDER_RESPONSE" | jq .
ORDER_ID=$(echo "$ORDER_RESPONSE" | jq -r '.order_id')
echo -e "${GREEN}✓ Order ID: $ORDER_ID${NC}"
echo ""

# Get the order
test_endpoint "GET" "/orders/$ORDER_ID" "" "6. Get Order Details"

# Process payment
PAYMENT_DATA="{
  \"order_id\": $ORDER_ID,
  \"amount\": 1029.98
}"

test_endpoint "POST" "/payment" "$PAYMENT_DATA" "7. Process Payment"

# ============================================================================
# MIXED INSTRUMENTATION TRACES
# ============================================================================

print_section "MIXED-INSTRUMENTED ENDPOINTS (Auto HTTP + Manual Business Logic)"

test_endpoint "GET" "/inventory/1" "" "8. Get Inventory (Mixed Instrumentation)"

# ============================================================================
# ERROR SCENARIOS
# ============================================================================

print_section "ERROR SCENARIOS (For Learning Error Handling)"

# Test order with empty items
INVALID_ORDER='{
  "customer_email": "user@example.com",
  "items": []
}'

test_endpoint "POST" "/orders" "$INVALID_ORDER" "9. Create Order with Empty Items (Expected Error)"

# Test payment with fail flag
PAYMENT_FAIL="{
  \"order_id\": $ORDER_ID,
  \"amount\": 500.00
}"

test_endpoint "POST" "/payment?fail=true" "$PAYMENT_FAIL" "10. Payment with Intentional Failure"

# ============================================================================
# HIGH-LOAD SCENARIO
# ============================================================================

print_section "GENERATE MULTIPLE TRACES"

echo -e "${YELLOW}Creating 5 orders to generate multiple traces...${NC}"

for i in {1..5}; do
    MULTI_ORDER="{
      \"customer_email\": \"customer$i@example.com\",
      \"items\": [
        {\"product_id\": $((RANDOM % 4 + 1)), \"quantity\": $((RANDOM % 3 + 1))}
      ]
    }"
    
    echo -e "${YELLOW}Order $i...${NC}"
    curl -s -X POST "$BASE_URL/orders" \
        -H "Content-Type: application/json" \
        -d "$MULTI_ORDER" | jq '.order_id'
    
    sleep 0.5
done

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

print_section "TRACE VIEWING"

echo -e "${GREEN}✓ Test suite complete!${NC}"
echo ""
echo "View traces in your LGTM stack Tempo UI:"
echo "  - Search by service.name = 'otel-learning-app'"
echo "  - Filter by instrumentation.type = 'auto' or 'manual'"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
