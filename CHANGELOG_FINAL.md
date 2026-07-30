# Vision AI v2.0 — Final package notes (2026-07-31)

## Working features (verified in testing)
- YouTube **MP3** server download
- YouTube **1080p MP4** server merge download
- Direct CDN links for quick browser/IDM use (with quality gate)
- Free multi-engine web search (`ddgs` + Wikipedia + Open-Meteo weather)
- Pakistani Urdu language matching
- Document Q&A / cheat sheets from uploaded PDFs
- Glass UI, dark/light themes, message actions (copy / height / width / zoom / full)
- Login, settings, upgrade/payment pages

## Deploy
See **DEPLOY.md** for Docker, Railway, Render, Fly.io, Cloudflare Tunnel, and free-tier VMs.

## Required local tools
```text
pip install -U yt-dlp ddgs
# ffmpeg on PATH or FFMPEG_LOCATION in .env
```
