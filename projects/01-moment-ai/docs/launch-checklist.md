# MOMent AI — public launch checklist

This checklist is for the first public MVP deployment. Keep all secrets in provider environment settings; never commit them.

## 1. Neon PostgreSQL

1. Create a free Neon project and database.
2. Copy the PostgreSQL connection string (use SSL; a pooled connection string is suitable for the web app).
3. Keep the connection string private. Add it only to Render as `DATABASE_URL`.

## 2. Render backend

1. In Render, choose **New → Blueprint** and connect `srisankariGIT/sri-builds-with-ai`.
2. Select branch `feature/moment-ai-live-launch` for the initial preview deployment.
3. Point Render to `projects/01-moment-ai/backend/render.yaml` if prompted.
4. Set `DATABASE_URL` to the Neon connection string.
5. Set `CORS_ALLOWED_ORIGINS` to the exact Vercel frontend origin, for example `https://your-app.vercel.app` (no trailing slash).
6. Optional: set `OPENAI_API_KEY` to enable natural-language drafting and `OPENAI_MODEL` to `gpt-4o-mini`.
7. Confirm the Render service is healthy at `https://YOUR-API.onrender.com/api/health/`.

Render's free web service can sleep when idle. The first request after inactivity may take noticeably longer. Do not promise time-critical scheduled notifications from this service.

## 3. Vercel frontend

1. Import the same GitHub repository in Vercel.
2. Set the root directory to `projects/01-moment-ai/frontend`.
3. Deploy branch `feature/moment-ai-live-launch` for preview.
4. Set `NEXT_PUBLIC_API_URL` to `https://YOUR-API.onrender.com/api`.
5. Redeploy after setting the environment variable.
6. Open the Vercel URL and test registration, sign-in, reminder CRUD, filters/search, and AI draft flow (if the API key is configured).

## 4. Smoke-test checklist

- [ ] Health endpoint returns `{"status":"ok"}`.
- [ ] A new user can register and sign in.
- [ ] A user can create, view, edit, complete and delete their own reminder.
- [ ] A user cannot view or modify another user's reminder.
- [ ] Past reminder times are rejected.
- [ ] AI asks a question when the date/time is missing or ambiguous.
- [ ] AI creates a draft but does not save it until the user presses **Save reminder**.
- [ ] Refreshing the page keeps a valid session; signing out clears it.
- [ ] Mobile layout is usable.

## 5. Before announcing the app

- [ ] Use a production-appropriate Django secret and verify no secrets are in Git history.
- [ ] Confirm database backups and provider limits.
- [ ] Confirm CORS contains only the production frontend origin.
- [ ] Review privacy policy, terms, and account/data deletion expectations.
- [ ] Test on mobile and desktop using the deployed URLs.
- [ ] Confirm whether the app is a preview or the final public domain.

## Current MVP limitations

- No recurring reminder scheduler or guaranteed push/email notifications yet.
- AI drafting requires an OpenAI API key and a configured model.
- Browser-side JWT storage is a launch MVP compromise; use a secure HttpOnly-cookie backend-for-frontend before broad production use.
- Render free instances may sleep; this is not suitable for guaranteed time-sensitive notification delivery.
