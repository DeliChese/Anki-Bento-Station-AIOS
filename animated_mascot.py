"""
Onigiri Animated Mascot Engine — "Nakama" (仲間)
=================================================
Quản lý nhân vật/nuôi thú 2D chuyển động trong giao diện Anki.

Hỗ trợ 2 chế độ:
  1. SPRITE SHEET  — Ảnh PNG chứa nhiều frame, render qua Canvas 2D
  2. LOTTIE/RIVE   — Animation vector JSON, render qua thư viện lottie.js / rive.js

Vị trí hiển thị:
  - Deck Browser (góc phải dưới màn hình chính)
  - Reviewer (góc trái dưới, tránh che nút answer)
  - Overview (góc phải dưới)

Tương tác:
  - Click vào nhân vật → phản ứng (animation "happy" hoặc "bounce")
  - Hover → animation "curious"
  - Khi trả lời đúng nhiều → animation "celebrate"
  - Khi trả lời sai nhiều → animation "sad"
  - Kéo thả nhẹ → di chuyển vị trí mascot
"""

import os
import json
import copy
from typing import Dict, Optional, List, Literal
from aqt import mw
from . import config

# ── Default Config ─────────────────────────────────────────────
MASCOT_DEFAULTS: Dict = {
    "enabled": False,
    "mode": "sprite",          # "sprite" | "lottie" | "rive"
    "position": "bottom-right", # "bottom-right" | "bottom-left" | "top-right" | "top-left"
    "scale": 1.0,              # Tỉ lệ phóng to/thu nhỏ (0.5 - 3.0)
    "size": 150,               # Kích thước vùng chứa (px)
    
    # ── Sprite Sheet Config ──
    "sprite": {
        "idle": "",            # Path tới sprite sheet idle (VD: "mascot_idle.png")
        "happy": "",           # Path tới sprite sheet happy
        "sad": "",             # Path tới sprite sheet sad
        "celebrate": "",       # Path tới sprite sheet celebrate
        "curious": "",         # Path tới sprite sheet curious (hover)
        "frame_count": 8,      # Số frame mỗi sprite sheet
        "frame_width": 128,    # Chiều rộng mỗi frame (px)
        "frame_height": 128,   # Chiều cao mỗi frame (px)
        "fps": 8,              # Tốc độ animation
    },
    
    # ── Lottie Config ──
    "lottie": {
        "idle": "",            # Path tới file JSON Lottie idle
        "happy": "",
        "sad": "",
        "celebrate": "",
        "curious": "",
    },
    
    # ── Rive Config ──
    "rive": {
        "src": "",             # Path tới file .riv
        "artboard": "",        # Tên artboard (nếu có nhiều)
        "idle_state": "idle",
        "happy_state": "happy",
        "sad_state": "sad",
        "celebrate_state": "celebrate",
    },
    
    # ── Behavior ──
    "auto_reactions": True,    # Tự động phản ứng khi trả lời đúng/sai
    "click_reaction": True,    # Phản ứng khi click
    "hover_reaction": True,    # Phản ứng khi hover
    "draggable": True,         # Cho phép kéo thả để di chuyển
    "show_in_deck_browser": True,
    "show_in_reviewer": True,
    "show_in_overview": True,
}

def get_mascot_config() -> Dict:
    """Lấy cấu hình mascot từ user config, merge với defaults."""
    conf = config.get_config()
    mascot_conf = conf.get("animatedMascot", {})
    merged = copy.deepcopy(MASCOT_DEFAULTS)
    _deep_merge(merged, mascot_conf)
    return merged

def _deep_merge(base: Dict, override: Dict) -> None:
    """Merge override dict vào base dict (đệ quy)."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value

# ── Path Helpers ───────────────────────────────────────────────

def _get_sprites_root() -> str:
    """Đường dẫn tuyệt đối tới thư mục user_files/sprites/"""
    addon_path = os.path.dirname(os.path.abspath(__file__))
    sprites_dir = os.path.join(addon_path, "user_files", "sprites")
    os.makedirs(sprites_dir, exist_ok=True)
    return sprites_dir

def _get_animations_root() -> str:
    """Đường dẫn tuyệt đối tới thư mục user_files/animations/"""
    addon_path = os.path.dirname(os.path.abspath(__file__))
    anim_dir = os.path.join(addon_path, "user_files", "animations")
    os.makedirs(anim_dir, exist_ok=True)
    return anim_dir

def get_mascot_web_url(filename: str, mode: str = "sprite") -> str:
    """
    Chuyển tên file thành URL web Anki.
    VD: "mascot_idle.png" → "/_addons/1011095603/user_files/sprites/mascot_idle.png"
    """
    if not filename:
        return ""
    addon_package = mw.addonManager.addonFromModule(__name__)
    if mode == "lottie" or mode == "rive":
        return f"/_addons/{addon_package}/user_files/animations/{filename}"
    return f"/_addons/{addon_package}/user_files/sprites/{filename}"

# ── JS/HTML Generation ─────────────────────────────────────────

def generate_mascot_html(context_type: str = "deck_browser") -> str:
    """
    Tạo HTML container cho nhân vật.

    Args:
        context_type: "deck_browser" | "reviewer" | "overview"
    """
    conf = get_mascot_config()
    if not conf.get("enabled", False):
        return ""

    # Kiểm tra context có được phép hiển thị không
    context_map = {
        "deck_browser": "show_in_deck_browser",
        "reviewer": "show_in_reviewer",
        "overview": "show_in_overview",
    }
    show_key = context_map.get(context_type, "show_in_deck_browser")
    if not conf.get(show_key, True):
        return ""

    position = conf.get("position", "bottom-right")
    size = conf.get("size", 150)
    scale = conf.get("scale", 1.0)
    draggable = conf.get("draggable", True)
    drag_class = "draggable" if draggable else ""

    return f"""
    <div id="onigiri-mascot-container"
         class="onigiri-mascot {drag_class}"
         data-position="{position}"
         style="width:{size}px; height:{size}px; --mascot-scale:{scale};"
         title="Click me! (✿◠‿◠)">
        <canvas id="onigiri-mascot-canvas"
                width="{size * 2}"
                height="{size * 2}"
                style="width:{size}px; height:{size}px;">
        </canvas>
        <div id="onigiri-mascot-lottie" style="display:none;"></div>
    </div>
    """

def generate_mascot_css() -> str:
    """Tạo CSS cho mascot container."""
    return """
    <style id="onigiri-mascot-style">
        #onigiri-mascot-container {
            position: fixed;
            z-index: 9999;
            pointer-events: auto;
            cursor: pointer;
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            user-select: none;
            -webkit-user-select: none;
            overflow: visible;
            filter: drop-shadow(0 4px 12px rgba(0,0,0,0.15));
        }
        #onigiri-mascot-container:hover {
            transform: scale(1.08);
            filter: drop-shadow(0 6px 20px rgba(255,183,197,0.3));
        }
        #onigiri-mascot-container:active {
            transform: scale(0.95);
        }
        #onigiri-mascot-container.dragging {
            cursor: grabbing;
            transition: none;
            opacity: 0.85;
        }

        /* Position variants */
        #onigiri-mascot-container[data-position="bottom-right"] {
            bottom: 30px;
            right: 30px;
        }
        #onigiri-mascot-container[data-position="bottom-left"] {
            bottom: 30px;
            left: 30px;
        }
        #onigiri-mascot-container[data-position="top-right"] {
            top: 30px;
            right: 30px;
        }
        #onigiri-mascot-container[data-position="top-left"] {
            top: 30px;
            left: 30px;
        }

        /* Bouncing entrance animation */
        @keyframes mascot-entrance {
            0%   { transform: scale(0) rotate(-10deg); opacity: 0; }
            50%  { transform: scale(1.2) rotate(3deg); opacity: 1; }
            70%  { transform: scale(0.9) rotate(-2deg); }
            100% { transform: scale(1) rotate(0deg); }
        }
        #onigiri-mascot-container.entrance {
            animation: mascot-entrance 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }

        /* Reaction bubble */
        .mascot-bubble {
            position: absolute;
            top: -45px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--canvas-inset, #fff);
            color: var(--fg, #333);
            border: 1px solid var(--border, #e0e0e0);
            border-radius: 20px;
            padding: 6px 14px;
            font-size: 13px;
            font-weight: 600;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease, transform 0.3s ease;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            font-family: "Nunito", "Segoe UI", sans-serif;
        }
        .mascot-bubble.show {
            opacity: 1;
            transform: translateX(-50%) translateY(-5px);
        }
        .mascot-bubble::after {
            content: '';
            position: absolute;
            bottom: -6px;
            left: 50%;
            transform: translateX(-50%) rotate(45deg);
            width: 10px;
            height: 10px;
            background: var(--canvas-inset, #fff);
            border-right: 1px solid var(--border, #e0e0e0);
            border-bottom: 1px solid var(--border, #e0e0e0);
        }

        /* Mascot canvas should be crisp */
        #onigiri-mascot-canvas {
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
            image-rendering: pixelated;
        }
    </style>
    """

def generate_mascot_js() -> str:
    """Tạo JavaScript khởi tạo mascot engine. Dữ liệu config được nhúng trực tiếp."""
    conf = get_mascot_config()
    if not conf.get("enabled", False):
        return ""

    mode = conf.get("mode", "sprite")
    addon_package = mw.addonManager.addonFromModule(__name__)

    # Build sprite URL map
    sprite_config = {}
    if mode == "sprite":
        sprite_cfg = conf.get("sprite", {})
        for state in ["idle", "happy", "sad", "celebrate", "curious"]:
            filename = sprite_cfg.get(state, "")
            if filename:
                sprite_config[state] = get_mascot_web_url(filename, "sprite")
        sprite_config["frame_count"] = sprite_cfg.get("frame_count", 8)
        sprite_config["frame_width"] = sprite_cfg.get("frame_width", 128)
        sprite_config["frame_height"] = sprite_cfg.get("frame_height", 128)
        sprite_config["fps"] = sprite_cfg.get("fps", 8)

    # Build lottie URL map
    lottie_config = {}
    if mode == "lottie":
        lottie_cfg = conf.get("lottie", {})
        for state in ["idle", "happy", "sad", "celebrate", "curious"]:
            filename = lottie_cfg.get(state, "")
            if filename:
                lottie_config[state] = get_mascot_web_url(filename, "lottie")

    # Build rive config
    rive_config = {}
    if mode == "rive":
        rive_cfg = conf.get("rive", {})
        rive_config["src"] = get_mascot_web_url(rive_cfg.get("src", ""), "rive")
        rive_config["artboard"] = rive_cfg.get("artboard", "")
        rive_config["idle_state"] = rive_cfg.get("idle_state", "idle")
        rive_config["happy_state"] = rive_cfg.get("happy_state", "happy")
        rive_config["sad_state"] = rive_cfg.get("sad_state", "sad")
        rive_config["celebrate_state"] = rive_cfg.get("celebrate_state", "celebrate")

    behavior = {
        "auto_reactions": conf.get("auto_reactions", True),
        "click_reaction": conf.get("click_reaction", True),
        "hover_reaction": conf.get("hover_reaction", True),
        "draggable": conf.get("draggable", True),
    }

    # Build JS config payload
    js_config = {
        "mode": mode,
        "sprite": sprite_config,
        "lottie": lottie_config,
        "rive": rive_config,
        "behavior": behavior,
        "addonPackage": addon_package,
    }

    return f"""
    <script>
        window.__ONIGIRI_MASCOT_CONFIG__ = {json.dumps(js_config)};
    </script>
    """

def generate_mascot_script_tag() -> str:
    """Tạo thẻ <script> để load file animated_mascot.js."""
    conf = get_mascot_config()
    if not conf.get("enabled", False):
        return ""
    
    addon_package = mw.addonManager.addonFromModule(__name__)
    mode = conf.get("mode", "sprite")
    
    tags = f'<script src="/_addons/{addon_package}/web/animated_mascot.js"></script>'
    
    # Load external libraries if needed
    if mode == "lottie":
        # Lottie-web CDN (fallback to bundled if available)
        tags += f'<script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js"></script>'
    elif mode == "rive":
        tags += f'<script src="https://unpkg.com/@rive-app/canvas@2.19.2/rive.js"></script>'
    
    return tags

# ── External API (gọi từ __init__.py) ──────────────────────────

def get_mascot_head_content(context_type: str = "deck_browser") -> str:
    """
    Trả về toàn bộ nội dung cần inject vào <head>:
    CSS + JS config + script tag.
    """
    conf = get_mascot_config()
    if not conf.get("enabled", False):
        return ""

    return (
        generate_mascot_css() +
        generate_mascot_js() +
        generate_mascot_script_tag()
    )

def get_mascot_body_content(context_type: str = "deck_browser") -> str:
    """
    Trả về HTML container cho mascot, để chèn vào <body>.
    """
    return generate_mascot_html(context_type)

# ── Available sprite files ─────────────────────────────────────

def list_available_sprites() -> List[str]:
    """Liệt kê các file sprite có sẵn trong user_files/sprites/"""
    sprites_dir = _get_sprites_root()
    if not os.path.isdir(sprites_dir):
        return []
    return sorted([
        f for f in os.listdir(sprites_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ])

def list_available_animations() -> List[str]:
    """Liệt kê các file animation có sẵn trong user_files/animations/"""
    anim_dir = _get_animations_root()
    if not os.path.isdir(anim_dir):
        return []
    return sorted([
        f for f in os.listdir(anim_dir)
        if f.lower().endswith(('.json', '.riv'))
    ])
