# Vision AI v2.5.5

Production multi-modal AI assistant — **free-tier first** (Railway + Colab + OpenRouter `:free` + HF).

**Current version:** `2.5.5`  
**Entry:** `main.py`  
**License:** MIT

---

## What's new in 2.5.5

| Area | Change |
|------|--------|
| **Chat images** | Larger display (up to ~720×640); no more 150px thumbnails |
| **Medical anatomy prompts** | Clinical framing for anatomy / genitalia education paths |
| **Colab secrets** | Reliable secret load + interactive paste if Notebook access is off; writes `/content/.vision_boost.env` |
| **CUDA / low-VRAM** | CPU offload, attention/VAE slicing, `empty_cache` after gen, `LOW_VRAM=1` |
| **Image quality (GPU)** | Higher default steps (SDXL-turbo 8, FLUX-schnell 6) + 1024×1024 |
| **RunPod** | Optional serverless GPU via `RUNPOD_API_KEY` + `RUNPOD_ENDPOINT_ID` |
| **Usage dashboard** | `/usage` — daily messages, images, estimated $ saved (`data/usage.json`) |
| **Upgrade page** | Payment section wider, QR rows, 2-column form layout |
| **Settings page** | Even card grid, full-width API keys card, tighter professional spacing |
| **Serverless images** | HF Inference → Pollinations → Colab/RunPod cascade |

### 2.5.0 highlights
- Colab worker warmup + streaming chat endpoint  
- Theme-ready static UI, payment QR, manual PKR verification  

---

## Free GPU boost (Colab)

1. Open `/boost` on your deployed app.  
2. Runtime → **GPU (T4)**.  
3. Secrets (exact names) with **Notebook access ON**:
   - `NGROK_TOKEN`, `HF_TOKEN`, `WORKER_SECRET`, `MAIN_APP_URL`
   - Plus at least one of: `GROQ_API_KEY` / `OPENROUTER_API_KEY` / `GOOGLE_API_KEY`
4. Runtime → **Restart runtime**, then run `colab_one_click_boost.py`.  
5. If Secrets still blocked, paste keys when prompted.

Without `HF_TOKEN`, FLUX may fail to download; worker falls back to SDXL-turbo.  
Without a chat API key on the worker, `/worker/chat` returns **503** (main app chat still works via Railway keys).

---

## Features
- Free-first LLM cascade (Groq → Gemini → OpenRouter free → optional Colab/RunPod)
- Agentic RAG (PDF / DOCX / images)
- Diagram & creative image generation
- Web search, YouTube tools
- JWT auth + Google OAuth
- Manual PKR payments (Easypaisa / bank) + admin verification
- Speech (mic STT + Speak TTS)
- Usage analytics at `/usage`

---

## Versions

| Version | Status | Notes |
|---------|--------|-------|
| **2.5.5** | current | Permissions-Policy mic fix, chat speed, full package |
| 2.5.4 | prior | Mic header, speed, exam PDF, settings |
| 2.5.1 | prior | UI layout, secrets, image size/quality |
| 2.5.0 | prior | CUDA, RunPod, usage dashboard |
| 2.4.9 | stable baseline | Production-ready package |

Registry: [`versions.json`](versions.json) · In-app: `/versions`

---

## Quick start

```bash
git clone https://github.com/admilucky1-cyber/Vision-AI-v2.git
cd Vision-AI-v2
cp .env.example .env   # free API keys + optional TELEGRAM_*
pip install -r requirements.txt
python main.py
```

Open http://localhost:5050

### Deploy
| Host | Config |
|------|--------|
| Railway | `railway.toml` |
| Render | `render.yaml` |
| Docker | `Dockerfile` / `docker-compose.yml` |

See [DEPLOY.md](DEPLOY.md), [FREE_STACK.md](FREE_STACK.md), [PROJECT_STATUS.md](PROJECT_STATUS.md).

---

## Env (high level)

```
GOOGLE_API_KEY / GROQ_API_KEY / OPENROUTER_API_KEY / HF_TOKEN
COLAB_WORKER_SECRET / MAIN_APP_URL
RUNPOD_API_KEY / RUNPOD_ENDPOINT_ID   # optional
LOW_VRAM=1                           # Colab default
```

Full list: [`.env.example`](.env.example)

---

## Changelog discipline

Every release updates:
- `VERSION`
- `README.md` (this file)
- `CHANGELOG.md` / `versions.json` when tagging
- Frontend cache-bust query on critical static assets when needed

---

MIT · Vision AI Team
