# Vision AI v2.4.2 — Regenerative

> Production-grade multi-modal AI assistant with document RAG, diagram generation, real-time search, and manual PKR payments.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![Version](https://img.shields.io/badge/version-2.4.2-brightgreen)](VERSION)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)

---

## GPU Boost (Colab)

**GPU Boost requires one manual step:** open Colab and click **Run**.  
This is due to Google’s authentication requirements. Once run, all traffic is automatically routed through your GPU worker via `/api/workers`.

- In-app page: `/boost` (header **Boost** / **GPU On**)
- **Ngrok token is required on first run of a fresh Colab session.**
- If the Colab session times out, copy your ngrok token, then use **Re-Boost** (new VMs wipe `/content/.vision_boost.env`)
- Chat keeps working on Groq/Gemini/OpenRouter keys while GPU is offline


## Features

- **Multi-provider AI** — Groq, Gemini, DeepSeek, OpenRouter (free-tier friendly)
- **Agentic RAG** — Upload PDFs, images, Office docs; semantic search via ChromaDB
- **Diagrams & images** — Plotly / Matplotlib / Hugging Face FLUX
- **Real-time web search** — Tavily / DuckDuckGo / Wikipedia
- **JWT + Google OAuth** — Secure auth
- **Manual payments (PKR)** — Easypaisa / bank → pending → owner approves
- **Owner notify** — Telegram (recommended), ntfy.sh, optional CallMeBot WhatsApp
- **Nature / regenerative theme** — Forest green UI (light + dark)
- **Speech** — Mic STT + Speak TTS with multi-language detection (Urdu, Hindi, etc.)

---

## Versions

| Version | Tag | Branch | Status | Entry |
|---------|-----|--------|--------|-------|
| **2.1.0** (current) | `v2.1.0` | `main` | stable | `main.py` |
| 2.0.2 | `v2.0.2` | `version/2.0` | archived | `main.py` |
| 2.0.0 | `v2.0.0` | `version/2.0` | archived | `main.py` |

Full registry: [`versions.json`](versions.json)  
In-app list: open `/versions` or `frontend/versions.html` after starting the server.

Each version keeps its own `main.py` entry point so you can checkout a tag/branch and run that release independently.

---

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/vision-ai.git
cd vision-ai
cp .env.example .env   # add API keys + TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
pip install -r requirements.txt
python main.py
```

Open http://localhost:5050

### Docker

```bash
docker compose up --build
```

### Free hosts (no credit card)

| Host | Config | Notes |
|------|--------|-------|
| **Railway** | `railway.toml` | Free tier limits apply |
| **Render** | `render.yaml` | Free web service may sleep |
| **Docker** | `Dockerfile` | Any free container host |
| **Local** | `main.py` | Best for testing mic (localhost) |

See [DEPLOY.md](DEPLOY.md) and [PROJECT_STATUS.md](PROJECT_STATUS.md).

---

## Environment (payment + Telegram)

```env
# AI (at least one)
GROQ_API_KEY=
GOOGLE_API_KEY=
OPENROUTER_API_KEY=

# Owner notify when user submits payment (pick one)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
# or
NTFY_TOPIC=

# Manual PKR payment details
EASYPAISA_NUMBER=
BANK_IBAN=
PRO_PRICE_PKR=1499
```

Full list: [`.env.example`](.env.example)

---

## Admin

- Payment requests: `/frontend/admin/payments.html`
- Approve API: `POST /upgrade/admin/payment-review`

---

## License

MIT — see [LICENSE](LICENSE)
