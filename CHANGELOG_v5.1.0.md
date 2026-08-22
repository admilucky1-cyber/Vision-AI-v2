# Vision AI 5.1.0 — Container & Widget (Web)

## Goal
Modular, beautiful workspace frontend without rewriting the backend.

## Added
- `frontend/static/css/tokens.css` — design system (color, space, radius, motion)
- `frontend/static/css/workspace.css` — shell polish
- `frontend/static/css/containers/*` — ChatShell, WorkspaceSidebar
- `frontend/static/css/widgets/*` — Composer, MessageBubble, ProfileMenu
- `frontend/static/css/responsive-900.css` — 900/901 drawer boundary
- `frontend/static/js/auth.js` — VisionAuth single logout path
- `frontend/static/js/sidebar.js` — `__vaSidebar` single state machine
- `frontend/static/js/containers/*` — ChatShell, WorkspaceSidebar, SettingsPanel
- `frontend/static/js/widgets/*` — Composer, MessageBubble, ProfileMenu
- `frontend/static/js/app.js` — boot loader
- Bridge at end of `index.js` so legacy callers use modular APIs

## Preserved
- All FastAPI routes / services
- Drive / LoRA / Colab worker paths
- Existing chat/send/model behavior in `index.js`
- Free-tier cascade

## Breakpoint
- ≤900px drawer · ≥901px desktop (sidebar controller)

## Version
5.1.0
