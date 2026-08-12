# --- Onigiri ---
# Handles the creation of the top-level Onigiri menu.
# Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.

from aqt import mw
from aqt.qt import QAction, QMenu

# Import the necessary components from other add-on files
from . import settings
from . import patcher

# 🧩 Bento Forge Bridge — điểm truy cập Xưởng chế tạo thẻ từ menu
from . import bento_forge_bridge

# 🛠 Study Tools — bộ công cụ học tập (Planner / Lookup / Gallery / Timer)
from . import study_tools

# A module-level variable to hold the addon path, set once on setup.
_addon_path = None

def open_settings(page_index=0):
    """
    Opens the Onigiri settings dialog to a specific page and resets the UI upon save.
    This function now accepts a page_index to open to a specific tab.
    """
    global _addon_path
    if not _addon_path:
        # This should not happen if setup_onigiri_menu is called correctly.
        print("Onigiri Error: addon_path not set. Cannot open settings.")
        return
        
    dialog = settings.SettingsDialog(mw, _addon_path, initial_page_index=page_index)
    if dialog.exec():
        mw.reset()

def setup_onigiri_menu(addon_path):
    """
    Creates and adds the 'Onigiri' top-level menu to Anki's main window.
    This menu will contain actions for general settings, profile settings, and viewing the profile.
    """
    global _addon_path
    _addon_path = addon_path

    # The function to open the profile page is already defined in the patcher module.
    open_profile = patcher.show_profile_page

    # Create the top-level menu with the Onigiri icon
    onigiri_menu = QMenu("Bento Station", mw)

    profile_action = QAction("Profile", mw)
    profile_action.triggered.connect(open_profile)
    onigiri_menu.addAction(profile_action)

    # Create the 'Settings' action (opens settings to General tab, index 0)
    settings_action = QAction("Bento Station Settings", mw)
    settings_action.triggered.connect(lambda _: open_settings(0))
    onigiri_menu.addAction(settings_action)

    # --- 🧩 BENTO FORGE (Xưởng chế biến) ---
    onigiri_menu.addSeparator()
    forge_menu = QMenu("🧪 Bento Forge", mw)
    forge_main_action = QAction("Open Bento Forge (Xưởng chế biến)", mw)
    forge_main_action.triggered.connect(lambda: bento_forge_bridge.open_forge(mw))
    forge_menu.addAction(forge_main_action)

    forge_ai_action = QAction("AI Settings (DeepSeek / Model / Cache)", mw)
    forge_ai_action.triggered.connect(lambda: bento_forge_bridge.open_ai_settings(mw))
    forge_menu.addAction(forge_ai_action)

    forge_deck_action = QAction("Deck Manager", mw)
    forge_deck_action.triggered.connect(lambda: bento_forge_bridge.open_deck_manager(mw))
    forge_menu.addAction(forge_deck_action)

    forge_menu.addSeparator()
    forge_clear_cache_action = QAction("Clear AI Cache", mw)
    forge_clear_cache_action.triggered.connect(_clear_forge_cache)
    forge_menu.addAction(forge_clear_cache_action)

    # Chỉ hiển thị mục Forge khi module thực sự khả dụng (tránh menu chết).
    if bento_forge_bridge.is_forge_available():
        onigiri_menu.addMenu(forge_menu)
    # --- END: BENTO FORGE ---

    # --- 🛠 STUDY TOOLS (Bộ công cụ học tập) ---
    onigiri_menu.addSeparator()
    tools_menu = QMenu("🛠 Study Tools", mw)

    t_planner = QAction("📅 Study Planner", mw)
    t_planner.triggered.connect(lambda: study_tools.open_study_planner(mw))
    tools_menu.addAction(t_planner)

    t_lookup = QAction("🔍 Quick Lookup", mw)
    t_lookup.triggered.connect(lambda: study_tools.open_quick_lookup(mw))
    tools_menu.addAction(t_lookup)

    t_gallery = QAction("🗂️ Flashcard Gallery", mw)
    t_gallery.triggered.connect(lambda: study_tools.open_flashcard_gallery(mw))
    tools_menu.addAction(t_gallery)

    t_timer = QAction("⏱️ Focus Timer", mw)
    t_timer.triggered.connect(lambda: study_tools.open_focus_timer(mw))
    tools_menu.addAction(t_timer)

    onigiri_menu.addMenu(tools_menu)
    # --- END: STUDY TOOLS ---

    # Add the newly created menu to the main window's menubar
    mw.form.menubar.addMenu(onigiri_menu)

def _clear_forge_cache():
    """Xoá cache AI của Bento Forge từ menu Onigiri."""
    from aqt.utils import tooltip
    if bento_forge_bridge.clear_ai_cache():
        tooltip("🧹 Bento Forge AI cache đã được xoá.")
    else:
        tooltip("❌ Không xoá được cache (Bento Forge không khả dụng).")