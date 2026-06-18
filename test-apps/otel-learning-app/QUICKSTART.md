# OTEL Learning App - Quick Start

Minimal quickstart for running the learning application. This repo provides only the application code — use your Alloy collector to receive traces.

## 1. Install Python dependencies

```bash
cd test-apps/otel-learning-app
pip install -r requirements.txt
```

## 2. Run the application

Recommended (auto-instrumentation):
```bash
opentelemetry-instrument python app.py
```

Or run without auto-instrumentation (manual spans still work):
```bash
python app.py
```

The app starts on `http://localhost:8000` and exports traces via OTLP to `localhost:4317` by default — configure your Alloy collector to accept OTLP on that endpoint.

## 3. Test the application

Run the included test script to generate traces:

```bash
bash test-api.sh
```

Or call endpoints manually (examples in README).

## 4. View traces

Traces are sent to your Alloy collector and stored in your existing LGTM stack. View them in Tempo/Grafana as configured by your environment.

## Troubleshooting

- Ensure Alloy is running and accepts OTLP at `localhost:4317`.
- Check app logs for the `OTEL initialized` message.
- If using Docker for Alloy, ensure the collector config forwards to your Tempo instance.

## Service Details

| Service | URL | Purpose |
|---------|-----|---------|
| FastAPI App | http://localhost:8000 | The learning app |
| FastAPI Docs | http://localhost:8000/docs | Interactive API |

## Commands Reference

```bash
# Install dependencies
pip install -r requirements.txt

# Run app with auto-instrumentation
opentelemetry-instrument python app.py

# Run test suite
bash test-api.sh
```

## Notes

This folder intentionally excludes any collector/docker-compose orchestration — use your Alloy collector from your LGTM stack to collect and store traces.

**Happy tracing! 🎯**
