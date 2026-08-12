## 3.1.1 — 2026-08-12

- **Package polish:** README + TROUBLESHOOTING for exam PDF; clean `.env.example` (no duplicate OAuth keys; PDF/RAG notes)
- Smoke test covers full-document RAG skip intent
- Dockerfile label v3.1.1; frontend version strings aligned
- Prior 3.1.0: skip top-k RAG on “solve this pdf” so real questions are used

## 3.1.0 — 2026-08-11

- **CRITICAL fix — exam PDF hallucination:** "solve this pdf" no longer runs top-k RAG that collapsed ~50k-char papers to ~12k random chunks (model then invented generic questions).
- Full-document intent (`solve`, `answer all`, question-paper tags) keeps the ordered extract intact (up to ~100k chars) with smart question-body preference.
- System prompt: must quote real question numbers/stems from context; forbid inventing unrelated physics problems.
- Prior: guest JWT (3.0.9), exam extract quality (3.0.8), Colab-only images (3.0.7)

## 3.0.9 — 2026-08-11

- **CRITICAL:** Guest JWT no longer fails with "Could not validate credentials" (guests are not in user_db)
- **Chat reliability:** if Groq/OpenRouter/DeepSeek alone fails, soft-fallback to other free keys
- **Groq:** prefer `llama-3.1-8b-instant` first; better empty/HTTP logging
- Prior: exam PDF full context (3.0.8), Colab-only images (3.0.7), Prompt Studio unfreeze (3.0.6)

## 3.0.8 — 2026-08-11

- **Exam PDF solve:** context no longer truncated to cover page (~16k chars)
- **Smart truncate:** prioritizes pages with Q1/Q2… over front-matter
- **PDF extract:** PyMuPDF + best-of methods; quality gate triggers OCR when extract is cover-only
- **Auto route:** long question papers use Gemini first (1M context)
- **Solve mode:** explicit instruction to work through every question present

## 3.0.7 — 2026-08-11

- **Chat speed:** auto cascade is light/free first (Groq → OpenRouter free → DeepSeek → Gemini Flash); optional **Light / fast** menu item
- **Image gen:** Colab **downloaded models only** by default — never uses Gemini/Groq/OpenRouter chat keys for images; `IMAGE_ALLOW_CLOUD=1` to re-enable HF/Pollinations
- **Latency:** fewer free-model tries, tighter chat timeout (45s light / 90s heavy), skip Colab local LLM on auto chat
- **Roman Urdu:** electrical slang (e.g. current bund) interpreted correctly; blank model replies handled better

## 3.0.6 — 2026-08-11

- **Prompt Studio:** close always clears overlay, body overflow, and drawer classes (fixes frozen/dimmed chat)
- **No more CDN highlight.js:** self-hosted `hljs-lite.js` + `hljs-atom-one-dark.css` (fixes Tracking Prevention block)
- **prompt_studio.js:** no longer overwrites `closePromptStudio`; Escape + backdrop close reliably
- **CSS safety:** closed drawers have pointer-events:none so they cannot trap clicks

## 3.0.5 — 2026-08-11

- **Custom API keys:** Settings keys with override are sent on every chat (`X-Vision-Key-*`); server applies them for that request only (never logged)
- **Local LLM:** Ollama, LM Studio, and generic OpenAI-compatible base URL + model (env + Settings)
- **Model menu:** Auto / Groq / Gemini / OpenRouter / DeepSeek / Ollama / LM Studio / OpenAI-compat / Colab
- **Version headers:** every response includes `X-Vision-AI-Version` and `X-App-Version`
