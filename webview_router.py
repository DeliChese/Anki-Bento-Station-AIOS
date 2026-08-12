"""
Hiện đại hóa P0 - A3: webview_router.py
Xử lý pycmd từ webview (on_webview_js_message) — tách từ patcher.py.

Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.
"""
import os
import json
import base64
import html
import time
from aqt import mw
from aqt.deckbrowser import DeckBrowser
from aqt.overview import Overview
from aqt.reviewer import Reviewer
from aqt.qt import *
from aqt.utils import tooltip
from . import config
from . import settings
from . import profile_page
from .profile_page import open_profile
from .toolbar_styling import get_sync_status

# 🧩 Bento Forge — route các lệnh pycmd từ Sidebar tới Xưởng chế biến.
#   Import trễ trong handler để tránh circular import & đảm bảo Bento Station
#   vẫn chạy bình thường khi Forge không khả dụng.
from . import bento_forge_bridge

# 🛠 Study Tools — bộ công cụ học tập (Planner / Lookup / Gallery / Timer)
from . import study_tools


def on_webview_js_message(handled, message, context):
    """
    Unified handler for messages from all webviews.
    """
    if message.startswith("saveImage:") and profile_page._profile_dialog and profile_page._profile_dialog.isVisible():
        try:
            # Extract base64 data after the "saveImage:" prefix
            base64_data = message[len("saveImage:"):]
            
            # Handle both raw base64 and data URI format
            if base64_data.startswith("data:image"):
                # data:image/png;base64,XXXX format
                base64_data = base64_data.split(",", 1)[1]
            
            # Add padding if needed (base64 strings must be multiple of 4)
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
            
            image_data = base64.b64decode(base64_data)

            filename, _ = QFileDialog.getSaveFileName(
                profile_page._profile_dialog, "Save Profile Image", "onigiri-profile.png", "PNG Images (*.png)"
            )

            if filename:
                with open(filename, "wb") as f:
                    f.write(image_data)
        except Exception as e:
            print(f"Onigiri: An error occurred during image save: {e}")

        return (True, None)

    if isinstance(context, DeckBrowser):
        cmd = message
        
        # Let webview_handlers handle the command
        # if cmd.startswith("onigiri_"):
        #    return webview_handlers.handle_webview_cmd((False, None), cmd, context)
        
        if cmd == "showUserProfile":
            open_profile()
            return (True, None)
        if cmd == "add":
            mw.onAddCard()
            return (True, None)
        if cmd == "browse":
            mw.onBrowse()
            return (True, None)
        if cmd == "stats":
            mw.onStats()
            return (True, None)
        if cmd == "sync":
            if hasattr(mw.deckBrowser, 'web') and mw.deckBrowser.web:
                mw.deckBrowser.web.eval("SyncStatusManager.setSyncing(true);")
            mw.onSync()
            return (True, None)
        if cmd == "onigiri_check_sync_status":
            sync_status = get_sync_status()
            if hasattr(mw.deckBrowser, 'web') and mw.deckBrowser.web:
                mw.deckBrowser.web.eval(f"SyncStatusManager.setSyncStatus('{sync_status}');")
            return (True, None)
        if cmd == "openOnigiriSettings":
            settings.open_settings(0)
            return (True, None)
        if cmd == "shared":
            QDesktopServices.openUrl(QUrl("https://ankiweb.net/shared/decks"))
            return (True, None)
        if cmd == "create":
            # Fix for duplicate dialog: Use QInputDialog directly and create deck manually
            # instead of calling _on_create() which was triggering the dialog twice
            name, ok = QInputDialog.getText(mw, "Create Deck", "Name:")
            if ok and name:
                # Create the deck
                mw.col.decks.id(name)
                # Refresh the deck browser to show the new deck
                mw.deckBrowser.refresh()
            return (True, None)
        if cmd.startswith("opts:"):
            try:
                deck_id = cmd.split(":")[1]
                # Call Anki's standard deck options functionality
                mw.deckBrowser._show_options_for_deck_id(int(deck_id))
                return (True, None)
            except (ValueError, IndexError, AttributeError):
                # If deck ID is invalid or deckBrowser doesn't have the method, fall through to default handler
                pass
        if cmd.startswith("saveSidebarWidth:"):
            try:
                width = int(cmd.split(":")[1])
                mw.col.conf["modern_menu_sidebar_width"] = width
                mw.col.setMod()
            except:
                pass
            return (True, None)
        if cmd.startswith("saveSidebarState:"):
            try:
                is_collapsed = cmd.split(":")[1] == 'true'
                mw.col.conf["onigiri_sidebar_collapsed"] = is_collapsed
                mw.col.setMod()
            except Exception as e:
                print(f"Onigiri: Error saving sidebar state: {e}")
            return (True, None)
        # --- Focus Mode ---
        if cmd.startswith("saveDeckFocusState:"):
            try:
                is_focused = cmd.split(":")[1] == 'true'
                mw.col.conf["onigiri_deck_focus_mode"] = is_focused
                mw.col.setMod()
            except Exception as e:
                print(f"Onigiri: Error saving deck focus state: {e}")
            return (True, None)
        # --- Focus Mode ---

        # ── 🧩 BENTO FORGE (Sidebar) ─────────────────────────────
        if cmd == "openBentoForge":
            bento_forge_bridge.open_forge(mw)
            return (True, None)
        if cmd == "openBentoForgeAI":
            bento_forge_bridge.open_ai_settings(mw)
            return (True, None)
        if cmd == "openBentoForgeDecks":
            bento_forge_bridge.open_deck_manager(mw)
            return (True, None)
        if cmd == "clearBentoForgeCache":
            if bento_forge_bridge.clear_ai_cache():
                tooltip("🧹 Bento Forge AI cache đã được xoá.")
            else:
                tooltip("❌ Không xoá được cache (Bento Forge không khả dụng).")
            return (True, None)

        # ── 🛠 STUDY TOOLS (Sidebar) ─────────────────────────────
        if cmd == "openStudyPlanner":
            study_tools.open_study_planner(mw)
            return (True, None)
        if cmd == "openQuickLookup":
            study_tools.open_quick_lookup(mw)
            return (True, None)
        if cmd == "openFlashcardGallery":
            study_tools.open_flashcard_gallery(mw)
            return (True, None)
        if cmd == "openFocusTimer":
            study_tools.open_focus_timer(mw)
            return (True, None)

    elif isinstance(context, Overview):
        cmd = message  # <-- This line must come FIRST
        

        
        # Now handle the commands normally
        if cmd == "deckBrowser":
            mw.moveToState("deckBrowser")
            return (True, None)
        if cmd in ["study", "opts", "refresh", "empty", "studymore", "description"]:
            return handled
        if cmd == "showUserProfile":
            open_profile()
            return (True, None)
        if cmd == "decks":
            mw.moveToState("deckBrowser")
            return (True, None)
        if cmd == "add":
            mw.onAddCard()
            return (True, None)
        if cmd == "browse":
            mw.onBrowse()
            return (True, None)
        if cmd == "stats":
            mw.onStats()
            return (True, None)
        if cmd == "sync":
            context.web.eval("SyncStatusManager.setSyncing(true);")
            mw.onSync()
            return (True, None)
        if cmd == "onigiri_check_sync_status":
            sync_status = get_sync_status()
            context.web.eval(f"SyncStatusManager.setSyncStatus('{sync_status}');")
            return (True, None)

    elif isinstance(context, Reviewer):
        cmd = message  # <-- This line must come FIRST
        
        # Now handle the commands normally
        if cmd == "decks":
            mw.moveToState("deckBrowser")
            return (True, None)
        if cmd == "add":
            mw.onAddCard()
            return (True, None)
        if cmd == "browse":
            mw.onBrowse()
            return (True, None)
        if cmd == "stats":
            mw.onStats()
            return (True, None)
        if cmd == "sync":
            context.web.eval("SyncStatusManager.setSyncing(true);")
            mw.onSync()
            return (True, None)
        if cmd == "onigiri_check_sync_status":
            sync_status = get_sync_status()
            context.web.eval(f"SyncStatusManager.setSyncStatus('{sync_status}');")
            return (True, None)

    return handled


