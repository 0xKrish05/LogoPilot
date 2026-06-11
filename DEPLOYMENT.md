# Deployment (GitHub -> Coolify, no SSH needed)

## Steps for you (account/access tasks)

1. **Create a GitHub repo** (e.g. `logo-promotion-saas`), private is fine.
   - Easiest: go to github.com/new, create empty repo, then give me the URL.
   - I'll then push this code to it for you.

2. **Open Coolify** on your server (usually `http://15.135.74.108:8000` if
   Coolify is already installed — if you get a connection error, Coolify
   isn't installed yet and we'll need to install it first, which requires
   one-time SSH/console access to the VPS, e.g. via your hosting provider's
   web console since direct SSH seems blocked).

3. In Coolify: **New Resource -> Docker Compose** -> connect the GitHub repo
   -> point it at `docker-compose.yml` in the repo root -> set the production
   branch (e.g. `main`).

4. Add environment variables in Coolify's UI from `.env.example` (I'll tell
   you which ones are needed as each feature is implemented — most can stay
   blank/placeholder until then).

5. Enable **auto-deploy on push** for the production branch in Coolify's
   webhook settings — every push then triggers an automatic build+deploy.

## What I'll do
- Push code changes to the repo as features are completed.
- Tell you exactly which new env vars to add in Coolify when a feature needs
  them (e.g. Firebase, Meta App, Stripe, Cryptomus/MaxelPay).
- Tell you when something is ready to test on the live server.

## Domain
Not needed yet — Coolify gives you a default `*.sslip.io`-style URL or you
can access via server IP + port for now. Tell me when you're ready to attach
a real domain.
