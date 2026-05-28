# Breathe ESG — Emission Data Platform

> Multi-tenant platform for ingesting, normalising, reviewing, and auditing corporate emission data from SAP, utility, and travel sources.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend Setup

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data   # creates demo tenant + users + sample data
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev   # starts on http://localhost:3000
```

### Login Credentials

| User    | Password    | Role    |
|---------|-------------|---------|
| analyst | analyst123  | Analyst |
| admin   | admin123    | Admin   |

## Architecture

```
React (Vite) ──REST/JSON──▶ Django REST Framework ──ORM──▶ SQLite / PostgreSQL
```

- **Multi-tenant**: Every model carries a `tenant` FK
- **Raw preservation**: Original files + row-level data stored immutably
- **Dual quantities**: Raw + normalised values kept side-by-side
- **Append-only audit**: Every mutation tracked in `AuditLog`

## API Endpoints

| Method | Endpoint                    | Description                    |
|--------|-----------------------------|--------------------------------|
| POST   | `/api/auth/login/`          | JWT token pair                 |
| POST   | `/api/auth/refresh/`        | Refresh access token           |
| GET    | `/api/me/`                  | Current user + tenant info     |
| POST   | `/api/ingestions/upload/`   | Upload & parse a data file     |
| GET    | `/api/ingestions/`          | List all ingestions            |
| GET    | `/api/records/`             | List emission records (filter) |
| PATCH  | `/api/records/{id}/review/` | Approve / reject / flag        |
| GET    | `/api/dashboard/summary/`  | Dashboard aggregations         |
| GET    | `/api/audit-log/`           | Full audit trail               |

## Deployment

See `IMPLEMENTATION_PLAN.md` §8 for Render + Vercel deployment instructions.

## Documentation

- `MODEL.md` — Data model design rationale
- `DECISIONS.md` — Technical decision log
- `TRADEOFFS.md` — Honest tradeoffs and limitations
- `SOURCES.md` — Data source research notes
