"""Runtime call-test cho css_engine (SHIM) sau khi tách sang package `css/`.

Gọi TỪNG hàm sinh CSS với stub (FakeMw cho config.get_config() trả DEFAULTS) và
kiểm tra trả về chuỗi. Bắt lỗi NameError/import thiếu KIỂU RUNTIME — loại lỗi
check_undefined (tĩnh) có thể bỏ sót (vd `config` dùng mà không import module).

Chỉ chạy khi dùng stub (không có PyQt thật); với PyQt thật verify bằng Anki.
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
def test_css_functions_return_strings():
    import importlib

    css = importlib.import_module("bento_station.css_engine")  # SHIM
    conf = {}
    calls = [
        ("generate_dynamic_css", (conf,)),
        ("generate_reviewer_buttons_css", (conf,)),
        ("generate_conditional_css", (conf,)),
        ("generate_icon_css", ("dummy_pkg", conf)),
        ("generate_font_css", ("dummy_pkg",)),
        ("generate_deck_browser_backgrounds", (".",)),
        ("generate_reviewer_background_css", (".",)),
        ("generate_overview_background_css", (".",)),
        ("generate_toolbar_background_css", (".",)),
        ("generate_profile_page_background_css", ()),
        ("generate_reviewer_bottom_bar_background_css", (".",)),
        ("generate_profile_bar_fix_css", ()),
        ("generate_icon_size_css", ()),
        ("_hex_to_rgba", ("#ffffff", 0.5)),
        ("_mix_colors", ("#ffffff", "#000000", 0.5)),
    ]
    for name, args in calls:
        fn = getattr(css, name, None)
        assert fn is not None, f"css_engine thiếu hàm {name}"
        result = fn(*args)
        assert isinstance(result, str), f"{name} không trả str mà {type(result).__name__}"
