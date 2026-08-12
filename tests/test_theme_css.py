
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
    assert "eye-care.css" in html or "vision-awesome.css" in html
