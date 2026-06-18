# OTEL Learning App - E-Commerce API

A comprehensive Python FastAPI application for learning OpenTelemetry with both **zero-code (auto-instrumentation)** and **manual instrumentation** of traces.

## Architecture

```
┌─────────────────────────┐
│   Python FastAPI App    │
│  (OTEL Learning App)    │
├─────────────────────────┤
│  Routes with 2 types:   │
│  • Auto-instrumented    │
│  • Manual-instrumented  │
│  • Mixed                │
└────────────┬────────────┘
             │ OTLP gRPC
             v
┌──────────────────────────┐
│    OTEL Collector        │
│  (localhost:4317)        │
└────────────┬─────────────┘
             │
             v
   ┌─────────────────┐
   │  Tempo/Jaeger   │
   └─────────────────┘
```

## Endpoints Overview

### Auto-Instrumented (Zero-Code)
These rely on OpenTelemetry auto-instrumentation middleware. No tracing code in the application.

```
GET  /health              - Health check
GET  /products            - List all products
GET  /products/{id}       - Get product details
GET  /orders/{id}         - Get order details
GET  /metrics             - Application metrics
```

**Run with:**
```bash
opentelemetry-instrument python app.py
```

### Manual-Instrumented
Explicit span creation and control. Perfect for business logic and nested operations.

```
POST /orders              - Create order with nested spans
  └── validate_order
  └── inventory_check
  └── reserve_stock
  └── persist_order

POST /payment             - Process payment with nested spans
  └── fraud_check
  └── payment_gateway
  └── update_order_status
```

### Mixed Instrumentation
Combines auto (HTTP span) with manual (business logic spans).

```
GET  /inventory/{id}      - Inventory details
  └── database_lookup (manual)
  └── warehouse_check (manual)
  └── stock_calculation (manual)
```

## Setup & Installation

### 1. Install Dependencies

```bash
cd test-apps/otel-learning-app
pip install -r requirements.txt
```

### 2. Collector

This repository includes only the application. Configure and run your Alloy collector to receive OTLP traces (default endpoint `localhost:4317`). The app exports traces to `localhost:4317` by default — update the exporter endpoint in `app.py` if your Alloy instance uses a different address.

### 3. Run with Auto-Instrumentation

**Option A: With auto-instrumentation (FastAPI + HTTP)**
```bash
opentelemetry-instrument python app.py
```

**Option B: Direct run (manual instrumentation still works)**
```bash
python app.py
```

The app starts on `http://localhost:8000`

## API Documentation

Access interactive API docs: http://localhost:8000/docs

## Learning Trace Examples

### Example 1: Auto-Instrumented Trace (GET /products)

```
GET /products (HTTP span) [auto]
├── method: GET
├── url.path: /products
├── instrumentation.type: auto
└── http.status_code: 200
```

### Example 2: Manual Instrumented Trace (POST /orders)

```
POST /orders (HTTP span) [auto]
├── method: POST
├── instrumentation.type: auto
└── span duration: 500ms
    │
    └── create_order [manual]
        ├── instrumentation.type: manual
        ├── customer.email: user@example.com
        ├── order.items_count: 2
        │
        ├── validate_order [manual]
        │  └── instrumentation.type: manual
        │
        ├── inventory_check [manual]
        │  └── items_to_check: 2
        │
        ├── reserve_stock [manual]
        │  ├── items_to_reserve: 2
        │  └── status: OK
        │
        └── persist_order [manual]
           ├── order.id: 1
           ├── order.total: 1029.98
           └── status: OK
```

### Example 3: Mixed Instrumentation (GET /inventory/1)

```
GET /inventory/1 (HTTP span) [auto]
├── instrumentation.type: auto
├── product.id: 1
└── span duration: 350ms
    │
    ├── database_lookup [manual]
    │  └── product.id: 1
    │
    ├── warehouse_check [manual]
    │  ├── warehouse.location: US-WEST-2
    │  └── available: true
    │
    └── stock_calculation [manual]
       ├── stock.available: 5
       └── reserved: 0
```

## Testing the Application

### 1. Create an Order (Manual Instrumentation)

```bash
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "user@example.com",
    "items": [
      {"product_id": 1, "quantity": 1},
      {"product_id": 2, "quantity": 2}
    ]
  }'
```

Response:
```json
{
  "order_id": 1,
  "status": "created",
  "customer_email": "user@example.com",
  "items": [...],
  "total": 1029.98,
  "instrumentation": "manual"
}
```

### 2. Process Payment (Manual with Error Scenario)

```bash
# Success
curl -X POST "http://localhost:8000/payment" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "amount": 1029.98
  }'

# Intentional failure (for error span visualization)
curl -X POST "http://localhost:8000/payment?fail=true" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "amount": 1029.98
  }'
```

### 3. List Products (Auto Instrumentation)

```bash
curl http://localhost:8000/products
```

### 4. Check Inventory (Mixed Instrumentation)

```bash
curl http://localhost:8000/inventory/1
```

### 5. View Metrics

```bash
curl http://localhost:8000/metrics
```

## Metadata Attributes

Each span includes metadata to identify instrumentation type:

### Auto-Instrumented Spans
```
instrumentation.type: "auto"
```

Added through middleware/FastAPI instrumentation.

### Manual-Instrumented Spans
```
span.set_attribute("instrumentation.type", "manual")
```

Explicitly set in span creation.

### Resource-Level Attributes
All traces include:
```
service.name: "otel-learning-app"
service.version: "1.0.0"
deployment.environment: "lab"
service.namespace: "observability-stack"
```

## Viewing Traces

Traces are exported to your LGTM stack via your Alloy collector (or any OTLP-compatible collector).

In your Tempo UI (or configured trace viewer):

1. Open your Tempo UI
2. Click on "Search"
3. Filter by:
  - `service.name = "otel-learning-app"`
  - `instrumentation.type = "auto"` or `"manual"`
  - Duration range

**Auto-Instrumented Traces:**
- Single HTTP span with auto-generated attributes
- Minimal overhead (FastAPI middleware)
- Good for baseline metrics

**Manual-Instrumented Traces:**
- Root HTTP span (auto)
- Multiple child spans (manual) showing business logic
- Rich attributes specific to operations
- Error handling with `span.record_exception()`

**Mixed Traces:**
- Combines both: HTTP is auto, business logic is manual
- Demonstrates real-world applications
- Shows parent-child span relationships

## Error Scenarios for Learning

### Scenario 1: Invalid Order
```bash
curl -X POST "http://localhost:8000/orders" \
  -d '{"customer_email": "user@example.com", "items": []}'
```
→ Trace shows failed `validate_order` span with error status

### Scenario 2: Out of Stock
```bash
# First, exhaust stock
for i in {1..10}; do
  curl -X POST "http://localhost:8000/orders" \
    -d '{
      "customer_email": "user@example.com",
      "items": [{"product_id": 1, "quantity": 1}]
    }'
done

# Next one will fail
curl -X POST "http://localhost:8000/orders" \
  -d '{
    "customer_email": "user@example.com",
    "items": [{"product_id": 1, "quantity": 1}]
  }'
```
→ Trace shows failed `inventory_check` span

### Scenario 3: Payment Failure
```bash
curl -X POST "http://localhost:8000/payment?fail=true" \
  -d '{"order_id": 1, "amount": 1029.98}'
```
→ Trace shows `payment_gateway` span with ERROR status and exception

## Key Learning Points

1. **Auto vs. Manual Instrumentation**
   - Auto provides baseline metrics with minimal code
   - Manual gives fine-grained control over business-critical spans

2. **Span Hierarchy**
   - Parent HTTP span (auto) contains child business logic spans (manual)
   - Demonstrates trace composition

3. **Error Handling**
   - Spans record exceptions with `span.record_exception(e)`
   - Status set to ERROR when operations fail
   - Errors appear in Tempo/Jaeger with red highlighting

4. **Attributes**
   - Business context (order ID, customer email, etc.)
   - Operational context (warehouse location, transaction IDs)
   - Status information for debugging

5. **Realistic Delays**
   - Random sleep times simulate real database/API calls
   - Makes traces visually interesting to analyze
   - Helps understand performance bottlenecks

## Development

### Adding New Endpoints

```python
@app.get("/new-endpoint")
async def new_endpoint():
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("instrumentation.type", "auto")
    
    return {"data": "value"}
```

### Adding Manual Spans

```python
def my_function():
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("instrumentation.type", "manual")
        span.set_attribute("custom.attribute", "value")
        
        try:
            # Your logic here
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(e)
            raise
```

## Environment Variables

Create a `.env` file if you need custom configuration:

```bash
OTEL_COLLECTOR_ENDPOINT=localhost:4317
OTEL_EXPORTER_OTLP_INSECURE=true
OTEL_TRACES_SAMPLER=always_on
```

## Troubleshooting

### No traces appearing in Tempo?

1. Verify your Alloy collector is running and accepting OTLP on the configured endpoint (default `localhost:4317`).
2. Check the app logs for the `OTEL initialized` message.
3. Confirm your Alloy config forwards traces to Tempo/Grafana as expected.
4. Enable debug logging in `app.py` if you need more details:
  ```python
  logging.basicConfig(level=logging.DEBUG)
  ```

### Service name not appearing?

Ensure Resource is created correctly:
```python
resource = Resource.create({
    "service.name": "otel-learning-app",
    ...
})
```

### Manual spans not showing in traces?

Verify they're created within an active trace context:
```python
with tracer.start_as_current_span("operation") as span:
    # Inside this context, spans become children of parent
```

## Next Steps

After mastering this app:

1. **Add metrics** (counters, histograms) to complement traces
2. **Implement sampling** strategies for high-volume services
3. **Add context propagation** for distributed tracing across services
4. **Explore baggage** for passing data across service boundaries
5. **Implement custom processors** for modifying traces before export

## References

- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Spec](https://opentelemetry.io/docs/specs/)
- [Tempo Query Syntax](https://grafana.com/docs/tempo/latest/api_docs/search-api/)
- [FastAPI Instrumentation](https://opentelemetry.io/docs/instrumentation/python/libraries/fastapi-asgi/)
