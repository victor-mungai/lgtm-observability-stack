.PHONY: help install app app-no-auto test docs

help:
	@echo "🚀 OTEL Learning App - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install Python dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make app            Run FastAPI app with auto-instrumentation"
	@echo "  make app-no-auto    Run FastAPI app without auto-instrumentation"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run API test suite"
	@echo ""
	@echo "Utilities:"
	@echo "  make docs           Open API documentation"
	@echo ""
	@echo "URLs:"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  Traces:    View in your LGTM stack (Alloy -> Tempo)"
	@echo ""

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

app:
	@echo "🚀 Starting FastAPI app with AUTO-INSTRUMENTATION..."
	@echo "   (Manual instrumentation still works in code)"
	opentelemetry-instrument python app.py

app-no-auto:
	@echo "🚀 Starting FastAPI app WITHOUT auto-instrumentation..."
	python app.py

test:
	@echo "🧪 Running test suite..."
	@echo ""
	bash test-api.sh

docs:
	@echo "📖 Opening API documentation..."
	@which open > /dev/null && open http://localhost:8000/docs || \
	@which xdg-open > /dev/null && xdg-open http://localhost:8000/docs || \
	@echo "Open http://localhost:8000/docs in your browser"
