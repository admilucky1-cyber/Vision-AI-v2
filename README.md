# Vision AI v2.4.6 — Regenerative
> Production-grade multi-modal AI assistant with document RAG, diagram generation, real-time search, and manual PKR payments.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![Version](https://img.shields.io/badge/version-2.4.6-brightgreen)](VERSION)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)

---

## GPU Boost (Colab)
**GPU Boost requires one manual step:** open Colab and click **Run**.  
This is due to Google’s authentication requirements. Once run, traffic can route through your GPU worker via `/api/workers`.

- In-app: `/boost` (header **Boost** / **GPU On**)
- **Ngrok token** required on first run of a fresh Colab session (use Colab Secret `NGROK_TOKEN`)
- Session timeout → Re-Boost (new VMs wipe `/content/.vision_boost.env`)
- Chat keeps working on Groq / Gemini / OpenRouter free keys while GPU is offline

One-click cell: `colab_one_click_boost.py` (see `/boost` page).

---

## Features
- **Free-first multi-provider AI** — Groq → Gemini Flash → OpenRouter `:free` cascade (see `FREE_STACK.md`)
- **Agentic RAG** — PDFs, images, Office docs; ChromaDB semantic search
- **Diagrams & images** — Colab GPU worker, HF Inference, educational AI diagrams (not ASCII junk)
- **Real-time web search** — Tavily / DuckDuckGo / Wikipedia
- **JWT + Google OAuth** — Secure auth
- **Manual payments (PKR)** — Easypaisa / bank → pending → owner approves
- **Payment QR codes** — Easypaisa number & IBAN on `/upgrade.html`
- **Owner notify** — Telegram (recommended), ntfy.sh, optional CallMeBot WhatsApp
- **Nature / regenerative theme** — Forest green UI (light + dark)
- **Speech** — Mic STT + Speak TTS; multi-language settings (Urdu, English, Arabic, Hindi, Chinese, French, …)
- **Stable chat history** — localStorage no longer stores huge base64 images (quota-safe)

---

## Versions
| Version | Tag | Branch | Status | Entry |
|---------|-----|--------|--------|-------|
| **2.4.6** (current) | `v2.4.6` | `main` | stable | `main.py` |
| 2.4.5 | `v2.4.5` | `main` | stable | `main.py` |
| 2.4.4 | `v2.4.4` | `main` | stable | `main.py` |
| 2.4.3 | `v2.4.3` | `main` | stable | `main.py` |
| 2.4.2 | `v2.4.2` | `main` | stable | `main.py` |
| 2.4.1 | `v2.4.1` | `main` | stable | `main.py` |
| 2.4.0 | `v2.4.0` | `main` | stable | `main.py` |
| 2.3.3 | `v2.3.3` | `main` | archived | `main.py` |
| 2.1.0 | `v2.1.0` | `version/2.1` | archived | `main.py` |

Full registry: [`versions.json`](versions.json)  
In-app: `/versions` or `frontend/versions.html`

---

## Quick start
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

### Free hosts (no credit card)
| Host | Config | Notes |
|------|--------|-------|
| **Railway** | `railway.toml` | Free tier limits apply |
| **Render** | `render.yaml` | Free web service may sleep |
| **Docker** | `Dockerfile` | Any free container host |
| **Local** | `main.py` | Best for testing mic (localhost) |

See [DEPLOY.md](DEPLOY.md), [FREE_STACK.md](FREE_STACK.md), [PROJECT_STATUS.md](PROJECT_STATUS.md).

---

## Environment (free AI + payments)
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
- Approve API: `POST /upgrade/admin/payment-review`

---

## License
MIT — see [LICENSE](LICENSE)
