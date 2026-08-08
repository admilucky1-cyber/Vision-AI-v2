# Vision AI v2.6.1

Production multi-modal AI assistant — **free-tier first** (Railway + Colab GPU + OpenRouter/Groq/Gemini + HF).

**Current version:** `2.6.1`  
**Status:** Production FINAL

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

## Quick start

```bash
python -m venv venv
# Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # set SECRET_KEY + at least one LLM key
python main.py
# http://localhost:5050
```

## Deploy

- **GitHub** → push (never commit `.env` / `cookies.txt`)
- **Railway** → Dockerfile builder + env vars
- **Colab** → run `colab_one_click_boost.py` with Secrets (NGROK_TOKEN, HF_TOKEN, GROQ_API_KEY, WORKER_SECRET, MAIN_APP_URL)

See `QUICKSTART.md`, `DEPLOY.md`, `GITHUB.md`.

## Image generation tips

1. Keep Colab Boost tab open until health shows `"warmed": true`
2. Match `WORKER_SECRET` on Railway and Colab
3. Prompt example: `Create a photorealistic image of a grand mosque with dome and minarets at golden hour`
4. First image after cold start may take 1–2 minutes

## Version history

See `CHANGELOG.md` and `versions.json`.

## License

MIT — see `LICENSE`
