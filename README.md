# Vision AI v2.7.2

> Production-grade, free-tier-first multi-modal AI assistant with RAG, GPU Boost, real-time web search, diagram generation, and manual PKR payments.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![Version](https://img.shields.io/badge/version-2.7.2-brightgreen)](VERSION)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)

**Live App:** [`https://vision-ai-v2-production.up.railway.app`](https://vision-ai-v2-production.up.railway.app)  
**GitHub:** [`https://github.com/admilucky1-cyber/Vision-AI-v2`](https://github.com/admilucky1-cyber/Vision-AI-v2)

---

## Features

| Area | Capability |
|------|------------|
| Chat | Multi-LLM cascade (Groq → Gemini → OpenRouter → DeepSeek) |
| Documents | PDF OCR, exam step-by-step solve, RAG notes |
| Images | Colab GPU (SDXL-turbo) + HF + Pollinations fallback |
| Vision Q&A | Upload image + ask |
| YouTube | Transcript, summary, quiz, **server download** (working links) |
| Voice | STT mic (HTTPS/localhost) + Speak TTS |
| Prompt Studio | Master prompts by category |
| Plans | Pakistan-friendly manual payments UI |
| Boost | Colab one-click GPU worker + auto-register |
| RAG | MiniLM re-ranker on long PDF/notes context |
| Local LLM | Optional Qwen on Colab for complex reasoning |
| UI | Mobile-safe top bar, modern chat bubbles, glass composer |

---

## Quick start

```bash
python -m venv venv
# Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # set SECRET_KEY + at least one LLM key
python main.py
# http://localhost:5050
```

---

## Deploy

- **GitHub** → push (never commit `.env` / `cookies.txt`)
- **Railway** → Dockerfile builder + env vars
- **Colab** → run `colab_one_click_boost.py` with Secrets (`NGROK_TOKEN`, `HF_TOKEN`, `GROQ_API_KEY`, `WORKER_SECRET`, `MAIN_APP_URL`)

See `READY.md`, `MONETIZE.md`, `QUICKSTART.md`, `DEPLOY.md`, `GITHUB.md`, `OAUTH_GOOGLE.md`, `COLAB_DRIVE_CACHE.md`.

---

## Image generation tips

1. Keep Colab Boost tab open until health shows `"warmed": true`
2. Match `WORKER_SECRET` on Railway and Colab
3. Prompt example: `Create a photorealistic image of a grand mosque with dome and minarets at golden hour`
4. First image after cold start may take 1–2 minutes

---

## Google OAuth

Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and:

```env
GOOGLE_REDIRECT_URI=https://vision-ai-v2-production.up.railway.app/auth/google/callback
APP_BASE_URL=https://vision-ai-v2-production.up.railway.app
```

Redirect URI in Google Cloud Console must match **exactly**. Details: [`OAUTH_GOOGLE.md`](OAUTH_GOOGLE.md)

---

## Versions

| Version | Status | Notes |
|---------|--------|-------|
| **2.7.2** | current | Mobile overlay fix, responsive chips/buttons, chat UI refresh, free-tier bar |
| 2.7.2 | prior | Mobile layout, extended chat timeouts, Colab secrets stability, OAuth harden |
| 2.7.2 | prior | GPU-first images, unified version, production FINAL baseline |
| 2.5.5 | prior | Full version bump, photography regex, fast chat |
| 2.5.4 | prior | Mic header, speed, exam PDF, settings |
| 2.5.3 | prior | Image routing for photography / architecture |
| 2.5.2 | prior | UI layout, secrets, image size/quality |
| 2.5.1 | prior | Medical anatomy, Colab secrets, UI polish |
| 2.5.0 | prior | CUDA, RunPod, usage dashboard |
| 2.4.9 | prior | Medical education, About, download chat |
| 2.4.8 | prior | UI polish & chat quality |
| 2.4.7 | prior | Strict images + Kaggle Boost |
| 2.4.6 | prior | Free-first & stability |
| 2.4.5 | prior | Storage fix & upgrade layout |
| 2.4.4 | prior | Mic, languages, payment QR |
| 2.4.3 | prior | Better educational diagrams |
| 2.4.2 | prior | Fast images & Boost fixes |
| 2.4.1 | prior | GPU Boost & Regenerative UI |
| 2.4.0 | prior | Permanent Free Setup |

Full registry: [`versions.json`](versions.json) · In-app: `/versions`

---

## License

MIT — see [LICENSE](LICENSE)
