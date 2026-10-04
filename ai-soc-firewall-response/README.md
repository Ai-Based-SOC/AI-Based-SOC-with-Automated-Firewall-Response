# AI-SOC Firewall Response

## Overview
Deterministic firewall response system with analyst approval flow, SQLite audit logging,
and mock LLM triage provider for SOC (Security Operations Center) workflows.

## Project Structure
```
ai-soc-firewall-response/
├── app/                    # FastAPI application source
│   ├── main.py            # Application entry point
│   ├── core/              # Core modules (database)
│   ├── policy/            # Policy engine
│   └── routes/            # API routes
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
└── tests/                # pytest test suite
```

## Quick Start - Windows PowerShell

### 1. Start the Backend Server
```powershell
# Navigate to project directory
cd C:\Users\abhishek\Downloads\ai-based soc\ai-soc-firewall-response

# Activate virtual environment
& .venv\Scripts\Activate.ps1

# Start the FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 2. Verify Backend is Running
```powershell
# Check health endpoint
curl http://127.0.0.1:8001/

# Check API documentation
open http://127.0.0.1:8001/docs
```

### 3. Run the Test Suite
```powershell
# From project directory
python -m pytest
```

### 4. Basic API Tests
```powershell
# Test root endpoint
python -c "from app.main import app; print(app.title)"

# Test alert ingestion
curl -X POST http://127.0.0.1:8001/api/v1/alerts -H "Content-Type: application/json" -d '{"id":"test-001","source_ip":"10.0.0.1","attack_type":"DoS","severity":"Critical","timestamp":"2024-01-01T00:00:00Z","raw_message":"test"}'

# Test LLM triage
curl -X POST http://127.0.0.1:8001/api/v1/triage -H "Content-Type: application/json" -d '{"alert_id":"test-001"}'

# Test policy determination
curl -X POST http://127.0.0.1:8001/api/v1/policy/determine -H "Content-Type: application/json" -d '{"source_ip":"10.0.0.1","attack_type":"DoS","severity":"Critical"}'

# Test analyst approval
curl -X POST http://127.0.0.1:8001/api/v1/approval/request -H "Content-Type: application/json" -d '{"id":"req-001"}'

# Check audit logs
curl http://127.0.0.1:8001/api/v1/audit/logs
```

## Features

- **Alert Ingestion**: Receive security alerts from monitoring systems
- **Mock LLM Triage**: Classify alert severity and potential threat
- **Deterministic Policy Engine**: Map alerts to response actions based on rules
- **Analyst Approval Flow**: Pending approval requests with expiry
- **SQLite Audit Logging**: Complete audit trail of all actions
- **Temporary IP Blocking**: Simulated firewall blocking
- **Full API Documentation**: Auto-generated Swagger UI at /docs

## Development

### Running Tests
```powershell
python -m pytest
```

### Code Quality
```powershell
# Format code
ruff format

# Lint code
ruff check

# Type checking
mypy app/
```

## Docker Deployment

```powershell
# Build Docker image
docker build -t ai-soc-firewall-response .

# Run with Docker Compose
docker-compose up -d
```

## License
MIT