# Deploy Frontend To Vercel

PalmVerse is a monorepo. The frontend app lives in `frontend/`.

## Vercel Settings

- Framework Preset: `Next.js`
- Root Directory: `frontend`
- Build Command: `npm run build`
- Install Command: `npm install`
- Output Directory: leave empty / default, and turn off Output Directory override if Vercel lets you

If Vercel shows `No Output Directory named "public" found`, open Project Settings and clear the Output Directory field. Do not set it to `public` for this Next.js app.

This project does not need a root `vercel.json` when Vercel's Root Directory is set to `frontend`.

## Environment Variables

Set this in Vercel after the backend is deployed:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-backend-url
```

For the first frontend-only deploy, this can be left unset, but scan requests will fail until the backend URL is configured.

## Backend

Deploy the FastAPI backend separately, for example on Render or Railway.

The backend service must allow CORS from the Vercel frontend domain.
