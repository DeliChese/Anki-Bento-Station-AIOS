# Bento Station Study Tools (tách từ study_tools.py — Bước 4 refactor)
# Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.
import time
from aqt import mw
from aqt.qt import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFormLayout, QSpinBox, QCheckBox, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QTimer, QFrame,
    QSizePolicy, Qt,
)
from aqt.utils import tooltip


def _defaults() -> dict:
    return {
        "enabled": True,
        "sidebar_button": True,
        "dashboard_widgets": {"planner": True, "timer": True},
        "planner": {
            "enabled": True,
            "daily_goal_cards": 50,
            "weekly_goal_cards": 350,
            "show_dashboard_widget": True,
        },
        "quick_lookup": {
            "enabled": True,
            "dictionary_url": "https://jisho.org/search/{word}",
            "open_browser_on_lookup": True,
        },
        "gallery": {
            "enabled": True,
            "per_page": 200,
            "default_query": "deck:*",
        },
        "focus_timer": {
            "enabled": True,
            "work_min": 25,
            "break_min": 5,
            "long_break_min": 15,
            "sessions_before_long": 4,
            "auto_start_break": True,
        },
    }


def get_tools_config() -> dict:
    """Đọc cấu hình studyTools (hợp nhất default) từ config Bento Station."""
    cfg = _defaults()
    try:
        station_cfg = _get_station_config()
        user = station_cfg.get("studyTools", {}) or {}
        _deep_merge(cfg, user)
    except Exception:
        pass
    return cfg


def save_tools_config(cfg: dict) -> None:
    """Lưu toàn bộ section studyTools vào config Bento Station."""
    try:
        station_cfg = _get_station_config()
        station_cfg["studyTools"] = cfg
        _save_station_config(station_cfg)
    except Exception:
        pass


def _get_station_config() -> dict:
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
    try:
        from . import config
        config.write_config(cfg)
    except Exception:
        try:
            from config import write_config
            write_config(cfg)
        except Exception:
            pass


def _deep_merge(base: dict, over: dict) -> None:
    for k, v in over.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def cards_reviewed_today() -> int:
    """Số thẻ (khác nhau) đã học hôm nay."""
    try:
        if mw is None or mw.col is None:
            return 0
        cutoff = mw.col.sched.day_cutoff
        return int(mw.col.db.scalar(
            "select count(distinct cid) from revlog where id >= ?",
            (cutoff - 86400) * 1000,
        ) or 0)
    except Exception:
        return 0


def cards_reviewed_week() -> int:
    """Số thẻ đã học trong 7 ngày gần nhất."""
    try:
        if mw is None or mw.col is None:
            return 0
        cutoff = mw.col.sched.day_cutoff
        return int(mw.col.db.scalar(
            "select count(distinct cid) from revlog where id >= ?",
            (cutoff - 7 * 86400) * 1000,
        ) or 0)
    except Exception:
        return 0


def current_streak() -> int:
    """Chuỗi ngày học liên tục (đếm từ revlog)."""
    try:
        if mw is None or mw.col is None:
            return 0
        cutoff = mw.col.sched.day_cutoff
        streak = 0
        for days_back in range(366):
            end_ms = (cutoff - days_back * 86400) * 1000
            start_ms = (cutoff - (days_back + 1) * 86400) * 1000
            cnt = int(mw.col.db.scalar(
                "select count(distinct cid) from revlog where id >= ? and id < ?",
                (start_ms, end_ms),
            ) or 0)
            if cnt > 0:
                streak += 1
            else:
                if days_back == 0:
                    return 0  # hôm nay chưa học → streak 0
                break
        return streak
    except Exception:
        return 0


def is_tools_available() -> bool:
    return bool(get_tools_config().get("enabled", True))
