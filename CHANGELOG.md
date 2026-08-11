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
- **About / title:** still report live `/api/version` (3.0.5)

## 3.0.5 — 2026-08-11 (deploy-complete)

- **Deploy truth:** browser title, meta app-version, README, versions.json, routes all report **3.0.5**
- **About:** Settings shows live `/api/version` + health + PKT time (exact running build)
- **Models:** Expanded free OpenRouter (Llama 3.3 70B, Qwen 2.5 72B, DeepSeek R1/Chat, Gemma 3, Mistral Small, Phi-4, Nemotron) + Groq multi-model cascade
- **Identity:** System prompt knows Vision AI v3.0.5; no fake 2023 cutoff identity; PKT = UTC+5
- **Time context:** get_current_info injects UTC + Pakistan PKT for accurate answers
- Prior 3.0.5 UI: Student plan, theme bootstrap, user-right bubbles, hamburger/focus fixes

## 3.0.5 — 2026-08-11

- **Plans:** Student plan now appears in payment Plan dropdown (all paid plans sync from API)
- **Themes:** Early theme-bootstrap.js on every page so light/dark + presets apply site-wide immediately
- **Chat UI:** User messages forced to the right with stronger bubble styling for light and dark
- **Hamburger fix:** Overlay no longer covers header; close handler always re-bound; desktop overlay killed
- **Polish:** prod-polish-v304.css — clearer light vs dark contrast, premium controls, payment form focus states
- **Upgrade page:** Back to Chat goes home; theme preset restored on load

## 3.0.3 — 2026-08-11

- **Critical:** restore missing `#chatOutput` message container (chat was blank)
- Pin composer to bottom; messages scroll in middle column
