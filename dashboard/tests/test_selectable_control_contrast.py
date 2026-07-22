"""Static guards for professional contrast on selectable controls."""

from pathlib import Path


THEME = (Path(__file__).resolve().parents[1] / "utils" / "theme.py").read_text(encoding="utf-8")


def test_primary_actions_use_light_text_on_a_restrained_surface():
    assert "background: #2E6654 !important;" in THEME
    assert "color: #F1F3F5 !important;" in THEME
    assert "border: 1px solid #477D6B !important;" in THEME


def test_select_and_multiselect_values_have_neutral_contrast():
    assert '[data-testid="stSelectbox"] [data-baseweb="select"] span' in THEME
    assert "color: #D8DDE5 !important;" in THEME
    assert "background: #252C38 !important;" in THEME


def test_segmented_controls_use_non_neon_selected_states():
    assert '[data-testid="stButtonGroup"] button[aria-checked="true"]' in THEME
    assert "background: #2A3340 !important;" in THEME
    assert "color: #F0F2F5 !important;" in THEME
