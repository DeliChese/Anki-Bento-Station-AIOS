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


def generate_profile_bar_fix_css():
    """Generates responsive CSS to ensure the profile picture fits within the profile bar."""
    return """
<style id="onigiri-profile-bar-fix">
/* --- NEW RULES START --- */
.profile-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    overflow: hidden;
    box-sizing: border-box;
    
    position: relative; /* Establishes a positioning context for the picture */
    flex-shrink: 0;     /* Prevents the bar itself from shrinking vertically */
    
    /* Top, Right, Bottom, Left padding. Left padding makes space for the picture. */
    padding: 6px 8px 6px 50px; 
    min-height: 50px; /* Ensures the bar has a minimum size */
}

.profile-pic, .profile-pic-placeholder {
    position: absolute;   /* Positions the picture relative to the bar */
    top: 5px;             /* 5px from the top of the bar */
    left: 5px;            /* 5px from the left of the bar */
    
    /* Forces the height to be the container's height minus 10px (for padding) */
    height: calc(100% - 10px);
    width: auto;          /* Width will follow height due to aspect-ratio */
    aspect-ratio: 1 / 1;  /* Guarantees it is a perfect circle */
    
    border-radius: 50%;
}
/* --- NEW RULES END --- */

.profile-pic {
    object-fit: cover;
}

.profile-pic-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: clamp(14px, 4vw, 20px);
    background-color: rgba(0,0,0,0.1);
    border: 1px solid rgba(255,255,255,0.1);
}

.profile-name {
    font-weight: 500;
    font-size: 16px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
</style>
"""


def generate_icon_size_css():
    """
    Generates CSS to control the size of various icons based on user settings.
    """
    # These keys correspond to the settings in the "Icons" tab.
    icon_configs = {
        "deck_folder": {
            "selector": "a.deck::before",
            "default": 18,
        },
        "action_button": {
            "selector": ".menu-item .icon, .add-button-dashed .icon",
            "default": 16,
        },
        "collapse": {
            "selector": "a.collapse, span.collapse",
            "default": 16,
        },
        "options_gear": {
            "selector": "td.opts a",
            "default": 16,
        },
    }

    css_rules = []
    for key, config in icon_configs.items():
        config_key = f"modern_menu_icon_size_{key}"
        size = mw.col.conf.get(config_key, config["default"])
        selector = config["selector"]
        css_rules.append(f"{selector} {{ width: {size}px; height: {size}px; }}")

    return f"<style id='modern-menu-icon-size-styles'>{''.join(css_rules)}</style>"


def generate_icon_css(addon_package, conf):
    all_icon_selectors = {
        "options": "td.opts a", "folder": "tr.is-folder a.deck::before",
        "deck": "tr.is-deck a.deck::before", "subdeck": "tr.is-subdeck a.deck::before",
        "filtered_deck": "tr.is-filtered a.deck::before", "add": ".action-add .icon",
        "browse": ".action-browse .icon", "stats": ".action-stats .icon", "sync": ".action-sync .icon",
        "settings": ".action-settings .icon", "more": ".action-more .icon",
        "get_shared": ".action-get-shared .icon", "create_deck": ".action-create-deck .icon",
        "import_file": ".action-import-file .icon",
        "retention_star": ".star",
        "focus": ".deck-focus-btn .icon",
        "edit": ".deck-edit-btn .icon",
    }
    
    addon_dir = os.path.dirname(__file__)

    def get_data_uri(path):
        if not path or not os.path.exists(path):
            return ""
        try:
            with open(path, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode("utf-8")
                # Detect file type for correct MIME type
                if path.lower().endswith(".png"):
                    return f"url('data:image/png;base64,{b64}')"
                else:
                    # Default to SVG
                    return f"url('data:image/svg+xml;base64,{b64}')"
        except Exception as e:
            print(f"Onigiri: Error loading icon {path}: {e}")
            return ""

    hide_defaults = mw.col.conf.get("modern_menu_hide_default_icons", False)

    css_rules = []
    for key, selector in all_icon_selectors.items():
        # Check global hide default setting
        if hide_defaults and key in ["folder", "subdeck", "deck", "filtered_deck"]:
             # If "Hide Default" is ON, we hide the default icons.
             # However, we must NOT 'continue' here because we still want the mask-image logic to be generated
             # just in case a custom icon is NOT set for a specific deck, so it defaults to hidden.
             # But WAIT: if we hide it with display:none, the mask-image doesn't matter.
             # AND if we have a custom icon, the later loop creates a specific rule for that deck ID.
             # That specific rule will override the mask-image/content.
             # BUT does it override display:none? 
             # Only if we explicitly add display:inline-block to the custom rule!
             css_rules.append(f"{selector} {{ display: none !important; }}")
             
             # We still generate the default icon URL logic below so that if the user toggles it back, or if there's some weird state, it's there?
             # Actually no, if display:none is set, it's hidden.
             # We can skip the rest of the logic for this iteration if we want to save bytes, 
             # OR we can just let it run. Let's just let it run but ensure display:none is applied.
             # BUT we need to be careful not to conflict with the specific hide toggles.
             pass

        if key == "folder" and mw.col.conf.get("modern_menu_hide_folder_icon", False):
            css_rules.append(f"{selector} {{ display: none !important; }}")
            continue
        if key == "subdeck" and mw.col.conf.get("modern_menu_hide_subdeck_icon", False):
            css_rules.append(f"{selector} {{ display: none !important; }}")
            continue
        if key == "deck" and mw.col.conf.get("modern_menu_hide_deck_icon", False):
            css_rules.append(f"{selector} {{ display: none !important; }}")
            continue
        if key == "filtered_deck" and mw.col.conf.get("modern_menu_hide_filtered_deck_icon", False):
            css_rules.append(f"{selector} {{ display: none !important; }}")
            continue

        filename = mw.col.conf.get(f"modern_menu_icon_{key}", "")
        url = ""
        if filename:
            # Check if filename refers to a registry icon (prefix "registry:")
            if filename.startswith("registry:"):
                registry_name = filename[9:]  # strip "registry:"
                url = icon_registry.get_icon_css_url(registry_name)
            else:
                path = os.path.join(addon_dir, "user_files", "icons", filename)
                url = get_data_uri(path)
        
        if not url: # Fallback to system
            # 🎌 Try icon registry first (using SYSTEM_ICON_MAP)
            registry_name = icon_registry.SYSTEM_ICON_MAP.get(key, key)
            url = icon_registry.get_icon_css_url(registry_name)
            if not url:
                system_icon_name = 'star' if key == 'retention_star' else key
                path = os.path.join(addon_dir, "system_files", "system_icons", f"{system_icon_name}.svg")
                url = get_data_uri(path)
        
        if url:
            css_rules.append(f"{selector} {{ mask-image: {url}; -webkit-mask-image: {url}; }}")

    # --- Custom Deck Icons ---
    custom_deck_icons = mw.col.conf.get("onigiri_custom_deck_icons", {})
    for did, data in custom_deck_icons.items():
        icon_file = data.get("icon")
        color = data.get("color")
        
        if icon_file:
                # Check if it's likely an emoji (short string, no extension)
                is_emoji = len(icon_file) <= 8 and "." not in icon_file

                if is_emoji:
                     # Emoji rendering style
                    css_rules.append(f"""
                    tr[data-did="{did}"] a.deck::before {{
                        content: "{icon_file}" !important;
                        mask-image: none !important;
                        -webkit-mask-image: none !important;
                        background-color: transparent !important;
                        display: inline-block !important;
                        text-align: center;
                        font-size: 14px; 
                        width: 20px !important; 
                        height: 20px !important;
                        line-height: 20px !important;
                        margin-right: 5px !important;
                        overflow: hidden !important;
                    }}
                    """)
                else:
                    path = os.path.join(addon_dir, "user_files", "custom_deck_icons", icon_file)
                    
                    # Check for PNG images
                    is_png = icon_file.strip().lower().endswith(".png")
                    
                    if is_png:
                        url = get_data_uri(path)
                        if url:
                             # PNG rendering style (no mask, original colors)
                            css_rules.append(f"""
                            tr[data-did="{did}"] a.deck::before {{
                                content: '';
                                background-image: {url} !important;
                                -webkit-mask-image: none !important;
                                mask-image: none !important;
                                background-color: transparent !important;
                                background-size: contain;
                                background-repeat: no-repeat;
                                background-position: center;
                                display: inline-block !important;
                                width: 20px !important;
                                height: 20px !important;
                                margin-right: 5px !important;
                            }}
                            """)
                    else:
                        # SVG rendering style (mask for colorization)
                        url = get_data_uri(path)
                        if url:
                            css_rules.append(f"""
                            tr[data-did="{did}"] a.deck::before {{
                                mask-image: {url} !important;
                                -webkit-mask-image: {url} !important;
                                background-color: {color} !important;
                                display: inline-block !important;
                                mask-size: contain;
                                -webkit-mask-size: contain;
                                mask-repeat: no-repeat;
                                -webkit-mask-repeat: no-repeat;
                                mask-position: center;
                                -webkit-mask-position: center;
                                width: 20px !important;
                                height: 20px !important;
                                margin-right: 5px !important;
                            }}
                            """)


    # --- Get URLs for collapse icons ---
    closed_icon_file = mw.col.conf.get("modern_menu_icon_collapse_closed", "")
    open_icon_file = mw.col.conf.get("modern_menu_icon_collapse_open", "")
    
    closed_icon_url = ""
    if closed_icon_file:
        closed_icon_url = get_data_uri(os.path.join(addon_dir, "user_files", "icons", closed_icon_file))
    if not closed_icon_url:
        closed_icon_url = get_data_uri(os.path.join(addon_dir, "system_files", "system_icons", "collapse_closed.svg"))

    open_icon_url = ""
    if open_icon_file:
        open_icon_url = get_data_uri(os.path.join(addon_dir, "user_files", "icons", open_icon_file))
    if not open_icon_url:
        open_icon_url = get_data_uri(os.path.join(addon_dir, "system_files", "system_icons", "collapse_open.svg"))
        
    # Create a list of selectors for the background color, EXCLUDING the star and filtered deck (filtered has own color)
    bg_color_selectors = {k: v for k, v in all_icon_selectors.items() if k not in ["retention_star", "filtered_deck"]}
    bg_selectors_str = ", ".join(bg_color_selectors.values())

    return f"""
<style id="modern-menu-icon-styles">
    /* Hide the original '+' or '-' text from the link. */
    a.collapse {{
        font-size: 0 !important;
    }}

    /* Create the icon using a pseudo-element on the link. */
    a.collapse::before {{
        content: '';
        display: inline-block;
        width: 100%;
        height: 100%;
        /* START FIX: Set background to transparent by default to prevent flash */
        background-color: transparent;
        transition: background-color 0.1s ease;
        /* END FIX */
        mask-size: contain;
        mask-repeat: no-repeat;
        mask-position: center;
        -webkit-mask-size: contain;
        -webkit-mask-repeat: no-repeat;
        -webkit-mask-position: center;
    }}

    /* Apply the correct SVG icon and background color only when the state class is present. */
    a.collapse.state-closed::before {{
        mask-image: {closed_icon_url};
        -webkit-mask-image: {closed_icon_url};
        background-color: var(--icon-color, #888888);
        /* END FIX */
    }}
    a.collapse.state-open::before {{
        mask-image: {open_icon_url};
        -webkit-mask-image: {open_icon_url};
        /* START FIX: Apply background color here */
        background-color: var(--icon-color, #888888);
        /* END FIX */
    }}

    /* Filtered Deck Specific Color */
    tr.is-filtered a.deck::before {{
        background-color: #0a84ff !important; /* Anki Blue */
        mask-size: contain;
        -webkit-mask-size: contain;
        mask-repeat: no-repeat;
        -webkit-mask-repeat: no-repeat;
        mask-position: center;
        -webkit-mask-position: center;
        display: inline-block;
    }}
    .night-mode tr.is-filtered a.deck::before {{
        background-color: #64d2ff !important; /* Light Blue for Dark Mode */
    }}

    /* General rules for other icons (Unchanged) */
    {bg_selectors_str} {{
        background-color: var(--icon-color, #888888);
        mask-size: contain;
        mask-repeat: no-repeat;
        mask-position: center;
        -webkit-mask-size: contain;
        -webkit-mask-repeat: no-repeat;
        -webkit-mask-position: center;
        display: inline-block;
    }}
    
    /* FIX: Layout and Spacing Overrides requested by user */
    .deck-info {{
        display: flex !important;
        align-items: center !important;
        gap: 0 !important;
        width: 100%;
    }}
    
    .deck-table a.deck {{
        padding: 0 !important;
        margin-left: 0 !important;
        /* Ensure it behaves nicely in flex container */
        display: inline-block !important; 
    }}
    
    /* Ensure indentation span works as expected */
    .deck-info > span:first-child {{
        display: inline-flex !important;
        align-items: center !important;
        flex-shrink: 0 !important;
    }}
    /* END FIX */    
    /* Individual mask images for other icons (Unchanged) */
    {''.join(css_rules)}
</style>
"""


def generate_conditional_css(conf):
	styles = []
	styles.append("""
        body.deck-browser .sidebar-left.deck-focus-mode .sidebar-expanded-content > #deck-list-header {
            display: flex !important;
        }
    """)
	if conf.get("hideTodaysStats", False):
		styles.append(".stats-grid { display: none !important; }")
	if conf.get("hideDeckCounts", False):
		styles.append(".deck-counts .zero { display: none !important; }")
	if conf.get("hideAllDeckCounts", False):
		styles.append(".deck-counts { display: none !important; }")
	# -- The old, unreliable CSS rule for the header and bottom bar has been removed. --
	if not styles: return ""
	return f"<style id='modern-menu-conditional-styles'>{' '.join(styles)}</style>"
