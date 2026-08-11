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
