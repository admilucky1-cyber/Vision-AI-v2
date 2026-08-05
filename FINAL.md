# Vision AI v2.0 — Final ship notes (2026-07-31)

## Run locally
```bash
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
pip install -U yt-dlp ddgs
cp .env.example .env
# Set SECRET_KEY + GOOGLE_API_KEY or GROQ_API_KEY
# Optional: cookies.txt + YTDLP_COOKIES=cookies.txt
# Optional Windows: FFMPEG_LOCATION=path\to\ffmpeg.exe
python main.py
# http://localhost:5050
```

## Features included
- Multi-LLM chat (Gemini / Groq / DeepSeek / OpenRouter free)
- YouTube: transcript, **direct CDN download links** (IDM/FDM/browser), server fallback
- Document Q&A (PDF etc.), web search, diagrams
- Auth (JWT + optional Google OAuth)
- Plans + Pakistan Easypaisa/bank payment requests
- Voice input/output (browser; needs HTTPS or localhost)
- Image upload + Q&A
- Docker / Railway / GitHub deploy files

## YouTube if blocked
1. Export Netscape cookies.txt (tabs) — never paste in chat
2. YTDLP_COOKIES=cookies.txt
3. Restart; check /upload/health

## Deploy
See DEPLOY.md → GitHub → Railway (Dockerfile) → Docker Compose

## Do not commit
.env, cookies.txt, data/users.json, downloads/*

## Production fixes (2026-07-31 evening)

### Images
- Local OCR (tesseract) always tried first
- Gemini vision when GOOGLE_API_KEY is set
- HF BLIP caption when HF_TOKEN is set
- Model instructed to use OCR/caption context (no false "cannot analyze")

### PDF exams
- Lower text threshold; stronger OCR path (pdf2image + tesseract)
- Clear install hint if scan has no text layer

### Microphone UI
- Toasts centered at top (not sidebar)
- Short permission messages; requires localhost or HTTPS

### Required system packages for full media
- tesseract-ocr, poppler-utils (Dockerfile includes these)
- Windows: install Tesseract OCR and add to PATH
