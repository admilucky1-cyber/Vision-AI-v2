# Vision AI v2.6.0 — FINAL package

This archive is the production-complete build.

## Includes
- Full FastAPI app (`main.py`, `routes/`, `services/`)
- Frontend (chat, login, settings, upgrade, admin)
- Colab GPU worker (`colab_worker_server.py`, `colab_one_click_boost.py`)
- Docker / Railway / Procfile / Caddy
- Docs: README, QUICKSTART, DEPLOY, GITHUB, CHANGELOG, versions.json

## Version
Single source: file `VERSION` → `APP_VERSION` in `main.py`.

## After unzip
1. Copy `.env.example` → `.env` and set keys
2. `pip install -r requirements.txt`
3. `python main.py`
4. Deploy: push GitHub → Railway (Dockerfile)
5. Optional GPU: run Colab boost with Secrets

## Image gen
Wait for worker `warmed: true`, then request images. GPU is preferred over serverless.
