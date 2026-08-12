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

from .utils import _hex_to_rgba

def _render_background_css(selector, mode, light_color, dark_color, light_image_path, dark_image_path, blur_val, addon_path, style_id, opacity_val=100, background_position="center"):
	"""Internal helper to generate a complete <style> block for a given background configuration."""
	blur_px = blur_val * 0.2
	addon_name = os.path.basename(addon_path)

	def get_img_url(image_path):
		if not image_path:
			return None
		if image_path.startswith("user_files/"):
			return f"/_addons/{addon_name}/{image_path}"
		else:
			return f"/_addons/{addon_name}/user_files/{image_path}"

	if mode == "accent":
		return f"""<style id="{style_id}">{selector} {{ background: var(--accent-color) !important; }}</style>"""

	if mode == "color":
		return f"""<style id="{style_id}">
			{selector} {{ background-color: {light_color} !important; }}
			.night-mode {selector} {{ background-color: {dark_color} !important; }}
		</style>"""

	# --- START OF REVISED LOGIC ---

	elif mode == "image":
		light_img_url = get_img_url(light_image_path)
		dark_img_url = get_img_url(dark_image_path) if dark_image_path else light_img_url
		if not light_img_url: return ""

		opacity_float = opacity_val / 100.0
		# Scale factor to prevent white borders when blur is applied
		scale = 1.0 + (blur_px / 50.0) if blur_px > 0 else 1.0
		if 'body' in selector:
			base_before_css = f"""
				content: ''; position: fixed;
				top: 50%; left: 50%;
				width: 100vw; height: 100vh;
				transform: translate(-50%, -50%) scale({scale});
				background-size: cover; background-position: {background_position};
				background-repeat: no-repeat; filter: blur({blur_px}px);
				image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;
				opacity: {opacity_float}; z-index: -1;
				pointer-events: none;
			"""
		else:
			base_before_css = f"""
				content: ''; position: absolute;
				top: 50%; left: 50%;
				width: 100%; height: 100%;
				transform: translate(-50%, -50%) scale({scale});
				background-size: cover; background-position: {background_position};
				background-repeat: no-repeat; filter: blur({blur_px}px);
				image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;
				opacity: {opacity_float}; z-index: -1;
			"""

		image_css = f"{selector}::before {{ {base_before_css} background-image: url('{light_img_url}'); }}"
		if dark_img_url and dark_img_url != light_img_url:
			image_css += f"\n.night-mode {selector}::before {{ background-image: url('{dark_img_url}'); }}"

		container_css = ""
		if "body" in selector:
			container_css += f"html {{ background: transparent !important; overflow: hidden !important; }} {selector} {{ background: transparent !important; overflow: hidden !important; }}"
		else:
			container_css += f"{selector} {{ background: transparent; overflow: hidden; }}"

		if "container" in selector or ".sidebar-left" in selector or "#outer" in selector:
			container_css += f"{selector} {{ position: relative; z-index: 1; overflow: hidden; }}"
		elif "body" in selector:
			container_css += f"{selector} {{ position: relative; z-index: 1; overflow: hidden; }}"

		return f"<style id='{style_id}'>{container_css}\n{image_css}</style>"

    # Located in patcher.py

	elif mode == "image_color":
		light_img_url = get_img_url(light_image_path)
		dark_img_url = get_img_url(dark_image_path) if dark_image_path else light_img_url

		# If no image, fallback to solid color
		if not light_img_url:
				return f"""<style id="{style_id}">
					{selector} {{ background-color: {light_color} !important; }}
					.night-mode {selector} {{ background-color: {dark_color} !important; }}
				</style>"""

		# --- START OF FIX ---
		image_opacity = opacity_val / 100.0
		blur_px = blur_val * 0.2
		# Scale factor to prevent white borders when blur is applied
		scale = 1.0 + (blur_px / 50.0) if blur_px > 0 else 1.0

		# This pseudo-element holds the background image with its effects.
		if 'body' in selector:
			base_before_css = f"""
				content: ''; position: fixed;
				top: 50%; left: 50%;
				width: 100vw; height: 100vh;
				transform: translate(-50%, -50%) scale({scale});
				background-size: cover; background-position: {background_position};
				background-repeat: no-repeat;
				filter: blur({blur_px}px);
				opacity: {image_opacity};
				z-index: -1;
				pointer-events: none;
			"""
		else:
			base_before_css = f"""
				content: ''; position: absolute;
				top: 50%; left: 50%;
				width: 100%; height: 100%;
				transform: translate(-50%, -50%) scale({scale});
				background-size: cover; background-position: {background_position};
				background-repeat: no-repeat;
				filter: blur({blur_px}px);
				opacity: {image_opacity};
				z-index: -1;
			"""

		image_css = f"{selector}::before {{ {base_before_css} background-image: url('{light_img_url}'); }}"
		if dark_img_url and dark_img_url != light_img_url:
			image_css += f"\n.night-mode {selector}::before {{ background-image: url('{dark_img_url}'); }}"

		# The container gets the SOLID color and acts as a positioning context.
		if "body" in selector:
			container_css = f"""
				html {{ background: transparent !important; overflow: hidden !important; }}
				{selector} {{
					position: relative; z-index: 1; overflow: hidden !important;
					background-color: {light_color} !important;
				}}
				.night-mode {selector} {{
					background-color: {dark_color} !important;
				}}
			"""
		else:
			container_css = f"""
				{selector} {{
					position: relative; z-index: 1; overflow: hidden;
					background-color: {light_color} !important;
				}}
				.night-mode {selector} {{
					background-color: {dark_color} !important;
				}}
			"""

		return f"<style id='{style_id}'>{container_css}\n{image_css}</style>"
	# --- END OF REVISED LOGIC ---

	return ""


def generate_profile_page_background_css():
    """Generates the CSS for the profile page's main container background."""
    # Reads the mode ("color" or "gradient") you set in the settings
    mode = mw.col.conf.get("onigiri_profile_page_bg_mode", "color")

    if mode == "gradient":
        # Uses the correct "gradient" color keys
        light1 = mw.col.conf.get("onigiri_profile_page_bg_light_color1", "#FFFFFF")
        light2 = mw.col.conf.get("onigiri_profile_page_bg_light_color2", "#E0E0E0")
        dark1 = mw.col.conf.get("onigiri_profile_page_bg_dark_color1", "#424242")
        dark2 = mw.col.conf.get("onigiri_profile_page_bg_dark_color2", "#212121")
        return f"""
        <style id="onigiri-profile-page-bg">
            .onigiri-profile-page {{
                background-image: linear-gradient(to bottom, {light1}, {light2});
                background-attachment: fixed;
            }}
            .night-mode .onigiri-profile-page {{
                background-image: linear-gradient(to bottom, {dark1}, {dark2});
            }}
        </style>
        """
    else: # Solid color
        # Uses the correct "solid color" keys
        light_color = mw.col.conf.get("onigiri_profile_page_bg_light_color1", "#F5F5F5")
        dark_color = mw.col.conf.get("onigiri_profile_page_bg_dark_color1", "#2c2c2c")
        return f"""
        <style id="onigiri-profile-page-bg">
            .onigiri-profile-page {{ background-color: {light_color} !important; }}
            .night-mode .onigiri-profile-page {{ background-color: {dark_color} !important; }}
        </style>
        """


def generate_deck_browser_backgrounds(addon_path):
    """Generates CSS for the main container background and sidebar."""
    conf = config.get_config()
    
    main_mode = mw.col.conf.get("modern_menu_background_mode", "color")
    main_image_mode = mw.col.conf.get("modern_menu_background_image_mode", "single")
    main_light_color = mw.col.conf.get("modern_menu_bg_color_light", "#F5F5F5")
    main_dark_color = mw.col.conf.get("modern_menu_bg_color_dark", "#2C2C2C")
    main_blur = mw.col.conf.get("modern_menu_background_blur", 0)
    main_opacity = mw.col.conf.get("modern_menu_background_opacity", 100)

    # Handle slideshow mode
    if main_mode == "slideshow":
        slideshow_images = mw.col.conf.get("modern_menu_slideshow_images", [])
        slideshow_interval = mw.col.conf.get("modern_menu_slideshow_interval", 10)
        
        if slideshow_images:
            addon_name = os.path.basename(addon_path)
            image_urls = [f"/_addons/{addon_name}/user_files/main_bg/{img}" for img in slideshow_images]
            
            blur_px = main_blur * 0.2
            scale = 1.0 + (blur_px / 50.0) if blur_px > 0 else 1.0
            opacity_float = main_opacity / 100.0
            
            # Generate CSS for slideshow with smooth crossfade effect
            first_image_url = image_urls[0]
            main_container_css = f"""
            <style id='modern-menu-main-background-style'>
                .container.modern-main-menu {{
                    position: relative;
                    z-index: 1;
                    overflow: hidden;
                    background-color: {main_light_color} !important;
                }}
                .night-mode .container.modern-main-menu {{
                    background-color: {main_dark_color} !important;
                }}
                /* Base layer - always visible */
                .container.modern-main-menu::before {{
                    content: '';
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 100%;
                    height: 100%;
                    transform: translate(-50%, -50%) scale({scale});
                    background-image: url('{first_image_url}');
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    filter: blur({blur_px}px);
                    opacity: {opacity_float};
                    z-index: -2;
                }}
                /* Transition layer - fades in/out */
                .container.modern-main-menu::after {{
                    content: '';
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 100%;
                    height: 100%;
                    transform: translate(-50%, -50%) scale({scale});
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    filter: blur({blur_px}px);
                    opacity: 0;
                    z-index: -1;
                    transition: opacity 1.2s cubic-bezier(0.4, 0, 0.2, 1);
                }}
                .container.modern-main-menu.slideshow-transitioning::after {{
                    opacity: {opacity_float};
                }}
            </style>
            <script>
                (function() {{
                    const images = {json.dumps(image_urls)};
                    const interval = {slideshow_interval * 1000};
                    let currentIndex = 0;
                    let nextIndex = 1;
                    
                    function updateBackground() {{
                        const container = document.querySelector('.container.modern-main-menu');
                        if (!container) return;
                        
                        // Set the next image on the ::after layer
                        let afterStyleTag = document.getElementById('slideshow-after-image');
                        if (!afterStyleTag) {{
                            afterStyleTag = document.createElement('style');
                            afterStyleTag.id = 'slideshow-after-image';
                            document.head.appendChild(afterStyleTag);
                        }}
                        afterStyleTag.textContent = `.container.modern-main-menu::after {{ background-image: url('${{images[nextIndex]}}'); }}`;
                        
                        // Trigger the fade-in transition
                        setTimeout(() => {{
                            container.classList.add('slideshow-transitioning');
                        }}, 50);
                        
                        // After transition completes, swap layers
                        setTimeout(() => {{
                            // Update the ::before layer with the new image
                            let beforeStyleTag = document.getElementById('slideshow-before-image');
                            if (!beforeStyleTag) {{
                                beforeStyleTag = document.createElement('style');
                                beforeStyleTag.id = 'slideshow-before-image';
                                document.head.appendChild(beforeStyleTag);
                            }}
                            beforeStyleTag.textContent = `.container.modern-main-menu::before {{ background-image: url('${{images[nextIndex]}}'); }}`;
                            
                            // Reset the transition
                            container.classList.remove('slideshow-transitioning');
                            
                            // Update indices
                            currentIndex = nextIndex;
                            nextIndex = (nextIndex + 1) % images.length;
                        }}, 1250); // Slightly longer than transition duration
                    }}
                    
                    // Start slideshow only if there are multiple images
                    if (images.length > 1) {{
                        setInterval(updateBackground, interval);
                    }}
                }})();
            </script>
            """
            main_container_css += "<style>.main-content { background: transparent !important; }</style>"
        else:
            # No images selected, fallback to color mode
            main_container_css = f"""
            <style id='modern-menu-main-background-style'>
                .container.modern-main-menu {{ background-color: {main_light_color} !important; }}
                .night-mode .container.modern-main-menu {{ background-color: {main_dark_color} !important; }}
            </style>
            """
            main_container_css += "<style>.main-content { background: transparent !important; }</style>"
    else:
        # Original image mode handling
        if main_image_mode == "separate":
            main_light_img_filename = mw.col.conf.get("modern_menu_background_image_light", "")
            main_dark_img_filename = mw.col.conf.get("modern_menu_background_image_dark", "")
        else:
            main_light_img_filename = mw.col.conf.get("modern_menu_background_image", "")
            main_dark_img_filename = main_light_img_filename

        main_light_img = f"user_files/main_bg/{main_light_img_filename}" if main_light_img_filename else ""
        main_dark_img = f"user_files/main_bg/{main_dark_img_filename}" if main_dark_img_filename else ""
    
        main_container_css = _render_background_css(
            ".container.modern-main-menu", main_mode, main_light_color, main_dark_color, 
            main_light_img, main_dark_img, main_blur, addon_path, "modern-menu-main-background-style", main_opacity
        )
        main_container_css += "<style>.main-content { background: transparent !important; }</style>"

    sidebar_mode = mw.col.conf.get("modern_menu_sidebar_bg_mode", "main")
    sidebar_css = ""
    if sidebar_mode == 'custom':
        side_mode = mw.col.conf.get("modern_menu_sidebar_bg_type", "color")
        side_light_color = mw.col.conf.get("modern_menu_sidebar_bg_color_light", "#F3F3F3")
        side_dark_color = mw.col.conf.get("modern_menu_sidebar_bg_color_dark", "#2C2C2C")
        side_blur = mw.col.conf.get("modern_menu_sidebar_bg_blur", 0)
        side_img_filename = mw.col.conf.get("modern_menu_sidebar_bg_image", "")
        side_img = f"user_files/sidebar_bg/{side_img_filename}" if side_img_filename else ""
        
        side_opacity = mw.col.conf.get("modern_menu_sidebar_bg_opacity", 100)
        side_transparency = mw.col.conf.get("modern_menu_sidebar_bg_transparency", 0)
        addon_name = os.path.basename(addon_path)

        if side_mode == "color" or side_mode == "accent":
            alpha = (100 - side_transparency) / 100.0
            
            if side_mode == "accent":
                 sidebar_css = f"""<style id='modern-menu-sidebar-background-style'>
                    .sidebar-left {{ position: relative; background: transparent !important; }}
                    .sidebar-left::before {{
                        content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                        background: var(--accent-color);
                        opacity: {alpha};
                        z-index: -1;
                    }}
                </style>"""
            else: # solid color
                if side_transparency > 0:
                    light_rgba = _hex_to_rgba(side_light_color, alpha)
                    dark_rgba = _hex_to_rgba(side_dark_color, alpha)
                    sidebar_css = f"""<style id='modern-menu-sidebar-background-style'>
                        .sidebar-left {{ background-color: {light_rgba} !important; }}
                        .night-mode .sidebar-left {{ background-color: {dark_rgba} !important; }}
                    </style>"""
                else: # No transparency
                    sidebar_css = f"""<style id='modern-menu-sidebar-background-style'>
                        .sidebar-left {{ background-color: {side_light_color} !important; }}
                        .night-mode .sidebar-left {{ background-color: {side_dark_color} !important; }}
                    </style>"""

        elif side_mode == "image_color" and side_img:
            img_url = f"/_addons/{addon_name}/{side_img}"
            opacity_float = side_opacity / 100.0
            blur_px = side_blur * 0.2

            sidebar_css = f"""
            <style id='modern-menu-sidebar-background-style'>
                .sidebar-left {{
                    position: relative;
                    background-color: {side_light_color} !important;
                    overflow: hidden;
                    z-index: 1;
                }}
                .night-mode .sidebar-left {{
                    background-color: {side_dark_color} !important;
                }}
                .sidebar-left::before {{
                    content: '';
                    position: absolute;
                    top: 50%; left: 50%;
                    width: 100%; height: 100%;
                    transform: translate(-50%, -50%) scale({1.0 + (blur_px / 50.0) if blur_px > 0 else 1.0});
                    background-image: url('{img_url}');
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    opacity: {opacity_float};
                    filter: blur({blur_px}px);
                    z-index: -1;
                }}
            </style>
            """
    else: # sidebar_mode == 'main'
        effect_mode = mw.col.conf.get("onigiri_sidebar_main_bg_effect_mode", "opaque")
        
        if effect_mode == "glassmorphism":
            intensity = mw.col.conf.get("onigiri_sidebar_main_bg_effect_intensity", 50)
            blur_px = (intensity / 100.0) * 15.0
            alpha = (intensity / 100.0) * 0.3
            
            sidebar_css = f"""
            <style id='modern-menu-sidebar-background-style'>
                .sidebar-left {{
                    background-color: rgba(255, 255, 255, {alpha}) !important;
                    backdrop-filter: blur({blur_px}px);
                    -webkit-backdrop-filter: blur({blur_px}px);
                }}
                .night-mode .sidebar-left {{
                    background-color: rgba(0, 0, 0, {alpha}) !important;
                }}
            </style>
            """
        else: # opaque color overlay
            intensity = mw.col.conf.get("onigiri_sidebar_opaque_tint_intensity", 30)
            alpha = intensity / 100.0
            
            light_color_hex = mw.col.conf.get("onigiri_sidebar_opaque_tint_color_light", "#FFFFFF")
            dark_color_hex = mw.col.conf.get("onigiri_sidebar_opaque_tint_color_dark", "#1D1D1D")
            
            light_rgba = _hex_to_rgba(light_color_hex, alpha)
            dark_rgba = _hex_to_rgba(dark_color_hex, alpha)

            sidebar_css = f"""
            <style id='modern-menu-sidebar-background-style'>
                .sidebar-left {{
                    background-color: {light_rgba} !important;
                }}
                .night-mode .sidebar-left {{
                    background-color: {dark_rgba} !important;
                }}
            </style>
            """
        
    return main_container_css + sidebar_css


def generate_reviewer_background_css(addon_path):
    """Generates CSS for the reviewer - exact copy of overview implementation with reviewer config keys."""
    conf = config.get_config()
    reviewer_mode = conf.get("onigiri_reviewer_bg_mode", "main")
    addon_name = os.path.basename(addon_path)
    
    # Show scrollbar with transparent background when needed
    scrollbar_css = """
        /* Styled scrollbar with transparent background */
        ::-webkit-scrollbar {
            width: 10px;
        }

        ::-webkit-scrollbar-track {
            background: transparent;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(128, 128, 128, 0.5);
            border-radius: 12px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(128, 128, 128, 0.7);
        }

        html {
            overflow-y: auto !important;
            scrollbar-width: thin;  /* Firefox */
            scrollbar-color: rgba(128, 128, 128, 0.5) transparent;  /* Firefox */
        }
        
        body {
            overflow-y: visible !important;
        }
    """
    
    if reviewer_mode == "main":
        # Use main background settings (like overview does)
        mode = mw.col.conf.get("modern_menu_background_mode", "color")
        light_color = mw.col.conf.get("modern_menu_bg_color_light", "#F5F5F5")
        dark_color = mw.col.conf.get("modern_menu_bg_color_dark", "#2C2C2C")
        blur_val = conf.get("onigiri_reviewer_bg_main_blur", 0)
        opacity_val = conf.get("onigiri_reviewer_bg_main_opacity", 100)
        
        if mode not in ["image", "image_color"]:
            return f"""<style id="onigiri-reviewer-background-style">
                body {{ background-color: {light_color} !important; }}
                .night-mode body {{ background-color: {dark_color} !important; }}
            
                #qa, #_flag {{
                    font-family: revert !important;
                }}

                /* Reset background inheritance for card content areas to prevent interference with card templates */
                #qa, #qa *, #_flag, #_flag * {{
                    background-attachment: initial !important;
                    background-blend-mode: initial !important;
                    background-clip: initial !important;
                    background-origin: initial !important;
                }}

                body.card {{

                }}
                {scrollbar_css}
            </style>"""

        image_mode = mw.col.conf.get("modern_menu_background_image_mode", "single")
        if image_mode == "separate":
            light_img_file = mw.col.conf.get("modern_menu_background_image_light", "")
            dark_img_file = mw.col.conf.get("modern_menu_background_image_dark", "")
        else:
            light_img_file = mw.col.conf.get("modern_menu_background_image", "")
            dark_img_file = light_img_file

        light_img_url = f"/_addons/{addon_name}/user_files/main_bg/{light_img_file}" if light_img_file else "none"
        dark_img_url = f"/_addons/{addon_name}/user_files/main_bg/{dark_img_file}" if dark_img_file else "none"
        
    elif reviewer_mode == "color":
        # Solid color only
        light_color = conf.get("onigiri_reviewer_bg_light_color", "#FFFFFF")
        dark_color = conf.get("onigiri_reviewer_bg_dark_color", "#2C2C2C")
        return f"""<style id="onigiri-reviewer-background-style">
            body {{ background-color: {light_color} !important; }}
            .night-mode body {{ background-color: {dark_color} !important; }}
            
            /* Ensure card content maintains complete independence from Onigiri's background system */
            #qa, #qa * {{
                background-attachment: initial !important;
                background-blend-mode: initial !important;
                background-clip: initial !important;
                background-origin: initial !important;
            }}
            
            body.card {{

            }}
            {scrollbar_css}
        </style>"""
    
    else:  # image_color mode
        light_color = conf.get("onigiri_reviewer_bg_light_color", "#FFFFFF")
        dark_color = conf.get("onigiri_reviewer_bg_dark_color", "#2C2C2C")
        blur_val = conf.get("onigiri_reviewer_bg_blur", 0)
        opacity_val = conf.get("onigiri_reviewer_bg_opacity", 100)
        
        image_mode = mw.col.conf.get("onigiri_reviewer_bg_image_theme_mode", "single")
        if image_mode == "separate":
            light_img_file = conf.get("onigiri_reviewer_bg_image_light", "")
            dark_img_file = conf.get("onigiri_reviewer_bg_image_dark", "")
        else:
            light_img_file = conf.get("onigiri_reviewer_bg_image", "")
            dark_img_file = light_img_file

        light_img_url = f"/_addons/{addon_name}/user_files/reviewer_bg/{light_img_file}" if light_img_file else "none"
        dark_img_url = f"/_addons/{addon_name}/user_files/reviewer_bg/{dark_img_file}" if dark_img_file else "none"

    # EXACT COPY of overview CSS generation
    blur_px = blur_val * 0.2
    opacity_float = opacity_val / 100.0

    return f"""
    <style id="onigiri-reviewer-background-style">
        /* Use body::before pseudo-element for instant background rendering - no JavaScript delay */
        body {{
            position: relative;
            background-color: {light_color} !important;
        }}
        .night-mode body {{
            background-color: {dark_color} !important;
        }}
        
        body::before {{
            content: '';
            position: fixed;
            top: 50%; left: 50%;
            width: 100vw; height: 100vh;
            transform: translate(-50%, -50%) scale({1.0 + (blur_px / 50.0) if blur_px > 0 else 1.0});
            background-position: center;
            background-size: cover;
            background-repeat: no-repeat;
            z-index: -1;
            filter: blur({blur_px}px);
            opacity: {opacity_float};
            pointer-events: none;
            background-image: url('{light_img_url}');
        }}
        .night-mode body::before {{
            background-image: url('{dark_img_url}');
        }}
        
        html, .overview-center-container, .congrats-container {{
            background: transparent !important;
        }}
        
        /* Ensure card content maintains complete independence from Onigiri's background system */
        /* Reset background inheritance for card content areas to prevent interference with card templates */
        #qa, #qa * {{
            background-attachment: initial !important;
            background-blend-mode: initial !important;
            background-clip: initial !important;
            background-origin: initial !important;
        }}
        
        /* Prevent body::before from affecting card content rendering */
        body.card {{

        }}
        {scrollbar_css}
    </style>
    """


def generate_overview_background_css(addon_path):
    """Generates CSS for the overview screen with instant background rendering using CSS pseudo-elements."""
    conf = config.get_config()
    overview_mode = conf.get("onigiri_overview_bg_mode", "main")
    
    # Defaults
    light_color = "#F5F5F5"
    dark_color = "#2C2C2C"
    blur_val = 0
    opacity_val = 100
    light_img_file = ""
    dark_img_file = ""
    is_image_mode = False

    if overview_mode == "main":
        # Use main menu background settings
        main_mode = mw.col.conf.get("modern_menu_background_mode", "color")
        light_color = mw.col.conf.get("modern_menu_bg_color_light", "#F5F5F5")
        dark_color = mw.col.conf.get("modern_menu_bg_color_dark", "#2C2C2C")
        
        # Use overview-specific blur/opacity for main mode
        blur_val = conf.get("onigiri_overview_bg_main_blur", 0)
        opacity_val = conf.get("onigiri_overview_bg_main_opacity", 100)
        
        if main_mode in ["image", "image_color"]:
            is_image_mode = True
            image_mode = mw.col.conf.get("modern_menu_background_image_mode", "single")
            if image_mode == "separate":
                light_img_file = mw.col.conf.get("modern_menu_background_image_light", "")
                dark_img_file = mw.col.conf.get("modern_menu_background_image_dark", "")
            else:
                light_img_file = mw.col.conf.get("modern_menu_background_image", "")
                dark_img_file = light_img_file
                
    elif overview_mode == "color":
        # Solid color only
        light_color = conf.get("onigiri_overview_bg_light_color", "#FFFFFF")
        dark_color = conf.get("onigiri_overview_bg_dark_color", "#2C2C2C")
        is_image_mode = False
        
    elif overview_mode == "image_color":
        # Image + Color
        light_color = conf.get("onigiri_overview_bg_light_color", "#FFFFFF")
        dark_color = conf.get("onigiri_overview_bg_dark_color", "#2C2C2C")
        
        blur_val = conf.get("onigiri_overview_bg_blur", 0)
        opacity_val = conf.get("onigiri_overview_bg_opacity", 100)
        is_image_mode = True
        
        image_mode = conf.get("onigiri_overview_bg_image_theme_mode", "single")
        if image_mode == "separate":
            light_img_file = conf.get("onigiri_overview_bg_image_light", "")
            dark_img_file = conf.get("onigiri_overview_bg_image_dark", "")
        else:
            light_img_file = conf.get("onigiri_overview_bg_image", "")
            dark_img_file = light_img_file

    if not is_image_mode:
        return f"""<style>
            body {{ background-color: {light_color} !important; }}
            .night-mode body {{ background-color: {dark_color} !important; }}
        </style>"""

    addon_name = os.path.basename(addon_path)
    light_img_url = f"/_addons/{addon_name}/user_files/main_bg/{light_img_file}" if light_img_file else "none"
    dark_img_url = f"/_addons/{addon_name}/user_files/main_bg/{dark_img_file}" if dark_img_file else "none"

    blur_px = blur_val * 0.2
    opacity_float = opacity_val / 100.0

    return f"""
    <style id="onigiri-overview-background-style">
        /* Use body::before pseudo-element for instant background rendering - no JavaScript delay */
        body {{
            position: relative;
            background-color: {light_color} !important;
        }}
        .night-mode body {{
            background-color: {dark_color} !important;
        }}
        
        body::before {{
            content: '';
            position: fixed;
            top: 50%; left: 50%;
            width: 100vw; height: 100vh;
            transform: translate(-50%, -50%) scale({1.0 + (blur_px / 50.0) if blur_px > 0 else 1.0});
            background-position: center;
            background-size: cover;
            background-repeat: no-repeat;
            z-index: -1;
            filter: blur({blur_px}px);
            opacity: {opacity_float};
            pointer-events: none;
            background-image: url('{light_img_url}');
        }}
        .night-mode body::before {{
            background-image: url('{dark_img_url}');
        }}
        
        /* Keep JavaScript-created div styling for backwards compatibility */
        #onigiri-background-div {{
            display: none !important;
        }}
        
        html, .overview-center-container, .congrats-container {{
            background: transparent !important;
        }}
    </style>
    """


def generate_toolbar_background_css(addon_path):
	"""Generates background CSS for the top and bottom toolbars based on user settings."""
	toolbar_mode = mw.col.conf.get("onigiri_toolbar_bg_mode", "main")

	if toolbar_mode == "main":
		# Use main background settings
		mode = mw.col.conf.get("modern_menu_background_mode", "color")
		light = mw.col.conf.get("modern_menu_bg_color_light", "#F5F5F5")
		dark = mw.col.conf.get("modern_menu_bg_color_dark", "#2C2C2C")
		image = mw.col.conf.get("modern_menu_background_image", "")
		blur = mw.col.conf.get("modern_menu_background_blur", 0)
		opacity = 100 # Opacity not supported for toolbar custom bg yet
		image_path = f"user_files/{image}" if image else ""
	else:
		# Use toolbar-specific settings
		mode = toolbar_mode
		light = mw.col.conf.get("onigiri_toolbar_bg_color_light", "#FFFFFF")
		dark = mw.col.conf.get("onigiri_toolbar_bg_color_dark", "#2C2C2C")
		image = mw.col.conf.get("onigiri_toolbar_bg_image", "")
		blur = mw.col.conf.get("onigiri_toolbar_bg_blur", 0)
		opacity = 100 # Opacity not supported for toolbar custom bg yet
		image_path = f"user_files/toolbar_bg/{image}" if image else ""

	return _render_background_css("body", mode, light, dark, image_path, image_path, blur, addon_path, "onigiri-toolbar-bg-style", opacity)


def _generate_outer_background_css(mode, light_color, dark_color, light_img_path, dark_img_path, blur_val, opacity_val, addon_path, bg_position):
    """Generate CSS for #outer element with ::before pseudo-element for background.
    This ensures buttons are not affected by opacity/blur."""
    addon_name = os.path.basename(addon_path)
    blur_px = blur_val * 0.2
    opacity_float = opacity_val / 100.0
    
    # Base styling for #outer
    base_css = "<style id='onigiri-reviewer-bottom-bar-bg-style'>"
    base_css += "#outer { position: relative; border: none !important; border-top: none !important; outline: none !important; overflow: hidden; box-sizing: border-box; }"
    
    if mode == "color":
        # Solid color background - apply directly to #outer
        base_css += f"""
            #outer {{ background-color: {light_color} !important; }}
            .night-mode #outer {{ background-color: {dark_color} !important; }}
        """
    elif mode in ["image", "image_color"]:
        # Image background with ::before pseudo-element
        def get_img_url(img_path):
            if not img_path:
                return None
            if img_path.startswith("user_files/"):
                return f"/_addons/{addon_name}/{img_path}"
            else:
                return f"/_addons/{addon_name}/user_files/{img_path}"
        
        light_img_url = get_img_url(light_img_path)
        dark_img_url = get_img_url(dark_img_path) if dark_img_path else light_img_url
        
        if mode == "image_color":
            # Solid color as base layer on #outer
            base_css += f"""
                #outer {{ background-color: {light_color} !important; }}
                .night-mode #outer {{ background-color: {dark_color} !important; }}
            """
        else:
            # No color, transparent background
            base_css += "#outer { background: transparent !important; }"
        
        if light_img_url:
            # Add ::before pseudo-element for image on top of the color
            # Using z-index: 0 so it's above the background but below content
            # Apply slight scale even with no blur to prevent edge artifacts
            scale_factor = max(1.02, 1.0 + (blur_px / 50.0)) if blur_px > 0 else 1.02
            base_css += f"""
                #outer::before {{
                    content: '';
                    position: absolute;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    transform: scale({scale_factor});
                    background-image: url('{light_img_url}');
                    background-size: cover;
                    background-position: {bg_position};
                    background-repeat: no-repeat;
                    filter: blur({blur_px}px);
                    opacity: {opacity_float};
                    z-index: 0;
                    pointer-events: none;
                    border: none !important;
                    outline: none !important;
                }}
                #outer > * {{
                    position: relative;
                    z-index: 1;
                }}
            """
            
            if dark_img_url and dark_img_url != light_img_url:
                base_css += f"""
                    .night-mode #outer::before {{
                        background-image: url('{dark_img_url}');
                    }}
                """
    
    base_css += "</style>"
    return base_css


def generate_reviewer_bottom_bar_background_css(addon_path: str) -> str:
    """Generates CSS for the reviewer's bottom bar background."""
    conf = config.get_config()
    # FIX: Read from conf, not mw.col.conf
    bar_mode = conf.get("onigiri_reviewer_bottom_bar_bg_mode", "match_reviewer_bg")

    bg_position = "center bottom"

    css = ""
    # We don't use 'selector' variable effectively in the original code's structure for this function, 
    # but we'll keep the structure clean.

    # Helper to get main window settings
    def get_main_bg_settings():
        # Main settings are in mw.col.conf
        main_mode = mw.col.conf.get("modern_menu_background_mode", "color")
        light_c = mw.col.conf.get("modern_menu_bg_color_light", "#FFFFFF")
        dark_c = mw.col.conf.get("modern_menu_bg_color_dark", "#2C2C2C")
        
        # Image handling for main
        img_mode = mw.col.conf.get("modern_menu_background_image_mode", "single")
        if img_mode == "separate":
            l_img = mw.col.conf.get("modern_menu_background_image_light", "")
            # If separate mode but no light image, fallback might be needed or it's just empty
            # But usually main bg logic handles this.
            # For main bg, the key 'modern_menu_background_image' is used for single mode.
        else:
            l_img = mw.col.conf.get("modern_menu_background_image", "")
        
        # For dark image in separate mode
        if img_mode == "separate":
            d_img = mw.col.conf.get("modern_menu_background_image_dark", "")
        else:
            d_img = l_img

        # Path adjustment for main images
        # Main images are in user_files/main_bg/
        l_img_path = f"user_files/main_bg/{l_img}" if l_img else ""
        d_img_path = f"user_files/main_bg/{d_img}" if d_img else ""

        return main_mode, light_c, dark_c, l_img_path, d_img_path

    # Helper to get reviewer settings
    def get_reviewer_bg_settings():
        # Reviewer settings are in conf
        rev_mode = conf.get("onigiri_reviewer_bg_mode", "main")
        
        if rev_mode == "main":
            return get_main_bg_settings()
            
        light_c = conf.get("onigiri_reviewer_bg_light_color", "#FFFFFF")
        dark_c = conf.get("onigiri_reviewer_bg_dark_color", "#2C2C2C")
        
        img_mode = conf.get("onigiri_reviewer_bg_image_mode", "single")
        if img_mode == "separate":
            l_img = conf.get("onigiri_reviewer_bg_image_light", "")
            d_img = conf.get("onigiri_reviewer_bg_image_dark", "")
        else:
            l_img = conf.get("onigiri_reviewer_bg_image", "") # Fallback or same key? Settings saves to 'image' and 'image_light'/'image_dark'
            # Let's check settings.py saving logic. 
            # It saves to 'onigiri_reviewer_bg_image' for single, and 'onigiri_reviewer_bg_image_light'/'dark' for separate.
            # But let's be safe and check specific keys.
            if not l_img:
                 l_img = conf.get("onigiri_reviewer_bg_image_light", "")
            d_img = l_img

        # Reviewer images are in user_files/reviewer_bg/
        l_img_path = f"user_files/reviewer_bg/{l_img}" if l_img else ""
        d_img_path = f"user_files/reviewer_bg/{d_img}" if d_img else ""
        
        # Determine the actual mode based on what's configured
        # If rev_mode is "color", return "color"
        # If rev_mode is "image_color", check if images exist to determine the actual mode
        actual_mode = rev_mode
        if rev_mode == "image_color":
            # If images are configured, use "image_color", otherwise fall back to "color"
            if l_img_path or d_img_path:
                actual_mode = "image_color"
            else:
                actual_mode = "color"
        
        return actual_mode, light_c, dark_c, l_img_path, d_img_path


    if bar_mode == "main":
        # Match Main Background DIRECTLY
        mode, light_color, dark_color, light_img, dark_img = get_main_bg_settings()
        
        # Use bottom bar specific blur and opacity settings for "Match Main"
        blur_val = conf.get("onigiri_reviewer_bottom_bar_match_main_blur", 5)
        opacity_val = conf.get("onigiri_reviewer_bottom_bar_match_main_opacity", 90)

        css += _generate_outer_background_css(mode, light_color, dark_color, light_img, dark_img, blur_val, opacity_val, addon_path, bg_position)

    elif bar_mode == "match_reviewer_bg":
        # Match Reviewer Background (which might itself match Main)
        mode, light_color, dark_color, light_img, dark_img = get_reviewer_bg_settings()
        
        # Use bottom bar specific blur and opacity settings for "Match Reviewer"
        blur_val = conf.get("onigiri_reviewer_bottom_bar_match_reviewer_bg_blur", 5)
        opacity_val = conf.get("onigiri_reviewer_bottom_bar_match_reviewer_bg_opacity", 90)

        css += _generate_outer_background_css(mode, light_color, dark_color, light_img, dark_img, blur_val, opacity_val, addon_path, bg_position)

    else: # Custom settings for the bar
        mode = bar_mode # "color" or "image_color" (mapped from radio buttons)
        
        # FIX: Read from conf, not mw.col.conf
        light_color = conf.get("onigiri_reviewer_bottom_bar_bg_light_color", "#FFFFFF")
        dark_color = conf.get("onigiri_reviewer_bottom_bar_bg_dark_color", "#2C2C2C")
        
        img_filename = conf.get("onigiri_reviewer_bottom_bar_bg_image", "")
        img = f"user_files/reviewer_bar_bg/{img_filename}" if img_filename else ""
        
        blur_val = conf.get("onigiri_reviewer_bottom_bar_bg_blur", 0)
        opacity_val = conf.get("onigiri_reviewer_bottom_bar_bg_opacity", 100)

        # Generate CSS for #outer with ::before pseudo-element for background
        css += _generate_outer_background_css(mode, light_color, dark_color, img, img, blur_val, opacity_val, addon_path, bg_position)

    return css
