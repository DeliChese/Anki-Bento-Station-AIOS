"""
Hiện đại hóa P0 - A3: profile_page.py
Profile page (ProfileDialog + HTML helpers) — tách từ patcher.py.
"""
import os
import json
import html
import base64
import time
import math
from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView
from . import config
from . import settings
from . import heatmap
from .css_engine import (
    generate_dynamic_css,
    generate_profile_page_background_css,
    generate_deck_browser_backgrounds,
    generate_profile_bar_fix_css,
    generate_icon_css,
)
from .constants import COLOR_LABELS
from .fonts import get_all_fonts


def _get_profile_pic_html(user_name: str, addon_package: str, css_class: str = "profile-pic") -> str:    
    """Generates profile picture HTML (img or default) based on user settings."""
    profile_pic_filename = mw.col.conf.get("modern_menu_profile_picture", "")
    if profile_pic_filename and os.path.exists(os.path.join(mw.addonManager.addonsFolder(addon_package), "user_files", "profile", profile_pic_filename)):
        pic_url = f"/_addons/{addon_package}/user_files/profile/{profile_pic_filename}"
        return f'<img src="{pic_url}" class="{css_class}">'
    else:
        # Use default profile picture when none is selected or file doesn't exist
        default_pic = "bento_station-san.png"
        pic_url = f"/_addons/{addon_package}/system_files/profile_default/{default_pic}"
        return f'<img src="{pic_url}" class="{css_class}">'


def _get_profile_pill_html(conf, addon_package):
    user_name = conf.get("userName", "USER")
    
    # Profile Picture
    pic_html = _get_profile_pic_html(user_name, addon_package, "profile-pic-pill")
    
    return f"""
    <div class="profile-pill">
        {pic_html}
        <span class="profile-name-pill">{user_name}</span>
    </div>
    """

def _get_theme_colors_html(mode, conf):
    colors = conf.get("colors", {}).get(mode, {})
    items_html = ""
    
    # Use COLOR_LABELS for ordering and friendly names
    for key, info in COLOR_LABELS.items():
        if key == "--shadow-sm":
            break
        if key in colors:
            hex_val = colors[key]
            items_html += f"""
            <div class="color-item">
                <div class="color-swatch" style="background-color: {hex_val};"></div>
                <div class="color-info">
                    <span class="color-name">{info['label']}</span>
                    <span class="color-code">{hex_val.upper()}</span>
                </div>
            </div>
            """
            
    return f"""
    <h2 class="section-title">Theme colors ({mode})</h2>
    <div class="color-list">{items_html}</div>
    """

def _get_backgrounds_html(addon_package):
    main_bg_style = ""
    main_text = ""
    sidebar_bg_style = ""
    sidebar_text = ""

    # --- 1. Process Main Background ---
    main_mode = mw.col.conf.get("modern_menu_background_mode", "color")

    if main_mode == "image" or main_mode == "image_color":
        if mw.col.conf.get("modern_menu_background_image_mode", "single") == "separate":
            main_img_file = mw.col.conf.get("modern_menu_background_image_light", "")
        else:
            main_img_file = mw.col.conf.get("modern_menu_background_image", "")
            
        if main_img_file:
            main_img_path = f"/_addons/{addon_package}/user_files/main_bg/{main_img_file}"
            main_bg_style = f"background-image: url('{main_img_path}');"
        else:
            main_bg_style = "" # Use default card color
            main_text = "Image mode selected, but no file chosen."
    
    if main_mode == "color" or main_mode == "image_color":
        # Use the correct color for the current theme in the preview swatch
        if mw.pm.night_mode():
            color = mw.col.conf.get("modern_menu_bg_color_dark", "#2C2C2C")
        else:
            color = mw.col.conf.get("modern_menu_bg_color_light", "#FFFFFF")
        # In combo mode, color is applied first, then image style.
        main_bg_style = f"background-color: {color}; {main_bg_style}"

    elif main_mode == "accent":
        main_bg_style = "background-color: var(--accent-color);"

    # --- 2. Process Sidebar Background ---
    sidebar_mode = mw.col.conf.get("modern_menu_sidebar_bg_mode", "main")

    if sidebar_mode == "main":
        sidebar_bg_style = "" # Use default card color
    else: # custom
        sidebar_type = mw.col.conf.get("modern_menu_sidebar_bg_type", "color")
        if sidebar_type == "image" or sidebar_type == "image_color":
            sidebar_img_file = mw.col.conf.get("modern_menu_sidebar_bg_image", "")
            if sidebar_img_file:
                sidebar_img_path = f"/_addons/{addon_package}/user_files/sidebar_bg/{sidebar_img_file}"
                sidebar_bg_style = f"background-image: url('{sidebar_img_path}');"
            else:
                sidebar_bg_style = ""
                sidebar_text = "Image mode selected, but no file chosen."
        
        if sidebar_type == "color" or sidebar_type == "image_color":
            if mw.pm.night_mode():
                color = mw.col.conf.get("modern_menu_sidebar_bg_color_dark", "#3C3C3C")
            else:
                color = mw.col.conf.get("modern_menu_sidebar_bg_color_light", "#EEEEEE")
            sidebar_bg_style = f"background-color: {color}; {sidebar_bg_style}"

        elif sidebar_type == "accent":
            sidebar_bg_style = "background-color: var(--accent-color);"

    # --- 3. Construct Final HTML ---
    # The title is changed to "Backgrounds" to be more accurate
    return f"""
    <h2 class="section-title">Backgrounds</h2>
    <div class="background-previews">
        <div class="preview-card">
            <div class="preview-image" style="{main_bg_style}">
                <span>{main_text}</span>
            </div>
            <div class="preview-info">Main Background</div>
        </div>
        <div class="preview-card">
            <div class="preview-image" style="{sidebar_bg_style}">
                 <span>{sidebar_text}</span>
            </div>
            <div class="preview-info">Sidebar Background</div>
        </div>
    </div>
    """

def _get_heatmap_data_and_config_for_profile():
    """Helper that calls the main heatmap data provider."""
    return heatmap.get_heatmap_and_config()

_profile_dialog = None

_profile_stats_cache = {
    "html": "",
    "timestamp": 0,
    "timeout": 300  # 5 minutes
}

def _get_stats_html():
    global _profile_stats_cache
    import time
    
    # Return cached if valid
    if time.time() - _profile_stats_cache["timestamp"] < _profile_stats_cache["timeout"] and _profile_stats_cache["html"]:
        return _profile_stats_cache["html"]

    conf = config.get_config()
    show_heatmap = conf.get("showHeatmapOnProfile", True)

    # Calculate today's stats from the database directly
    # This correctly counts only actual reviews from today, not deck resets or other operations
    # type IN (0,1,2,3) filters out manual operations (type 4 = manual rescheduling/resets)
    cards_today, time_today_seconds = mw.col.db.first(
        "select count(), sum(time)/1000 from revlog where type IN (0,1,2,3) and id > ?", 
        (mw.col.sched.day_cutoff - 86400) * 1000
    ) or (0, 0)
    time_today_seconds = time_today_seconds if time_today_seconds is not None else 0
    cards_today = cards_today if cards_today is not None else 0

    time_today_minutes = time_today_seconds / 60
    seconds_per_card = time_today_seconds / cards_today if cards_today > 0 else 0
    
    # --- START: New Retention Calculation ---
    total_reviews, correct_reviews = mw.col.db.first(
        "select count(*), sum(case when ease > 1 then 1 else 0 end) from revlog where type = 1 and id > ?",
        (mw.col.sched.day_cutoff - 86400) * 1000
    ) or (0, 0)
    total_reviews = total_reviews or 0
    correct_reviews = correct_reviews or 0
    retention_percentage = (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0

    if retention_percentage >= 90: stars = 5
    elif retention_percentage >= 70: stars = 4
    elif retention_percentage >= 50: stars = 3
    elif retention_percentage >= 30: stars = 2
    elif total_reviews > 0: stars = 1
    else: stars = 0
    
    star_html = "".join([f"<i class='star{' empty' if i >= stars else ''}'></i>" for i in range(5)])

    retention_stat_html = f"""
    <div class="stat-card retention-card">
        <h3>Retention</h3>
        <p>{retention_percentage:.0f}%</p>
        <div class="star-rating">{star_html}</div>
    </div>
    """
    # --- END: New Retention Calculation ---

    # 2. Generate the HTML for the stats grid
    stats_grid_parts = [] 
    if not conf.get("hideStudiedStat", False):
        stats_grid_parts.append(f"""<div class="stat-card studied-card"><h3>Studied</h3><p>{cards_today} cards</p></div>""")
    if not conf.get("hideTimeStat", False):
        stats_grid_parts.append(f"""<div class="stat-card time-card"><h3>Time</h3><p>{time_today_minutes:.1f} min</p></div>""")
    if not conf.get("hidePaceStat", False):
        stats_grid_parts.append(f"""<div class="stat-card pace-card"><h3>Pace</h3><p>{seconds_per_card:.1f} s/card</p></div>""")
    # Add the retention card to the grid
    if not conf.get("hideRetentionStat", False):
        stats_grid_parts.append(retention_stat_html)

    stats_grid_html = f"""<div class="stats-grid">{''.join(stats_grid_parts)}</div>""" if stats_grid_parts else ""

    heatmap_html = ""
    if show_heatmap:
        heatmap_html = "<div id='onigiri-profile-heatmap-container'></div>"

    # 3. Construct the final HTML for the stats section
    html_content = f"""
    {stats_grid_html}
    <div id='onigiri-profile-heatmap-wrapper' style='margin-top: 20px;'>
        {heatmap_html}
    </div>
    """
    
    # Update cache
    _profile_stats_cache["html"] = html_content
    _profile_stats_cache["timestamp"] = time.time()
    
    return html_content


def _get_profile_header_html(conf, addon_package):
    # This function now ONLY creates the banner background
    bg_style = ""
    bg_mode = mw.col.conf.get("modern_menu_profile_bg_mode", "accent")
    if bg_mode == "image":
        bg_image_file = mw.col.conf.get("modern_menu_profile_bg_image", "")
        if bg_image_file and os.path.exists(os.path.join(mw.addonManager.addonsFolder(addon_package), "user_files", "profile_bg", bg_image_file)):
            bg_url = f"/_addons/{addon_package}/user_files/profile_bg/{bg_image_file}"
        else:
            # Use default background image when none is selected or file doesn't exist
            bg_url = f"/_addons/{addon_package}/system_files/profile_default/bento_station-bg.png"
        bg_style = f"background-image: url('{bg_url}'); background-size: cover; background-position: center;"
    elif bg_mode == "custom":
        light_color = mw.col.conf.get("modern_menu_profile_bg_color_light", "#EEEEEE")
        dark_color = mw.col.conf.get("modern_menu_profile_bg_color_dark", "#3C3C3C")
        bg_style = f"background-color: {light_color};"
    else: # accent
        bg_style = "background-color: var(--accent-color);"

    return f'<div class="profile-header-banner" style="{bg_style}"></div>'

def _generate_profile_html_body():
    conf = config.get_config()
    addon_package = mw.addonManager.addonFromModule(__name__)

    # --- Page Components ---
    banner_html = _get_profile_header_html(conf, addon_package)
    profile_pill_html = _get_profile_pill_html(conf, addon_package)

    theme_page_content = ""
    stats_page_content = ""

    # These variable definitions were missing and have been restored.
    show_light = mw.col.conf.get("onigiri_profile_show_theme_light", True)
    show_dark = mw.col.conf.get("onigiri_profile_show_theme_dark", True)
    show_bgs = mw.col.conf.get("onigiri_profile_show_backgrounds", True)

    if show_light: theme_page_content += _get_theme_colors_html("light", conf)
    if show_dark: theme_page_content += _get_theme_colors_html("dark", conf)
    if show_bgs: theme_page_content += _get_backgrounds_html(addon_package)
    if not theme_page_content:
        theme_page_content = '<p class="empty-section">Theme sections are hidden in settings.</p>'

    if conf.get("showHeatmapOnProfile", True):
        stats_page_content = _get_stats_html()
    else:
        stats_page_content = '<p class="empty-section">Stats section is hidden in settings.</p>'


    share_svg_icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/></svg>"""
    export_button_html = f"""
    <button id="export-btn" class="page-export-button" title="Share Profile">
        {share_svg_icon}
    </button>
    """
    
    return f"""
    <div class="onigiri-profile-page">
        {banner_html}

        <div class="profile-controls">
            <div class="controls-spacer"></div>
            {profile_pill_html}
            
            <button id="nav-theme" class="nav-button">Themes</button>
            <button id="nav-stats" class="nav-button">Stats</button>
            
            {export_button_html}
        </div>

        <div class="profile-content-wrapper">
            <main>
                <div id="page-theme">{theme_page_content}</div>
                <div id="page-stats">{stats_page_content}</div>
            </main>
        </div>
    </div>
    """

class ProfileDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Your Bento Station Profile")
        self.setMinimumSize(500, 600)
        self.setMaximumSize(700, 900)
        self.web = AnkiWebView(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.web)
        self.setLayout(layout)

        addon_package = mw.addonManager.addonFromModule(__name__)
        body_html = _generate_profile_html_body()
        
        # Inject the dynamic theme CSS and the custom profile page BG CSS
        head_html = generate_dynamic_css(config.get_config())
        head_html += generate_profile_page_background_css()

        css_files = [
            f"/_addons/{addon_package}/web/profile.css",
            f"/_addons/{addon_package}/web/heatmap.css" # Add heatmap CSS
        ]
        
        js_files = [
            f"/_addons/{addon_package}/web/lib/html2canvas.min.js",
            f"/_addons/{addon_package}/web/profile_page.js",
            f"/_addons/{addon_package}/web/heatmap.js"
        ]

        self.web.stdHtml(body_html, css=css_files, js=js_files, head=head_html, context=self)
        
        # After webview is set up, run javascript to render heatmap
        heatmap_data, heatmap_config = _get_heatmap_data_and_config_for_profile()
        self.web.eval(f"""
            if (document.getElementById('onigiri-profile-heatmap-container')) {{
                OnigiriHeatmap.render('onigiri-profile-heatmap-container', {json.dumps(heatmap_data)}, {json.dumps(heatmap_config)});
            }}
        """)


def open_profile():
    """Wrapper function to open the profile page dialog."""
    global _profile_dialog
    if _profile_dialog is not None:
        _profile_dialog.close()
    _profile_dialog = ProfileDialog(mw)
    _profile_dialog.show()

show_profile_page = open_profile

