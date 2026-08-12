"""Runtime call-test cho study_tools/ và themes/ sau khi tách (Bước 4).

Verify package wiring: config helpers + dữ liệu thuần chạy được (bắt NameError
runtime). Các dialog (planner/lookup/gallery/timer) cần db thật — verify bằng Anki.
"""
from __future__ import annotations

import importlib.util

import pytest


def _has_real_qt() -> bool:
    for name in ("PyQt6", "PyQt5"):
        try:
            if importlib.util.find_spec(name) is not None:
                return True
        except ValueError:
            pass
    return False


@pytest.mark.skipif(_has_real_qt(), reason="Cần stub — verify bằng Anki thật")
def test_study_tools_config_helpers():
    import importlib

    st = importlib.import_module("bento_station.study_tools")
    assert isinstance(st._defaults(), dict)
    cfg = st.get_tools_config()
    assert isinstance(cfg, dict)
    assert isinstance(st.is_tools_available(), bool)
    # Router open_tool tồn tại (không gọi vì cần dialog thật)
    assert callable(st.open_tool)
    # Các hàm widget HTML tồn tại qua package
    for name in ("get_planner_widget_html", "get_timer_widget_html",
                 "get_lookup_widget_html", "get_gallery_widget_html"):
        assert callable(getattr(st, name)), f"study_tools thiếu {name}"


@pytest.mark.skipif(_has_real_qt(), reason="Cần stub — verify bằng Anki thật")
def test_themes_data():
    import importlib

    th = importlib.import_module("bento_station.themes")
    assert isinstance(th.THEMES, dict) and len(th.THEMES) > 0
    assert isinstance(th.define_theme({"a": "1"}, {"a": "2"}), dict)
    # Ít nhất 1 theme có light+dark
    sample = next(iter(th.THEMES.values()))
    assert "light" in sample and "dark" in sample
