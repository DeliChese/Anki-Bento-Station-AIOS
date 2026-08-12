"""
Hiện đại hóa P0 - A3: toolbar_styling.py
Menu styling, QMenu patch, sync status, toolbar visibility — tách từ patcher.py.

Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.
"""
import os
import re
import time
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.main import MainWebView
from . import config


def apply_menu_styling():
    """
    Applies modern styling to QMenu widgets (context menus) using Qt Style Sheets.
    This gives the 'Options' menu and others a rounded, modern look.
    """
    # 1. Determine which colors to use based on the current mode
    # Safely check for night mode; default to False if PM not ready
    night_mode = False
    if mw.col:
        # If collection is loaded, use its schedule/display preferences if applicable, 
        # but mw.pm.night_mode() is the standard check.
        night_mode = mw.pm.night_mode()
    elif mw.pm:
        night_mode = mw.pm.night_mode()

    # 2. Define Colors
    if night_mode:
        bg_color = "#2c2c2c"
        border_color = "#424242"
        text_color = "#e0e0e0"
        hover_bg = "#3c3c3c" # Highlight background
        hover_text = "#ffffff"
    else:
        bg_color = "#ffffff"
        border_color = "#d0d0d0"
        text_color = "#000000"
        hover_bg = "#e5f1fb" # Light blue-ish highlight
        hover_text = "#000000"

    # 3. Construct the QSS
    new_style_block = f"""
    /* ONIGIRI_MENU_START */
    QMenu {{
        background-color: {bg_color};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 5px;
        color: {text_color};
        font-family: -apple-system, sans-serif;
    }}
    QMenu::item {{
        background-color: transparent;
        padding: 6px 20px 6px 12px;
        border-radius: 12px;
        margin: 2px 4px;
    }}
    QMenu::item:selected {{
        background-color: {hover_bg};
        color: {hover_text};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {border_color};
        margin: 4px 10px;
    }}
    /* ONIGIRI_MENU_END */
    """
    
    # 4. Inject the stylesheet safely (Replace if exists, Append if not)
    app = QApplication.instance()
    if app:
        current_sheet = app.styleSheet()
        
        # Regex to find existing block
        pattern = re.compile(r'/\* ONIGIRI_MENU_START \*/.*?/\* ONIGIRI_MENU_END \*/', re.DOTALL)
        
        if pattern.search(current_sheet):
            # Replace existing block
            updated_sheet = pattern.sub(new_style_block.strip(), current_sheet)
        else:
            # Append new block
            updated_sheet = current_sheet + "\n" + new_style_block.strip()
            
        app.setStyleSheet(updated_sheet)

def patch_qmenu():
    """
    Patches QMenu to enable translucent background, allowing for real rounded corners
    without square artifacts on the window backdrop.
    """
    # We need to monkeypatch the __init__ method of QMenu
    # to set the WA_TranslucentBackground attribute on every new menu instances.
    
    # Store reference to original init
    if hasattr(QMenu, "_onigiri_patched"):
        return

    original_init = QMenu.__init__

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Enable transparency for the window/widget background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    # Apply the patch
    QMenu.__init__ = new_init
    QMenu._onigiri_patched = True


_toolbar_patched = False
_original_MainWebView_eventFilter = None


def get_sync_status():
    """
    Determines the current sync status of the collection.
    Returns 'sync' if any sync is needed, 'none' if no sync needed.
    """
    try:
        # Check if collection is available
        if not mw.col:
            return 'none'
        
        # Get last sync timestamp and modification time from database
        try:
            # Get last sync timestamp from database
            ls = mw.col.db.scalar("select ls from col")
            mod = mw.col.mod if hasattr(mw.col, 'mod') else 0
            
            # If ls is None or 0, we've never synced - no indicator needed yet
            if ls is None or ls == 0:
                return 'none'
            
            # Show sync needed if mod > ls (changes since last sync)
            if mod > ls:
                return 'sync'
        except:
            pass
        
        # No sync needed
        return 'none'
    except:
        return 'none'


def _new_MainWebView_eventFilter(self: MainWebView, obj: QObject, evt: QEvent) -> bool:
	"""Prevents Anki's default hover-to-show-toolbar behavior."""
	conf = config.get_config()
	should_hide_setting = conf.get("hideNativeHeaderAndBottomBar", False)

	screens_to_interfere = ["deckBrowser", "overview", "review"]
	
	should_interfere = should_hide_setting and mw.state in screens_to_interfere

	if should_interfere:
		# On deck browser/overview, prevent Anki's native hover logic from showing toolbars
		if super(MainWebView, self).eventFilter(obj, evt):
			return True
		if evt.type() == QEvent.Type.Leave and self.mw.fullscreen:
			self.mw.show_menubar()
			return True
		# Block other events from reaching the original handler, which would show the toolbars.
		return False
	else:
		# On all other screens (like reviewer), or if the setting is off, use Anki's original logic.
		if _original_MainWebView_eventFilter:
			return _original_MainWebView_eventFilter(self, obj, evt)
		return super(MainWebView, self).eventFilter(obj, evt)


def _update_toolbar_visibility(new_state: str, _old_state: str) -> None:
    """This function is called by a hook every time the screen changes."""
    conf = config.get_config()
    should_hide_setting = conf.get("hideNativeHeaderAndBottomBar", False)
    pro_hide = conf.get("proHide", False)
    max_hide = conf.get("maxHide", False)

    if not should_hide_setting:
        # If the feature is disabled in settings, ensure toolbars are always visible
        mw.toolbar.web.setVisible(True)
        mw.bottomWeb.setVisible(True)
        return

    # Handle reviewer state first with new priority
    if new_state == "review":
        # Always show bottom bar in reviewer, regardless of hide mode
        if max_hide:
            # Max hide: Hide only top toolbar, keep bottom bar visible
            mw.toolbar.web.setVisible(False)
            mw.bottomWeb.setVisible(True)
        elif pro_hide:
            # Pro hide: Hide only top toolbar
            mw.toolbar.web.setVisible(False)
            mw.bottomWeb.setVisible(True)
        else:
            # Base hide mode: Hide top toolbar but keep bottom bar visible
            mw.toolbar.web.setVisible(False)
            mw.bottomWeb.setVisible(True)
        return

    # General hiding logic for other screens
    states_to_hide = ["deckBrowser", "overview"]
    if new_state in states_to_hide:
        # Hide both toolbars on the main menu and deck overview
        mw.toolbar.web.setVisible(False)
        mw.bottomWeb.setVisible(False)
    else:
        # Show toolbars on ALL other screens (this will now exclude the 'review' case when pro_hide is on)
        mw.toolbar.web.setVisible(True)
        mw.bottomWeb.setVisible(True)



def _on_sync_did_finish():
    """Removes the syncing animation from the sync button."""
    try:
        if mw.state == "deckBrowser" and hasattr(mw.deckBrowser, 'web') and mw.deckBrowser.web:
            mw.deckBrowser.web.eval("SyncStatusManager.setSyncing(false);")
        elif mw.state == "overview" and hasattr(mw.overview, 'web') and mw.overview.web:
             mw.overview.web.eval("SyncStatusManager.setSyncing(false);")
        elif mw.state == "review" and hasattr(mw.reviewer, 'web') and mw.reviewer.web:
             mw.reviewer.web.eval("SyncStatusManager.setSyncing(false);")
    except Exception as e:
        print(f"Onigiri: Error stopping sync animation: {e}")

