# Bento Station's dedicated Deck Browser Rendering Engine
# Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.

import html
import json
import os
import math
from dataclasses import dataclass
from aqt import mw
from . import patcher
from aqt.deckbrowser import DeckBrowser, RenderDeckNodeContext
from . import config, heatmap, deck_tree_updater
from . import study_tools
from .templates import custom_body_template
import copy
# ── Widget generators (tách sang widgets/ — Bước 3 refactor) ──
from .widgets.levelbar import _get_exp_data, award_exp, _get_onigiri_level_bar_html, _get_level_bar_js_refresh
from .widgets.stats import _get_onigiri_stat_card_html, _get_sakura_stat_card_html, _get_onigiri_retention_html
from .widgets.heatmap import _get_onigiri_heatmap_html
from .widgets.session import _get_onigiri_session_widget_html
from .widgets.favorites import _get_onigiri_favorites_html

# ═══════════════════════════════════════════════════════════
# Sidebar buttons HTML + Dashboard stats cache
# (khôi phục từ bản gốc qua __pycache__/*.pyc sau khi tách widgets/ — Bước 3)
# ═══════════════════════════════════════════════════════════
BUTTON_HTML = {
    "profile": "{profile_bar}",
    "add": """
        <div class="add-button-dashed action-add" onclick="pycmd('add')">
            <i class="icon"></i>
            <span>Add</span>
        </div>
    """,
    "browse": """
        <div class="menu-item action-browse" onclick="pycmd('browse')">
            <i class="icon"></i>
            <span>Browser</span>
        </div>
    """,
    "stats": """
        <div class="menu-item action-stats" onclick="pycmd('stats')">
            <i class="icon"></i>
            <span>Stats</span>
        </div>
    """,
    "sync": """
        <div class="menu-item action-sync" onclick="pycmd('sync')">
            <i class="icon"></i>
            <span>Sync</span>
            <span class="sync-status-indicator"></span>
        </div>
    """,
    "settings": """
        <div class="menu-item action-settings" onclick="pycmd('openOnigiriSettings')">
            <i class="icon"></i>
            <span>Settings</span>
        </div>
    """,
    "more": """
        <details class="menu-group">
            <summary class="menu-item action-more">
                <i class="icon"></i>
                <span>More</span>
            </summary>
            <div class="menu-group-items">
                <div class="menu-item action-get-shared" onclick="pycmd('shared')">
                    <i class="icon"></i>
                    <span>Get Shared</span>
                </div>
                <div class="menu-item action-create-deck" onclick="pycmd('onigiri_create_deck')">
                    <i class="icon"></i>
                    <span>Create Deck</span>
                </div>
                <div class="menu-item action-import-file" onclick="pycmd('import')">
                    <i class="icon"></i>
                    <span>Import File</span>
                </div>
            </div>
        </details>
    """,
    "forge": """
        <details class="menu-group">
            <summary class="menu-item action-forge">
                <i class="icon"></i>
                <span>Bento Forge</span>
            </summary>
            <div class="menu-group-items">
                <div class="menu-item action-forge-open" onclick="pycmd('openBentoForge')">
                    <i class="icon"></i>
                    <span>Open Bento Forge</span>
                </div>
                <div class="menu-item action-forge-ai" onclick="pycmd('openBentoForgeAI')">
                    <i class="icon"></i>
                    <span>AI Settings</span>
                </div>
                <div class="menu-item action-forge-decks" onclick="pycmd('openBentoForgeDecks')">
                    <i class="icon"></i>
                    <span>Deck Manager</span>
                </div>
                <div class="menu-item action-forge-clear-cache" onclick="pycmd('clearBentoForgeCache')">
                    <i class="icon"></i>
                    <span>Clear AI Cache</span>
                </div>
            </div>
        </details>
    """,
    "study": """
        <details class="menu-group">
            <summary class="menu-item action-study">
                <i class="icon"></i>
                <span>Study Tools</span>
            </summary>
            <div class="menu-group-items">
                <div class="menu-item action-study-planner" onclick="pycmd('openStudyPlanner')">
                    <i class="icon"></i>
                    <span>Study Planner</span>
                </div>
                <div class="menu-item action-study-lookup" onclick="pycmd('openQuickLookup')">
                    <i class="icon"></i>
                    <span>Quick Lookup</span>
                </div>
                <div class="menu-item action-study-gallery" onclick="pycmd('openFlashcardGallery')">
                    <i class="icon"></i>
                    <span>Flashcard Gallery</span>
                </div>
                <div class="menu-item action-study-timer" onclick="pycmd('openFocusTimer')">
                    <i class="icon"></i>
                    <span>Focus Timer</span>
                </div>
            </div>
        </details>
    """,
}

_DASHBOARD_STATS_CACHE = {}
_DASHBOARD_LAST_UPDATE = 0
_DASHBOARD_CACHE_TTL = 60  # giây — cache thống kê "hôm nay" (giá trị hợp lý, khôi phục từ bản gốc)

@dataclass
class RenderData:
    """Wrapper for deck tree data that Anki's context menu expects."""
    tree: object  # DeckDueTreeNode from Anki


def _build_sidebar_html(conf: dict) -> str:
    """
    Builds the sidebar HTML content based on the user's saved layout.
    """
    layout_config = conf.get("sidebarButtonLayout", copy.deepcopy(config.DEFAULTS["sidebarButtonLayout"]))
    visible_keys = layout_config.get("visible", [])

    # 🧩 Bento Forge: tôn trọng cấu hình bật/tắt nút trên sidebar.
    forge_cfg = conf.get("bentoForge", {}) or {}
    forge_sidebar_enabled = bool(forge_cfg.get("enabled", True)) and bool(forge_cfg.get("sidebar_button", True))

    # 🛠 Study Tools: tôn trọng cấu hình bật/tắt nút trên sidebar.
    study_cfg = conf.get("studyTools", {}) or {}
    study_sidebar_enabled = bool(study_cfg.get("enabled", True)) and bool(study_cfg.get("sidebar_button", True))

    html_parts = []
    for key in visible_keys:
        if key == "forge" and not forge_sidebar_enabled:
            continue
        if key == "study" and not study_sidebar_enabled:
            continue
        if key in BUTTON_HTML:
            html_parts.append(BUTTON_HTML[key])

    return "\n".join(html_parts)


def _get_profile_pic_html(user_name: str, addon_package: str, css_class: str = "profile-pic") -> str:    
    profile_pic_filename = mw.col.conf.get("modern_menu_profile_picture", "")
    if profile_pic_filename and os.path.exists(os.path.join(mw.addonManager.addonsFolder(addon_package), "user_files", "profile", profile_pic_filename)):
        pic_url = f"/_addons/{addon_package}/user_files/profile/{profile_pic_filename}"
        return f'<img src="{pic_url}" class="{css_class}">'
    else:
        # Use default profile picture when none is selected or file doesn't exist
        default_pic = "bento_station-san.png"
        pic_url = f"/_addons/{addon_package}/system_files/profile_default/{default_pic}"
        return f'<img src="{pic_url}" class="{css_class}">'


def render_bento_station_deck_browser(self: DeckBrowser, reuse: bool = False) -> None:
    """
    A complete replacement for Anki's DeckBrowser._renderPage.
    It builds the entire modern UI, including Onigiri and external widgets,
    into a stable CSS grid.
    """
    # Ensure hooks from other add-ons are captured just-in-time
    patcher.take_control_of_deck_browser_hook()
    conf = config.get_config()
    addon_package = mw.addonManager.addonFromModule(__name__)
    
    # --- Part 1: Build Onigiri Widgets Grid ---
    onigiri_layout = conf.get("onigiriWidgetLayout", {}).get("grid", {})
    onigiri_grid_html = ""
    
    # Check cache for main stats
    global _DASHBOARD_STATS_CACHE, _DASHBOARD_LAST_UPDATE, _DASHBOARD_CACHE_TTL
    now = __import__("time").time()
    
    if now - _DASHBOARD_LAST_UPDATE < _DASHBOARD_CACHE_TTL and "cards_today" in _DASHBOARD_STATS_CACHE:
        cards_today = _DASHBOARD_STATS_CACHE["cards_today"]
        time_today_seconds = _DASHBOARD_STATS_CACHE["time_today_seconds"]
    else:
        # type IN (0,1,2,3) filters out manual operations (type 4 = manual rescheduling/resets)
        cards_today, time_today_seconds = self.mw.col.db.first("select count(), sum(time)/1000 from revlog where type IN (0,1,2,3) and id > ?", (self.mw.col.sched.day_cutoff - 86400) * 1000) or (0, 0)
        
        # Update cache
        _DASHBOARD_STATS_CACHE["cards_today"] = cards_today
        _DASHBOARD_STATS_CACHE["time_today_seconds"] = time_today_seconds
        _DASHBOARD_LAST_UPDATE = now
        
        # Invalidate retention cache so it re-calculates
        if "retention" in _DASHBOARD_STATS_CACHE:
            del _DASHBOARD_STATS_CACHE["retention"]
        
    time_today_seconds = time_today_seconds or 0
    cards_today = cards_today or 0
    time_today_minutes = time_today_seconds / 60
    seconds_per_card = time_today_seconds / cards_today if cards_today > 0 else 0

    widget_generators = {
        "studied": lambda: _get_sakura_stat_card_html("🌸", "Studied", f"{cards_today} cards", "studied"),
        "time": lambda: _get_sakura_stat_card_html("⏱️", "Time", f"{time_today_minutes:.1f} min", "time"),
        "pace": lambda: _get_sakura_stat_card_html("🎯", "Pace", f"{seconds_per_card:.1f} s/card", "pace"),
        "retention": _get_onigiri_retention_html,
        "heatmap": _get_onigiri_heatmap_html,
        "favorites": _get_onigiri_favorites_html,
        "level": _get_onigiri_level_bar_html,
        "session": _get_onigiri_session_widget_html,
        "planner": study_tools.get_planner_widget_html,
        "timer": study_tools.get_timer_widget_html,
        "lookup": study_tools.get_lookup_widget_html,
        "gallery": study_tools.get_gallery_widget_html,
    }
    
    for widget_id, widget_config in onigiri_layout.items():
        if widget_id in widget_generators:
            pos = widget_config.get("pos", 0)
            row_span = widget_config.get("row", 1)
            col_span = widget_config.get("col", 1)
            row = pos // 4 + 1
            col = pos % 4 + 1
            style = f"grid-area: {row} / {col} / span {row_span} / span {col_span};"
            onigiri_grid_html += f'<div class="onigiri-widget-container" style="{style}">{widget_generators[widget_id]()}</div>'

    # --- Part 2: Build External Add-on Widgets (into the same unified grid) ---
    external_hooks = patcher._get_external_hooks()
    external_layout = conf.get("externalWidgetLayout", {})
    grid_config = external_layout.get("grid", {})
    external_widgets_html = ""
    
    external_widgets_data = {}
    for hook in external_hooks:
        hook_id = patcher._get_hook_name(hook)
        class TempContent: stats = ""
        temp_content = TempContent()
        try:
            hook(self, temp_content)
            external_widgets_data[hook_id] = temp_content.stats
        except Exception as e:
            external_widgets_data[hook_id] = f"<div style='color: red;'>Error in {hook_id}:<br>{e}</div>"

    for hook_id, widget_config in grid_config.items():
        if hook_html := external_widgets_data.get(hook_id):
            pos = widget_config.get("grid_position", 0)
            row = pos // 4 + 1
            col = pos % 4 + 1
            row_span = widget_config.get("row_span", 1)
            col_span = widget_config.get("column_span", 1)
            style = f"grid-area: {row} / {col} / span {row_span} / span {col_span};"
            # Add external widgets to the same grid as Onigiri widgets
            external_widgets_html += f'<div class="external-widget-container" style="{style}">{hook_html}</div>'

    # --- Part 3: Assemble the Final Stats Block ---
    stats_title = mw.col.conf.get("modern_menu_statsTitle", config.DEFAULTS["statsTitle"])
    title_html = f'<h1 class="onigiri-widget-title">{stats_title}</h1>' if stats_title else ""

    # Combine both Onigiri and External widgets into a single unified grid
    unified_grid_html = onigiri_grid_html + external_widgets_html

    # [CHANGED] Updated CSS to force grid expansion and row height
    stats_block_html = f"""
    <style>
        /* FIX: Reset margin for Evolution Graph to prevent squeezing */
        .evolution-graph-main-wrapper {{
            margin: 0 !important;
            padding: 0 !important;
        }}

        .unified-grid {{
            display: grid;
            gap: 15px;
            /* grid-auto-rows ensures every '1 row' has a fixed minimum height (e.g. 110px) */
            grid-auto-rows: minmax(110px, auto);
            grid-template-columns: repeat(4, 1fr);
            width: 100%;
            box-sizing: border-box;
            overflow: hidden;
        }}
        
        /* Make the container expand to fill the grid area (rows/cols) */
        .onigiri-widget-container, .external-widget-container {{
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }}

        /* Force the inner content (cards, heatmap, favorites, level bar) to fill the container */
        .stat-card, #onigiri-heatmap-container, .onigiri-favorites-widget, #onigiri-level-bar-container {{
            flex: 1;
            width: 100%;
            height: 100%;
            box-sizing: border-box;
        }}

        /* EXP Level Bar — styles riêng cho #onigiri-level-bar-container (không phụ thuộc restaurant widget) */
        #onigiri-level-bar-container {{
            align-items: stretch;
            justify-content: flex-start;
            text-align: left;
            gap: 8px;
        }}
        .level-bar-header {{
            display: flex;
            align-items: center;
            gap: 14px;
            width: 100%;
        }}
        .level-badge {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-width: 60px;
            height: 60px;
            border-radius: 16px;
            background: linear-gradient(135deg, #ffd700, #ff8c00);
            color: #1a1a2e;
            box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
            flex-shrink: 0;
        }}
        .level-badge .level-label {{
            font-size: 0.65em;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 700;
        }}
        .level-badge .level-number {{
            font-size: 24px;
            font-weight: 800;
            line-height: 1;
        }}
        .level-info {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 0;
        }}
        .level-title {{
            font-size: 15px;
            font-weight: 700;
            color: var(--fg, #333);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .level-exp-text {{
            font-size: 12px;
            color: var(--fg-subtle, #888);
        }}
        .level-bar-track {{
            width: 100%;
            height: 14px;
            background: var(--border, #e0e0e0);
            border-radius: 8px;
            overflow: hidden;
        }}
        .level-bar-fill {{
            height: 100%;
            border-radius: 8px;
            background: linear-gradient(90deg, #ffd700, #ff8c00);
            transition: width 0.6s ease;
            position: relative;
        }}
        .level-bar-glow {{
            position: absolute;
            top: 0;
            right: 0;
            width: 34px;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5));
            border-radius: 8px;
        }}
        .level-bar-footer {{
            display: flex;
            justify-content: space-between;
            width: 100%;
            font-size: 11px;
            color: var(--fg-subtle, #888);
            gap: 8px;
        }}

        /* Restaurant Level Widget Styles */
        .onigiri-restaurant-level-widget {{
            display: flex;
            flex-direction: row;
            background: var(--canvas-inset, #f5f5f5);
            border-radius: 16px;
            overflow: hidden;
            height: 100%;
            border: 1px solid var(--border, #e0e0e0);
            /* cursor: pointer; removed - only image is clickable */
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .onigiri-restaurant-level-widget.expanded-view {{
            background: var(--theme-bg) !important;
            border-color: transparent;
        }}
        
        .night .onigiri-restaurant-level-widget {{
            background: var(--canvas-inset, #2c2c2c);
            border-color: var(--border, #444);
        }}

        .restaurant-image-container {{
            flex: 0 0 45%; /* Fixed width percentage */
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--canvas-inset);
            padding: 10px;
            position: relative;
            transition: all 0.3s ease;
            box-sizing: border-box;
            min-width: 0;
            min-height: 0;
            overflow: hidden;
        }}
        
        .onigiri-restaurant-level-widget.expanded-view .restaurant-image-container {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: transparent;
            padding: 5px; /* Reduced padding to make image larger */
            z-index: 10;
        }}
        
        .night .restaurant-image-container {{
            background: var(--canvas-inset);
        }}

        .restaurant-image {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.15));
            transition: transform 0.3s ease;
        }}
        
        .onigiri-restaurant-level-widget:hover .restaurant-image {{
            transform: scale(1.05);
        }}
        
        .onigiri-restaurant-level-widget.expanded-view .restaurant-image {{
            transform: scale(1.0);
            filter: drop-shadow(0 8px 12px rgba(0,0,0,0.2));
        }}

        .restaurant-info {{
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 15px 20px;
            gap: 15px;
            transition: opacity 0.2s ease;
        }}
        
        .onigiri-restaurant-level-widget.expanded-view .restaurant-info {{
            display: none;
            opacity: 0;
        }}

        .level-display {{
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }}

        .level-label {{
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--fg-subtle, #888);
            font-weight: 600;
            margin-bottom: 2px;
        }}

        .level-value {{
            font-size: 2.8em;
            font-weight: 800;
            color: var(--fg, #333);
            line-height: 1;
        }}

        .level-progress-container {{
            width: 100%;
            margin-top: 6px;
        }}
        
        .lp-bar {{
            height: 6px;
            background: var(--border, #e0e0e0);
            border-radius: 3px;
            overflow: hidden;
            width: 100%;
            margin-bottom: 2px;
        }}
        
        .lp-fill {{
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }}
        
        .lp-text {{
            font-size: 0.7em;
            color: var(--fg-subtle, #888);
            text-align: right;
            font-weight: 500;
        }}

        .daily-special-section {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            width: 100%;
        }}
        
        .ds-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }}

        .ds-label {{
            font-size: 0.9em;
            font-weight: 600;
            color: var(--fg, #333);
        }}

        .ds-progress-bar {{
            height: 8px;
            background: var(--border, #e0e0e0);
            border-radius: 4px;
            overflow: hidden;
            width: 100%;
        }}

        .ds-progress-fill {{
            height: 100%;
            background: var(--accent-color, #007bff);
            border-radius: 4px;
            transition: width 0.5s ease;
        }}

        .ds-text {{
            font-size: 0.85em;
            color: var(--fg-subtle, #888);
            font-weight: 500;
        }}
        
        /* Snow Animation for Santa's Coffee Theme */
        .onigiri-restaurant-level-widget.with-snow .restaurant-image-container {{
            overflow: visible;
        }}
        
        .snowflake {{
            position: absolute;
            top: -20px;
            color: #fff;
            font-size: 1.2em;
            opacity: 0.8;
            pointer-events: none;
            animation: snowfall linear infinite;
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.8);
            z-index: 10;
        }}
        
        @keyframes snowfall {{
            0% {{
                transform: translateY(0) translateX(0);
                opacity: 0;
            }}
            10% {{
                opacity: 0.8;
            }}
            90% {{
                opacity: 0.8;
            }}
            100% {{
                transform: translateY(300px) translateX(20px);
                opacity: 0;
            }}
        }}
        
        /* Make snowflakes visible in expanded view too */
        .onigiri-restaurant-level-widget.expanded-view.with-snow .snowflake {{
            display: block;
        }}
        
        /* Navigation buttons for Restaurant Level Widget */
        .rl-widget-nav-buttons {{
            display: flex;
            gap: 0;
            z-index: 20;
            margin-bottom: 2px;
            margin-left: 0; 
            padding-left: 0;
        }}
        
        .rl-nav-btn {{
            width: 24px;
            height: 24px;
            padding: 0;
            margin-left: 0;
            border: none;
            background: transparent;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            transition: all 0.2s ease;
            color: var(--fg-subtle, #757575);
        }}
        
        .night .rl-nav-btn {{
            background: transparent;
            color: var(--fg-subtle, #9e9e9e);
        }}
        
        .rl-nav-btn:hover {{
            background: transparent;
            color: var(--theme-color);
            transform: none;
            border: none;
            box-shadow: none;
            outline: none;
        }}
        
        .night .rl-nav-btn:hover {{
            background: transparent;
            color: var(--theme-color);
            border: none;
        }}
        
        .rl-nav-icon {{
            width: 16px;
            height: 16px;
            margin-left: 4px;
        }}
        
        /* Style for expanded view - reduce button visibility */
        .onigiri-restaurant-level-widget.expanded-view .rl-widget-nav-buttons {{
            opacity: 0.5;
        }}

        /* ============================================ */
        /* JAPANESE SAKURA STYLES                       */
        /* ============================================ */

        /* Sakura Stat Card */
        .sakura-stat-card {{
            background: var(--canvas-inset);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-sizing: border-box;
            height: 100%;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        .sakura-stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 183, 197, 0.25);
            border-color: #f4a7b9;
        }}

        .sakura-stat-icon {{
            font-size: 28px;
            line-height: 1;
            filter: drop-shadow(0 2px 4px rgba(255, 183, 197, 0.3));
            transition: transform 0.3s ease;
        }}
        .sakura-stat-card:hover .sakura-stat-icon {{
            transform: scale(1.15);
        }}

        .sakura-stat-value {{
            font-family: var(--font-subtle), "Nunito", "Segoe UI", sans-serif;
            font-size: 26px;
            font-weight: 700;
            color: var(--fg);
            line-height: 1;
            letter-spacing: -0.5px;
        }}

        .sakura-stat-label {{
            font-family: var(--font-subtle), "Nunito", "Segoe UI", sans-serif;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--fg-subtle);
        }}

        /* Sakura section title */
        .onigiri-widget-title {{
            font-family: var(--font-subtle), "Nunito", "Segoe UI", sans-serif !important;
            font-size: 1.6em !important;
            font-weight: 700 !important;
            color: var(--fg) !important;
            text-align: left !important;
            letter-spacing: 0.05em !important;
            margin-bottom: 16px !important;
            position: relative;
            padding-left: 28px;
        }}
        .onigiri-widget-title::before {{
            content: "🌸";
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1.1em;
        }}

        /* Sakura: Retention card */
        .retention-card {{
            border-radius: 16px !important;
            border: 1px solid var(--border) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: all 0.3s ease;
        }}
        .retention-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 183, 197, 0.25);
            border-color: #f4a7b9 !important;
        }}
        .retention-card h3 {{
            font-family: var(--font-subtle), "Nunito", "Segoe UI", sans-serif !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.12em !important;
            border-bottom: none !important;
            color: var(--fg-subtle) !important;
        }}
        .retention-card p {{
            font-family: var(--font-subtle), "Nunito", "Segoe UI", sans-serif !important;
            font-size: 26px !important;
            font-weight: 700 !important;
        }}
        .retention-content .star-rating {{
            gap: 6px;
        }}
        .retention-content .star {{
            width: 18px;
            height: 18px;
            border-radius: 50%;
        }}

        /* Sakura: Heatmap container */
        #onigiri-heatmap-container {{
            border-radius: 16px !important;
            border: 1px solid var(--border) !important;
            background: var(--canvas-inset) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        #onigiri-heatmap-container:hover {{
            box-shadow: 0 6px 20px rgba(255, 183, 197, 0.2);
        }}

        /* Sakura: Favorites widget */
        .onigiri-favorites-widget {{
            border-radius: 16px !important;
            border: 1px solid var(--border) !important;
            background: var(--canvas-inset) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            padding: 16px !important;
            transition: all 0.3s ease;
        }}
        .onigiri-favorites-widget:hover {{
            box-shadow: 0 6px 20px rgba(255, 183, 197, 0.2);
        }}
        .onigiri-favorites-widget h3 {{
            font-family: var(--font-subtle), "Nunito", "Segoe UI", sans-serif !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.12em !important;
            color: var(--fg-subtle) !important;
            border-bottom: none !important;
        }}
        .favorite-deck-link {{
            border-radius: 12px !important;
            padding: 8px 12px !important;
            margin: 2px 0 !important;
            transition: all 0.2s ease;
        }}
        .favorite-deck-link:hover {{
            background: rgba(255, 183, 197, 0.15) !important;
        }}
    </style>
    {title_html}
    <div class="unified-grid">{unified_grid_html}</div>
    """

    # --- Part 4: Manually Build the Deck Tree HTML ---
    # CRITICAL: Store tree data for Anki's context menu operations (e.g., deck deletion)
    # Anki's native _delete method expects self._render_data.tree to exist
    tree_data = self.mw.col.sched.deck_due_tree()
    self._render_data = RenderData(tree=tree_data)
    tree_html = deck_tree_updater._render_deck_tree_html_only(self)
    
    # Add OnigiriEngine JavaScript
    onigiri_engine_js = """
    <script>
    // Onigiri Performance Engine
    window.OnigiriEngine = {
        currentHoveredRow: null,

        init: function() {
            this.deckListContainer = document.getElementById('deck-list-container');
            if (!this.deckListContainer) return;
            this.bindEvents();
            this.observeMutations();
            console.log('OnigiriEngine initialized');
        },

        saveScrollPosition: function() {
            const container = document.querySelector('.deck-list-scroll-container');
            if (container) {
                this.scrollPosition = container.scrollTop;
            }
        },

        restoreScrollPosition: function() {
            const container = document.querySelector('.deck-list-scroll-container');
            if (container && typeof this.scrollPosition !== 'undefined') {
                container.scrollTop = this.scrollPosition;
            }
        },

        bindEvents: function() {
            if (this.deckListContainer.dataset.engineBound) return;
            this.deckListContainer.dataset.engineBound = 'true';

            // Handle deck row hover
            this.deckListContainer.addEventListener('mouseenter', (event) => {
                const deckRow = event.target.closest('tr.deck');
                if (deckRow) {
                    this.currentHoveredRow = deckRow;
                    deckRow.classList.add('is-hovered');
                }
            }, true);

            this.deckListContainer.addEventListener('mouseleave', (event) => {
                const deckRow = event.target.closest('tr.deck');
                if (deckRow && deckRow === this.currentHoveredRow) {
                    deckRow.classList.remove('is-hovered');
                    this.currentHoveredRow = null;
                }
            }, true);

            // Handle deck collapse/expand
            this.deckListContainer.addEventListener('click', (event) => {
                const collapseLink = event.target.closest('a.collapse');
                if (collapseLink) {
                    event.preventDefault();
                    event.stopPropagation();
                    this.saveScrollPosition();
                    
                    const deckRow = event.target.closest('tr.deck');
                    if (deckRow && deckRow.dataset.did) {
                        pycmd(`onigiri_collapse:${deckRow.dataset.did}`);
                    }
                    return false;
                }
            });
        },

        observeMutations: function() {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        this.processNewNodes(mutation.addedNodes);
                    }
                });
            });

            observer.observe(this.deckListContainer, {
                childList: true,
                subtree: true,
            });
        },

        processNewNodes: function(nodes) {
            nodes.forEach(node => {
                if (node.nodeType !== Node.ELEMENT_NODE) return;
                
                const elementsToProcess = [];
                if (node.matches('a.collapse, tr.deck')) {
                    elementsToProcess.push(node);
                }
                elementsToProcess.push(...node.querySelectorAll('a.collapse, tr.deck'));

                elementsToProcess.forEach(this.classifyCollapseIcon.bind(this));
            });
        },

        classifyCollapseIcon: function(el) {
            if (el.matches('a.collapse')) {
                if (el.classList.contains('state-closed')) {
                    el.textContent = '+';
                } else {
                    el.textContent = '-';
                }
            }
        },

        // Update the deck tree with new HTML
        updateDeckTree: function(html) {
            const tbody = document.querySelector('#decktree > tbody');
            if (tbody) {
                tbody.innerHTML = html;
                this.restoreScrollPosition();
                
                // Re-process any new collapse icons
                this.processNewNodes([tbody]);
                
                // Trigger any layout updates
                if (window.updateDeckLayouts) {
                    window.updateDeckLayouts();
                }
            }
        }
    };

    // Initialize the engine once the DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => OnigiriEngine.init());
    } else {
        OnigiriEngine.init();
    }
    </script>
    """
    
    # --- Part 5: Populate the Main Template ---
    is_collapsed = mw.col.conf.get("onigiri_sidebar_collapsed", False)
    is_focused = mw.col.conf.get("onigiri_deck_focus_mode", False)
    
    sidebar_initial_class = ""
    if is_collapsed:
        sidebar_initial_class += "sidebar-collapsed"
    if is_focused:
        sidebar_initial_class += " deck-focus-mode" if sidebar_initial_class else "deck-focus-mode"

    # --- MODIFICATION START ---
    
    # Build the dynamic profile bar HTML
    user_name = conf.get("userName", "USER")
    
    profile_bg_mode = mw.col.conf.get("modern_menu_profile_bg_mode", "accent")
    profile_bg_image = mw.col.conf.get("modern_menu_profile_bg_image", "")
    bg_style_str = ""
    bg_class_str = ""

    if profile_bg_mode == "image":
        if profile_bg_image and os.path.exists(os.path.join(mw.addonManager.addonsFolder(addon_package), "user_files", "profile_bg", profile_bg_image)):
            bg_image_url = f"/_addons/{addon_package}/user_files/profile_bg/{profile_bg_image}"
        else:
            # Use default background image when none is selected or file doesn't exist
            bg_image_url = f"/_addons/{addon_package}/system_files/profile_default/bento_station-bg.png"
        bg_style_str = f"background-image: url('{bg_image_url}'); background-size: cover; background-position: center;"
        bg_class_str = "with-image-bg"
    elif profile_bg_mode == "custom":
        bg_style_str = "background-color: var(--profile-bg-custom-color);"
    else: # accent
        bg_style_str = "background-color: var(--accent-color);"
    
    profile_pic_html_expanded = _get_profile_pic_html(user_name, addon_package)

    profile_bar_contents = (
        f"{profile_pic_html_expanded}"
        f"<span class=\"profile-name\">{user_name}</span>"
    )

    profile_bar_html = (
        f"<div class=\"profile-bar {bg_class_str}\" style=\"{bg_style_str}\" "
        f"onclick=\"pycmd('showUserProfile')\">{profile_bar_contents}</div>"
    )
    
    # 1. Build the dynamic sidebar HTML from the layout config
    sidebar_buttons_html = _build_sidebar_html(conf)
    
    # 2. Manually replace {profile_bar} inside the sidebar HTML string
    #    (This is necessary because {profile_bar} is one of the items in BUTTON_HTML)
    sidebar_buttons_html = sidebar_buttons_html.replace("{profile_bar}", profile_bar_html)
    
    # --- This logic remains the same ---
    profile_pic_html_collapsed = _get_profile_pic_html(user_name, addon_package, "collapsed-profile-pic")
    welcome_message = f"WELCOME {user_name.upper()}" if not conf.get("hideWelcomeMessage", False) else ""
    saved_width = mw.col.conf.get("modern_menu_sidebar_width", 300)
    sidebar_style = f"width: {saved_width}px;"
    container_extra_class = ""

    # 3. Use the new {sidebar_buttons} placeholder in the template
    #    and remove the old {profile_bar} placeholder.
    # 🎌 Animated Mascot HTML
    from . import animated_mascot
    mascot_html = animated_mascot.get_mascot_body_content("deck_browser")

    final_body = custom_body_template \
        .replace("{tree}", tree_html) \
        .replace("{stats}", stats_block_html) \
        .replace("{container_extra_class}", container_extra_class) \
        .replace("{sidebar_initial_class}", sidebar_initial_class) \
        .replace("{sidebar_style}", sidebar_style) \
        .replace("{welcome_message}", welcome_message) \
        .replace("{sidebar_buttons}", sidebar_buttons_html) \
        .replace("{profile_pic_html_collapsed}", profile_pic_html_collapsed) \
        .replace("{onigiri_mascot_html}", mascot_html)
    
    # --- MODIFICATION END ---
    
    # --- Part 6: Render the Final Page ---
    self.web.stdHtml(
        body=final_body,
        css=["css/deckbrowser.css"],
        js=["js/vendor/jquery.min.js", "js/vendor/jquery-ui.min.js", "js/deckbrowser.js"],
        context=self,
    )

    from aqt import gui_hooks
    gui_hooks.deck_browser_did_render(self)
