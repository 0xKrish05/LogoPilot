# Logo Promotion Automation SaaS

Multi-tenant SaaS that takes Instagram reel URLs, applies a user's logo via FFmpeg,
re-uploads to the user's Instagram account, and submits the resulting URL to a
campaign platform (e.g. Clipster) via Playwright automation.

## Stack
- Frontend: Next.js
- Backend API: FastAPI
- DB: PostgreSQL
- Queue/Cache: Redis
- Workers: Celery (filter, download, edit, upload, submit)
- Video: FFmpeg + yt-dlp
- Submission automation: Playwright
- Auth: Firebase (Google Sign-In)
- Deployment: Docker + Coolify + GitHub CI/CD
- Monitoring: Prometheus + Grafana

## Project layout
```
backend/        FastAPI app, Celery workers, Alembic migrations
frontend/       Next.js app (user + admin dashboards)
docker-compose.yml
.env.example    All required environment variables (no secrets committed)
```

## Status
Phase 1 (Foundation) in progress:
- [x] Project scaffold
- [x] Docker Compose (postgres, redis, backend, worker, frontend)
- [x] Core DB models (User, Plan, Subscription, Automation, InstagramAccount, QueueItem)
- [ ] Firebase auth integration
- [ ] Admin-configurable plan/limit system
- [ ] Filter / Schedule / Queue engines
- [ ] FFmpeg editing engine
- [ ] Instagram upload (requires Meta Developer App + App Review)
- [ ] Clipster submission engine (Playwright)
- [ ] Billing (Stripe + Cryptomus/MaxelPay)
- [ ] Admin dashboard

## What I'll need from you, and when
I'll ask for each item with step-by-step instructions right before the relevant
phase starts (not all at once):
- Firebase project credentials (Auth phase)
- Meta Developer App credentials + App Review submission (Instagram upload phase)
- Sample Clipster cookies.txt + walkthrough video (Submission engine phase)
- Stripe + Cryptomus/MaxelPay API keys (Billing phase)
- VPS access / Coolify setup details (Deployment phase)
