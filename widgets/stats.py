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

# Cache thống kê retention (khôi phục từ bản gốc sau khi tách widgets/ — Bước 3)
_DASHBOARD_STATS_CACHE = {}
_DASHBOARD_LAST_UPDATE = 0
_DASHBOARD_CACHE_TTL = 60  # giây — khớp với giá trị trong bento_station_renderer.py


def _get_onigiri_stat_card_html(label: str, value: str, widget_id: str) -> str:
    return f"""<div class="stat-card {widget_id}-card"><h3>{label}</h3><p>{value}</p></div>"""


def _get_sakura_stat_card_html(icon: str, label: str, value: str, widget_id: str) -> str:
    """Generate a Japanese sakura-themed stat card."""
    return f"""
    <div class="sakura-stat-card {widget_id}-card">
        <div class="sakura-stat-icon">{icon}</div>
        <div class="sakura-stat-value">{value}</div>
        <div class="sakura-stat-label">{label}</div>
    </div>"""


def _get_onigiri_retention_html() -> str:
    # Use cached retention if available and fresh
    global _DASHBOARD_STATS_CACHE, _DASHBOARD_LAST_UPDATE
    now = __import__("time").time()
    
    if now - _DASHBOARD_LAST_UPDATE < _DASHBOARD_CACHE_TTL and "retention" in _DASHBOARD_STATS_CACHE:
         retention_percentage = _DASHBOARD_STATS_CACHE["retention"]
         total_reviews = _DASHBOARD_STATS_CACHE.get("total_reviews_retention", 0) # Fallback for stars check logic if needed
    else:
        total_reviews, correct_reviews = mw.col.db.first(
            "select count(*), sum(case when ease > 1 then 1 else 0 end) from revlog where type = 1 and id > ?",
            (mw.col.sched.day_cutoff - 86400) * 1000
        ) or (0, 0)
        total_reviews = total_reviews or 0
        correct_reviews = correct_reviews or 0
        retention_percentage = (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0
        
        # Update cache
        _DASHBOARD_STATS_CACHE["retention"] = retention_percentage
        _DASHBOARD_STATS_CACHE["total_reviews_retention"] = total_reviews

    if retention_percentage >= 90: stars = 5
    elif retention_percentage >= 70: stars = 4
    elif retention_percentage >= 50: stars = 3
    elif retention_percentage >= 30: stars = 2
    elif total_reviews > 0: stars = 1 # Use total_reviews from scope
    else: stars = 0
    
    conf = config.get_config()
    if conf.get("hideRetentionStars", False):
        star_rating_html = ""
    else:
        star_html = "".join([f"<i class='star{' empty' if i >= stars else ''}'></i>" for i in range(5)])
        star_rating_html = f'<div class="star-rating">{star_html}</div>'

    return f"""
    <div class="stat-card retention-card">
        <h3>Retention</h3>
        <div class="retention-content">
            <p>{retention_percentage:.0f}%</p>
            {star_rating_html}
        </div>
    </div>
    """
