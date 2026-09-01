# Vision AI

**Production multi-modal AI workspace** — chat, private RAG, routing profiles, GPU boost, and Aether-ready UI.

> **Product name:** Vision AI  
> **This repository** (`Vision-AI-v2`) contains the **full application source** (`main.py`, `routes/`, `services/`, `frontend/`, …).

**Rename tip (recommended):**  
On GitHub → **Settings** → **General** → **Repository name** → change `Vision-AI-v2` → `Vision-AI`  
(If a new empty `Vision-AI` repo exists, delete that empty one first, then rename this repo.)

---

## Quick start

```bash
git clone https://github.com/admilucky1-cyber/Vision-AI-v2.git
cd Vision-AI-v2
cp .env.example .env   # add API keys
pip install -r requirements.txt
python run.py
# or: python main.py
```

Open **http://127.0.0.1:5050**

## Layout

| Path | Role |
|------|------|
| `main.py` | FastAPI app entry |
| `run.py` | Production launcher |
| `routes/` | HTTP API |
| `services/` | LLM, RAG, search, workers |
| `frontend/` | Web UI |

## Deploy

- Railway / Render / Docker — see `DEPLOY.md`, `Dockerfile`, `railway.toml`

## License

MIT
