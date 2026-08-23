# Vision AI v5.1.1 — Regenerative

> Production-grade multi-modal AI assistant with document RAG, real-time search, diagram & image generation, medical/anatomy educational mode, QR code PKR payments, Telegram/WhatsApp alerts, and One-Click Colab/Kaggle GPU Boost.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Version](https://img.shields.io/badge/version-5.1.1-brightgreen)](VERSION)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)
[![Deploy](https://img.shields.io/badge/Deploy-Railway-0B0D0E?logo=railway)](https://vision-ai-v2-production.up.railway.app)

**Live**: [vision-ai-v2-production.up.railway.app](https://vision-ai-v2-production.up.railway.app)

---

## Highlights

| Area | Capability |
|------|------------|
| **AI Cascade** | Groq → Gemini Flash → OpenRouter `:free` (free-first failover) |
| **RAG** | PDFs, images, Office docs · ChromaDB semantic search |
| **Generation** | Diagrams, educational anatomy, HF Inference, Colab GPU worker |
| **Search** | Tavily / DuckDuckGo / Wikipedia real-time |
| **Auth** | JWT + Google OAuth |
| **Payments** | Manual PKR (Easypaisa / bank) · QR codes · pending → owner approve |
| **Alerts** | Telegram (primary), ntfy.sh, CallMeBot WhatsApp |
| **UI** | Nature / regenerative forest-green theme (light + dark) |
| **Speech** | Mic STT + Speak TTS · multi-language (Urdu, English, Arabic, Hindi, …) |
| **Architecture** | Container / Widget pattern (web + Flutter clients) · ChatShell / Composer / MessageBubble |
| **Keep-alive** | Free-tier 24/7 friendly |

---

## Architecture (v5.x)

- **Backend** — FastAPI · routes · services · untouched core API
- **Web frontend** — Container/Widget scaffold (`containers/`, `widgets/`, `tokens.css`, VisionAuth, sidebar ≥900)
- **Flutter client** — ChatShell / Composer / MessageBubble · auth · studio · settings · rail ≥900
- **GPU Boost** — One-click Colab / Kaggle worker · ngrok · `/api/workers`

See project zips and course notes for Flutter v5.2.0 and web v5.1.x builds.

---

## GPU Boost (Colab)

**One manual step required** (Google auth): open Colab → Run.

- In-app: `/boost` (header **Boost** / **GPU On**)
- Use Colab Secret `NGROK_TOKEN` on first run of a fresh session
- Session timeout → Re-Boost (new VMs wipe `/content/.vision_boost.env`)
- Chat continues on free Groq / Gemini / OpenRouter while GPU is offline

One-click cell: `colab_one_click_boost.py`

---

## Quick Start

```bash
git clone https://github.com/admilucky1-cyber/Vision-AI-v2.git
cd Vision-AI-v2
cp .env.example .env   # add free API keys + optional TELEGRAM_*
pip install -r requirements.txt
python main.py
```

Open http://localhost:5050

### Docker
```bash
docker compose up --build
```

### Free hosts
| Host | Config | Notes |
|------|--------|-------|
| **Railway** | `railway.toml` | Free tier limits apply |
| **Render** | `render.yaml` | Free web service may sleep |
| **Docker** | `Dockerfile` | Any free container host |
| **Local** | `main.py` | Best for mic testing |

See [DEPLOY.md](DEPLOY.md) · [FREE_STACK.md](FREE_STACK.md) · [PROJECT_STATUS.md](PROJECT_STATUS.md)

---

## Environment (essentials)

```env
# Free AI (use several for failover)
GROQ_API_KEY=
GOOGLE_API_KEY=
OPENROUTER_API_KEY=
HF_TOKEN=

# GPU worker
COLAB_WORKER_SECRET=vision-colab-secret

# Owner notify
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Manual PKR
EASYPAISA_NUMBER=
BANK_IBAN=
PRO_PRICE_PKR=1499
```

Full list: [`.env.example`](.env.example)

---

## Admin

- Payment requests: `/frontend/admin/payments.html`
- Approve: `POST /upgrade/admin/payment-review`

---

## Version History

| Version | Status | Notes |
|---------|--------|-------|
| **5.1.1** | Current | Railway fix · web Container/Widget |
| 5.1.0 | Stable | Web tokens.css · VisionAuth · sidebar 900/901 |
| 5.0.x | Stable | Flutter + web Container/Widget architecture |
| 2.4.9 | Archived line | Regenerative theme baseline |

Full registry: [`versions.json`](versions.json) · in-app `/versions`

---

## License

MIT — see [LICENSE](LICENSE)

---

**Built for free-tier production.** Regenerative · reliable · ready.
