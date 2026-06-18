"""
OTEL Learning Application - E-commerce style API
Demonstrates both auto and manual OpenTelemetry instrumentation
"""

import time
import random
import logging
from typing import Optional
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.trace import Status, StatusCode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# OTEL SETUP
# ============================================================================

def setup_otel():
    """Initialize OpenTelemetry SDK"""
    
    # Create resource with service metadata
    resource = Resource.create({
        "service.name": "otel-learning-app",
        "service.version": "1.0.0",
        "deployment.environment": "lab",
        "service.namespace": "observability-stack"
    })
    
    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter (sends to OTEL Collector -> your LGTM stack)
    otlp_exporter = OTLPSpanExporter(
        endpoint="localhost:4317",
        insecure=True
    )
    
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(tracer_provider)
    
    logger.info("✓ OpenTelemetry initialized")
    return tracer_provider


# Initialize OTEL before creating FastAPI app
tracer_provider = setup_otel()
tracer = trace.get_tracer(__name__)

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="OTEL Learning App",
    description="E-commerce API for learning OpenTelemetry",
    version="1.0.0"
)


# ============================================================================
# MIDDLEWARE FOR AUTO-INSTRUMENTATION METADATA
# ============================================================================

class OTELMetadataMiddleware(BaseHTTPMiddleware):
    """Add instrumentation type metadata to auto-instrumented spans"""
    
    async def dispatch(self, request, call_next):
        # Get the current span
        current_span = trace.get_current_span()
        
        # Mark as auto-instrumented if it's a traced endpoint
        if current_span and current_span.is_recording():
            # This will be picked up by FastAPI instrumentation
            request.state.instrumentation_type = "auto"
        
        response = await call_next(request)
        return response


# Add middleware
app.add_middleware(OTELMetadataMiddleware)


# ============================================================================
# MODELS & DATA
# ============================================================================

class Product:
    def __init__(self, id: int, name: str, price: float, stock: int):
        self.id = id
        self.name = name
        self.price = price
        self.stock = stock
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock
        }


class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    FAILED = "failed"
    DECLINED = "declined"


# Simulated database
PRODUCTS = {
    1: Product(1, "Laptop", 999.99, 5),
    2: Product(2, "Mouse", 29.99, 50),
    3: Product(3, "Keyboard", 79.99, 30),
    4: Product(4, "Monitor", 299.99, 10),
}

ORDERS = {}
ORDER_COUNTER = 0


# ============================================================================
# HELPER FUNCTIONS - MANUAL INSTRUMENTATION
# ============================================================================

def validate_order(order_data: dict) -> bool:
    """Validate order data with manual span"""
    with tracer.start_as_current_span("validate_order") as span:
        span.set_attribute("instrumentation.type", "manual")
        span.set_attribute("order.items_count", len(order_data.get("items", [])))
        
        time.sleep(random.uniform(0.05, 0.15))  # Simulate validation
        
        if not order_data.get("items"):
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(ValueError("Order must contain items"))
            return False
        
        if not order_data.get("customer_email"):
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(ValueError("Customer email required"))
            return False
        
        span.set_status(Status(StatusCode.OK))
        return True


def inventory_check(items: list) -> dict:
    """Check inventory with manual span"""
    with tracer.start_as_current_span("inventory_check") as span:
        span.set_attribute("instrumentation.type", "manual")
        span.set_attribute("items_to_check", len(items))
        
        time.sleep(random.uniform(0.1, 0.3))
        
        available = True
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 1)
            
            if product_id not in PRODUCTS:
                span.set_status(Status(StatusCode.ERROR))
                available = False
                break
            
            product = PRODUCTS[product_id]
            if product.stock < quantity:
                span.set_status(Status(StatusCode.ERROR))
                available = False
                break
        
        if available:
            span.set_status(Status(StatusCode.OK))
        
        return {"available": available}


def reserve_stock(items: list) -> bool:
    """Reserve inventory with manual span"""
    with tracer.start_as_current_span("reserve_stock") as span:
        span.set_attribute("instrumentation.type", "manual")
        span.set_attribute("items_to_reserve", len(items))
        
        time.sleep(random.uniform(0.05, 0.2))
        
        try:
            for item in items:
                product_id = item.get("product_id")
                quantity = item.get("quantity", 1)
                PRODUCTS[product_id].stock -= quantity
            
            span.set_status(Status(StatusCode.OK))
            return True
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(e)
            return False


def persist_order(order_data: dict) -> int:
    """Save order with manual span"""
    with tracer.start_as_current_span("persist_order") as span:
        span.set_attribute("instrumentation.type", "manual")
        
        global ORDER_COUNTER
        ORDER_COUNTER += 1
        order_id = ORDER_COUNTER
        
        time.sleep(random.uniform(0.05, 0.1))
        
        ORDERS[order_id] = {
            "id": order_id,
            "customer_email": order_data.get("customer_email"),
            "items": order_data.get("items"),
            "total": order_data.get("total"),
            "created_at": datetime.now().isoformat()
        }
        
        span.set_attribute("order.id", order_id)
        span.set_status(Status(StatusCode.OK))
        
        return order_id


def fraud_check(customer_email: str, amount: float) -> bool:
    """Check for fraud with manual span"""
    with tracer.start_as_current_span("fraud_check") as span:
        span.set_attribute("instrumentation.type", "manual")
        span.set_attribute("payment.amount", amount)
        span.set_attribute("customer.email", customer_email)
        
        time.sleep(random.uniform(0.1, 0.4))
        
        # Simulate fraud check (randomly flag high amounts)
        is_suspicious = amount > 5000 and random.random() < 0.1
        
        span.set_attribute("fraud.is_suspicious", is_suspicious)
        span.set_status(Status(StatusCode.OK))
        
        return not is_suspicious


def payment_gateway(amount: float, fail: bool = False) -> dict:
    """Call payment gateway with manual span"""
    with tracer.start_as_current_span("payment_gateway") as span:
        span.set_attribute("instrumentation.type", "manual")
        span.set_attribute("payment.amount", amount)
        span.set_attribute("payment.gateway", "stripe-mock")
        
        time.sleep(random.uniform(0.2, 0.8))
        
        if fail:
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(Exception("Payment gateway declined"))
            return {
                "status": PaymentStatus.FAILED,
                "error": "Payment declined"
            }
        
        # 5% chance of decline
        if random.random() < 0.05:
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(Exception("Card declined"))
            return {
                "status": PaymentStatus.DECLINED,
                "error": "Card declined"
            }
        
        span.set_attribute("payment.transaction_id", f"txn_{int(time.time())}")
        span.set_status(Status(StatusCode.OK))
        return {
            "status": PaymentStatus.APPROVED,
            "transaction_id": f"txn_{int(time.time())}"
        }


def update_order_status(order_id: int, status: str) -> bool:
    """Update order status with manual span"""
    with tracer.start_as_current_span("update_order_status") as span:
        span.set_attribute("instrumentation.type", "manual")
        span.set_attribute("order.id", order_id)
        span.set_attribute("order.new_status", status)
        
        time.sleep(random.uniform(0.05, 0.1))
        
        if order_id in ORDERS:
            ORDERS[order_id]["status"] = status
            span.set_status(Status(StatusCode.OK))
            return True
        
        span.set_status(Status(StatusCode.ERROR))
        return False


# ============================================================================
# ENDPOINTS - AUTO INSTRUMENTED (FastAPI auto-instrumentation)
# ============================================================================

@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint
    **Instrumentation: AUTO** (FastAPI middleware)
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("instrumentation.type", "auto")
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "instrumentation": "auto"
    }


@app.get("/products", tags=["Products"])
async def list_products():
    """
    List all products
    **Instrumentation: AUTO** (FastAPI middleware)
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("instrumentation.type", "auto")
        current_span.set_attribute("products.count", len(PRODUCTS))
    
    time.sleep(random.uniform(0.05, 0.1))
    
    return {
        "products": [p.to_dict() for p in PRODUCTS.values()],
        "count": len(PRODUCTS),
        "instrumentation": "auto"
    }


@app.get("/products/{product_id}", tags=["Products"])
async def get_product(product_id: int):
    """
    Get product by ID
    **Instrumentation: AUTO** (FastAPI middleware)
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("instrumentation.type", "auto")
        current_span.set_attribute("product.id", product_id)
    
    time.sleep(random.uniform(0.05, 0.1))
    
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "product": PRODUCTS[product_id].to_dict(),
        "instrumentation": "auto"
    }


# ============================================================================
# ENDPOINTS - MANUAL INSTRUMENTED
# ============================================================================

@app.post("/orders", tags=["Orders"])
async def create_order(
    customer_email: str,
    items: list[dict],
    query_fail: Optional[bool] = Query(False, alias="fail")
):
    """
    Create a new order
    **Instrumentation: MANUAL** (explicit spans in code)
    
    Trace structure:
    ```
    POST /orders (auto)
    ├── validate_order
    ├── inventory_check
    ├── reserve_stock
    └── persist_order
    ```
    """
    # FastAPI span will be created automatically
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("instrumentation.type", "auto")  # HTTP is auto
    
    # Create parent span for order logic
    with tracer.start_as_current_span("create_order") as order_span:
        order_span.set_attribute("instrumentation.type", "manual")
        order_span.set_attribute("customer.email", customer_email)
        order_span.set_attribute("order.items_count", len(items))
        
        order_data = {
            "customer_email": customer_email,
            "items": items,
            "total": sum(item.get("quantity", 1) * PRODUCTS[item["product_id"]].price 
                        for item in items if item["product_id"] in PRODUCTS)
        }
        
        # Validate
        if not validate_order(order_data):
            order_span.set_status(Status(StatusCode.ERROR))
            raise HTTPException(status_code=400, detail="Invalid order")
        
        # Check inventory
        inv = inventory_check(items)
        if not inv["available"]:
            order_span.set_status(Status(StatusCode.ERROR))
            raise HTTPException(status_code=400, detail="Item out of stock")
        
        # Fail scenario
        if query_fail:
            order_span.set_status(Status(StatusCode.ERROR))
            raise HTTPException(status_code=500, detail="Intentional failure")
        
        # Reserve stock
        if not reserve_stock(items):
            order_span.set_status(Status(StatusCode.ERROR))
            raise HTTPException(status_code=500, detail="Could not reserve stock")
        
        # Save order
        order_id = persist_order(order_data)
        
        order_span.set_attribute("order.id", order_id)
        order_span.set_attribute("order.total", order_data["total"])
        order_span.set_status(Status(StatusCode.OK))
        
        return {
            "order_id": order_id,
            "status": "created",
            "customer_email": customer_email,
            "items": items,
            "total": order_data["total"],
            "instrumentation": "manual"
        }


@app.post("/payment", tags=["Payment"])
async def process_payment(
    order_id: int,
    amount: float,
    query_fail: Optional[bool] = Query(False, alias="fail")
):
    """
    Process payment for an order
    **Instrumentation: MANUAL** (explicit nested spans)
    
    Trace structure:
    ```
    POST /payment (auto)
    ├── fraud_check
    ├── payment_gateway
    └── update_order_status
    ```
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("instrumentation.type", "auto")
    
    with tracer.start_as_current_span("process_payment") as payment_span:
        payment_span.set_attribute("instrumentation.type", "manual")
        payment_span.set_attribute("order.id", order_id)
        payment_span.set_attribute("payment.amount", amount)
        
        if order_id not in ORDERS:
            payment_span.set_status(Status(StatusCode.ERROR))
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = ORDERS[order_id]
        
        # Fraud check
        if not fraud_check(order["customer_email"], amount):
            payment_span.set_status(Status(StatusCode.ERROR))
            raise HTTPException(status_code=403, detail="Fraud detected")
        
        # Process payment
        result = payment_gateway(amount, fail=query_fail)
        
        if result["status"] != PaymentStatus.APPROVED:
            payment_span.set_status(Status(StatusCode.ERROR))
            raise HTTPException(status_code=402, detail=result.get("error", "Payment failed"))
        
        # Update order
        if not update_order_status(order_id, "paid"):
            payment_span.set_status(Status(StatusCode.ERROR))
            raise HTTPException(status_code=500, detail="Could not update order")
        
        payment_span.set_attribute("payment.transaction_id", result.get("transaction_id"))
        payment_span.set_status(Status(StatusCode.OK))
        
        return {
            "order_id": order_id,
            "status": "paid",
            "transaction_id": result.get("transaction_id"),
            "amount": amount,
            "instrumentation": "manual"
        }


# ============================================================================
# ENDPOINTS - MIXED INSTRUMENTATION
# ============================================================================

def database_lookup(product_id: int) -> dict:
    """Lookup product in database"""
    with tracer.start_as_current_span("database_lookup") as span:
        span.set_attribute("instrumentation.type", "manual")
        span.set_attribute("product.id", product_id)
        
        time.sleep(random.uniform(0.05, 0.15))
        
        if product_id not in PRODUCTS:
            span.set_status(Status(StatusCode.ERROR))
            return {"found": False}
        
        span.set_status(Status(StatusCode.OK))
        return {"found": True, "product": PRODUCTS[product_id].to_dict()}


def warehouse_check(product_id: int) -> dict:
    """Check warehouse location"""
    with tracer.start_as_current_span("warehouse_check") as span:
        span.set_attribute("instrumentation.type", "manual")
        span.set_attribute("product.id", product_id)
        
        time.sleep(random.uniform(0.1, 0.2))
        
        span.set_attribute("warehouse.location", "US-WEST-2")
        span.set_status(Status(StatusCode.OK))
        return {"warehouse": "US-WEST-2", "available": True}


def stock_calculation(product_id: int) -> dict:
    """Calculate available stock"""
    with tracer.start_as_current_span("stock_calculation") as span:
        span.set_attribute("instrumentation.type", "manual")
        span.set_attribute("product.id", product_id)
        
        time.sleep(random.uniform(0.05, 0.1))
        
        if product_id in PRODUCTS:
            stock = PRODUCTS[product_id].stock
            span.set_attribute("stock.available", stock)
            span.set_status(Status(StatusCode.OK))
            return {"available": stock, "reserved": 0}
        
        span.set_status(Status(StatusCode.ERROR))
        return {"available": 0, "reserved": 0}


@app.get("/inventory/{product_id}", tags=["Inventory"])
async def get_inventory(product_id: int):
    """
    Get inventory details for a product
    **Instrumentation: MIXED** (auto HTTP span + manual child spans)
    
    Trace structure:
    ```
    GET /inventory/{id} (auto)
    ├── database_lookup (manual)
    ├── warehouse_check (manual)
    └── stock_calculation (manual)
    ```
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("instrumentation.type", "auto")
        current_span.set_attribute("product.id", product_id)
    
    # These manual spans become children of the auto HTTP span
    db_result = database_lookup(product_id)
    
    if not db_result["found"]:
        raise HTTPException(status_code=404, detail="Product not found")
    
    warehouse = warehouse_check(product_id)
    stock = stock_calculation(product_id)
    
    return {
        "product": db_result["product"],
        "warehouse": warehouse,
        "stock": stock,
        "instrumentation": "mixed"
    }


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@app.get("/orders/{order_id}", tags=["Orders"])
async def get_order(order_id: int):
    """Get order details - AUTO instrumented"""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("instrumentation.type", "auto")
        current_span.set_attribute("order.id", order_id)
    
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "order": ORDERS[order_id],
        "instrumentation": "auto"
    }


@app.get("/metrics", tags=["System"])
async def metrics():
    """Application metrics"""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("instrumentation.type", "auto")
    
    return {
        "total_products": len(PRODUCTS),
        "total_orders": len(ORDERS),
        "total_stock": sum(p.stock for p in PRODUCTS.values()),
        "instrumentation": "auto"
    }


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Instrument FastAPI and requests
    FastAPIInstrumentor.instrument_app(app)
    RequestsInstrumentor.instrument()
    
    logger.info("🚀 Starting OTEL Learning App on http://0.0.0.0:8000")
    logger.info("📖 API Docs: http://localhost:8000/docs")
    logger.info("📊 Traces will be exported to OTEL Collector at localhost:4317 -> your LGTM stack")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
