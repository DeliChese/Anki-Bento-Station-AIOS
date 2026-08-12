"""Runtime call-test cho bento_station_renderer + widgets/ sau khi tách (Bước 3).

Verify:
1. `BUTTON_HTML` được tái dựng đúng → `_build_sidebar_html()` chứa đủ nút
   (action-add/browse/forge/study) + placeholder {profile_bar}.
2. Các hàm widget thuần trả chuỗi (bắt NameError runtime).

Chỉ chạy khi dùng stub (không có PyQt thật); verify UI bằng Anki thật.
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
def test_sidebar_html_reconstructed():
    import importlib

    r = importlib.import_module("bento_station.bento_station_renderer")
    # conf mô phỏng user đã bật đủ nút (forge/study thêm qua config sync)
    conf = {"sidebarButtonLayout": {
        "visible": ["profile", "add", "browse", "stats", "sync", "settings", "more", "forge", "study"]}}
    html = r._build_sidebar_html(conf)
    for btn in ("action-add", "action-browse", "action-stats", "action-sync",
                "action-settings", "action-more", "action-forge", "action-study"):
        assert btn in html, f"thiếu nút {btn}"
    assert "{profile_bar}" in html, "thiếu placeholder profile_bar"


@pytest.mark.skipif(_has_real_qt(), reason="Cần stub — verify bằng Anki thật")
def test_widget_functions_run():
    import importlib

    r = importlib.import_module("bento_station.bento_station_renderer")
    # @dataclass phải còn nguyên (đã từng bị tách bỏ)
    rd = r.RenderData(tree="x")
    assert rd.tree == "x"
    assert isinstance(r._get_exp_data(), tuple)
    assert isinstance(r._get_onigiri_level_bar_html(), str)
    assert isinstance(r._get_onigiri_stat_card_html("L", "V", "id"), str)
    assert isinstance(r._get_sakura_stat_card_html("🌸", "L", "V", "id"), str)
    r.award_exp(10)  # ghi vào mw.col.conf (dict thật)
    assert isinstance(r.BUTTON_HTML, dict)
    assert "profile" in r.BUTTON_HTML and "forge" in r.BUTTON_HTML
