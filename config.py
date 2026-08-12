# Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.
import copy
import json
import os
import time
from aqt import mw

# ── Config cache (Hiện đại hóa P0 - A1) ──────────────────────────────
_CONFIG_CACHE = {"data": None, "ts": 0.0}
_CONFIG_TTL = 1.0  # giây

def invalidate_config_cache():
    """Xoá cache config — gọi khi write_config hoặc khi mở profile mới."""
    _CONFIG_CACHE["data"] = None
    _CONFIG_CACHE["ts"] = 0.0

# Default settings for the add-on
DEFAULTS = {
    # ... (content remains same, will be merged by tool if unreferenced, but I should be careful not to delete DEFAULTS content if I can help it. 
    # Actually wait, replace_file_content replaces the WHOLE chunk. I need to keep DEFAULTS intact. 
    # I will target the imports and the functions at the end, leaving DEFAULTS in the middle untouched if possible.
    # Ah, I cannot "leave in the middle untouched" easily with one chunk if I want to wrap everything.
    # I will use multiple chunks.)
}

# ... (I will use multi_replace to target specific areas)

DEFAULTS = {
    "userName": "USER",
    "statsTitle": "Today's Stats",
    "studyNowText": "Study Now",
    "hideWelcomeMessage": False,
    "hideAllDeckCounts": False,
    "hideDeckCounts": True,
    "hideNativeHeaderAndBottomBar": True,
    "proHide": False,
    "maxHide": False,
    "flowMode": False,
    "fullHideMode": False,
    "sidebarCollapsed": False,
    "showCongratsProfileBar": True,
    "congratsMessage": "Congratulations! You have finished this deck for now.",
    "showWelcomePopup": True,
    "userBirthday": "",  # Format: YYYY-MM-DD, empty = not set
    "lastBirthdayShown": "",  # Year when birthday popup was last shown
    "hideRetentionStars": False,
    "showHeatmapOnProfile": True,
    "achievements": {
        "enabled": False,
        "earned": {},
        "history": [],
        "last_refresh": None,
        "snapshot": {},
        "custom_goals": {
            "last_modified_at": None,
            "daily": {
                "enabled": False,
                "target": 100,
                "last_notified_day": None,
                "completion_count": 0,
            },
            "weekly": {
                "enabled": False,
                "target": 700,
                "last_notified_week": None,
                "completion_count": 0,
            },
        },
    },
    "heatmapShape": "square.svg",
    "heatmapShowStreak": True,
    "heatmapShowMonths": True,
    "heatmapShowWeekdays": True,
    "heatmapShowWeekHeader": True,
    "heatmapDefaultView": "year",
    # --- Effort-Adjusted Heatmap (Habit Engine GĐ1) ---
    "heatmapEffortMode": False,  # bật chế độ màu theo nỗ lực (Effort) thay cho đếm thẻ
    "heatmapEffortWeights": {"time": 1.0, "correct": 1.0, "difficulty": 0.5},
    "heatmapEffortFormulaVersion": 1,
    # --- Suggested Session (Habit Engine GĐ2) ---
    "sessionSuggestEnabled": True,  # bật logic đề xuất số thẻ hôm nay (widget opt-in qua editor)
    "sessionMoodMultipliers": {"tired": 0.6, "normal": 1.0, "hype": 1.3},
    "sessionTargetMinRatio": 0.5,   # target tối thiểu = 50% khối lượng trung bình
    "sessionTargetMaxRatio": 1.5,   # target tối đa = 150% khối lượng trung bình
    # --- Streak Insurance (Habit Engine GĐ3) ---
    "streakInsuranceEnabled": True,  # bật token bảo hiểm chuỗi ngày
    "streakTokenThresholdRatio": 1.2,  # học vượt 120% khối lượng TB → +1 token/ngày
    "streakTokenMaxPerDay": 1,
    # --- Future Self Letter (Habit Engine GĐ4) ---
    "futureLetterEnabled": True,
    "futureLetterMilestones": [
        {"type": "streak", "value": 30, "key": "streak_30", "label": "30-day streak"},
        {"type": "streak", "value": 90, "key": "streak_90", "label": "90-day streak"},
        {"type": "streak", "value": 180, "key": "streak_180", "label": "180-day streak"},
        {"type": "total_cards", "value": 1000, "key": "cards_1000", "label": "1,000 cards mastered"},
        {"type": "total_cards", "value": 5000, "key": "cards_5000", "label": "5,000 cards mastered"},
    ],
    # --- Icon Registry Settings ---
    "iconSource": "registry",  # "registry" | "file"
    "iconOverrides": {},        # {"key": "icon_name"} override riêng lẻ
    # --- Animated Mascot (Nakama) Settings ---
    "animatedMascot": {
        "enabled": False,
        "mode": "sprite",
        "position": "bottom-right",
        "scale": 1.0,
        "size": 150,
        "sprite": {
            "idle": "",
            "happy": "",
            "sad": "",
            "celebrate": "",
            "curious": "",
            "frame_count": 8,
            "frame_width": 128,
            "frame_height": 128,
            "fps": 8,
        },
        "lottie": {
            "idle": "",
            "happy": "",
            "sad": "",
            "celebrate": "",
            "curious": "",
        },
        "rive": {
            "src": "",
            "artboard": "",
            "idle_state": "idle",
            "happy_state": "happy",
            "sad_state": "sad",
            "celebrate_state": "celebrate",
        },
        "auto_reactions": True,
        "click_reaction": True,
        "hover_reaction": True,
        "draggable": True,
        "show_in_deck_browser": True,
        "show_in_reviewer": True,
        "show_in_overview": True,
    },
    # --- EXP Level Bar Settings ---
    "expBarEnabled": True,
    "expBarTitle": "Bento Station Mastery",
    "expBarLevelLabel": "LV",
    "expBarNextLevelText": "Next level:",
    "expBarShowPercent": True,
    "expBarShowRemaining": True,
    "onigiriWidgetLayout": {
    "grid": {
        "studied": {"pos": 0, "row": 1, "col": 1},
        "time": {"pos": 1, "row": 1, "col": 1},
        "pace": {"pos": 2, "row": 1, "col": 1},
        "retention": {"pos": 3, "row": 1, "col": 1},
        "heatmap": {"pos": 4, "row": 2, "col": 4},
        "level": {"pos": 12, "row": 2, "col": 2}
        },
    "archive": ["favorites", "planner", "timer", "lookup", "gallery"]
    },
    "externalWidgetLayout": {}, 

    # --- ADDED: Sidebar Button Layout ---
    "sidebarButtonLayout": {
        "visible": [
            "profile",
            "add",
            "browse",
            "stats",
            "sync",
            "settings",
            "more"
        ],
        "archived": []
    },

    # --- 🧩 Bento Forge Integration (Xưởng chế biến thẻ từ vựng/AI) ---
    #   Nơi tập trung để người dùng chỉnh API Key DeepSeek, model, cache
    #   của Bento Forge cùng với cấu hình Bento Station — bridge sẽ đồng bộ
    #   sang Bento Forge/utils/ai_config.json khi mở profile.
    "bentoForge": {
        "enabled": True,
        "sidebar_button": True,
        "api_key": "",
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "temperature": 0.2,
        "max_tokens": 8192,
        "max_chars": 45000,
        "chunk_size": 8000,
        "reasoning_effort": "",
        "cache_enabled": True,
        "cache_dir": "",
    },

    # --- 🛠 Study Tools (Bộ công cụ học tập) ---
    #   1) Study Planner  2) Quick Lookup  3) Flashcard Gallery  4) Focus Timer
    #   Mỗi công cụ có trang tùy chỉnh sâu trong "Bento Station Settings".
    "studyTools": {
        "enabled": True,
        "sidebar_button": True,
        "dashboard_widgets": {"planner": True, "timer": True},
        "planner": {
            "enabled": True,
            "daily_goal_cards": 50,
            "weekly_goal_cards": 350,
            "show_dashboard_widget": True,
        },
        "quick_lookup": {
            "enabled": True,
            "dictionary_url": "https://jisho.org/search/{word}",
            "open_browser_on_lookup": True,
        },
        "gallery": {
            "enabled": True,
            "per_page": 200,
            "default_query": "deck:*",
        },
        "focus_timer": {
            "enabled": True,
            "work_min": 25,
            "break_min": 5,
            "long_break_min": 15,
            "sessions_before_long": 4,
            "auto_start_break": True,
        },
    },


    # --- NEW: Reviewer Background Settings ---
    "onigiri_reviewer_bg_mode": "main", # "main", "color", "image_color"
    # --- Fonts ---
    "onigiri_font_main": "system",
    "onigiri_font_subtle": "system",
    "onigiri_font_small_title": "system",
    "onigiri_font_size_main": 14,
    "onigiri_font_size_subtle": 20,
    "onigiri_font_size_small_title": 15,
    # -------------
    "onigiri_reviewer_bg_main_blur": 0, # Blur when using main background
    "onigiri_reviewer_bg_main_opacity": 100, # Opacity when using main background
    "onigiri_reviewer_bg_light_color": "#f2f2f2",
    "onigiri_reviewer_bg_dark_color": "#2C2C2C",
    "onigiri_reviewer_bg_image_light": "",
    "onigiri_reviewer_bg_image_dark": "",
    "onigiri_reviewer_bg_image_mode": "single", # "single" or "separate"
    "onigiri_reviewer_bg_blur": 0,
    "onigiri_reviewer_bg_opacity": 100,
    # --- Reviewer Notification Position ---
    "onigiri_reviewer_notification_position": "top-center", # top-left, top-center, top-right, bottom-left, bottom-center, bottom-right
    # --- Reviewer Bottom Bar Settings ---
    "onigiri_reviewer_bottom_bar_bg_mode": "match_reviewer_bg", # "main", "color", "image", "image_color", "match_reviewer_bg"
    "onigiri_reviewer_bottom_bar_bg_light_color": "#f2f2f2",
    "onigiri_reviewer_bottom_bar_bg_dark_color": "#2C2C2C",
    "onigiri_reviewer_bottom_bar_bg_image": "",
    "onigiri_reviewer_bottom_bar_bg_blur": 0,
    "onigiri_reviewer_bottom_bar_bg_opacity": 100,
    "onigiri_reviewer_bottom_bar_match_main_blur": 0,
    "onigiri_reviewer_bottom_bar_match_main_opacity": 100,
    "onigiri_reviewer_bottom_bar_match_reviewer_bg_blur": 0,
    "onigiri_reviewer_bottom_bar_match_reviewer_bg_opacity": 100,
    "restaurant_countdown_hour": 4,  # Default to 4 AM
    "restaurant_countdown_minute": 0,  # Default to 0 minutes
    
    # --- NEW: Overviewer Background Settings ---
    "onigiri_overview_bg_mode": "main", # "main", "color", "image_color"
    "onigiri_overview_bg_main_blur": 0,
    "onigiri_overview_bg_main_opacity": 100,
    "onigiri_overview_bg_light_color": "#f2f2f2",
    # The following lines appear to be UI setup code and cannot be directly inserted into a dictionary.
    # Assuming the intent was to add a default for 'onigiri_reviewer_btn_custom_enabled' if not already present.
    # The other lines are likely from a different context (e.g., a settings dialog setup).
    "onigiri_reviewer_btn_border_size": 0,
    "onigiri_reviewer_btn_custom_enabled": True, # Global toggle (Default OFF)
    "deck_indentation_mode": "default", # default, smaller, bigger, custom
    "deck_indentation_custom_px": 20, # px per level
    "onigiri_reviewer_btn_radius": 12, # px
    "onigiri_reviewer_btn_radius": 12, # px
    "onigiri_reviewer_btn_padding": 5, # px (affects size)
    "onigiri_reviewer_btn_height": 40, # px (button height)
    "onigiri_reviewer_bar_height": 60, # px (default height)
    "onigiri_reviewer_btn_interval_color_light": "#555555",
    "onigiri_reviewer_btn_interval_color_dark": "#dddddd",
    "onigiri_reviewer_btn_border_color_light": "#DBDBDB",
    "onigiri_reviewer_btn_border_color_dark": "#444444",
    "onigiri_reviewer_btn_again_bg_light": "#ffb3b3",
    "onigiri_reviewer_btn_again_text_light": "#4d0000",
    "onigiri_reviewer_btn_again_bg_dark": "#ffcccb",
    "onigiri_reviewer_btn_again_text_dark": "#4a0000",
    "onigiri_reviewer_btn_hard_bg_light": "#ffe0b3",
    "onigiri_reviewer_btn_hard_text_light": "#4d2600",
    "onigiri_reviewer_btn_hard_bg_dark": "#ffd699",
    "onigiri_reviewer_btn_hard_text_dark": "#4d1d00",
    "onigiri_reviewer_btn_good_bg_light": "#b3ffb3",
    "onigiri_reviewer_btn_good_text_light": "#004d00",
    "onigiri_reviewer_btn_good_bg_dark": "#90ee90",
    "onigiri_reviewer_btn_good_text_dark": "#004000",
    "onigiri_reviewer_btn_easy_bg_light": "#b3d9ff",
    "onigiri_reviewer_btn_easy_text_light": "#00264d",
    "onigiri_reviewer_btn_easy_bg_dark": "#add8e6",
    "onigiri_reviewer_btn_easy_text_dark": "#002952",
    
    # --- Other Bottom Bar Buttons (Show Answer, Edit, More, etc.) ---
    "onigiri_reviewer_other_btn_bg_light": "#ffffff",
    "onigiri_reviewer_other_btn_text_light": "#2c2c2c",
    "onigiri_reviewer_other_btn_bg_dark": "#3a3a3a",
    "onigiri_reviewer_other_btn_text_dark": "#e0e0e0",
    "onigiri_reviewer_other_btn_hover_bg_light": "#2c2c2c",
    "onigiri_reviewer_other_btn_hover_text_light": "#f0f0f0",
    "onigiri_reviewer_other_btn_hover_bg_dark": "#e0e0e0",
    "onigiri_reviewer_other_btn_hover_text_dark": "#3a3a3a",
    
    # --- Stat Text (.stattxt) Colors (intervals like "10m", "4d" and "+" signs) ---
    "onigiri_reviewer_stattxt_color_light": "#666666",
    "onigiri_reviewer_stattxt_color_dark": "#aaaaaa",

    "onigiri_overview_bg_dark_color": "#2C2C2C",
    "onigiri_overview_bg_image_light": "",
    "onigiri_overview_bg_image_dark": "",
    "onigiri_overview_bg_image": "",
    "onigiri_overview_bg_image_mode": "single",
    "onigiri_overview_bg_blur": 0,
    "onigiri_overview_bg_opacity": 100,
    "onigiri_overview_bg_color_theme_mode": "single",
    "onigiri_overview_bg_image_theme_mode": "single",
    # -----------------------------------------
    # --- REMOVED: Top-level focusDango was here ---
    "colors": {
        "light": {
            "--accent-color": "#007aff",
            "--bg": "#f3f3f3",
            "--fg": "#212121",
            "--icon-color": "#333333",
            "--icon-color-filtered": "#007AFF",
            "--fg-subtle": "#757575",
            "--border": "#e0e0e0",
            "--highlight-bg": "#eeeeee",
            "--canvas-inset": "#ffffff",
            "--button-primary-bg": "#007aff",
            "--button-primary-gradient-start": "#0088ff",
            "--button-primary-gradient-end": "#0065c7",
            "--new-count-bubble-bg": "#a3c5e8",
            "--new-count-bubble-fg": "#13375b",
            "--learn-count-bubble-bg": "#e8a3a3",
            "--learn-count-bubble-fg": "#731717",
            "--review-count-bubble-bg": "#a3e8b8",
            "--review-count-bubble-fg": "#1b7a38",
            "--heatmap-color": "#007aff",
            "--heatmap-color-zero": "#f0f0f0",
            "--star-color": "#FFD700",
            "--empty-star-color": "#e0e0e0",
            "--stats-fg": "#212121",
            # Shadow and overlay colors
            "--shadow-sm": "rgba(0, 0, 0, 0.1)",
            "--shadow-md": "rgba(0, 0, 0, 0.1)",
            "--shadow-lg": "rgba(0, 0, 0, 0.1)",
            "--overlay-dark": "rgba(0, 0, 0, 0.4)",
            "--overlay-light": "rgba(0, 0, 0, 0.4)",
            # Profile page specific colors
            "--profile-page-bg": "#d9d9d9",
            "--profile-card-bg": "#FFFFFF",
            "--profile-pill-placeholder-bg": "rgba(0, 0, 0, 0.2)",
            "--profile-export-btn-bg": "rgba(255, 255, 255, 1)",
            "--profile-export-btn-fg": "#374151",
            "--profile-export-btn-border": "rgba(0, 0, 0, 0.1)",
            "--overlay-close-btn-bg": "#e0e0e0",
            "--overlay-close-btn-fg": "#333333",
            # Deck list specific colors
            "--deck-hover-bg": "rgba(128, 128, 128, 0.1)",
            "--deck-dragging-bg": "#cde4f9",
            "--deck-edit-mode-bg": "rgba(128, 128, 128, 0.05)",
            # Text shadow colors
            "--text-shadow-light": "rgba(0, 0, 0, 0.5)",
            "--profile-pic-border": "rgba(255, 255, 255, 0.8)",
        },
        "dark": {
            "--accent-color": "#0a84ff",
            "--bg": "#2c2c2c",
            "--fg": "#e0e0e0",
            "--icon-color": "#E0E0E0",
            "--icon-color-filtered": "#0A84FF", 
            "--fg-subtle": "#9e9e9e",
            "--border": "#424242",
            "--highlight-bg": "#3c3c3c",
            "--canvas-inset": "#2c2c2c",
            "--button-primary-bg": "#0a84ff",
            "--button-primary-gradient-start": "#0a94ff",
            "--button-primary-gradient-end": "#0a74d9",
            "--new-count-bubble-bg": "#68a0d9",
            "--new-count-bubble-fg": "#13375b",
            "--learn-count-bubble-bg": "#d96868",
            "--learn-count-bubble-fg": "#731717",
            "--review-count-bubble-bg": "#68d98a",
            "--review-count-bubble-fg": "#1b7a38",
            "--heatmap-color": "#0a84ff",
            "--heatmap-color-zero": "#3a3a3a",
            "--star-color": "#FFD700",
            "--empty-star-color": "#4a4a4a",
            "--stats-fg": "#e0e0e0",
            # Shadow and overlay colors
            "--shadow-sm": "rgba(0, 0, 0, 0.1)",
            "--shadow-md": "rgba(0, 0, 0, 0.15)",
            "--shadow-lg": "rgba(0, 0, 0, 0.4)",
            "--overlay-dark": "rgba(0, 0, 0, 0.7)",
            "--overlay-light": "rgba(0, 0, 0, 0.4)",
            # Profile page specific colors
            "--profile-page-bg": "#1f1f1f",
            "--profile-card-bg": "#1e1e1e",
            "--profile-pill-placeholder-bg": "rgba(0, 0, 0, 0.2)",
            "--profile-export-btn-bg": "rgba(255, 255, 255, 1)",
            "--profile-export-btn-fg": "#374151",
            "--profile-export-btn-border": "rgba(0, 0, 0, 0.1)",
            "--overlay-close-btn-bg": "#e0e0e0",
            "--overlay-close-btn-fg": "#333333",
            # Deck list specific colors
            "--deck-hover-bg": "rgba(128, 128, 128, 0.1)",
            "--deck-dragging-bg": "#2c3e50",
            "--deck-edit-mode-bg": "rgba(128, 128, 128, 0.05)",
            # Text shadow colors
            "--text-shadow-light": "rgba(0, 0, 0, 0.5)",
            "--profile-pic-border": "rgba(255, 255, 255, 0.8)",
        }
    }
}



# A unique ID for our add-on's configuration
config_id = None
def get_config_id():
    global config_id
    if config_id is None:
        config_id = mw.addonManager.addonFromModule(__name__)
    return config_id

def _get_settings_path() -> str:
    """Get the path to the profile-specific settings file."""
    try:
        # Calculate addon_path dynamically
        current_dir = os.path.dirname(os.path.abspath(__file__))
        user_files = os.path.join(current_dir, 'user_files')
        os.makedirs(user_files, exist_ok=True)
        
        # Determine profile name
        if mw.col and mw.pm and mw.pm.name:
            profile_name = mw.pm.name
        else:
            profile_name = "default"
            
        return os.path.join(user_files, f'settings_{profile_name}.json')
    except Exception as e:
        print(f"Error determining settings path: {e}")
        return ""

def get_config():
    """
    Loads the add-on's configuration from the profile-specific JSON file,
    falling back to Anki's shared config for migration or defaults.
    """
    # Cache hit → trả deepcopy (mỗi caller có bản riêng, tránh rò rỉ mutation)
    now = time.time()
    if _CONFIG_CACHE["data"] is not None and (now - _CONFIG_CACHE["ts"]) < _CONFIG_TTL:
        return copy.deepcopy(_CONFIG_CACHE["data"])

    # Start with a clean copy of the defaults
    clean_config = copy.deepcopy(DEFAULTS)


    
    # helper to merge dictionaries
    def merge_config(target, source):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                merge_config(target[key], value)
            else:
                target[key] = value

    user_config = {}
    settings_path = _get_settings_path()
    
    # Try to load from profile specific file
    loaded_from_file = False
    if settings_path and os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                loaded_from_file = True
        except Exception as e:
            print(f"Error loading settings from {settings_path}: {e}")
    
    # If not found (First run for this profile), try migration from legacy shared config
    if not loaded_from_file and mw.col:
        try:
            legacy_config = mw.addonManager.getConfig(get_config_id())
            if legacy_config:
                print(f"Migrating legacy settings to {settings_path}")
                user_config = legacy_config
                # Save immediately to establish the new file
                try:
                    with open(settings_path, 'w', encoding='utf-8') as f:
                        json.dump(user_config, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"Error saving migrated settings: {e}")
        except Exception as e:
            print(f"Error reading legacy config: {e}")

    # Merge user settings into defaults
    if user_config:
        merge_config(clean_config, user_config)
    
    # Compatibility migrations (logic preserved from original)
    custom_goals_conf = clean_config.get("achievements", {}).get("custom_goals", {})
    if "last_modified_at" not in custom_goals_conf:
        custom_goals_conf["last_modified_at"] = None
        if "achievements" in clean_config:
            clean_config["achievements"].setdefault("custom_goals", custom_goals_conf)

    # Compatibility: Check for old profile page visibility settings and migrate them
    # This ensures users updating the addon don't lose their settings
    if "showHeatmapOnProfile" not in user_config:
         if mw.col and "onigiri_profile_show_stats" in mw.col.conf:
            clean_config["showHeatmapOnProfile"] = mw.col.conf.get("onigiri_profile_show_stats", True)

    # --- NEW FIX: Enforce Archive Exclusivity ---
    # Ensure items in 'archive' are NOT in 'grid'. The merge process might have
    # kept default grid positions for items the user wanted to archive.
    layout_conf = clean_config.get("onigiriWidgetLayout", {})
    if "grid" in layout_conf and "archive" in layout_conf:
        grid_conf = layout_conf["grid"]
        archive_conf = layout_conf["archive"]
        
        # Get set of archived IDs
        if isinstance(archive_conf, dict):
            archived_ids = set(archive_conf.keys())
        elif isinstance(archive_conf, list):
            archived_ids = set(archive_conf)
        else:
            archived_ids = set()
            
        # Remove them from grid
        for widget_id in archived_ids:
            if widget_id in grid_conf:
                del grid_conf[widget_id]
    # --------------------------------------------

    _CONFIG_CACHE["data"] = copy.deepcopy(clean_config)
    _CONFIG_CACHE["ts"] = now
    return clean_config


def write_config(config):
    """
    Saves the provided configuration dictionary to the profile-specific JSON file.
    """
    # Vô hiệu cache để lần get_config kế tiếp đọc lại từ disk
    invalidate_config_cache()
    settings_path = _get_settings_path()
    if settings_path:
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing settings to {settings_path}: {e}")
            
    # Optional: We could also write to Anki's config as a backup, 
    # but we want to simulate isolation, so maybe better not to, 
    # or obscure it to avoid confusion in the Add-on Config dialog.
    # For user clarity, let's NOT write to the shared config.
    # mw.addonManager.writeConfig(get_config_id(), config)