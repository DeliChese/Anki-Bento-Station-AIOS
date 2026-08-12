# Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.
"""Tách từ css_engine.py (Bước 2 refactor) — di chuyển nguyên vẹn, không đổi logic."""
import os
import re
import json
import html
import base64
import time
import math
from aqt import mw
from .. import config
from .. import fonts
from .. import icon_registry
from ..constants import COLOR_LABELS
from ..fonts import get_all_fonts


def generate_font_css(addon_package):
    """Generates @font-face rules and CSS variables for selected fonts."""
    main_font_key = mw.col.conf.get("onigiri_font_main", "system")
    subtle_font_key = mw.col.conf.get("onigiri_font_subtle", "system")
    small_title_font_key = mw.col.conf.get("onigiri_font_small_title", "system")
    
    # --- NEW: Font Sizes ---
    main_font_size = mw.col.conf.get("onigiri_font_size_main", 14)
    subtle_font_size = mw.col.conf.get("onigiri_font_size_subtle", 20)
    small_title_font_size = mw.col.conf.get("onigiri_font_size_small_title", 15)
    # -----------------------
    
    # <<< MODIFIED: Use get_all_fonts to include user-added fonts >>>
    all_fonts = get_all_fonts(os.path.dirname(__file__))
    main_font_info = all_fonts.get(main_font_key)
    subtle_font_info = all_fonts.get(subtle_font_key)
    small_title_font_info = all_fonts.get(small_title_font_key)
    # <<< END MODIFIED >>>

    if not main_font_info or not subtle_font_info or not small_title_font_info:
        return ""

    font_faces = ""
    # Use a set to avoid generating duplicate @font-face rules
    fonts_to_load = {main_font_key, subtle_font_key, small_title_font_key}
    
    # <<< MODIFIED: Loop through all fonts to generate @font-face rules >>>
    for font_key in fonts_to_load:
        font_info = all_fonts.get(font_key)
        if font_info and font_info.get("file"):
            # Handle different paths for user vs system fonts
            if font_info.get("user"):
                font_url = f"/_addons/{addon_package}/user_files/fonts/{font_info['file']}"
            else:
                font_url = f"/_addons/{addon_package}/system_files/fonts/system_fonts/{font_info['file']}"
            
            font_faces += f"""
                @font-face {{
                    font-family: '{font_info['family']}';
                    src: url('{font_url}');
                }}
            """
    # <<< END MODIFIED >>>

    # Generate the final CSS block
    font_css = f"""
    <style id="onigiri-font-styles">
        {font_faces}
        :root {{
            --font-main: {main_font_info['family']};
            --font-subtle: {subtle_font_info['family']};
            --font-small-title: {small_title_font_info['family']};
            --font-size-main: {main_font_size}px;
            --font-size-subtle: {subtle_font_size}px;
            --font-size-small-title: {small_title_font_size}px;
        }}
        
        /* Apply fonts to specific elements */
        #onigiri-reveal-btn {{
            font-family: var(--font-main) !important;
            box-shadow: none !important;
            border: none !important;
        }}
        
        #study, .mini-overview #study {{
            font-family: var(--font-main) !important;
        }}
        
        body:not(.card) {{
            font-family: var(--font-main), -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
            font-size: var(--font-size-main) !important;
        }}
        
        /* Apply font size to specific elements explicitly if needed */
        .deck-table a.deck {{
             font-size: var(--font-size-main) !important;
        }}
        
        /* Titles (Subtle) - e.g. Today's Stats */
        .onigiri-widget-title {{
            font-family: var(--font-subtle), -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
            font-size: var(--font-size-subtle) !important;
        }}

        /* Small Titles - Sidebar Headers and Widget Titles */
        .sidebar-left h2, .stat-card h3, .onigiri-widget-container h3 {{
            font-family: var(--font-small-title), -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
            font-size: var(--font-size-small-title) !important;
        }}
    </style>
    """
    
    return font_css
