"""Smoke test: import toàn bộ module root của addon (không cần chạy Anki).

Bắt lỗi "import vỡ / thiếu re-export" khi refactor theo kiểu SHIM.
- Mọi module được test ở mức import (stub aqt/anki/PyQt6 trong conftest).
- Lưu ý: chỉ đảm bảo IMPORT KHÔNG VỠ — hành vi Qt thật phải verify bằng Anki.
"""
from __future__ import annotations

import importlib

import pytest

# (module trong package "bento_station", cần PyQt trực tiếp?, [symbol bắt buộc])
MODULES = [
    # ── module thuần (không cần aqt) ─────────────────────────────
    ("constants", False, ["COLOR_LABELS", "ICON_DEFAULTS", "ALL_THEME_KEYS"]),
    ("themes", False, ["THEMES", "define_theme"]),
    ("icon_registry", False, ["get_icon", "get_icon_url", "list_icons"]),
    ("templates", False, []),
    # ── module chỉ cần stub aqt.mw ───────────────────────────────
    ("config", False, ["get_config", "write_config", "invalidate_config_cache", "DEFAULTS"]),
    ("css_engine", False, [
        "generate_dynamic_css", "generate_reviewer_buttons_css",
        "generate_deck_browser_backgrounds", "generate_icon_css", "generate_font_css",
    ]),
    ("patching", False, ["_safe_apply"]),
    ("heatmap", False, ["get_heatmap_data"]),
    ("habit_engine", False, []),
    ("animated_mascot", False, ["get_mascot_config"]),
    ("favorites_cleanup", False, []),
    # ── module dùng aqt.qt (Qt qua aqt — dummy class đủ cho import) ──
    ("fonts", False, []),
    ("patcher", False, ["apply_patches", "patch_overview", "on_webview_js_message"]),
    ("webview_handlers", False, []),
    ("deck_tree_updater", False, []),
    ("future_letter_dialog", False, []),
    ("welcome_dialog", False, []),
    ("icon_chooser", False, []),
    ("create_deck_dialog", False, []),
    ("credits_dialog", False, []),
    ("toolbar_styling", False, ["apply_menu_styling"]),
    ("profile_page", False, []),
    ("webview_router", False, ["on_webview_js_message"]),
    ("menu_buttons", False, []),
    ("study_tools", False, []),
    ("bento_station_renderer", False, ["render_bento_station_deck_browser"]),
    # ── module import PyQt6 TRỰC TIẾP (dùng stub Qt — import-only) ──
    ("settings", False, ["open_settings", "SettingsDialog"]),
    ("birthday_dialog", False, []),
    ("coloris_picker", False, []),
]


@pytest.mark.parametrize(
    "name,needs_qt,attrs",
    MODULES,
    ids=[m[0] for m in MODULES],
)
def test_module_imports(name, needs_qt, attrs):
    # needs_qt giữ để ghi chú module gắn sâu Qt (nên verify thêm bằng Anki thật)
    mod = importlib.import_module(f"bento_station.{name}")
    for attr in attrs:
        assert hasattr(mod, attr), f"{name} thiếu symbol: {attr}"
