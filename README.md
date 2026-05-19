# PalmVerse

PalmVerse is a mobile-first palmistry web app MVP.

The first implementation focuses on a reliable hybrid flow:

1. Capture a palm photo in the browser.
2. Upload it to a FastAPI backend.
3. Receive a mock scan result and suggested palm lines.
4. Display the annotated result and readings.

See [docs/palmverse_improvement_plan.md](docs/palmverse_improvement_plan.md) for the implementation plan.

## Project Structure

```text
backend/   FastAPI API
frontend/  Next.js app
docs/      planning docs
```

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8089
```

If the project folder was moved after creating `.venv`, do not run `uvicorn ...` directly. Use `python -m uvicorn ...` so Windows does not use a stale `uvicorn.exe` launcher path.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8089` if needed.

The frontend runs at `http://localhost:8088`.
