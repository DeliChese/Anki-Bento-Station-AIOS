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


def generate_reviewer_buttons_css(conf):
    """
    Generates CSS for the reviewer answer buttons based on user configuration.
    """
    css = []
    
    # Zen Mode: Hide the bottom bar (#outer) completely
    max_hide = conf.get("maxHide", False)
    if max_hide:
        css.append("""
        #outer {
            display: none !important;
        }
        """)
        # Return early since the bottom bar is hidden, no need for button styling
        return "<style>" + "\\n".join(css) + "</style>"
    
    # Global Settings
    border_color_light = conf.get("onigiri_reviewer_btn_border_color_light", "#DBDBDB")
    border_color_dark = conf.get("onigiri_reviewer_btn_border_color_dark", "#444444")
    
    # New Settings
    custom_enabled = conf.get("onigiri_reviewer_btn_custom_enabled", True)
    radius = conf.get("onigiri_reviewer_btn_radius", 12)
    padding = conf.get("onigiri_reviewer_btn_padding", 5)
    btn_height = conf.get("onigiri_reviewer_btn_height", 40)
    bar_height = conf.get("onigiri_reviewer_bar_height", 60)
    
    interval_color_light = conf.get("onigiri_reviewer_stattxt_color_light", "#666666")
    interval_color_dark = conf.get("onigiri_reviewer_stattxt_color_dark", "#aaaaaa")

    if custom_enabled:
        # Base button style (Applied to all buttons: Show Answer, Edit, More, and Answer Buttons)
        css.append(f"""
        /* Bottom Bar Height */
        #outer {{
             height: {bar_height}px !important;
             display: block !important;
             width: 100% !important;
        }}
        
        /* Flexbox-on-row approach for robust centering */
        #outer > table {{
            width: 100% !important;
            height: 100% !important;
            display: table !important; /* Keep table display but control rows */
            border-collapse: collapse !important;
        }}
        
        #outer > table > tbody {{
            display: table-row-group !important;
            width: 100% !important;
        }}
        
        #outer > table tr {{
            display: flex !important;
            width: 100% !important;
            height: 100% !important;
            align-items: center !important;
            justify-content: space-between !important;
        }}
        
        /* Left Cell (Edit) - Grows to fill space */
        #outer > table td:first-child {{
            display: flex !important;
            flex: 1 !important;
            justify-content: flex-start !important;
            align-items: center !important;
            padding-left: 10px !important;
            width: auto !important; /* Override previous fixed width */
        }}
        
        /* Right Cell (More) - Grows exactly as much as Left */
        #outer > table td:last-child {{
            display: flex !important;
            flex: 1 !important;
            justify-content: flex-end !important;
            align-items: center !important;
            padding-right: 10px !important;
            width: auto !important; /* Override previous fixed width */
        }}
        
        /* Middle Cell (Buttons) - Only takes needed space */
        #outer > table td:nth-child(2) {{
            display: flex !important;
            flex: 0 0 auto !important; /* Don't grow or shrink */
            justify-content: center !important;
            align-items: center !important;
            width: auto !important; /* Override previous fixed width */
        }}
        
        /* Modernize ALL buttons in the bottom bar */
        button {{
            border: 2px solid transparent !important; /* Force transparent border */
            border-radius: {radius}px !important; /* Customizable radius */
            box-shadow: none !important; /* No shadow */
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important; /* Smooth transition */
            box-sizing: border-box !important;
            cursor: pointer !important;
            padding: {padding}px 15px !important; /* Customizable padding (size) */
            margin: 0 5px !important; /* Spacing between buttons */
            height: {btn_height}px !important; /* Customizable height */
            min-height: {btn_height}px !important;
        }}
        
        /* Hover effects for ease buttons only */
        button[onclick*="ease"]:hover {{
            transform: translateY(-2px);
            box-shadow: none !important;
        }}
        
        /* Other Buttons (Show Answer, Edit, More, etc.) - Explicit Colors with hover effects */
        #outer button:not([onclick*="ease"]):not([data-cmd*="ease"]) {{
            background: {conf.get("onigiri_reviewer_other_btn_bg_light", "#f0f0f0")} !important;
            background-color: {conf.get("onigiri_reviewer_other_btn_bg_light", "#f0f0f0")} !important;
            background-image: none !important;
            color: {conf.get("onigiri_reviewer_other_btn_text_light", "#2c2c2c")} !important;
        }}
        
        #outer button:not([onclick*="ease"]):not([data-cmd*="ease"]):hover {{
            background: {conf.get("onigiri_reviewer_other_btn_hover_bg_light", "#2c2c2c")} !important;
            background-color: {conf.get("onigiri_reviewer_other_btn_hover_bg_light", "#2c2c2c")} !important;
            background-image: none !important;
            color: {conf.get("onigiri_reviewer_other_btn_hover_text_light", "#f0f0f0")} !important;
            transform: translateY(-2px) !important;
            box-shadow: none !important;
        }}
        
        .nightMode #outer button:not([onclick*="ease"]):not([data-cmd*="ease"]) {{
            background: {conf.get("onigiri_reviewer_other_btn_bg_dark", "#3a3a3a")} !important;
            background-color: {conf.get("onigiri_reviewer_other_btn_bg_dark", "#3a3a3a")} !important;
            background-image: none !important;
            color: {conf.get("onigiri_reviewer_other_btn_text_dark", "#e0e0e0")} !important;
        }}
        
        .nightMode #outer button:not([onclick*="ease"]):not([data-cmd*="ease"]):hover {{
            background: {conf.get("onigiri_reviewer_other_btn_hover_bg_dark", "#e0e0e0")} !important;
            background-color: {conf.get("onigiri_reviewer_other_btn_hover_bg_dark", "#e0e0e0")} !important;
            background-image: none !important;
            color: {conf.get("onigiri_reviewer_other_btn_hover_text_dark", "#3a3a3a")} !important;
            transform: translateY(-2px) !important;
            box-shadow: none !important;
        }}
        
        button:active {{
            transform: translateY(0);
            box-shadow: none !important;
        }}
        
        .nightMode button {{
            box-shadow: none !important;
        }}
        
        .nightMode button:hover {{
            box-shadow: none !important;
        }}

        /* Specific Answer Buttons Colors */
        button[onclick*="ease"], button[data-cmd="ease"] {{
            overflow: visible !important; /* Ensure content isn't clipped */
            display: inline-flex !important; /* Align content nicely */
            flex-direction: column !important; /* Stack text and interval if needed */
            justify-content: center !important;
            align-items: center !important;
        }}

        /* Fix missing interval numbers */
        button[onclick*="ease"] table, button[onclick*="ease"] tr, button[onclick*="ease"] td,
        button[data-cmd="ease"] table, button[data-cmd="ease"] tr, button[data-cmd="ease"] td {{
            background: transparent !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
            color: inherit !important;
        }}
        
        
        /* Stat Text (.stattxt and .nobold) - intervals and + signs */
        .stattxt, .nobold {{
            color: {interval_color_light} !important;
            opacity: 0.9 !important;
            font-weight: normal !important;
            display: inline-block !important;
            font-size: 0.9em !important;
        }}
        
        .nightMode .stattxt, .nightMode .nobold {{
             color: {interval_color_dark} !important;
        }}
        """)
    
        # Per-button settings
        buttons = {
            "1": "again",
            "2": "hard",
            "3": "good",
            "4": "easy"
        }
        
        defaults = {
            "again": ("#ffb3b3", "#4d0000", "#ffcccb", "#4a0000"),
            "hard": ("#ffe0b3", "#4d2600", "#ffd699", "#4d1d00"),
            "good": ("#b3ffb3", "#004d00", "#90ee90", "#004000"),
            "easy": ("#b3d9ff", "#00264d", "#add8e6", "#002952")
        }
        
        for ease, key in buttons.items():
            def_bg_l, def_txt_l, def_bg_d, def_txt_d = defaults[key]
            
            bg_light = conf.get(f"onigiri_reviewer_btn_{key}_bg_light", def_bg_l)
            text_light = conf.get(f"onigiri_reviewer_btn_{key}_text_light", def_txt_l)
            bg_dark = conf.get(f"onigiri_reviewer_btn_{key}_bg_dark", def_bg_d)
            text_dark = conf.get(f"onigiri_reviewer_btn_{key}_text_dark", def_txt_d)
            
            css.append(f"""
            #outer button[data-onigiri-ease="{ease}"],
            #outer button[onclick*="ease{ease}"], 
            #outer button[data-cmd="ease{ease}"], 
            #outer #ease{ease} {{
                background: {bg_light} !important;
                background-color: {bg_light} !important;
                background-image: none !important;
                color: {text_light} !important;
            }}
            #outer button[data-onigiri-ease="{ease}"]:hover,
            #outer button[onclick*="ease{ease}"]:hover, 
            #outer button[data-cmd="ease{ease}"]:hover, 
            #outer #ease{ease}:hover {{
                background: {text_light} !important;
                background-color: {text_light} !important;
                background-image: none !important;
                color: {bg_light} !important;
                cursor: pointer !important;
            }}

            .nightMode #outer button[data-onigiri-ease="{ease}"],
            .nightMode #outer button[onclick*="ease{ease}"], 
            .nightMode #outer button[data-cmd="ease{ease}"], 
            .nightMode #outer #ease{ease} {{
                background: {bg_dark} !important;
                background-color: {bg_dark} !important;
                background-image: none !important;
                color: {text_dark} !important;
            }}
            .nightMode #outer button[data-onigiri-ease="{ease}"]:hover,
            .nightMode #outer button[onclick*="ease{ease}"]:hover, 
            .nightMode #outer button[data-cmd="ease{ease}"]:hover, 
            .nightMode #outer #ease{ease}:hover {{
                background: {text_dark} !important;
                background-color: {text_dark} !important;
                background-image: none !important;
                color: {bg_dark} !important;
            }}
            """)

        # JS Injection for robust button detection
        css.append("""
        <script>
        (function() {
            function classifyButtons() {
                const buttons = document.querySelectorAll('#outer button, button');
                buttons.forEach(btn => {
                    // Check if already processed
                    if (btn.hasAttribute('data-onigiri-ease')) return;

                    const onclick = btn.getAttribute('onclick') || '';
                    const cmd = btn.getAttribute('data-cmd') || '';
                    const id = btn.id || '';
                    const text = btn.innerText.toLowerCase();

                    let ease = null;
                    
                    // Heuristic 1: Standard IDs or Attributes
                    if (onclick.includes('ease1') || cmd === 'ease1' || id === 'ease1') ease = "1";
                    else if (onclick.includes('ease2') || cmd === 'ease2' || id === 'ease2') ease = "2";
                    else if (onclick.includes('ease3') || cmd === 'ease3' || id === 'ease3') ease = "3";
                    else if (onclick.includes('ease4') || cmd === 'ease4' || id === 'ease4') ease = "4";

                    // Heuristic 2: Text Content (Fallback)
                    if (!ease) {
                        if (text.includes('again')) ease = "1";
                        else if (text.includes('hard')) ease = "2";
                        else if (text.includes('good')) ease = "3";
                        else if (text.includes('easy')) ease = "4";
                    }

                    if (ease) {
                        btn.setAttribute('data-onigiri-ease', ease);
                    } else {
                        btn.classList.add('onigiri-other-btn');
                    }
                });
            }

            // Run repeatedly to catch dynamic updates
            setInterval(classifyButtons, 100);
            
            // Also run on mutation
            const observer = new MutationObserver(classifyButtons);
            observer.observe(document.body, { childList: true, subtree: true });
        })();
        </script>
        """)
        
    return "<style>" + "\\n".join(css) + "</style>"
