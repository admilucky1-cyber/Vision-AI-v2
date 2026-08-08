# Vision AI — Security notes (v2.7.3)

## Fixed / enforced
- JWT auth with optional **guest** mode (`ALLOW_GUEST=1`) for public use without login wall
- Rate limits on chat / login
- Plan message quotas (stricter for guests)
- Security headers: nosniff, frame deny, HSTS, XSS, referrer
- Upload size limits; path-safe downloads
- Never commit `.env` or `cookies.txt`

## Operator checklist
1. Set a long random `SECRET_KEY` in production
2. Set `CORS_ORIGINS` / `ALLOWED_HOSTS` to your domain
3. `ALLOW_GUEST=1` for public try-without-login; `0` to force accounts
4. Keep admin password strong; empty `ADMIN_PASSWORD` = no weak default
5. Rotate Google OAuth secrets if leaked
6. Review Railway logs for 401/402 spikes

## Known free-tier limits (not bugs)
- LLM provider rate limits
- Colab GPU only while Boost tab is open
- Guest usage is best-effort (IP-ish username); accounts track better
