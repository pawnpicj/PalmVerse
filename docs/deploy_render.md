# Deploy Backend To Render

The PalmVerse backend is a FastAPI service in `backend/`.

## Render Settings

Create a new Render Web Service from the same GitHub repo.

- Service Type: `Web Service`
- Runtime: `Python 3`
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Plan: Free is okay for testing

## Python Version

The backend includes `.python-version` with:

```text
3.11
```

This avoids Render's newer default Python version, which can be incompatible with some binary packages such as MediaPipe.

## After Deploy

Open:

```text
https://your-render-service.onrender.com/health
```

Expected response:

```json
{"status":"ok"}
```

## Connect Frontend

After backend deploys, add this environment variable in Vercel:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com
```

Then redeploy the Vercel frontend.

## CORS

Before production testing, add the Vercel frontend domain to the backend CORS allowlist in `backend/app/main.py`.
