# ═══════════════════════════════════════════════════════════════
# Original code/structure from Onigiri Add-on.
# Customized and expanded for Bento Station AIOS.
# ═══════════════════════════════════════════════════════════════
import os
import json
import random
from aqt import mw, gui_hooks
from aqt.deckbrowser import DeckBrowser
from . import bento_station_renderer
from aqt.reviewer import Reviewer
from aqt.overview import Overview
from aqt.toolbar import Toolbar, BottomBar
from aqt.qt import QWidget, QHBoxLayout, QPushButton, Qt, QToolBar, QAction, QTimer
from . import patcher
from . import settings
from . import config
from . import menu_buttons
from . import welcome_dialog
from . import deck_tree_updater
from . import webview_handlers
from . import birthday_dialog
from . import icon_chooser
from . import animated_mascot
from . import future_letter_dialog
from . import heatmap

# 🧩 Bento Forge Bridge — nối Xưởng chế tạo thẻ từ vựng/AI vào Bento Station
from . import bento_forge_bridge


addon_path = os.path.dirname(__file__)
addon_package = mw.addonManager.addonFromModule(__name__)
user_files_root = f"/_addons/{addon_package}/user_files"
web_assets_root = f"/_addons/{addon_package}/web"

# Make addon_path available to other modules
import sys
sys.modules[__name__].addon_path = addon_path

def generate_notification_position_css(conf):
    """Generates CSS for notification positioning logic."""
    pos = conf.get("onigiri_reviewer_notification_position", "top-right")
    
    css = ".onigiri-notification-stack { "
    
    # Defaults (resetting properties that might conflict)
    css += "top: auto; bottom: auto; left: auto; right: auto; transform: none; "
    
    # Base top offset calculation: Header Offset + 20px padding
    top_offset = "calc(var(--onigiri-reviewer-header-offset, 0px) + 5px)"
    
    if pos == "top-left":
        css += f"top: {top_offset}; left: 20px; align-items: flex-start; flex-direction: column; "
    elif pos == "top-center":
        css += f"top: {top_offset}; left: 50%; transform: translateX(-50%); align-items: center; flex-direction: column; "
    elif pos == "top-right":
        css += f"top: {top_offset}; right: 20px; align-items: flex-end; flex-direction: column; "
    elif pos == "bottom-left":
        css += "bottom: 20px; left: 20px; align-items: flex-start; flex-direction: column-reverse; "
    elif pos == "bottom-center":
        css += "bottom: 20px; left: 50%; transform: translateX(-50%); align-items: center; flex-direction: column-reverse; "
    elif pos == "bottom-right":
        css += "bottom: 20px; right: 20px; align-items: flex-end; flex-direction: column-reverse; "
    else:
        # Fallback to top-right
        css += f"top: {top_offset}; right: 20px; align-items: flex-end; flex-direction: column; "
        
    css += "}"
    return f"<style>{css}</style>"

def inject_menu_files(web_content, context):
    conf = config.get_config()
    should_hide = conf.get("hideNativeHeaderAndBottomBar", False)
    is_deck_browser = isinstance(context, DeckBrowser)
    is_reviewer = isinstance(context, Reviewer)
    is_overview = isinstance(context, Overview)
    is_top_toolbar = isinstance(context, Toolbar)
    is_bottom_toolbar = isinstance(context, BottomBar)
    is_reviewer_bottom_bar = type(context).__name__ == "ReviewerBottomBar"
    # Inject global Onigiri CSS only for deck browser and overview, NOT reviewer
    # Reviewer has its own dedicated CSS and doesn't need text-related global styles
    if is_deck_browser or is_overview:
        web_content.head += patcher.generate_dynamic_css(conf)
    if is_deck_browser:
        css_path = os.path.join(addon_path, "web", "menu.css")
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                web_content.head += f"<style>{f.read()}</style>"
        except FileNotFoundError:
            pass
        heatmap_css_path = os.path.join(addon_path, "web", "heatmap.css")
        try:
            with open(heatmap_css_path, "r", encoding="utf-8") as f:
                web_content.head += f"<style>{f.read()}</style>"
        except FileNotFoundError:
            pass
        web_content.head += patcher.generate_profile_bar_fix_css()
        web_content.head += patcher.generate_deck_browser_backgrounds(addon_path)
        web_content.head += patcher.generate_icon_css(addon_package, conf)
        web_content.head += patcher.generate_conditional_css(conf)
        web_content.head += patcher.generate_icon_size_css()
        web_content.head += f'<link rel="stylesheet" href="{web_assets_root}/notifications.css">'
        web_content.head += f'<script src="{web_assets_root}/injector.js"></script>'
        web_content.head += f'<script src="{web_assets_root}/engine.js"></script>'
        web_content.head += f'<script src="{web_assets_root}/heatmap.js"></script>'
        web_content.head += f'<script src="{web_assets_root}/notifications.js"></script>'
        # 🎌 Animated Mascot (Nakama)
        web_content.head += animated_mascot.get_mascot_head_content("deck_browser")
        
    elif is_reviewer:
        web_content.head += f'<link rel="stylesheet" href="{web_assets_root}/notifications.css">'
        web_content.head += generate_notification_position_css(conf)
        web_content.head += patcher.generate_reviewer_background_css(addon_path)
        web_content.head += patcher.generate_reviewer_buttons_css(conf)
        top_bar_html, top_bar_css = patcher.generate_reviewer_top_bar_html_and_css()
        web_content.head += top_bar_css
        escaped_top_bar_html = top_bar_html.replace("`", "\\`")
        js_injector = f"""
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                if (!document.getElementById('onigiri-background-div')) {{
                    const bgDiv = document.createElement('div');
                    bgDiv.id = 'onigiri-background-div';
                    document.body.prepend(bgDiv);
                }}

                const insertTopBar = () => {{
                    const topBarHtml = `{escaped_top_bar_html}`;
                    if (!topBarHtml.trim()) {{
                        return null;
                    }}
                    let headerEl = document.getElementById('onigiri-reviewer-header');
                    if (!headerEl) {{
                        document.body.insertAdjacentHTML('afterbegin', topBarHtml);
                        headerEl = document.getElementById('onigiri-reviewer-header');
                    }}
                    return headerEl;
                }};

                const headerEl = insertTopBar();
                if (!headerEl) {{
                    return;
                }}

                // 🎌 Animated Mascot: create container if config exists
                if (window.__ONIGIRI_MASCOT_CONFIG__) {{
                    if (!document.getElementById('onigiri-mascot-container')) {{
                        const mascotHTML = `{animated_mascot.generate_mascot_html("reviewer").strip().replace("`", "\\`")}`;
                        if (mascotHTML.trim()) {{
                            document.body.insertAdjacentHTML('beforeend', mascotHTML);
                        }}
                    }}
                }}

                const updateHeaderOffset = () => {{
                    const header = document.getElementById('onigiri-reviewer-header');
                    if (!header) {{
                        return;
                    }}
                    const styles = window.getComputedStyle(header);
                    const marginTop = parseFloat(styles.marginTop) || 0;
                    const marginBottom = parseFloat(styles.marginBottom) || 0;
                    const offset = header.offsetHeight + marginTop + marginBottom;
                    document.body.style.setProperty('--onigiri-reviewer-header-offset', `${{Math.ceil(offset)}}px`);
                }};

                updateHeaderOffset();
                window.addEventListener('resize', updateHeaderOffset);

                if ('ResizeObserver' in window) {{
                    const resizeObserver = new ResizeObserver(updateHeaderOffset);
                    resizeObserver.observe(headerEl);
                }} else {{
                    // As a fallback, re-run after layout-affecting mutations.
                    const mutationObserver = new MutationObserver(updateHeaderOffset);
                    mutationObserver.observe(document.body, {{ attributes: true, childList: false, subtree: false }});
                }}
            }});
        </script>
        """
        web_content.head += js_injector
        web_content.head += f'<script src="{web_assets_root}/notifications.js"></script>'
        # 🎌 Animated Mascot (Nakama) - Reviewer
        web_content.head += animated_mascot.get_mascot_head_content("reviewer")
    elif is_overview:
        web_content.head += f'<link rel="stylesheet" href="{web_assets_root}/notifications.css">'
        web_content.head += patcher.generate_overview_background_css(addon_path)
        _top_bar_html, top_bar_css = patcher.generate_reviewer_top_bar_html_and_css()
        web_content.head += top_bar_css
        css_path = os.path.join(addon_path, "web", "overview.css")
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                web_content.head += f"<style>{f.read()}</style>"
        except FileNotFoundError:
            pass
        web_content.head += f'<script src="{web_assets_root}/notifications.js"></script>'
        # 🎌 Animated Mascot (Nakama) - Overview
        web_content.head += animated_mascot.get_mascot_head_content("overview")
    if is_reviewer_bottom_bar:
        web_content.head += patcher.generate_reviewer_bottom_bar_background_css(addon_path)
        web_content.head += patcher.generate_reviewer_buttons_css(conf)
    elif (is_top_toolbar or is_bottom_toolbar):
        if not should_hide:
            web_content.head += patcher.generate_toolbar_background_css(addon_path)

# Delegate to the webview_handlers module
_on_webview_cmd = webview_handlers.handle_webview_cmd

def maybe_show_welcome_popup():
    """Shows the welcome pop-up if it hasn't been disabled by the user."""
    conf = config.get_config()
    
    # Check if we should force show based on version
    last_seen_version = conf.get("lastSeenWelcomeVersion", "")
    current_version = welcome_dialog.CURRENT_WELCOME_VERSION
    
    # Force show if version doesn't match, OR if user hasn't opted out
    should_show = (last_seen_version != current_version) or conf.get("showWelcomePopup", True)
    
    if should_show:
        welcome_dialog.show_welcome_dialog()


def apply_full_hide_mode():
    """Hide the menu bar on Windows and Linux if Full Hide Mode is enabled"""
    import platform
    conf = config.get_config()
    full_hide = conf.get("fullHideMode", False)
    
    # Only hide menu bar on Windows and Linux, not macOS
    system = platform.system()
    if full_hide and system in ["Windows", "Linux"]:
        if hasattr(mw, 'menuBar') and mw.menuBar():
            mw.menuBar().hide()
    else:
        if hasattr(mw, 'menuBar') and mw.menuBar():
            mw.menuBar().show()


def setup_global_hooks():
    """
    Sets up global hooks and initial patches that do NOT depend on a loaded profile.
    This runs when the main window initializes.
    """
    # Move UI patching to initial_setup so it happens after mw.col is initialized.
    # We rely on using 'wrap' for compatibility, so it's safe to run this later.
    patcher.apply_patches()
    menu_buttons.setup_onigiri_menu(addon_path)

    # 🧩 Bento Forge: import một lần (đăng ký reviewer/overview hooks + menu Tools).
    #   Chống lỗi: nếu Forge thiếu/lỗi, Bento Station vẫn chạy bình thường.
    bento_forge_bridge.initialize_forge()

def on_profile_did_open():
    """
    Runs when a profile is successfully loaded.
    Logic that requires access to `mw.col` (collection/database/config) goes here.
    """
    # Now it is safe to patch overview since mw.col is available
    patching.apply_overview_patch()
    # Hiện đại hóa P0 - A1: vô hiệu config cache khi đổi profile (path settings thay đổi)
    config.invalidate_config_cache()

    # Apply Full Hide Mode (hide menu bar on Windows/Linux)
    apply_full_hide_mode()

    # Show welcome popup if needed (requires mw.col)
    maybe_show_welcome_popup()

    # Show birthday popup if it's the user's birthday (requires mw.col)
    # Delay by 1s to ensure main window is fully rendered for screenshot blur
    QTimer.singleShot(1000, lambda: birthday_dialog.maybe_show_birthday_popup())

    # GĐ4: Future Self Letter — deliver old letters / prompt to write at milestones
    QTimer.singleShot(1600, lambda: future_letter_dialog.maybe_check_milestones())

    # 🧩 Bento Forge: đồng bộ cấu hình (API key DeepSeek / model / cache) giữa
    #   config Bento Station (một nơi duy nhất) và Bento Forge (ai_config.json).
    try:
        bento_forge_bridge.ensure_config_sync()
        bento_forge_bridge.configure_cache()
    except Exception:
        pass

    # Re-apply menu styling now that we definitely know the theme
    patcher.apply_menu_styling()

# --- INITIALIZATION ---

# Move UI patching to top-level so it happens during module load.
# This ensures Onigiri's hooks and wraps are established before other add-ons
# might overwrite them, and prevents unstyled flashes.
# NOTE: patch_congrats_page is safe to run here as it doesn't access mw.col immediately.
from . import patching
patching.apply_congrats_patch()

# Initialize renderer immediately (version-guarded — Hiện đại hóa P0-A2)
# Patch _render_deck_node at top-level to ensure it's applied before first render.
# This is critical - if done later (in apply_patches via main_window_did_init),
# the initial deck browser render would use Anki's default, missing icons/counts.
patching.apply_deck_browser_render_patches()

def on_deck_browser_did_render(deck_browser: DeckBrowser):
    conf = config.get_config()
    grid_layout = conf.get("onigiriWidgetLayout", {}).get("grid", {})
    if "heatmap" in grid_layout:
        try:
            heatmap_data, heatmap_config = heatmap.get_heatmap_and_config()
            js = f"OnigiriHeatmap.render('onigiri-heatmap-container', {json.dumps(heatmap_data)}, {json.dumps(heatmap_config)});"
            deck_browser.web.eval(js)
        except Exception as e:
            pass

    # GĐ3: Streak Insurance — check if yesterday was missed, auto-protect with a token
    try:
        from . import habit_engine
        result = habit_engine.maybe_protect_streak()
        if result is not None:
            if result.get("protected"):
                js = (
                    "if (typeof OnigiriNotifications !== 'undefined') {"
                    "OnigiriNotifications.show({"
                    f"name: 'Streak protected!',"
                    f"description: 'A streak token was used to cover yesterday. {result.get('remaining', 0)} token(s) left.',"
                    "icon: '🛡️',"
                    "variant: 'success',"
                    "duration: 6000"
                    "});}"
                )
            else:
                js = (
                    "if (typeof OnigiriNotifications !== 'undefined') {"
                    "OnigiriNotifications.show({"
                    "name: 'Streak broken',"
                    "description: 'No review yesterday and no streak tokens left. Today is a fresh start!',"
                    "icon: '💪',"
                    "variant: 'info',"
                    "duration: 6000"
                    "});}"
                )
            deck_browser.web.eval(js)
    except Exception:
        pass

    # Update sync status indicator
    update_sync_status_indicator()

# ⚡ Last sync status to avoid redundant web.eval calls
_SYNC_LAST_STATUS = None

def update_sync_status_indicator():
    """Updates the sync status indicator in the Onigiri menu."""
    global _SYNC_LAST_STATUS
    try:
        sync_status = patcher.get_sync_status()
        # Skip if status hasn't changed
        if sync_status == _SYNC_LAST_STATUS:
            return
        _SYNC_LAST_STATUS = sync_status
        if hasattr(mw, 'deckBrowser') and hasattr(mw.deckBrowser, 'web') and mw.deckBrowser.web:
            mw.deckBrowser.web.eval(f"if(typeof SyncStatusManager!=='undefined')SyncStatusManager.setSyncStatus('{sync_status}');")
    except Exception:
        pass

def on_state_change(new_state, old_state):
    """Called when Anki's state changes - update sync indicator."""
    update_sync_status_indicator()
      
def on_deck_browser_will_show(deck_browser: DeckBrowser):
    """
    Ensures that Onigiri takes control of external hooks at the last possible moment,
    right before the deck browser is displayed for the first time. This guarantees
    that other add-ons have had time to register their hooks.
    """
    patcher.take_control_of_deck_browser_hook()

def on_show_icon_chooser(deck_id):
    """Opens the dialog to choose a custom icon for the deck."""
    dialog = icon_chooser.IconChooserDialog(deck_id, mw)
    if dialog.exec():
        # Refresh the deck browser to show changes immediately
        mw.deckBrowser.refresh()

def on_deck_options_shown(menu, deck_id):
    """Appends the 'Change Icon' action to the deck options menu."""
    a = menu.addAction("Change Icon")
    a.triggered.connect(lambda _, did=deck_id: on_show_icon_chooser(did))

# ═══════════════════════════════════════════════════════════
# 🎌 SAKURA RPG: EXP Awarding Hook
# ═══════════════════════════════════════════════════════════

def _on_reviewer_did_answer_card(reviewer: Reviewer, card, ease):
    """Awards EXP when the user answers a card. EXP scales with card type, memory strength, and performance."""
    try:
        # Habit Engine: invalidate telemetry cache so today's effort stays fresh,
        # and track today's progress for streak insurance tokens (GĐ3)
        try:
            from . import habit_engine
            habit_engine.invalidate_cache()
            habit_engine.track_today_review()
        except Exception:
            pass
        # --- Card Type Analysis ---
        # card.type: 0=new, 1=learning, 2=review, 3=relearning
        # card.queue: -1=suspended, 0=new, 1=learning, 2=review, 3=day-learn, 4=preview
        card_type = getattr(card, 'type', 0)
        card_queue = getattr(card, 'queue', 0)
        interval = getattr(card, 'ivl', 0) or 0       # Days until next review
        reps = getattr(card, 'reps', 0) or 0           # Total times reviewed
        lapses = getattr(card, 'lapses', 0) or 0       # Times forgotten
        
        # --- Base EXP by Card State ---
        if card_type == 0 or card_queue == 0:   # New card - first time seeing it
            base_exp = 15
            card_label = "New"
        elif card_type == 3:                     # Relearning (forgotten card)
            base_exp = 5
            card_label = "Relearn"
        elif card_type == 1:                     # Learning (in progress)
            base_exp = 10
            card_label = "Learning"
        else:                                    # Review (mature card)
            base_exp = 8
            card_label = "Review"
        
        # --- Ease Multiplier (performance-based) ---
        # Again=1, Hard=2, Good=3, Easy=4
        ease_multiplier = {1: 0.5, 2: 0.75, 3: 1.0, 4: 1.5}
        multiplier = ease_multiplier.get(ease, 1.0)
        
        # --- Memory Strength Bonus (interval-based, only for review cards) ---
        # Longer interval = stronger memory = more EXP
        interval_bonus = 0
        if card_type == 2 or card_type == 1:  # Review or Learning
            if interval >= 365:      # 1 year+ → huge bonus
                interval_bonus = 15
                card_label = "Master"
            elif interval >= 180:    # 6 months+
                interval_bonus = 10
            elif interval >= 90:     # 3 months+
                interval_bonus = 7
            elif interval >= 30:     # 1 month+
                interval_bonus = 5
            elif interval >= 7:      # 1 week+
                interval_bonus = 3
            elif interval >= 1:      # 1 day+
                interval_bonus = 1
        
        # --- Dedication Bonus (total reviews on this card) ---
        # Rewards persistent study of the same card
        dedication_bonus = min(reps * 0.3, 10)  # Max +10 for 33+ reviews
        
        # --- Lapse Penalty ---
        # Cards that keep being forgotten give slightly less
        lapse_penalty = min(lapses * 0.5, 5)  # Max -5 for 10+ lapses
        
        # --- Final EXP Calculation ---
        exp_gained = max(1, int((base_exp + interval_bonus + dedication_bonus - lapse_penalty) * multiplier))
        
        leveled_up, new_level = bento_station_renderer.award_exp(exp_gained)
        
        # --- Show toast in the REVIEWER webview (not deck browser) ---
        if hasattr(reviewer, 'web') and reviewer.web:
            if leveled_up:
                reviewer.web.eval(f"""
                    if (typeof OnigiriExpToast !== 'undefined') {{
                        OnigiriExpToast.show({exp_gained}, true, {new_level}, '{card_label}');
                    }}
                    if (typeof OnigiriMascot !== 'undefined' && OnigiriMascot.onLevelUp) {{
                        OnigiriMascot.onLevelUp({new_level});
                    }}
                """)
            elif ease >= 3:
                # Good/Easy answer → happy mascot
                reviewer.web.eval(f"""
                    if (typeof OnigiriExpToast !== 'undefined') {{
                        OnigiriExpToast.show({exp_gained}, false, 0, '{card_label}');
                    }}
                    if (typeof OnigiriMascot !== 'undefined' && OnigiriMascot.onCorrectAnswer) {{
                        OnigiriMascot.onCorrectAnswer();
                    }}
                """)
            else:
                # Again/Hard answer → sad mascot
                reviewer.web.eval(f"""
                    if (typeof OnigiriExpToast !== 'undefined') {{
                        OnigiriExpToast.show({exp_gained}, false, 0, '{card_label}');
                    }}
                    if (typeof OnigiriMascot !== 'undefined' && OnigiriMascot.onWrongAnswer) {{
                        OnigiriMascot.onWrongAnswer();
                    }}
                """)
        
        # Store pending notification for deck browser (persistent, survives page reload)
        pending = mw.col.conf.get("onigiri_pending_exp", {"amount": 0, "leveled_up": False, "new_level": 0, "label": ""})
        pending["amount"] = pending.get("amount", 0) + exp_gained
        if leveled_up:
            pending["leveled_up"] = True
            pending["new_level"] = new_level
        pending["label"] = card_label
        mw.col.conf["onigiri_pending_exp"] = pending
        mw.col.setMod()
    except Exception as e:
        pass  # Silently fail - EXP is cosmetic

# ═══════════════════════════════════════════════════════════
# 🎌 SAKURA RPG: Toast & Level Bar JS/CSS Injection
# ═══════════════════════════════════════════════════════════

# Minimal toast CSS injected into reviewer (since menu.css is only for deck browser)
_EXP_TOAST_CSS = """
<style id="onigiri-exp-toast-style">
.onigiri-exp-toast {
    position: fixed;
    top: 20px;
    left: 20px;
    transform: translateX(-120%);
    background: linear-gradient(135deg, #2d2d2d 0%, #1a1a2e 100%);
    color: #fff;
    padding: 12px 24px;
    border-radius: 16px;
    font-size: 14px;
    font-weight: 700;
    z-index: 10000;
    pointer-events: none;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    border: 1px solid rgba(255, 183, 197, 0.3);
    transition: transform 0.5s cubic-bezier(0.22, 0.61, 0.36, 1), opacity 0.4s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
    opacity: 1;
}
.onigiri-exp-toast.show {
    transform: translateX(0);
}
.onigiri-exp-toast.hide {
    transform: translateX(0) translateY(-30px);
    opacity: 0;
    transition: transform 0.5s cubic-bezier(0.55, 0, 1, 0.45), opacity 0.5s ease;
}
.onigiri-exp-toast .exp-icon {
    font-size: 20px;
}
.onigiri-exp-toast .exp-amount {
    color: #ffd700;
    font-size: 16px;
    font-weight: 800;
}
.onigiri-exp-toast .exp-label {
    font-size: 11px;
    opacity: 0.7;
    margin-left: 4px;
}
.onigiri-exp-toast.level-up-toast {
    background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
    border-color: rgba(255,255,255,0.5);
    color: #1a1a2e;
}
.onigiri-exp-toast.level-up-toast .exp-amount {
    color: #1a1a2e;
}
</style>
"""

# Standalone toast JS for reviewer (no DOM dependency on level bar container)
_EXP_TOAST_JS = """
<script>
const OnigiriExpToast = {
    show: function(amount, leveledUp, newLevel, cardLabel) {
        var toast = document.createElement('div');
        toast.className = 'onigiri-exp-toast' + (leveledUp ? ' level-up-toast' : '');
        if (leveledUp) {
            toast.innerHTML = '<span class="exp-icon">\\u2B50</span> LEVEL UP! <span class="exp-amount">LV ' + newLevel + '</span> (+' + amount + ' EXP)';
        } else {
            var labelHtml = cardLabel ? '<span class="exp-label">[' + cardLabel + ']</span>' : '';
            toast.innerHTML = '<span class="exp-icon">\\u2728</span> +<span class="exp-amount">' + amount + '</span> EXP' + labelHtml;
        }
        document.body.appendChild(toast);
        // Slide in from left
        requestAnimationFrame(function() { toast.classList.add('show'); });
        // Fade out and slide up
        setTimeout(function() {
            toast.classList.add('hide');
            setTimeout(function() { toast.remove(); }, 550);
        }, 2200);
    }
};
</script>
"""

# Full level bar JS for deck browser (has DOM dependency on #onigiri-level-bar-container)
_LEVEL_BAR_JS = """
<script>
const OnigiriLevelBar = {
    init: function() {
        var container = document.getElementById('onigiri-level-bar-container');
        if (!container) return;
        this.container = container;
        this.fillBar = container.querySelector('.level-bar-fill');
    },

    refresh: function() {
        if (!this.fillBar) return;
        this.fillBar.classList.add('exp-gained');
        setTimeout(function() { this.fillBar.classList.remove('exp-gained'); }.bind(this), 600);
    }
};

// Also define toast for deck browser context
var OnigiriExpToast = {
    show: function(amount, leveledUp, newLevel, cardLabel) {
        var toast = document.createElement('div');
        toast.className = 'onigiri-exp-toast' + (leveledUp ? ' level-up-toast' : '');
        if (leveledUp) {
            toast.innerHTML = '<span class="exp-icon">\\u2B50</span> LEVEL UP! <span class="exp-amount">LV ' + newLevel + '</span> (+' + amount + ' EXP)';
        } else {
            var labelHtml = cardLabel ? '<span class="exp-label">[' + cardLabel + ']</span>' : '';
            toast.innerHTML = '<span class="exp-icon">\\u2728</span> +<span class="exp-amount">' + amount + '</span> EXP' + labelHtml;
        }
        document.body.appendChild(toast);
        requestAnimationFrame(function() { toast.classList.add('show'); });
        setTimeout(function() {
            toast.classList.add('hide');
            setTimeout(function() { toast.remove(); }, 550);
        }, 2200);
        OnigiriLevelBar.refresh();
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { OnigiriLevelBar.init(); });
} else {
    OnigiriLevelBar.init();
}
</script>
"""

# Inject JS/CSS into both deck browser AND reviewer
_inject_menu_files_original = inject_menu_files
def inject_menu_files_with_level_bar(web_content, context):
    _inject_menu_files_original(web_content, context)
    if isinstance(context, DeckBrowser):
        web_content.head += _LEVEL_BAR_JS
    elif isinstance(context, Reviewer):
        web_content.head += _EXP_TOAST_CSS
        web_content.head += _EXP_TOAST_JS

inject_menu_files = inject_menu_files_with_level_bar

# Hook Registration
gui_hooks.main_window_did_init.append(setup_global_hooks)
gui_hooks.profile_did_open.append(on_profile_did_open)
gui_hooks.webview_will_set_content.append(inject_menu_files)
gui_hooks.deck_browser_did_render.append(on_deck_browser_did_render)
gui_hooks.webview_did_receive_js_message.append(patcher.on_webview_js_message)
# MODIFICATION: Use the current, correct hook instead of the outdated one.
gui_hooks.webview_did_receive_js_message.append(_on_webview_cmd)
# Update sync status when state changes
gui_hooks.state_did_change.append(on_state_change)
# Update sync status after sync completes
gui_hooks.sync_did_finish.append(lambda: update_sync_status_indicator())
# Update sync status after operations that modify the collection
gui_hooks.operation_did_execute.append(lambda *args: update_sync_status_indicator())
# Update sync status when sync status changes
gui_hooks.sync_will_start.append(lambda: update_sync_status_indicator())
gui_hooks.deck_browser_will_show_options_menu.append(on_deck_options_shown)
gui_hooks.theme_did_change.append(patcher.apply_menu_styling)
# 🎌 SAKURA RPG: EXP hook
gui_hooks.reviewer_did_answer_card.append(_on_reviewer_did_answer_card)
mw.addonManager.setWebExports(__name__, r"(.*)")