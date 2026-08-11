# Vision AI v3.0.3

> Production-grade, free-tier-first multi-modal AI assistant with RAG, GPU Boost, real-time web search, diagram generation, and manual PKR payments.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![Version](https://img.shields.io/badge/version-3.0.3-brightgreen)](VERSION)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)

**Live App:** https://vision-ai-v2-production.up.railway.app  
**GitHub:** https://github.com/admilucky1-cyber/Vision-AI-v2

---

## What is Vision AI?

Vision AI is a browser-based assistant for students and professionals in Pakistan and worldwide. It combines chat, PDF/exam solving, YouTube tools, optional GPU images (Google Colab), and Easypaisa/bank plan upgrades—without requiring a waitlist for guests.

---

## What is new in v3.0.3

- Glassmorphism shell UI and 15 themes (Emerald, Frost, Ember)
- API Vault + Smart Image Router + Skill Market

## What is new in v3.0.3

- **Plans page width:** Full-width responsive grid (5→3→2→1 columns); cards ordered Free → Student → Pro → Team → Enterprise
- **Payment block:** Balanced container width, compact QR, mobile-friendly form
- **Chat chrome:** Removed redundant Image Q&A / PDF / YouTube / Voice chips above the composer (actions remain via attach, mic, Prompts)
- **Header:** Hide duplicate Vision AI brand when the sidebar is open
- **Profile menu:** Settings, Upgrade Plan, Download chat, Log out in one menu
- **Stop control:** Quieter style (not a large solid red block)
- **Chat bubbles:** Improved max-width, padding, and line-height for reading
- **Themes:** Humanly Teal, Default, Nord, Sunset, High Contrast, Soft Sepia (dark + light)
- **Login:** Humanly glass card with Login/Register, Google, guest
- **Prompt Studio:** Wider full-height drawer; cleaner chrome

---

## Features

| Area | Capability |
|------|------------|
| Chat | Multi-LLM cascade (Groq → Gemini → OpenRouter → DeepSeek) |
| Documents | PDF OCR, exam step-by-step, RAG notes |
| Images | Colab GPU (SDXL-turbo) + HF + Pollinations fallback |
| Vision Q&A | Upload image + ask (composer attach) |
| YouTube | Transcript, summary, quiz, server download |
| Voice | STT mic (HTTPS/localhost) + Speak TTS |
| Prompt Studio | Master prompts by category |
| Plans | PKR manual payments (Easypaisa / bank) |
| Boost | Colab one-click GPU worker + auto-register |
| UI | Unified teal glass system, theme presets, mobile-safe layout |

---

## Themes

| Preset | Notes |
|--------|--------|
| **Humanly Teal** | Default — green/teal glass |
| Vision Default | Cyan / violet |
| Nord | Cool blue-gray |
| Sunset | Warm orange |
| High Contrast | Accessibility |
| Soft Sepia | Light, low glare |

Use **Theme** in the chat header or on the Upgrade page. Choice is stored in `localStorage`.

---

## Quick start

```bash
python -m venv venv
# Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # SECRET_KEY + at least one LLM key
python main.py
# http://localhost:5050
```

```bash
pytest tests/ -q
python scripts/smoke_test.py
```

---

## Deploy

1. Push to GitHub (**never** commit `.env` or `cookies.txt`)
2. Railway: Dockerfile + environment variables
3. Colab Boost: `colab_one_click_boost.py` with Secrets  
   (`NGROK_TOKEN`, `HF_TOKEN`, `GROQ_API_KEY`, `WORKER_SECRET`, `MAIN_APP_URL`)

Docs: `DEPLOY.md`, `QUICKSTART.md`, `COLAB_GPU.md`, `DRIVE_MOUNT.md`, `SECURITY.md`, `TROUBLESHOOTING.md`, `MONETIZE.md`

Optional: `ENABLE_DOCS=1` for `/docs` OpenAPI UI.

---

## Image generation tips

1. Keep Colab Boost open until health shows `"warmed": true`
2. Match `WORKER_SECRET` on Railway and Colab
3. Prefer clear prompts (subject, lighting, style)
4. First image after a cold start may take 1–2 minutes

---

## Google OAuth

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://vision-ai-v2-production.up.railway.app/auth/google/callback
APP_BASE_URL=https://vision-ai-v2-production.up.railway.app
```

Redirect URI in Google Cloud Console must match **exactly**.

---

## Versions

| Version | Notes |
|---------|--------|
| **3.0.3** | Plans width, chat chrome, profile menu, README, stop/composer polish |
| 2.8.8 | Plans sort/size, payment responsive, themes on upgrade |
| 2.8.7 | Login redesign, sidebar profile |
| 2.8.6 | Unified UI, Prompt Studio, contrast |
| 2.8.5 | Humanly Teal + theme picker |
| 2.8.4 | Critical index.js hotfix (chat/buttons) |
| 2.8.0–2.8.3 | Graphs, tests, CI, mobile, OpenAPI |

---

## License

MIT — see [LICENSE](LICENSE)
