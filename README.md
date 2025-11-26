# moneyTracker

A simple personal finance tracker with a Python backend and a frontend. This repository contains a FastAPI-based backend and a frontend app (Vite). It also includes Docker support for easy local setup.

## What this project is

- **Backend:** Python service (FastAPI) providing APIs for transactions, budgets, recurring items, and import features.
- **Frontend:** Modern single-page app (Vite) for interacting with your data.
- **Dev tooling:** `docker-compose` for running the full stack locally, plus sample CSV fixtures in the repository.

## Quick start (recommended)

Prerequisites: `docker` and `docker-compose` installed.

1. Build and start both services:

```
docker-compose up --build
```

2. Open the frontend in your browser (usually at `http://localhost:5173`) and the backend API at `http://localhost:8000`.

## Run backend locally (development)

If you prefer to run only the backend directly:

```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run tests:

```
cd backend
pytest
```

## Run frontend locally (development)

```
cd frontend
npm install
npm run dev
```

## Sample data

There are a few sample CSV files in the repo root (for import/testing):

- `fake_transations.csv`
- `fake_transations_for_test2.csv`
- `fake_recurring_test_2025.csv`

You can import these through the application's CSV import feature or use the API endpoints provided by the backend.

## Where to look next

- Backend code: `backend/app`
- Frontend code: `frontend/src`
- Docker compose: `docker-compose.yml`

## Contributing

Contributions, issues and feature requests are welcome. Please open an issue or submit a pull request.
