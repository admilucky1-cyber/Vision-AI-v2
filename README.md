# Vision AI v2.0

Production multi-modal AI assistant (FastAPI + vanilla JS).

## Features

- Multi-LLM chat (Gemini / DeepSeek / Groq)
- YouTube transcript + download (MP3 / MP4 / quality selection)
- Document upload & Q&A (PDF, etc.)
- Free web search fallbacks (`ddgs`, Wikipedia, Open-Meteo weather)
- Dark / light glass UI
- Auth, settings, upgrade plans

## Quick start

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # set SECRET_KEY + AI keys
python main.py
# http://localhost:5050
```

Optional:

```bash
pip install -U yt-dlp ddgs
# ffmpeg on PATH (or FFMPEG_LOCATION in .env)
```

## Docker

```bash
cp .env.example .env
docker compose up --build -d
```

## Deploy

See [DEPLOY.md](DEPLOY.md) for Railway, Render, Fly.io, Cloudflare Tunnel, and free VMs.

## License

See [LICENSE](LICENSE).
