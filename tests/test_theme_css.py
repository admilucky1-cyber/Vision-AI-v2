
"""Static checks: theme CSS files exist and contain key tokens."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_eye_care_exists():
    p = ROOT / "frontend/static/css/eye-care.css"
    assert p.is_file()
    t = p.read_text(encoding="utf-8")
    assert "0c1017" in t or "eye" in t.lower()


def test_theme_presets_exists():
    p = ROOT / "frontend/static/css/theme-presets.css"
    assert p.is_file()
    t = p.read_text(encoding="utf-8")
    assert "nord" in t and "high-contrast" in t


def test_index_links_css():
    html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    assert any(x in html for x in ("eye-care.css", "vision-awesome.css", "themes.css", "glass-ui.css", "theme-bridge.css"))


def test_modern_ui_css_present():
    assert (ROOT / "frontend/static/css/modern-ui.css").is_file()
    assert (ROOT / "frontend/static/css/tokens.css").is_file()


def test_welcome_suggestions_in_index():
    html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    assert "suggestion-chip" in html
    assert "suggestionGrid" in html


def test_index_app_version_matches():
    html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    ver = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert f'content="{ver}"' in html or "4.8.2" in html
