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

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8089
```

If the project folder was moved after creating `.venv`, do not run `uvicorn ...` directly. Use `python -m uvicorn ...` so Windows does not use a stale `uvicorn.exe` launcher path.

You can also run:

```powershell
cd backend
.\run_backend.ps1
```

Backend health check:

```text
http://localhost:8089/health
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8089` if needed.

The frontend runs at `http://localhost:8088`.

## Deploy Backend To Render

Create a Render **Web Service** from this GitHub repository.

Use these settings:

```text
Runtime: Python 3
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
Plan: Free is okay for testing
```

The backend includes:

```text
backend/.python-version
backend/models/hand_landmarker.task
```

`.python-version` pins Python to `3.11`, which is safer for MediaPipe compatibility.

After deploy, test:

```text
https://YOUR_RENDER_SERVICE.onrender.com/health
```

Expected response:

```json
{"status":"ok"}
```

Example:

```text
https://palmverse.onrender.com/health
```

### Render Notes

Render Free services can cold start. The first scan after inactivity may be slow.

MediaPipe may fall back on Render if native graphics libraries are unavailable. The API is designed to return success with `manual_template` fallback instead of crashing.

If backend changes do not appear, use:

```text
Manual Deploy > Clear build cache & deploy
```

## Deploy Frontend To Vercel

Create a Vercel project from the same GitHub repository.

Use these settings exactly:

```text
Framework Preset: Next.js
Root Directory: frontend
Install Command: npm install
Build Command: npm run build
Output Directory: leave empty / do not override
```

Do not set Output Directory to:

```text
public
.next
```

This project does not need a root `vercel.json` when `Root Directory` is set to `frontend`.

### Vercel Environment Variable

After the Render backend is live, add this environment variable in Vercel:

```text
NEXT_PUBLIC_API_BASE_URL=https://YOUR_RENDER_SERVICE.onrender.com
```

Example:

```text
NEXT_PUBLIC_API_BASE_URL=https://palmverse.onrender.com
```

Then redeploy the frontend. `NEXT_PUBLIC_*` values are embedded during build, so changing this value requires a new Vercel deployment.

## Deploy Order

Recommended order:

```text
1. Push code to GitHub
2. Deploy backend on Render
3. Verify /health
4. Add NEXT_PUBLIC_API_BASE_URL in Vercel
5. Deploy frontend on Vercel
6. Open Vercel URL and run a scan test
```

## Git Push Flow

```bash
git add .
git commit -m "Update PalmVerse"
git push
```

Then redeploy:

```text
Render: Manual Deploy > Clear build cache & deploy
Vercel: Redeploy latest production deployment
```

## Troubleshooting

### Vercel: 404 NOT_FOUND

Check Vercel settings:

```text
Root Directory: frontend
Framework Preset: Next.js
Output Directory: empty / not overridden
```

Open the latest deployment from the Vercel Deployments page using the `Visit` button.

### Vercel: No Output Directory named "public"

Clear the Output Directory field. Do not set it to `public` for this Next.js app.

### Frontend Still Calls localhost:8089

Set this in Vercel:

```text
NEXT_PUBLIC_API_BASE_URL=https://YOUR_RENDER_SERVICE.onrender.com
```

Then redeploy Vercel. Environment variables are not applied to an already-built deployment.

### Scan Fails But /health Works

Check Render logs. Common causes:

- Backend did not redeploy after code changes.
- Render service is cold starting.
- MediaPipe native dependency fallback is active.
- Vercel environment variable points to the wrong backend URL.

### CORS Issues

The backend currently allows localhost and `*.vercel.app` origins in `backend/app/main.py`.

If using a custom domain, add it to the CORS allowlist.
