# Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.
import os
import re
import json
import base64
import html
from anki.hooks import wrap
from . import webview_handlers

# Default configuration values
DEFAULTS = {
    "congratsMessage": "Congratulations! You have finished this deck for now."
}

# Import after DEFAULTS to avoid circular imports
from aqt import mw, gui_hooks
from aqt.qt import *
import aqt
from aqt import mw, gui_hooks
from aqt.utils import showInfo, tooltip
from aqt.webview import AnkiWebView
from aqt.deckbrowser import DeckBrowser
from aqt.main import MainWebView
from aqt.utils import tr
from aqt.overview import Overview
from aqt.reviewer import Reviewer
import os
import json
import time
import re
import html
import base64
import random
import math
import webbrowser
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, unquote, quote_plus
from typing import Optional, Dict, List, Tuple, Any, Callable, Union
from . import config
from . import bento_station_renderer
from . import deck_tree_updater
from . import menu_buttons, settings, heatmap, fonts
from .fonts import get_all_fonts
from . import deck_tree_updater
from .constants import COLOR_LABELS
from . import icon_registry  # 🎌 Icon Registry

# --- Menu Styling ---
# --- Re-export từ css_engine (Hiện đại hóa P0-A3) ---
# Giữ các tên CSS trong namespace patcher để mọi `patcher.X` cũ vẫn hoạt động.
from .css_engine import (
    _render_background_css,
    generate_profile_page_background_css,
    generate_deck_browser_backgrounds,
    generate_reviewer_background_css,
    generate_overview_background_css,
    generate_toolbar_background_css,
    _generate_outer_background_css,
    generate_reviewer_bottom_bar_background_css,
    generate_profile_bar_fix_css,
    generate_icon_size_css,
    generate_icon_css,
    generate_conditional_css,
    generate_font_css,
    _hex_to_rgba,
    _mix_colors,
    generate_dynamic_css,
    generate_reviewer_buttons_css,
)


# --- Toolbar Patching ---
_managed_hooks = []
# --- Re-export từ toolbar_styling / profile_page / webview_router (P0-A3) ---
from .toolbar_styling import (
    apply_menu_styling,
    patch_qmenu,
    get_sync_status,
    _new_MainWebView_eventFilter,
    _update_toolbar_visibility,
    _on_sync_did_finish,
    _toolbar_patched,
    _original_MainWebView_eventFilter,
)
from .profile_page import (
    _get_profile_pic_html,
    _get_profile_pill_html,
    _get_theme_colors_html,
    _get_backgrounds_html,
    _get_heatmap_data_and_config_for_profile,
    _get_stats_html,
    _get_profile_header_html,
    _generate_profile_html_body,
    open_profile,
    show_profile_page,
    ProfileDialog,
    _profile_dialog,
    _profile_stats_cache,
)
from .webview_router import on_webview_js_message


def take_control_of_deck_browser_hook():
    """
    Finds external hooks, removes them from the main hook,
    and stores them for Onigiri to manage, preventing duplication.
    """
    global _managed_hooks
    if _managed_hooks: # Ensure this runs only once
        return

    onigiri_module_name = config.__name__.split('.')[0]
    # Make a copy of the list to modify it safely
    original_hooks = list(gui_hooks.deck_browser_will_render_content._hooks)

    for hook in original_hooks:
        hook_id = _get_hook_name(hook)
        if onigiri_module_name not in hook_id:
            _managed_hooks.append(hook)
            # Remove the hook so it doesn't run on its own
            gui_hooks.deck_browser_will_render_content.remove(hook)

# --- Profile Page Generation ---

# --- Caching for Profile Stats ---
def patch_overview():
	"""Replaces the HTML generation for the overview screen."""
	
	conf = config.get_config()
	show_toolbar_replacements = conf.get("hideNativeHeaderAndBottomBar", False)
	max_hide = conf.get("maxHide", False)
	flow_mode = conf.get("flowMode", False)
    
	overview_style = mw.col.conf.get("onigiri_overview_style", "pro")
	style_class = "mini-overview" if overview_style == "mini" else ""

	mini_css = ""
	if overview_style == "mini":
		mini_css = """
        <style id="onigiri-mini-overview-style">
            body.mini-overview {
                align-items: flex-start; /* Override the vertical centering */
                padding-top: 5vh;      /* Add space from the top */
            }

            /* --- The rest of the styling for the mini-overview components --- */
            .mini-overview .overview-title { font-size: 20px; font-weight: 600; margin-bottom: 10px; text-align: center; }
            .mini-overview .stats-container { width: 280px; margin: 0 auto 20px auto; background: var(--canvas-inset); padding: 6px; border: 1px solid var(--border); border-radius: 12px}
            .mini-overview .stats-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; font-size: 14px; }
            .mini-overview .stats-row span:first-child { color: var(--fg-subtle); }
            .mini-overview .new-count-bubble, .mini-overview .learn-count-bubble, .mini-overview .review-count-bubble { font-size: 12px; font-weight: bold; padding: 3px 10px; border-radius: 12px; min-width: 30px; text-align: center; }
            .mini-overview #study { width: 280px; margin: 0 auto; padding: 10px; font-size: 16px; border-radius: 12px; box-shadow: none !important; }
            .mini-overview .overview-bottom-actions { 
                width: 280px; 
                margin: 15px auto 0 auto; 
                display: flex; 
                justify-content: center; 
                gap: 10px; 
                text-align: center;
            }
            .mini-overview .overview-bottom-actions .overview-button { 
                background: var(--button-bg, #f5f5f5) !important; 
                color: var(--button-fg, #333); 
                border: 1px solid var(--button-border, #d9d9d9); 
                border-radius: 12px; 
                text-decoration: none; 
                font-size: 13px; 
                padding: 5px 12px; 
                font-weight: 500; 
                transition: background-color 0.2s, border-color 0.2s, color 0.2s; 
                opacity: 1 !important; 
                box-shadow: none !important;
            }
            .mini-overview .overview-bottom-actions .overview-button:hover { 
                background-color: var(--button-hover-bg, #e6e6e6) !important; 
                border-color: var(--button-hover-border, #bfbfbf);
                color: var(--button-hover-fg, #000);
                box-shadow: none !important;
            }
            /* Dark mode overrides */
            .nightMode .mini-overview .overview-bottom-actions .overview-button {
                --button-bg: var(--window-bg, #2a2a2a);
                --button-fg: var(--fg, #e0e0e0);
                --button-border: var(--border, #3a3a3a);
                --button-hover-bg: var(--window-bg, #333333);
                --button-hover-border: var(--border, #4a4a4a);
                --button-hover-fg: var(--fg, #ffffff);
                box-shadow: none !important;
            }
        </style>
        """
    
	def new_table(self) -> str:
		counts = list(self.mw.col.sched.counts())
		
		count_data = [
			{"label": tr.actions_new(), "count": counts[0], "class": "new-count-bubble"},
			{"label": tr.scheduling_learning(), "count": counts[1], "class": "learn-count-bubble"},
			{"label": tr.studying_to_review(), "count": counts[2], "class": "review-count-bubble"},
		]

		rows_html = ""
		for item in count_data:
			rows_html += (
				'<div class="stats-row">'
				f"<span>{item['label']}</span>"
				f"<span class=\"{item['class']}\">{item['count']}</span>"
				'</div>'
			)
		
		study_now_text = mw.col.conf.get("modern_menu_studyNowText") or tr.studying_study_now()

		bottom_actions_html = ""
		if show_toolbar_replacements:
			# Check if current deck is filtered (dynamic)
			current_deck = self.mw.col.decks.current()
			is_filtered = current_deck and current_deck.get("dyn", False)
			
			if is_filtered:
				# Filtered deck buttons: Options, Rebuild, Empty
				bottom_actions_html = (
					'<div class="overview-bottom-actions">'
					'<a href="#" key=O onclick="pycmd(\'opts\'); return false;" class="overview-button">Options</a>'
					'<a href="#" key=R onclick="pycmd(\'refresh\'); return false;" class="overview-button">Rebuild</a>'
					'<a href="#" key=E onclick="pycmd(\'empty\'); return false;" class="overview-button">Empty</a>'
					'</div>'
				)
			else:
				# Non-filtered deck buttons: Options, Custom Study, Description
				bottom_actions_html = (
					'<div class="overview-bottom-actions">'
					'<a href="#" key=O onclick="pycmd(\'opts\'); return false;" class="overview-button overview-button-normal">Options</a>'
					'<a href="#" key=C onclick="pycmd(\'studymore\'); return false;" class="overview-button overview-button-normal">Custom Study</a>'
					'<a href="#" onclick="pycmd(\'description\'); return false;" class="overview-button overview-button-normal">Description</a>'
					'</div>'
				)

		return (
			'<div class="overview-container">'
				'<div class="stats-container">'
					f'{rows_html}'
				'</div>'
				f'<button id="study" class="add-button-dashed" onclick="pycmd(\'study\'); return false;" autofocus>'
					f'{study_now_text}'
				'</button>'
				f'{bottom_actions_html}'
				'<button id="onigiri-reveal-btn">Click to reveal</button>'
			'</div>'
		)

	Overview._table = new_table
	
	header_html = ""
	if show_toolbar_replacements and not flow_mode:
		header_html = """
    <div id="onigiri-overview-header" class="overview-header">
        <div class="onigiri-reviewer-header-buttons">
            <a href="#" onclick="pycmd('decks'); return false;" class="onigiri-reviewer-button">Decks</a>
            <a href="#" onclick="pycmd('add'); return false;" class="onigiri-reviewer-button">Add</a>
            <a href="#" onclick="pycmd('browse'); return false;" class="onigiri-reviewer-button">Browse</a>
            <a href="#" onclick="pycmd('stats'); return false;" class="onigiri-reviewer-button">Stats</a>
            <a href="#" onclick="pycmd('sync'); return false;" class="onigiri-reviewer-button">Sync</a>
        </div>
    </div>
"""

	js_code = """
    document.addEventListener("DOMContentLoaded", function() {
        // Onigiri Deck Title Fix
        const titleElement = document.querySelector('.overview-title');
        if (titleElement) {
            // Anki provides the full deck path, so we split it by "::" and take the last part.
            const fullTitle = titleElement.textContent;
            const shortTitle = fullTitle.split('::').pop();
            titleElement.textContent = shortTitle;
        }
        
        if (!document.getElementById('onigiri-background-div')) {
            const bgDiv = document.createElement('div');
            bgDiv.id = 'onigiri-background-div';
            document.body.prepend(bgDiv);
        }

        // 🎌 Animated Mascot: create container if config exists
        if (window.__ONIGIRI_MASCOT_CONFIG__ && !document.getElementById('onigiri-mascot-container')) {
            const mascotDiv = document.createElement('div');
            mascotDiv.id = 'onigiri-mascot-container';
            mascotDiv.className = 'onigiri-mascot';
            const cfg = window.__ONIGIRI_MASCOT_CONFIG__;
            const size = (cfg && cfg.size) || 150;
            const scale = (cfg && cfg.scale) || 1.0;
            const pos = (cfg && cfg.position) || 'bottom-right';
            mascotDiv.setAttribute('data-position', pos);
            mascotDiv.style.cssText = 'width:' + size + 'px; height:' + size + 'px; --mascot-scale:' + scale + ';';
            mascotDiv.title = 'Click me! (✿◠‿◠)';
            
            const canvas = document.createElement('canvas');
            canvas.id = 'onigiri-mascot-canvas';
            canvas.width = size * 2;
            canvas.height = size * 2;
            canvas.style.cssText = 'width:' + size + 'px; height:' + size + 'px;';
            mascotDiv.appendChild(canvas);
            
            const lottieEl = document.createElement('div');
            lottieEl.id = 'onigiri-mascot-lottie';
            lottieEl.style.display = 'none';
            mascotDiv.appendChild(lottieEl);
            
            document.body.appendChild(mascotDiv);
        }

        // NEW SCRIPT TO ADD CLASS TO BODY
        // This allows our CSS to target the body tag and override the alignment
        if (document.querySelector('.overview-center-container.mini-overview')) { 
            document.body.classList.add('mini-overview');
        }
        
        // Collect all external content (anything not Onigiri)
        const container = document.querySelector('.overview-center-container');
        const onigiriHeader = document.getElementById('onigiri-overview-header');
        const onigiriTitle = document.querySelector('.overview-title');
        const onigiriContainer = document.querySelector('.overview-container');
        const revealBtn = document.getElementById('onigiri-reveal-btn');
        
        // Find all direct children of the container that are NOT Onigiri content
        const allExternalElements = [];
        if (container) {
            Array.from(container.children).forEach(function(child) {
                // Skip Onigiri elements and the reveal button
                if (child !== onigiriHeader &&
                    child !== onigiriTitle && 
                    child !== onigiriContainer && 
                    child !== revealBtn && 
                    child.id !== 'onigiri-overview-header' &&
                    child.id !== 'onigiri-reveal-btn' &&
                    !child.classList.contains('overview-header') &&
                    !child.classList.contains('overview-title') &&
                    !child.classList.contains('overview-container')) {
                    
                    // Check if element has visible content
                    const hasVisibleContent = function(el) {
                        // Skip if element is already hidden by CSS
                        const style = window.getComputedStyle(el);
                        if (style.display === 'none') return false;
                        
                        // Check for visible children (excluding hidden elements)
                        const visibleChildren = Array.from(el.children).filter(function(c) {
                            const childStyle = window.getComputedStyle(c);
                            return childStyle.display !== 'none' && c.textContent.trim() !== '';
                        });
                        
                        if (visibleChildren.length > 0) return true;
                        
                        // Check for direct text content (not in child elements)
                        const textContent = Array.from(el.childNodes)
                            .filter(function(node) { return node.nodeType === 3; })
                            .map(function(node) { return node.textContent.trim(); })
                            .join('');
                        
                        return textContent !== '';
                    };
                    
                    if (hasVisibleContent(child)) {
                        child.classList.add('onigiri-external-overview-addon');
                        allExternalElements.push(child);
                        child.style.display = 'none'; // Hide initially
                    }
                }
            });
        }
        
        // Hide reveal button if there are no external elements with content
        if (revealBtn && allExternalElements.length === 0) {
            revealBtn.style.display = 'none';
        }
        
        // Handle reveal button functionality
        if (revealBtn && allExternalElements.length > 0) {
            let isRevealed = false;
            revealBtn.addEventListener('click', function() {
                isRevealed = !isRevealed;
                
                if (isRevealed) {
                    // Show all external elements
                    allExternalElements.forEach(function(el) {
                        el.style.display = '';
                    });
                    revealBtn.innerHTML = 'Click to hide';
                } else {
                    // Hide all external elements
                    allExternalElements.forEach(function(el) {
                        el.style.display = 'none';
                    });
                    revealBtn.innerHTML = 'Click to reveal';
                }
            });
        }
    });
    """

	reveal_button_css = """
    <style id="onigiri-reveal-button-style">
        #onigiri-reveal-btn {
            display: block;
            margin: 20px auto;
            padding: 10px 20px;
            background: var(--button-primary-bg);
            color: white !important;
            border-radius: 12px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        #onigiri-reveal-btn:hover {
            transform: scale(1.05);
        }
        .night-mode #onigiri-reveal-btn {
            color: white !important;
        }
        .descfont.descmid.description.dyn {
            display: none !important;
        }
    </style>
    """

	Overview._body = f"""
{mini_css}
{reveal_button_css}
<div class="overview-center-container {style_class}">
	{header_html}
	<h3 class="overview-title">%(deck)s</h3>
	%(table)s
	<div>%(shareLink)s</div>
	<div>%(desc)s</div>
</div>
<script>{js_code}</script>
"""
    

# --- Congrats Page Patcher ---

def patch_congrats_page():
    """Replaces the default congratulations screen with a custom, stylable one."""
    
    def new_show_finished_screen(self: Overview, _old):
        addon_path = os.path.dirname(__file__)
        conf = config.get_config()
        addon_package = mw.addonManager.addonFromModule(__name__)

        # Check for hide mode to determine if the header should be shown
        show_toolbar_replacements = conf.get("hideNativeHeaderAndBottomBar", False)
        max_hide = conf.get("maxHide", False)
        flow_mode = conf.get("flowMode", False)

        header_html = ""
        if show_toolbar_replacements and not flow_mode:
            header_html = """
            <div class="overview-header">
                <div class="onigiri-reviewer-header-buttons">
                    <a href="#" onclick="pycmd('decks'); return false;" class="onigiri-reviewer-button">Decks</a>
                    <a href="#" onclick="pycmd('add'); return false;" class="onigiri-reviewer-button">Add</a>
                    <a href="#" onclick="pycmd('browse'); return false;" class="onigiri-reviewer-button">Browse</a>
                    <a href="#" onclick="pycmd('stats'); return false;" class="onigiri-reviewer-button">Stats</a>
                    <a href="#" onclick="pycmd('sync'); return false;" class="onigiri-reviewer-button">Sync</a>
                </div>
            </div>
            """

        # 1. Build Profile Bar HTML (if enabled)
        profile_bar_html = ""
        if conf.get("showCongratsProfileBar", True):
            user_name = conf.get("userName", "USER")
            profile_pic_html = _get_profile_pic_html(user_name, addon_package, "profile-pic")

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
            
            profile_bar_html = f"""
            <div class="profile-bar {bg_class_str}" style="{bg_style_str}" onclick="pycmd('showUserProfile')">
                {profile_pic_html}
                <span class="profile-name">{user_name}</span>
            </div>
            """

        # 2. Get Custom Message with fallback to default
        message = conf.get("congratsMessage", DEFAULTS["congratsMessage"])

        # 3. Build Bottom Actions HTML
        bottom_actions_html = ""
        if show_toolbar_replacements:
            current_deck = self.mw.col.decks.current()
            is_filtered = current_deck and current_deck.get("dyn", False)
            
            if is_filtered:
                # Filtered deck buttons: Options, Rebuild, Empty
                bottom_actions_html = """
                <div class="congrats-bottom-actions">
                    <a href="#" key=O onclick="pycmd('opts'); return false;" class="overview-button">Options</a>
                    <a href="#" key=R onclick="pycmd('refresh'); return false;" class="overview-button">Rebuild</a>
                    <a href="#" key=E onclick="pycmd('empty'); return false;" class="overview-button">Empty</a>
                </div>
                """
            else:
                # Non-filtered deck buttons: Options, Custom Study, Description
                bottom_actions_html = """
                <div class="congrats-bottom-actions">
                    <a href="#" key=O onclick="pycmd('opts'); return false;" class="overview-button">Options</a>
                    <a href="#" key=C onclick="pycmd('studymore'); return false;" class="overview-button">Custom Study</a>
                    <a href="#" onclick="pycmd('description'); return false;" class="overview-button">Description</a>
                </div>
                """

        # 4. Construct Final HTML Body
        body_html = f"""
        <div class="congrats-container">
            {header_html}
            {profile_bar_html}
            <div class="congrats-card">
                <h1>{message}</h1>
            </div>
            {bottom_actions_html}
        </div>
        """
        
        # 5. Generate Head Content (CSS)
        head_html = generate_dynamic_css(conf)
        head_html += generate_overview_background_css(addon_path)
        
        # 6. Render the page
        self.web.stdHtml(
            body_html,
            css=[f"/_addons/{addon_package}/web/congrats.css"],
            js=[], # JS messages are handled by the hook, no need to inject a file
            head=head_html,
            context=self,
        )
        # Manually run JS to create the background div after the page is loaded.
        self.web.eval("""
            if (!document.getElementById('onigiri-background-div')) {
                const bgDiv = document.createElement('div');
                bgDiv.id = 'onigiri-background-div';
                document.body.prepend(bgDiv);
            }
        """)

    Overview._show_finished_screen = wrap(Overview._show_finished_screen, new_show_finished_screen, "around")


def generate_reviewer_top_bar_html_and_css():
    """Generates the HTML and basic structural CSS for the new web-based reviewer top bar."""

    conf = config.get_config()
    is_base_hide_mode = (
        conf.get("hideNativeHeaderAndBottomBar", False)
        and not conf.get("flowMode", False)
    )
    if not is_base_hide_mode:
        return "", ""

    # Build the HTML for reviewer header buttons
    header_buttons = """
    <div class="onigiri-reviewer-header-buttons">
        <a href="#" onclick="pycmd('decks'); return false;" class="onigiri-reviewer-button">Decks</a>
        <a href="#" onclick="pycmd('add'); return false;" class="onigiri-reviewer-button">Add</a>
        <a href="#" onclick="pycmd('browse'); return false;" class="onigiri-reviewer-button">Browse</a>
        <a href="#" onclick="pycmd('stats'); return false;" class="onigiri-reviewer-button">Stats</a>
        <a href="#" onclick="pycmd('sync'); return false;" class="onigiri-reviewer-button">Sync</a>
    </div>
    """
    
    html = f"""
    <div id="onigiri-reviewer-header" class="header">
        {header_buttons}
    </div>
    """

    css = """
    <style id="onigiri-reviewer-top-bar-structure">
        :root {
            --onigiri-reviewer-header-offset: 65px;
        }
        
        html {
            scroll-padding-top: var(--onigiri-reviewer-header-offset);
        }

        #onigiri-reviewer-header, .overview-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            width: 35%;
            margin: 10px auto;
            margin-top: 5px;
            border-radius: 12px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 10px;
            box-sizing: border-box;
            -webkit-font-smoothing: antialiased;
            pointer-events: auto;
            z-index: 1000; /* Increased z-index */

            /* ISOLATION FROM CARD TEMPLATES */
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
            font-size: 13px !important;
            line-height: normal !important;
            color: initial !important;
            text-align: center !important;
            text-transform: none !important;
            white-space: normal !important;
            letter-spacing: normal !important;
            word-spacing: normal !important;
            text-shadow: none !important;
        }
        

        
        .onigiri-reviewer-header-buttons {
            display: flex;
            gap: 10px;
        }

        /* Target A tags specifically to override card template global a {} styles */
        #onigiri-reviewer-header a.onigiri-reviewer-button,
        #onigiri-overview-header a.onigiri-reviewer-button,
        .overview-header a.onigiri-reviewer-button {
            color: var(--fg) !important;
            background: rgba(247, 247, 247) !important;
            padding: 5px 12px !important;
            border-radius: 12px !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            font-size: 13px !important;
            text-decoration: none !important;
            font-style: normal !important;
            font-weight: normal !important;
            transition: background-color 0.2s ease, border-color 0.2s ease !important;
            display: inline-block !important;
            line-height: normal !important;
        }

        .night_mode #onigiri-reviewer-header a.onigiri-reviewer-button,
        .night_mode #onigiri-overview-header a.onigiri-reviewer-button,
        .night_mode .overview-header a.onigiri-reviewer-button {
            color: var(--fg) !important;
            background: rgba(42, 42, 42) !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
        }

        #onigiri-reviewer-header a.onigiri-reviewer-button:hover,
        #onigiri-overview-header a.onigiri-reviewer-button:hover,
        .overview-header a.onigiri-reviewer-button:hover {
            background: rgba(128, 128, 128, 0.25) !important;
            color: var(--fg) !important;
        }
        
        /* Restaurant level progress bar styles */
        .restaurant-level-chip {
            display: flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            padding: 0;
            margin-left: 12px;
            width: 180px;
            height: 28px;
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .night_mode .restaurant-level-chip {
            background: rgba(0, 0, 0, 0.3);
            border-color: rgba(255, 255, 255, 0.05);
        }
        
        .level-progress-container {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .level-progress-bar {
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            background: linear-gradient(90deg, #ffb347, #ff6b6b);
            border-radius: 12px;
            transition: width 0.5s ease-out;
            z-index: 1;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
        }
        
        .level-progress-text {
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            z-index: 2;
            font-size: 12px;
            font-weight: 600;
            color: white;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.7);
            padding: 0 12px;
            box-sizing: border-box;
            height: 100%;
        }
        
        .level-text {
            font-weight: 700;
            display: flex;
            align-items: center;
            text-shadow: none !important;
        }
        

        
        .xp-text {
            font-size: 11px;
            opacity: 0.95;
            background: rgba(0, 0, 0, 0.2);
            padding: 2px 6px;
            border-radius: 12px;
            font-weight: 500;
        }
        
        .restaurant-level-chip:hover {
            transform: translateY(-1px);
            box-shadow: 0 3px 6px rgba(0,0,0,0.15);
        }
        
        .restaurant-level-chip:hover .level-progress-bar {
            background: linear-gradient(90deg, #ff9a3c, #ff5e62);
            box-shadow: 0 0 15px rgba(255, 107, 107, 0.4);
        }

        /* Create space for the header and ensure proper stacking */
        body.card, body {
            --onigiri-reviewer-header-offset: 65px;
            padding-top: var(--onigiri-reviewer-header-offset) !important;

        }
        

    </style>
    """

    
    
    return html, css

def _get_hook_name(hook):
    """Creates a unique, stable identifier for a hook function."""
    module_name = hook.__module__ if hasattr(hook, '__module__') else 'unknown_module'
    return f"{module_name}.{hook.__name__}"

def _get_external_hooks():
    """Returns the list of hooks that Onigiri is managing."""
    return _managed_hooks


def _onigiri_render_deck_node(self, node, ctx) -> str:
    """
    A patched version of DeckBrowser._render_deck_node that creates the
    HTML structure Onigiri's CSS and JS expect (e.g., td.collapse-cell).
    """
    buf = []  # Use a list for efficient string building

    if node.collapsed:
        prefix = "+"
        state_class = "state-closed"
    else:
        prefix = "-"
        state_class = "state-open"

    conf = getattr(ctx, "onigiri_conf", None)
    if conf is None:
        conf = config.get_config()
        setattr(ctx, "onigiri_conf", conf)

    # --- ADD THIS BLOCK ---
    # --- Onigiri Favorites ---
    favorites = mw.col.conf.get("onigiri_favorite_decks", [])
    did_str = str(node.deck_id)
    is_favorite = did_str in favorites
    fav_class = "is-favorite" if is_favorite else ""
    
    fav_star_html = f"""
    <span class="favorite-star-icon {fav_class}"
          onclick="event.stopPropagation(); pycmd('onigiri_toggle_favorite:{node.deck_id}')"
          title="Toggle favorite">
    </span>
    """
    # --- End Onigiri Favorites ---
    # --- END OF BLOCK ---

    hide_all_deck_counts = conf.get("hideAllDeckCounts", False)

    new_count = node.new_count
    learn_count = node.learn_count
    review_count = node.review_count

    # --- Counts HTML ---
    counts_html = ""
    
    # Enhanced Deck Stats Logic
    # Enhanced Deck Stats Logic
    # 1. Try checking the instance directly (set by our new _render_deck_tree patch or deck_tree_updater)
    enhanced_stats = getattr(self, "_onigiri_enhanced_stats", None)
    
    # 2. Fallback to _render_data if not found (legacy/redundancy)
    if enhanced_stats is None and hasattr(self, "_render_data"):
         enhanced_stats = getattr(self._render_data, "enhanced_stats", None)

    show_enhanced = conf.get("enhancedDeckStats", False)
    
    # Debug Logging
    # print(f"Onigiri Debug: Deck {node.deck_id} | Show: {show_enhanced} | Has Stats: {enhanced_stats is not None} | In Stats: {node.deck_id in enhanced_stats if enhanced_stats else False}")

    
    if not hide_all_deck_counts:
        if show_enhanced and enhanced_stats and node.deck_id in enhanced_stats:
            # --- ENHANCED MODE ---
            stats = enhanced_stats[node.deck_id]
            stats_list = conf.get("enhancedDeckStatsList", ["total", "new", "learn", "review", "buried", "suspended"])
            show_bar = conf.get("enhancedDeckProportionBar", True)
            
            # 1. Stats Grid
            grid_items = []
            for key in stats_list:
                val = stats.get(key, 0)
                label = key.capitalize()
                # Special styling for zero values? Maybe opacity.
                zero_class = " zero" if val == 0 else ""
                grid_items.append(f'<div class="stat-item {key}{zero_class}"><span class="stat-label">{label}</span><span class="stat-value">{val}</span></div>')
            
            stats_grid_html = f'<div class="enhanced-stats-grid">{"".join(grid_items)}</div>'
            
            # 2. Proportion Bar
            bar_html = ""
            if show_bar:
                total = stats.get("total", 0)
                if total > 0:
                    # Calculate percentages
                    p_new = (stats.get("new", 0) / total) * 100
                    p_learn = (stats.get("learn", 0) / total) * 100
                    p_review = (stats.get("review", 0) / total) * 100
                    p_buried = (stats.get("buried", 0) / total) * 100
                    p_suspended = (stats.get("suspended", 0) / total) * 100
                    
                    # Build bar segments
                    segments = []
                    if p_new > 0: segments.append(f'<div class="bar-segment new" style="width: {p_new}%;"></div>')
                    if p_learn > 0: segments.append(f'<div class="bar-segment learn" style="width: {p_learn}%;"></div>')
                    if p_review > 0: segments.append(f'<div class="bar-segment review" style="width: {p_review}%;"></div>')
                    if p_buried > 0: segments.append(f'<div class="bar-segment buried" style="width: {p_buried}%;"></div>')
                    if p_suspended > 0: segments.append(f'<div class="bar-segment suspended" style="width: {p_suspended}%;"></div>')
                    
                    bar_html = f'<div class="enhanced-proportion-bar">{"".join(segments)}</div>'
                else:
                    bar_html = '<div class="enhanced-proportion-bar empty"></div>'
            
            # Combine into a container that uses container queries
            counts_html = f"""
            <div class="enhanced-deck-info">
                 <div class="standard-counts">
                    <span class="new-count-bubble{' zero' if new_count == 0 else ''}">{new_count}</span>
                    <span class="learn-count-bubble{' zero' if learn_count == 0 else ''}">{learn_count}</span>
                    <span class="review-count-bubble{' zero' if review_count == 0 else ''}">{review_count}</span>
                 </div>
                 <div class="expanded-details">
                    {stats_grid_html}
                    {bar_html}
                 </div>
            </div>
            """
        else:
            # --- STANDARD MODE ---
            counts_html_parts = []
            counts_html_parts.append(f'<span class="new-count-bubble{" zero" if new_count == 0 else ""}">{new_count}</span>')
            counts_html_parts.append(f'<span class="learn-count-bubble{" zero" if learn_count == 0 else ""}">{learn_count}</span>')
            counts_html_parts.append(f'<span class="review-count-bubble{" zero" if review_count == 0 else ""}">{review_count}</span>')
            counts_html = '<div class="deck-counts">' + ''.join(counts_html_parts) + '</div>'
    # --- Counts HTML ---

    def indent():
        mode = conf.get("deck_indentation_mode", "default")
        
        if mode == "default":
            return "&nbsp;" * 6 * (node.level - 1)
            
        custom_px = conf.get("deck_indentation_custom_px", 20)
        step = 20
        if mode == "smaller":
            step = 10
        elif mode == "bigger":
            step = 40
        elif mode == "custom":
            step = int(custom_px)

        px = step * (node.level - 1)
        if px <= 0:
            return ""
            
        return f"<span style='display:inline-block; width:{px}px;'></span>"

    klass = "deck current" if node.deck_id == ctx.current_deck_id else "deck"
    
    # Determine precise deck type for styling
    # Priority: 1) node.filtered (direct from tree node), 2) DB lookup
    is_filtered = False
    
    # First, try the direct node property (most reliable in modern Anki)
    if hasattr(node, 'filtered'):
        is_filtered = bool(node.filtered)
    
    # Fallback: database lookup if node.filtered not available or returned False
    if not is_filtered:
        try:
            did = int(node.deck_id)
            deck_obj = mw.col.decks.get(did)
            if deck_obj:
                if isinstance(deck_obj, dict):
                    is_filtered = bool(deck_obj.get("dyn", 0))
                elif hasattr(deck_obj, "dyn"):
                    is_filtered = bool(deck_obj.dyn)
        except Exception:
            pass  # Keep is_filtered as False
    
    if is_filtered:
        deck_type_class = "is-filtered"
    elif node.children:
        deck_type_class = "is-folder"
    elif node.level > 1:
        deck_type_class = "is-subdeck"
    else:
        deck_type_class = "is-deck"

    buf.append(f"<tr class='{klass} {deck_type_class}' id='{node.deck_id}' data-did='{node.deck_id}'>")

    if node.children:
        collapse_link = f"<a class='collapse {state_class}' href=# onclick='return pycmd(\"onigiri_collapse:{node.deck_id}\")'>{prefix}</a>"
    else:
        collapse_link = "<span class=collapse></span>"

    # Removed class='deck-prefix' as requested by user
    deck_prefix = f"<span>{indent()}{collapse_link}</span>"
    extraclass = "filtered" if node.filtered else ""

    # --- START MODIFICATION: Update colspan and add counts_html ---
    buf.append(f"""
    <td class=decktd colspan=7>
        {fav_star_html}
        <div class="deck-info">
            {deck_prefix}
            <a class="deck {extraclass}" href=# onclick="return pycmd('open:{node.deck_id}')">
                {node.name}
            </a>
        </div>
        {counts_html}
    </td>
    """)
    # --- END MODIFICATION ---

    # --- START MODIFICATION: Remove old count columns ---
    # The old count tds are removed from here.
    # --- END MODIFICATION ---

    buf.append(f"""
    <td align=center class=opts>
      <a onclick='return pycmd("opts:{node.deck_id}");'>
        <img src='/_anki/imgs/gears.svg' class=gears>
      </a>
    </td>
    </tr>""")

    if not node.collapsed:
        for child in node.children:
            buf.append(self._render_deck_node(child, ctx))

    return "".join(buf) # Join the list into a single string at the end
    
def apply_patches():
    """
    Applies all legacy method patches (wrapping).
    """
    # ... (existing patches)
    
    # Apply modern menu styling
    apply_menu_styling()
    
    # Patch QMenu class for transparency
    patch_qmenu()
    """Apply all patches to Anki's UI."""
    # Register the reviewer_did_answer_card hook
    from aqt import gui_hooks
    gui_hooks.sync_did_finish.append(_on_sync_did_finish)
    
    # NOTE: DeckBrowser._render_deck_node is patched at top-level in __init__.py
    # to ensure it's applied before the first render (main_window_did_init is too late)
    
    # Patch the overview page
    # REMOVED: Called explicitly in __init__.py when profile is loaded to ensure mw.col exists
    # patch_overview()
    
    # Patch the congrats page
    # REMOVED: Called explicitly in __init__.py at top-level to ensure correct hook order
    # patch_congrats_page()
    
    # Patch the webview to handle our custom messages
    # REMOVED: This hook is already registered in __init__.py line 292
    # Keeping this line would cause double registration and duplicate dialogs
    # gui_hooks.webview_did_receive_js_message.append(on_webview_js_message)
    
    # Add hook for toolbar visibility changes
    gui_hooks.state_did_change.append(_update_toolbar_visibility)
    
    # Mark the hook as registered and update toolbar state
    mw._onigiri_restaurant_hook_registered = True
    mw.progress.single_shot(0, lambda: _update_toolbar_visibility(mw.state, "startup"))

def _onigiri_render_deck_tree(self, *args, **kwargs):
    """
    Patched version of DeckBrowser._render_deck_tree to pre-fetch enhanced stats.
    """
    try:
        from . import config
        conf = config.get_config()
        if conf.get("enhancedDeckStats", False):
            # Pre-fetch stats
            try:
                # Same query as in deck_tree_updater.py
                rows = self.mw.col.db.all("select did, queue, count() from cards group by did, queue")
                enhanced_stats = {}
                for did, queue, count in rows:
                    if did not in enhanced_stats:
                        enhanced_stats[did] = {"total": 0, "buried": 0, "suspended": 0, "new": 0, "learn": 0, "review": 0}
                    
                    stats = enhanced_stats[did]
                    stats["total"] += count
                    
                    if queue < 0:
                        if queue == -1: stats["suspended"] += count
                        elif queue == -2 or queue == -3: stats["buried"] += count
                    elif queue == 0: stats["new"] += count
                    elif queue == 1 or queue == 3: stats["learn"] += count
                    elif queue == 2: stats["review"] += count
                
                # Attach to instance
                self._onigiri_enhanced_stats = enhanced_stats
                # print(f"Onigiri: Pre-fetched enhanced stats for {len(enhanced_stats)} decks")
            except Exception as e:
                print(f"Onigiri: Error pre-fetching enhanced stats: {e}")
                self._onigiri_enhanced_stats = None
        else:
             self._onigiri_enhanced_stats = None

    except Exception as e:
        print(f"Onigiri: Error in _onigiri_render_deck_tree wrapper: {e}")

    # Call original
    return _old_render_deck_tree(self, *args, **kwargs)

# Store original method
from aqt.deckbrowser import DeckBrowser
if not hasattr(DeckBrowser, '_onigiri_patched_render_tree'):
    if hasattr(DeckBrowser, '_render_deck_tree'):
        _old_render_deck_tree = DeckBrowser._render_deck_tree
        DeckBrowser._render_deck_tree = _onigiri_render_deck_tree
        DeckBrowser._onigiri_patched_render_tree = True
    else:
        print("Onigiri: Warning - DeckBrowser._render_deck_tree not found, enhanced stats patch optional skipped.")
