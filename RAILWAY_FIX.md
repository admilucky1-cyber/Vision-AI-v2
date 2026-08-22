# Railway deploy fix (5.1.1)

## Error you saw
```
python: can't open file '/app/run.py': [Errno 2] No such file or directory
Healthcheck failed — 1/1 replicas never became healthy
```

## Cause
Build **succeeded**. Start command in Railway UI was `python run.py`, but older packages had **no** `run.py` (entry is `main.py` / `uvicorn main:app`).

## Fix (pick one)

### A — Recommended (use Dockerfile CMD)
Railway → Service → **Settings** → **Deploy** → **Custom Start Command** → **clear / leave empty** → Redeploy.

Dockerfile already runs:
```bash
uvicorn main:app --host 0.0.0.0 --port ${PORT:-5050} --workers ${WEB_WORKERS:-2} --proxy-headers --forwarded-allow-ips=*
```

### B — Keep `python run.py`
This package includes `run.py`. Push/redeploy so `/app/run.py` exists, then Start Command:
```bash
python run.py
```

### C — Explicit uvicorn
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1 --proxy-headers --forwarded-allow-ips=*
```

## After fix
1. Redeploy  
2. Open `https://YOUR_APP.up.railway.app/health`  
3. Hard-refresh the site  

## Optional env
```
WEB_WORKERS=1
PORT=5050
HOST=0.0.0.0
DEBUG=false
```
