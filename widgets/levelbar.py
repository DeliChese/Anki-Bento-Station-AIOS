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


def _get_exp_data():
    """Reads EXP data from Anki collection config. Returns (exp, level, progress, exp_next, exp_current_level)."""
    exp = mw.col.conf.get("onigiri_exp", 0)
    level = int(math.sqrt(exp / 100)) + 1  # Level 1 at 0 EXP
    exp_for_current = ((level - 1) ** 2) * 100
    exp_for_next = (level ** 2) * 100
    progress = ((exp - exp_for_current) / (exp_for_next - exp_for_current)) * 100 if exp_for_next > exp_for_current else 100
    return exp, level, min(progress, 100), exp_for_next, exp_for_current


def award_exp(amount: int):
    """Awards EXP to the user. Call this after completing card reviews.
    NOTE: mw.col.setMod() is called by the caller to batch writes."""
    if not mw.col:
        return False, 1
    current_exp = mw.col.conf.get("onigiri_exp", 0)
    old_level = int(math.sqrt(current_exp / 100)) + 1
    new_exp = current_exp + amount
    mw.col.conf["onigiri_exp"] = new_exp
    new_level = int(math.sqrt(new_exp / 100)) + 1
    # setMod is called by _on_reviewer_did_answer_card (batched with pending)
    return new_level > old_level, new_level


def _get_onigiri_level_bar_html() -> str:
    """Generates the Japanese RPG-themed level bar HTML for the dashboard."""
    conf = config.get_config()
    if not conf.get("expBarEnabled", True):
        return ""
    
    exp, level, progress, exp_next, exp_current = _get_exp_data()
    exp_remaining = exp_next - exp
    
    # Read customizable text from config
    title_text = conf.get("expBarTitle", "Bento Station Mastery")
    lv_label = conf.get("expBarLevelLabel", "LV")
    next_level_text = conf.get("expBarNextLevelText", "Next level:")
    show_remaining = conf.get("expBarShowRemaining", True)
    show_percent = conf.get("expBarShowPercent", True)
    
    exp_label = f"{exp:,} / {exp_next:,} EXP"

    # Build footer conditionally
    footer_parts = []
    if show_remaining:
        footer_parts.append(f'<span class="level-remaining">{next_level_text} {exp_remaining:,} EXP</span>')
    if show_percent:
        footer_parts.append(f'<span class="level-percent">{progress:.1f}%</span>')
    footer_html = f'<div class="level-bar-footer">{"".join(footer_parts)}</div>' if footer_parts else ""

    # Check for pending EXP notification from review session
    pending = mw.col.conf.get("onigiri_pending_exp", None)
    pending_js = ""
    if pending and pending.get("amount", 0) > 0:
        amt = pending["amount"]
        lvl_up = "true" if pending.get("leveled_up") else "false"
        new_lvl = pending.get("new_level", 0)
        label = pending.get("label", "")
        pending_js = f"""
        <script>
            (function() {{
                var check = setInterval(function() {{
                    if (typeof OnigiriExpToast !== 'undefined') {{
                        clearInterval(check);
                        OnigiriExpToast.show({amt}, {lvl_up}, {new_lvl}, '{label}');
                    }}
                }}, 100);
                setTimeout(function() {{ clearInterval(check); }}, 5000);
            }})();
        </script>"""
        # Clear pending notification
        mw.col.conf["onigiri_pending_exp"] = None
        mw.col.setMod()
    
    return f"""
    <div id="onigiri-level-bar-container" class="sakura-stat-card">
        <div class="level-bar-header">
            <div class="level-badge">
                <span class="level-label">{lv_label}</span>
                <span class="level-number">{level}</span>
            </div>
            <div class="level-info">
                <span class="level-title">{html.escape(title_text)}</span>
                <span class="level-exp-text">{exp_label}</span>
            </div>
        </div>
        <div class="level-bar-track">
            <div class="level-bar-fill" style="width: {progress:.1f}%;" data-exp-current="{exp}" data-exp-next="{exp_next}">
                <div class="level-bar-glow"></div>
            </div>
        </div>
        {footer_html}
    </div>
    {pending_js}"""


def _get_level_bar_js_refresh() -> str:
    """Returns JS to refresh the level bar after EXP changes."""
    return """
    if (typeof OnigiriLevelBar !== 'undefined' && OnigiriLevelBar.refresh) {
        OnigiriLevelBar.refresh();
    }
    """
