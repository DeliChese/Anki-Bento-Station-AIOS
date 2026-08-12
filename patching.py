"""
Hiện đại hóa P0 - A2: Patch registry + version-guard.

Tập trung mọi monkey-patch trực tiếp vào Anki internals, kèm guard:
  - hasattr: nếu method/attr của Anki không còn tồn tại (đổi API) → bỏ qua patch,
    dùng giao diện mặc định của Anki thay vì crash hoặc vỡ lặng lẽ.
  - try/except: lỗi runtime → log warning, không lan ra ngoài.
  - applied_patches(): danh sách patch đã áp dụng (debug khi Anki update).
"""

import logging

_LOGGER = logging.getLogger(__name__)
_APPLIED: list = []


def _safe_apply(name, apply_fn, guard_fn=None):
    """
    Áp dụng một patch an toàn.
    Trả về True nếu patch được áp dụng, False nếu bị bỏ qua (guard) hoặc lỗi.
    """
    try:
        if guard_fn is not None and not guard_fn():
            _LOGGER.warning("Onigiri: skipped patch '%s' (guard failed — Anki internals changed?)", name)
            return False
        apply_fn()
        _APPLIED.append(name)
        return True
    except Exception as e:  # noqa: BLE001
        _LOGGER.warning("Onigiri: patch '%s' failed: %s", name, e)
        return False


def applied_patches():
    """Danh sách tên patch đã áp dụng thành công."""
    return list(_APPLIED)


def apply_overview_patch():
    """Patch Overview._table / Overview._body (gọi khi mở profile)."""
    from aqt.overview import Overview
    from . import patcher

    def guard():
        return hasattr(Overview, "_table") or hasattr(Overview, "_body")

    return _safe_apply("overview_table_body", patcher.patch_overview, guard)


def apply_congrats_patch():
    """Patch Overview._show_finished_screen (wrap trang chúc mừng)."""
    from aqt.overview import Overview
    from . import patcher

    return _safe_apply(
        "overview_congrats",
        patcher.patch_congrats_page,
        lambda: hasattr(Overview, "_show_finished_screen"),
    )


def apply_deck_browser_render_patches():
    """
    Patch DeckBrowser._renderPage + _render_deck_node.
    Gọi ở top-level (__init__.py) — TRƯỚC render đầu tiên, vì main_window_did_init quá muộn.
    """
    from aqt.deckbrowser import DeckBrowser
    from . import patcher
    from . import bento_station_renderer

    def guard():
        return hasattr(DeckBrowser, "_renderPage") and hasattr(DeckBrowser, "_render_deck_node")

    def apply():
        DeckBrowser._renderPage = bento_station_renderer.render_bento_station_deck_browser
        DeckBrowser._render_deck_node = patcher._onigiri_render_deck_node

    return _safe_apply("deck_browser_render", apply, guard)
