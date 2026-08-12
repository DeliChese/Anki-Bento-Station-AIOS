# Bento Station Deck Browser Widgets (tách từ bento_station_renderer.py — Bước 3 refactor)
# Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.
import html
import json
import os
import math
import copy
from dataclasses import dataclass
from aqt import mw
from .. import patcher
from aqt.deckbrowser import DeckBrowser, RenderDeckNodeContext
from .. import config, heatmap, deck_tree_updater
from .. import study_tools
from ..templates import custom_body_template


def _get_onigiri_session_widget_html() -> str:
    """
    GĐ2: Widget "Suggested Session" — mood 1 click + đề xuất số thẻ hôm nay
    dựa trên khối lượng trung bình và tốc độ lịch sử (chống burnout).
    """
    try:
        from . import habit_engine
        suggestion = habit_engine.get_session_suggestion()
    except Exception:
        return ""

    mood = suggestion.get("mood", "normal")
    target = suggestion.get("target", 0)
    today_count = suggestion.get("today_count", 0)
    avg_volume = suggestion.get("avg_volume", 0.0)
    remaining = max(0, target - today_count)
    progress_pct = min(100, int(today_count / target * 100)) if target > 0 else 0

    mood_btns = ""
    for m, label in [("tired", "Tired"), ("normal", "Normal"), ("hype", "Hype")]:
        active_cls = " active" if mood == m else ""
        mood_btns += (
            f'<button class="session-mood-btn{active_cls}" data-mood="{m}" '
            f'onclick="pycmd(\'onigiri_set_mood:{m}\')">{label}</button>'
        )

    tokens = 0
    try:
        tokens = habit_engine.get_streak_tokens()
    except Exception:
        pass
    tokens_text = f" · 🛡️ {tokens} token{'s' if tokens != 1 else ''}" if tokens else ""

    if target <= 0:
        summary = f"{today_count} done today · avg {avg_volume}/day{tokens_text}"
    else:
        summary = f"{today_count} done · {remaining} to go · avg {avg_volume}/day{tokens_text}"

    return f"""
    <div id="onigiri-session-container" class="sakura-stat-card session-widget">
        <div class="session-header">
            <span class="session-title">🎯 Suggested Session</span>
            <span class="session-target">{target} cards</span>
        </div>
        <div class="session-progress">
            <div class="session-progress-fill" style="width:{progress_pct}%;"></div>
        </div>
        <div class="session-meta">{summary}</div>
        <div class="session-mood-row">
            <span class="session-mood-label">Mood:</span>
            {mood_btns}
        </div>
    </div>
    """
