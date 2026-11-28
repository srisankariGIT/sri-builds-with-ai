# MOMent AI

**Your personal motherhood and family assistant.** A calmer place to organise family reminders and everyday responsibilities.

## Current MVP
- Account registration and JWT login
- Private, user-scoped reminders
- Create, list, edit, complete and delete reminders
- Categories, search and ordering
- Responsive Next.js dashboard
- Django REST Framework API with PostgreSQL support
- Health endpoint and automated backend tests

AI natural-language extraction, recurring reminders and push/email notifications are planned follow-up features. They are not represented as working in this MVP yet.

## Project structure
- `backend/`: Django REST Framework API
- `frontend/`: Next.js App Router application
- `docs/`: product and architecture notes

## Local setup

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py test
python manage.py runserver
```
Without database environment variables the backend uses SQLite for local development. For production, set `DATABASE_URL` to a PostgreSQL connection string.

### Frontend
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```
Open http://localhost:3000. The frontend expects the API at http://localhost:8000/api by default.

## Deployment
- Backend: Render, using `backend/render.yaml`; set `DATABASE_URL` and `CORS_ALLOWED_ORIGINS`.
- Database: Neon PostgreSQL; use its pooled or direct connection string with SSL.
- Frontend: Vercel; set the project root to `projects/01-moment-ai/frontend` and configure `NEXT_PUBLIC_API_URL` to the deployed backend API base, ending in `/api`.

## Security notes
Never commit `.env`, API keys, database passwords or production tokens. The browser MVP currently stores the short-lived access token in localStorage; before broad production use, move authentication behind a secure HttpOnly-cookie backend-for-frontend and add refresh-token rotation/rate limiting.
