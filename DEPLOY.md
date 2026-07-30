# Vision AI v2.0 — Free / Low-cost Deployment

## 1. Local (Windows / Mac / Linux)

```bash
cd VISION_AI_V2_PRODUCTION
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set SECRET_KEY, GEMINI_API_KEY, etc.
# Optional: FFMPEG_LOCATION, YTDLP_COOKIES, TAVILY_API_KEY
python main.py
# → http://localhost:5050
```

Install system tools:
- **ffmpeg** (required for MP3 / merged MP4)
- **yt-dlp**: `pip install -U yt-dlp`
- **ddgs**: `pip install -U ddgs` (free web search)

---

## 2. Docker (recommended production shape)

```bash
cp .env.example .env   # fill secrets
docker compose up --build -d
# → http://localhost:5050
```

Health: `curl http://localhost:5050/health`

Volumes persist: `data/`, `chroma_db/`, `uploads/`, `downloads/`, `logs/`.

---

## 3. Free / cheap cloud options

### Railway (easy)
1. Push this folder to GitHub
2. [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add variables from `.env`
4. Set start command:
   `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Free trial credit; paid after trial (not lifetime free)

### Render
1. [render.com](https://render.com) → Web Service → connect repo
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Free tier sleeps after idle

### Fly.io
```bash
fly launch
fly secrets set SECRET_KEY=... GEMINI_API_KEY=...
fly deploy
```

### Cloudflare Tunnel (keep server at home — true free public URL)
```bash
# Run Vision AI on your PC
python main.py
# Install cloudflared, then:
cloudflared tunnel --url http://localhost:5050
```
Gives a public `https://….trycloudflare.com` URL with no VPS cost.

### Oracle Cloud Free Tier / Google Cloud free VM
- Always-free VM → install Docker → `docker compose up -d`
- Closest to **lifetime free** self-hosting if you manage the VM

---

## 4. Important production notes

| Item | Notes |
|------|--------|
| YouTube downloads | Need **ffmpeg** in the image (Dockerfile already includes it) |
| Large videos | Prefer server with enough disk; clean `/downloads` periodically |
| Secrets | Never commit `.env` |
| Cookies | For restricted YT: mount `cookies.txt` or set `YTDLP_COOKIES` |
| Workers | `WEB_WORKERS=2` default; lower on small free tiers |

---

## 5. Quick checklist before go-live

- [ ] `SECRET_KEY` set (long random string)
- [ ] At least one LLM key (`GEMINI_API_KEY` / Groq / DeepSeek)
- [ ] `/health` returns 200
- [ ] `/upload/health` shows `ytdlp_available` + ffmpeg
- [ ] Login works; upgrade/payment flow tested if used
- [ ] Hard-refresh frontend (`Ctrl+Shift+R`) after deploy

---

*Vision AI v2.0 — production package*
