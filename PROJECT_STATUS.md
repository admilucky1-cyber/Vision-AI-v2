# Vision AI v2.0 — Project Status (Regenerative Theme Update)

**Updated:** 2026-08-02

## Theme
- Applied **Regenerative / Nature (permaculture-inspired)** green theme across CSS variables (light + dark).
- Primary: forest green `#2d6a3e` / leaf `#3d8b4f`, soft gold accent, soft leaf backgrounds.
- Matches the spirit of the Regenerative Leadership Institute screenshot (greens, natural, sustainable feel) while remaining a full AI chat product.

## Payment system (fixed)
- Clicking **Upgrade** on a paid plan no longer pretends payment succeeded.
- Flow: user pays via Easypaisa/Bank → submits Txn ID → UI shows **“Waiting for payment confirmation”**.
- Backend status stays `pending` until **admin approves** in `/frontend/admin/payments.html` (or API `/upgrade/admin/payment-review`).
- **Owner notify: Telegram (recommended) + ntfy.sh + optional CallMeBot WhatsApp
  - `PAYMENT_WHATSAPP=923xxxxxxxxx` (your number, country code, no +)
  - `CALLMEBOT_APIKEY=...` (free CallMeBot — see `.env.example`)
- Also writes in-app admin notification + optional `PAYMENT_WEBHOOK_URL`.

## What works on free / no-credit-card hosts

| Target | Works? | Notes |
|--------|--------|-------|
| **GitHub** | Yes | Push repo; use Actions only if you want CI |
| **Docker** | Yes | `Dockerfile` + `docker-compose.yml` included |
| **Railway** | Yes | `railway.toml` + free tier (limits apply) |
| **Render** | Yes | `render.yaml` (free web service sleeps) |
| **Cloudflare Pages/Workers** | Partial | Frontend static can go to Pages; FastAPI needs a worker/container or external backend (Pages is static only) |
| **Fly.io / others** | Yes | Any Docker-capable free tier |

**Required for real AI:** free API keys (Groq, Gemini, OpenRouter free models). No paid Stripe required for manual Easypaisa/bank flow.

## Mic (browser blocked)
- Web Speech API **requires secure context**: `https://` or `http://localhost`.
- On `http://192.168.x.x` or plain HTTP remote host → browser blocks mic. Message already explains: allow mic in site settings + use HTTPS/localhost.
- Cannot be fixed in code alone — host with HTTPS (Railway/Render/Caddy/Cloudflare tunnel).

## Speak / TTS (Urdu + all languages)
- Detects script (Urdu/Arabic, Hindi, Chinese, Japanese, Korean, Cyrillic, etc.).
- Uses browser `speechSynthesis` voices. **Quality depends on the device OS language packs.**
- If Urdu voice missing: install Urdu language pack on phone/PC (Chrome settings / Windows language / Android TTS).
- Chat itself answers in any language the model supports (Gemini/Groq/OpenRouter handle Urdu well).

## Chat “do anything”
- Multi-provider failover (Groq → Gemini → OpenRouter free → DeepSeek).
- RAG uploads, web search, YouTube tools — all present.
- Quality ≈ free-tier models (strong for most tasks; not identical to GPT-4o / Claude / Grok paid every time).

## Image generation
- Engines: Google image search, Plotly/Matplotlib diagrams, Hugging Face FLUX/SD (needs `HF_TOKEN`).
- Free HF has rate limits / queues — results can be good but not guaranteed “ChatGPT/Gemini quality every prompt”.
- Diagrams/charts work offline without keys.

## Deploy quick
```bash
cp .env.example .env   # fill keys + PAYMENT_WHATSAPP + CALLMEBOT_APIKEY
pip install -r requirements.txt
python main.py
# or: docker compose up
```

Admin payment panel: `/frontend/admin/payments.html` (login as admin).
