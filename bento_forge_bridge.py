"""
═══════════════════════════════════════════════════════════════
 bento_forge_bridge.py
 ===============================================================

 BRIDGE INTEGRATION — Nối "Bento Forge" (Xưởng chế tạo thẻ từ vựng /
 AI DeepSeek / Cache) vào "Bento Station AIOS".

 ── NGUYÊN TẮC THIẾT KẾ ─────────────────────────────────────────
 1. Import TRỄ (lazy import) + chống lỗi: Bento Station phải luôn
    khởi động bình thường kể cả khi "Bento Forge" thiếu / lỗi.
 2. Không import vòng lặp: bridge chỉ import 1 chiều (Station → Forge),
    Forge KHÔNG bao giờ import ngược lại Bento Station.
 3. Thư mục "Bento Forge" chứa KHOẢNG TRẮNG → cú pháp `from ... import`
    không hợp lệ, phải dùng `importlib.import_module()`.
 4. Cùng chia sẻ 1 runtime Python + Qt: mọi dialog của Forge được mở
    với parent = mw (cửa sổ Anki) → hiển thị ngay trong Bento Station.

 ── API EXPOSED ─────────────────────────────────────────────────
   is_forge_available()          -> bool   Forge có sẵn không
   initialize_forge()            -> bool   import + đăng ký hook 1 lần
   open_forge()                  -> None   mở Xưởng chế biến (main dialog)
   open_ai_settings()            -> None   mở Cài Đặt AI (DeepSeek...)
   open_deck_manager()           -> None   mở Deck Manager
   ensure_config_sync()          -> None   đồng bộ cấu hình 2 chiều
   configure_cache()             -> dict   áp cấu hình cache từ Station
   clear_ai_cache()              -> bool   xoá toàn bộ cache AI
   refresh_anki_ui()             -> None   làm mới Deck Browser ngay

 ── ĐƯỜNG DẪN ──────────────────────────────────────────────────
   - config Bento Station: user_files/settings_<profile>.json (config.get_config)
   - config Bento Forge  : Bento Forge/utils/ai_config.json
   - cache Bento Forge   : Bento Forge/utils/ai_cache/

 Original code/structure from Onigiri Add-on. Customized and expanded
 for Bento Station AIOS.
═══════════════════════════════════════════════════════════════
"""

import importlib
import os
import sys

from aqt import mw

# ═══════════════════════════════════════════════════════════
#  HẰNG SỐ
# ═══════════════════════════════════════════════════════════

# Tên package của Forge (thư mục con chứa khoảng trắng — bắt buộc importlib).
_FORGE_PACKAGE = "Bento Forge"

# Các "chỉ báo" để xác định module Forge đã load thành công (tránh nhầm lẫn).
_FORGE_SENTINEL_ATTRS = ("AnkiSmartFactory", "start_smart_factory")

# Khoá section cấu hình của Forge bên trong config Bento Station.
_STATION_CONFIG_KEY = "bentoForge"

# Cache trong bộ nhớ (tránh import lặp + lưu lỗi import cuối cùng).
_forge_module = None
_forge_import_error = None
_forge_initialized = False


# ═══════════════════════════════════════════════════════════
#  DISCOVERY / IMPORT (chống circular import & ModuleNotFoundError)
# ═══════════════════════════════════════════════════════════

def _addon_root() -> str:
    """Thư mục gốc của addon Bento Station AIOS."""
    return os.path.dirname(os.path.abspath(__file__))


def _discover_forge():
    """
    Tìm & import package "Bento Forge" đúng MỘT lần.

    Returns:
        (module_or_None, error_or_None)
    """
    global _forge_module, _forge_import_error

    # Đã thử 1 lần rồi → trả kết quả cache (dù thành công hay thất bại).
    if _forge_module is not None or _forge_import_error is not None:
        return _forge_module, _forge_import_error

    root = _addon_root()
    if root not in sys.path:
        sys.path.insert(0, root)

    # Ưu tiên 1: package con "Bento Forge" ngay trong thư mục addon.
    candidates = [_FORGE_PACKAGE]
    # Ưu tiên 2: nếu người dùng cài Forge như addon độc lập khác (dự phòng).
    candidates.append("bento_forge")

    for name in candidates:
        try:
            mod = importlib.import_module(name)
            if mod is not None and any(hasattr(mod, a) for a in _FORGE_SENTINEL_ATTRS):
                _forge_module = mod
                return mod, None
        except Exception as e:  # noqa: BLE001 — ghi lỗi & thử candidate kế tiếp
            _forge_import_error = e
            continue

    return None, _forge_import_error


def is_forge_available() -> bool:
    """Trả True nếu module Bento Forge có thể import thành công."""
    mod, _err = _discover_forge()
    return mod is not None


def initialize_forge() -> bool:
    """
    Import "Bento Forge" ĐÚNG MỘT LẦN (idempotent).

    Việc import module-level của Forge sẽ tự đăng ký:
      - reviewer hooks   (hooks/reviewer.py)
      - overview hooks   (hooks/overview_mode.py)
      - action trên menu Tools (Ctrl+Shift+I)

    Gọi từ setup_global_hooks() của Bento Station.
    """
    global _forge_initialized
    if _forge_initialized:
        return True
    mod, _err = _discover_forge()
    if mod is None:
        return False
    _forge_initialized = True
    return True


# ═══════════════════════════════════════════════════════════
#  MỞ DIALOG (hiển thị trực tiếp trong cửa sổ Bento Station)
# ═══════════════════════════════════════════════════════════

def _focus_or_raise(dialog):
    """Đưa dialog đã tồn tại lên trước (tránh tạo trùng)."""
    try:
        if dialog.isMinimized():
            dialog.showNormal()
        dialog.raise_()
        dialog.show()
        dialog.activateWindow()
    except Exception:
        pass


def open_forge(parent=None):
    """
    Mở "Xưởng chế biến" (AnkiSmartFactory) — giao diện tạo thẻ từ vựng,
    gọi AI DeepSeek, quản lý cache — ngay bên trong Bento Station.
    """
    mod, err = _discover_forge()
    if mod is None:
        _notify_unavailable(err)
        return

    dialog_cls = getattr(mod, "AnkiSmartFactory", None)
    if dialog_cls is None:
        _notify_unavailable("Thiếu class AnkiSmartFactory trong Bento Forge.")
        return

    parent = parent if parent is not None else mw
    existing = getattr(mw, "factory_dialog", None)
    if existing is not None and existing.isVisible():
        _focus_or_raise(existing)
        return

    try:
        mw.factory_dialog = dialog_cls(parent)
        mw.factory_dialog.show()
        _focus_or_raise(mw.factory_dialog)
    except Exception as e:  # noqa: BLE001
        from aqt.utils import showInfo
        showInfo(f"❌ Không mở được Bento Forge:\n{e}")


def open_ai_settings(parent=None):
    """Mở dialog Cài Đặt AI (API key DeepSeek, model, temperature, cache...)."""
    mod, err = _discover_forge()
    if mod is None:
        _notify_unavailable(err)
        return
    try:
        from aqt.qt import QDialog
        from ui import show_ai_settings_dialog  # noqa: F401 — import nội bộ Forge
        show_ai_settings_dialog(parent if parent is not None else mw)
    except Exception as e:  # noqa: BLE001
        from aqt.utils import showInfo
        showInfo(f"❌ Không mở được Cài Đặt AI:\n{e}")


def open_deck_manager(parent=None):
    """Mở Deck Manager của Bento Forge (tạo/đổi tên/xóa deck, tự refresh UI)."""
    mod, err = _discover_forge()
    if mod is None:
        _notify_unavailable(err)
        return
    try:
        from ui.deck_manager_dialog import DeckManagerDialog
        dialog = DeckManagerDialog(parent if parent is not None else mw)
        dialog.exec()
    except Exception as e:  # noqa: BLE001
        from aqt.utils import showInfo
        showInfo(f"❌ Không mở được Deck Manager:\n{e}")


def _notify_unavailable(error=None):
    from aqt.utils import showInfo
    msg = (
        "🧩 Bento Forge chưa khả dụng.\n\n"
        "Bridge đã bảo vệ Bento Station không bị lỗi.\n"
        "Hãy đảm bảo thư mục 'Bento Forge' nằm trong addon "
        "Bento Station AIOS (đúng tên, có __init__.py)."
    )
    if error:
        msg += f"\n\nChi tiết: {error}"
    showInfo(msg)


# ═══════════════════════════════════════════════════════════
#  ĐỒNG BỘ CẤU HÌNH (API key / model / cache một nơi duy nhất)
# ═══════════════════════════════════════════════════════════

# Ánh xạ khoá config Station ⇄ Forge.
_CONFIG_FIELD_MAP = {
    "api_key": "api_key",
    "api_base": "api_base",
    "model": "model",
    "temperature": "temperature",
    "max_tokens": "max_tokens",
    "max_chars": "max_chars",
    "chunk_size": "chunk_size",
    "reasoning_effort": "reasoning_effort",
}


def _get_station_config():
    """Đọc config Bento Station (profile-specific), trả dict rỗng nếu lỗi."""
    try:
        from . import config
        return config.get_config()
    except Exception:
        try:
            from config import get_config
            return get_config()
        except Exception:
            return {}


def _save_station_config(cfg):
    """Ghi config Bento Station (profile-specific)."""
    try:
        from . import config
        config.write_config(cfg)
    except Exception:
        try:
            from config import write_config
            write_config(cfg)
        except Exception:
            pass


def _get_forge_api_module():
    """Trả module utils.ai_extractor của Forge (hoặc None)."""
    mod, _err = _discover_forge()
    if mod is None:
        return None
    try:
        from utils import ai_extractor
        return ai_extractor
    except Exception:
        return None


def _default_forge_section() -> dict:
    """Bản mặc định của section bentoForge (khớp DEFAULTS trong config.py)."""
    return {
        "enabled": True,
        "sidebar_button": True,
        "api_key": "",
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "temperature": 0.2,
        "max_tokens": 8192,
        "max_chars": 45000,
        "chunk_size": 8000,
        "reasoning_effort": "",
        "cache_enabled": True,
        "cache_dir": "",
    }


def ensure_config_sync() -> bool:
    """
    Đồng bộ cấu hình AI/cache 2 chiều giữa Bento Station và Bento Forge.

    Chiến lược (tránh ghi đè mất dữ liệu):
      - Nếu Station đã cấu hình api_key (khác rỗng) → PUSH toàn bộ section
        `bentoForge` lên Forge (nguồn chân lý = config Bento Station).
      - Ngược lại (user chưa đặt key ở Station)      → PULL cấu hình hiện có
        của Forge về Station (chỉ để "thấy một nơi"), KHÔNG đẩy ngược lại —
        tránh ghi đè cấu hình thật mà user đã chỉnh trong Cài Đặt AI của Forge.
      - Luôn ghi qua `save_api_config()` của Forge để giữ nguyên quy ước mã hoá
        API key (Fernet/XOR) và sanitize đầu vào.

    Returns:
        True nếu Forge khả dụng và đồng bộ chạy; False nếu không.
    """
    station_cfg = _get_station_config()
    if not station_cfg:
        return False

    section = station_cfg.get(_STATION_CONFIG_KEY)
    section = dict(_default_forge_section() if not isinstance(section, dict) else section)

    api_mod = _get_forge_api_module()
    if api_mod is None:
        return False

    try:
        forge_cfg = api_mod.get_api_config()  # dict đã có defaults + key đã giải mã
    except Exception:
        forge_cfg = {}

    station_key = str(section.get("api_key") or "").strip()

    if station_key:
        # ── PUSH: Station là nguồn chân lý khi đã có key ──────────────
        merged = dict(forge_cfg)
        merged["api_key"] = station_key
        for station_field, forge_field in _CONFIG_FIELD_MAP.items():
            if station_field == "api_key":
                continue
            if station_field in section and section[station_field] not in (None, ""):
                merged[forge_field] = section[station_field]
        try:
            api_mod.save_api_config(
                api_key=str(merged.get("api_key") or ""),
                api_base=str(merged.get("api_base") or "https://api.deepseek.com/v1"),
                model=str(merged.get("model") or "deepseek-chat"),
                temperature=float(merged.get("temperature") or 0.2),
                max_chars=int(merged.get("max_chars") or 45000),
                chunk_size=int(merged.get("chunk_size") or 8000),
                reasoning_effort=str(merged.get("reasoning_effort") or ""),
            )
        except Exception:
            pass
    else:
        # ── PULL: kéo cấu hình thật của Forge về Station (không đẩy ngược) ──
        for station_field, forge_field in _CONFIG_FIELD_MAP.items():
            if forge_field in forge_cfg and forge_cfg[forge_field] not in (None, ""):
                section[station_field] = forge_cfg[forge_field]
        section.setdefault("cache_enabled", True)
        section.setdefault("cache_dir", "")

    # Ghi lại section vào config Station nếu chưa tồn tại / đã thay đổi.
    existing_section = station_cfg.get(_STATION_CONFIG_KEY)
    if not isinstance(existing_section, dict) or existing_section != section:
        station_cfg[_STATION_CONFIG_KEY] = section
        _save_station_config(station_cfg)

    return True


def configure_cache() -> dict:
    """
    Áp cấu hình cache từ Bento Station vào Bento Forge.

    Đọc `bentoForge.cache_dir` (tuỳ chọn) để chuyển nơi lưu cache AI,
    và `bentoForge.cache_enabled` để cho phép/tắt (mặc định bật).

    Returns:
        dict mô tả trạng thái cache hiệu lực.
    """
    api_mod = _get_forge_api_module()
    if api_mod is None:
        return {"enabled": False, "cache_dir": None, "error": "Bento Forge unavailable"}

    station_cfg = _get_station_config() or {}
    section = station_cfg.get(_STATION_CONFIG_KEY) or _default_forge_section()

    cache_enabled = bool(section.get("cache_enabled", True))
    custom_dir = str(section.get("cache_dir") or "").strip()

    try:
        if custom_dir:
            api_mod._CACHE_DIR = custom_dir
        if cache_enabled:
            api_mod._ensure_cache_dir()
    except Exception as e:  # noqa: BLE001
        return {"enabled": cache_enabled, "cache_dir": getattr(api_mod, "_CACHE_DIR", None), "error": str(e)}

    return {
        "enabled": cache_enabled,
        "cache_dir": getattr(api_mod, "_CACHE_DIR", None),
        "error": None,
    }


def clear_ai_cache() -> bool:
    """
    Xoá toàn bộ cache AI của Bento Forge.

    Returns:
        True nếu xoá thành công (hoặc Forge không khả dụng → True, coi như xong).
    """
    api_mod = _get_forge_api_module()
    if api_mod is None:
        return True  # không có gì để xoá
    try:
        api_mod.clear_cache()
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
#  LUỒNG DỮ LIỆU — thẻ mới cập nhật Deck/Review KHÔNG cần restart
# ═══════════════════════════════════════════════════════════

def refresh_anki_ui() -> None:
    """
    Làm mới toàn bộ UI Anki để deck/thẻ mới hiển thị tức thì.

    Bento Forge vốn đã tự gọi mw.reset() sau khi import thẻ
    (xem _on_import_finished trong Bento Forge/__init__.py).
    Bridge này bổ sung thêm mw.deckBrowser.refresh() để chắc chắn
    danh sách deck + số lượng thẻ cập nhật ngay lập tức.
    """
    try:
        if mw is not None:
            mw.reset()
            if getattr(mw, "deckBrowser", None) is not None:
                mw.deckBrowser.refresh()
    except Exception:
        pass


def invalidate_deck_cache(model_name: str = None, deck_id: int = None) -> None:
    """
    Vô hiệu hoá cache từ vựng của deck (buộc Bento Forge rescan lần sau).
    Gọi sau khi đúc thẻ mới để dữ liệu trùng lặp được phát hiện chính xác.
    """
    mod, _err = _discover_forge()
    if mod is None:
        return
    try:
        from utils.deck_cache import invalidate_deck_cache as _invalidate
        _invalidate(model_name=model_name, deck_id=deck_id)
    except Exception:
        pass
