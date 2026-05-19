# Deploy Frontend To Vercel

PalmVerse is a monorepo. The frontend app lives in `frontend/`.

## Vercel Settings

- Framework Preset: `Next.js`
- Root Directory: `frontend`
- Build Command: `npm run build`
- Install Command: `npm install`
- Output Directory: leave default

## Environment Variables

Set this in Vercel after the backend is deployed:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-backend-url
```

For the first frontend-only deploy, this can be left unset, but scan requests will fail until the backend URL is configured.

## Backend

Deploy the FastAPI backend separately, for example on Render or Railway.

The backend service must allow CORS from the Vercel frontend domain.
