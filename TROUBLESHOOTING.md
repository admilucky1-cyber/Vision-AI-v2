# Troubleshooting flowchart

## Chat timeout
1. Select **Groq** in model menu (faster free tier)
2. Shorten message / split PDF questions
3. If image/graph: wait for Colab Boost warm (`[status] Ready`)
4. Retry once after 10s

## Graph not appearing (I–V / plot)
1. Phrase: `create graph between current and voltage`
2. Confirm matplotlib on server (`pip show matplotlib`)
3. Check response `images[]` not empty in Network tab
4. Hard refresh (`Ctrl+Shift+R`)

## Image empty / vague
1. Boost tab open + GPU runtime
2. HF_TOKEN / worker registered on `/boost`
3. Prefer photo prompts for mosques; graph prompts for plots

## Drive mount
1. Same Google account as Colab
2. Allow popup → `/content/drive/MyDrive/vision_ai_models`
3. Restart runtime after adding Secrets

## Theme / UI
1. Hard refresh
2. `localStorage` theme: dark/light
3. Preset: `applyThemePreset('nord')` in console

## Colab SyntaxError `__future__`
- File must start: docstring → `from __future__ import annotations` → imports
- Pull latest `colab_one_click_boost.py` and Restart runtime

## 403 YouTube download
- Use server download path; add cookies.txt only privately (never commit)
