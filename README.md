# AI-Based-SOC-with-Automated-Firewall-Response

Dark-themed AI SOC dashboard with authentication, real-time attack feed, threat analytics, firewall actions, report generation, assistant chat, and settings management.

## Stack
- **Frontend:** React + Vite + Tailwind + Recharts
- **Backend:** FastAPI + WebSocket
- **Persistence:** MongoDB when available, in-memory demo fallback for local/CI

## Project Structure
- `frontend/` — SOC web UI (login, signup, dashboard, threats, health, logs, reports, assistant, settings)
- `backend/` — FastAPI API + WebSocket endpoints + demo data/runtime store

## Quick Start
### 1) Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://127.0.0.1:5173` and targets backend `http://127.0.0.1:8000/api/v1` by default.

## Environment Variables
Backend (`backend/app/main.py`) supports:
- `ENV` (default: `dev`)
- `DOCS_ENABLED` (default: `true`)
- `SECRET_KEY` (required in production, min 32 chars)
- `CORS_ORIGINS` (comma-separated list)
- `RATE_LIMIT_DEFAULT` (default: `120/minute`)
- `RATE_LIMIT_LOGIN` (default: `5/minute`)
- Mongo config from `backend/core/config.py` (`MONGODB_URI`, `MONGODB_DB`)

Frontend:
- `VITE_API_URL` (default: `http://127.0.0.1:8000/api/v1`)

## Demo Authentication
- Seed admin: `admin@soc.local` / `Admin@123`
- Signup is enabled (`/api/v1/auth/signup`) and returns an auth token for immediate login flow.

## API Coverage (used by frontend)
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/signup`
- `GET /api/v1/auth/me`
- `GET /api/v1/attacks`
- `GET /api/v1/attacks/{attack_id}`
- `POST /api/v1/attacks`
- `GET /api/v1/system/health`
- `GET /api/v1/health`
- `POST /api/v1/firewall/block`
- `POST /api/v1/firewall/unblock`
- `GET /api/v1/threat-intel/check`
- `GET /api/v1/geo/lookup`
- `POST /api/v1/reports/generate`
- `POST /api/v1/assistant`
- `PATCH /api/v1/settings/profile`
- `POST /api/v1/settings/password`

## Real-time Behavior
- WebSocket endpoint: `ws://127.0.0.1:8000/ws/attacks`
- Frontend listens for `new_attack` events and updates views live.
- If WebSocket is unavailable, frontend falls back to API polling.

## Reports
- PDF reports are generated under `backend/reports/` and exposed at `/reports/<file>.pdf`.

## Testing and Build
### Backend tests
```bash
python -m pytest -q backend/tests
```

### Frontend build
```bash
cd frontend
npm run build
```

## Notes for Production Storage
If MongoDB is unavailable, the app runs in demo fallback mode using in-memory data. For production use, configure MongoDB and persistent backups for attacks, users, reports, and audit records.
