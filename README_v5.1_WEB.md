# Vision AI 5.1.0 — Web Container & Widget

## Architecture

```
Containers (state / regions)     Widgets (UI pieces)
─────────────────────────────    ──────────────────
ChatShell                        Composer
WorkspaceSidebar                 MessageBubble
SettingsPanel                    ProfileMenu
```

Shared services: `VisionAuth`, `__vaSidebar` (900/901).

## Deploy

Same as before (`python run.py` / Railway). Hard-refresh after deploy (`?v=510` assets).

## Smoke

1. Login → chat → logout  
2. Resize across 899 → 901 (drawer ↔ desktop)  
3. Profile menu open / Escape close  
4. Composer focus ring uses accent teal  

## Note

`index.js` remains the chat engine; the modular layer owns auth, sidebar, and presentation namespaces. Further extraction of send/render into modules can be incremental.
