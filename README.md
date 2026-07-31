I see you have a **merge conflict** in your `README.md` between two branches (`HEAD` and `origin/main`).  
Here is the **fully resolved, merged, and updated `README.md`** — combining your **Vision AI v2.0** documentation with the **AI-Lab** branding, while keeping all the accurate features and deployment details intact.

---

## ✅ Final Resolved `README.md` (Merge Completed)

```markdown
# AI-Lab / Vision AI v2.0

> **Production‑grade multi‑modal AI assistant with document processing, diagram generation, and real‑time web search.**  
> *Built as part of the AI-Lab training environment.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)

---

## ✨ Why Vision AI?

Vision AI is an enterprise‑ready AI assistant built for **real‑world productivity**.  
It combines **multi‑model intelligence**, **document‑aware RAG**, **self‑learning capabilities**, and a **beautiful DeepSeek‑style interface** — all wrapped in a secure, scalable FastAPI backend.

Whether you're a developer, educator, or researcher, Vision AI helps you:
- **Upload and query** PDFs, images, Word docs, and Excel files using semantic search.
- **Generate diagrams** on‑the‑fly (charts, physics, UML, network graphs).
- **Search the web** in real time and get up‑to‑date answers.
- **Learn from every interaction** and improve over time.
- **Stay secure** with JWT + Google OAuth2 authentication.

---

## ✨ Core Features

- **Multi‑Provider AI Routing** – Auto‑fallback between Gemini 1.5 Pro, Gemini 1.5 Flash, DeepSeek, Groq, and OpenRouter.
- **Agentic RAG with Vector Store** – Upload PDFs, images, Office docs, and text files. Semantic search via ChromaDB.
- **Diagram & Image Generation** – Google Image Search + Plotly + Matplotlib + Hugging Face FLUX / SD3.5.
- **Self‑Learning Optimizer** – Tracks interaction quality, provider performance, and subject expertise.
- **Real‑Time Web Search** – Live data via Tavily, DuckDuckGo, and Wikipedia with intelligent caching.
- **JWT + Google OAuth2** – Secure authentication, registration, token refresh, and profile management.
- **DeepSeek‑Style UI** – Modern, responsive interface with dark/light/system themes and animated loading states.

---

## 🏗️ Tech Stack

| Backend | Frontend | Data & AI |
|---------|----------|-----------|
| FastAPI | HTML5 / CSS3 / Vanilla JS | ChromaDB |
| Uvicorn | Highlight.js | Sentence‑Transformers |
| Python‑Jose (JWT) | Marked / DOMPurify | Gemini 1.5 Pro |
| Bcrypt | CSS Variables | DeepSeek / Groq / OpenRouter |
| Authlib (Google OAuth) | Responsive Flexbox | Tavily / DuckDuckGo |
| SlowAPI (Rate Limiting) | Toast Notifications | Hugging Face FLUX / SD3.5 |

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/your-username/vision-ai-v2.0.git
cd vision-ai-v2.0
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
```

**Windows:**
```bash
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy the example file and edit it with your API keys:
```bash
cp .env.example .env
```
**Required keys:**

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | JWT secret (change in production) |
| `GOOGLE_API_KEY` | Gemini API key |
| `GROQ_API_KEY` | Groq API key |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `TAVILY_API_KEY` | Tavily search API key |
| `HF_TOKEN` | Hugging Face token (image gen) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (optional) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret (optional) |

### 5. Run the application
```bash
python main.py
```

Open your browser and go to:
```
http://localhost:5050
```

---

## 📂 Project Structure

```
vision-ai-v2.0/
├── frontend/               # Static HTML/CSS/JS
├── routes/                 # FastAPI route handlers
│   ├── chat.py
│   ├── login.py
│   ├── upgrade.py
│   └── upload.py
├── services/               # Business logic & AI modules
│   ├── llm.py              # AI provider router
│   ├── image_gen.py        # Multi-model HF generator
│   ├── vector_store.py     # ChromaDB + embeddings
│   └── self_optimizer.py   # Learning engine
├── data/                   # Persistent JSON state (search cache, learning DB)
├── uploads/ / downloads/ / logs/ / cache/
├── main.py                 # FastAPI entry point
├── .env.example            # Template for environment variables
├── .env                    # Local secrets (do not commit)
├── requirements.txt
├── CHANGELOG.md
├── FIX_REPORT.md
└── README.md
```

---

## 📌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Authenticate and receive JWT tokens |
| `/auth/register` | POST | Register a new user |
| `/auth/me` | GET | Get current user profile |
| `/auth/google` | GET | Redirect to Google OAuth |
| `/chat/send` | POST | Send a message with optional file uploads |
| `/chat/clear-cache` | POST | Clear the RAG vector cache |
| `/upgrade/plans` | GET | List available subscription plans |
| `/upgrade/upgrade` | POST | Upgrade to a new plan |

---

## 🌐 Deployment (Render)

1. Push your code to GitHub.
2. Go to [render.com](https://render.com) → **New Web Service** → connect your repo.
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 8000`
4. Add all `.env` variables in the Render dashboard.
5. Click **Create Web Service** – your app will be live in minutes.

> ⚠️ **Note:** Render is stateless. For persistent logs and vector embeddings, use a cloud database (Supabase, Pinecone) or Render’s Disk add‑on.

---

## 🏭 Production

See **[PRODUCTION.md](PRODUCTION.md)** for Docker, Render, secrets, and checklist.

```bash
# Quick production container
cp .env.example .env   # set SECRET_KEY + API keys + DEBUG=false
docker compose up -d --build
```

Bootstrap admin (optional) via `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `.env`.

## 🔐 First user

No default passwords are shipped. Register at `/login.html` or set:

- `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `.env` (created on first start)

---

## 📄 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Google Gemini](https://ai.google.dev/)
- [DeepSeek](https://deepseek.com/)
- [Groq](https://groq.com/)
- [OpenRouter](https://openrouter.ai/)
- [Tavily](https://tavily.com/)
- [Hugging Face](https://huggingface.co/)
- [ChromaDB](https://www.trychroma.com/)
- [FastAPI](https://fastapi.tiangolo.com/)

---

**Made with ❤️ by the Vision AI Team / AI-Lab**
```

---

### ✅ What I Resolved

| Conflict | Resolution |
|----------|------------|
| `# Vision AI v2.0` vs `# AI-Lab` | Merged: **`AI-Lab / Vision AI v2.0`** |
| `README` content vs `AI-Lab` placeholder | Kept all **Vision AI v2.0** details, added **AI-Lab** branding |
| `origin/main` vs `HEAD` | Fully merged — no data loss |

---

### 🚀 Next Steps

1. **Replace** your local `README.md` with this final version.
2. **Commit** the change:
   ```bash
   git add README.md
   git commit -m "Resolve README merge conflict, finalize AI-Lab branding"
   ```
3. **Push** to GitHub:
   ```bash
   git push
   ```

**Your `README.md` is now clean, accurate, and ready for deployment.** 🚀