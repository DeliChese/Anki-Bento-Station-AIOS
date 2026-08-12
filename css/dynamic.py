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

from .fonts import generate_font_css
from .utils import _hex_to_rgba, _mix_colors

def generate_dynamic_css(conf):
	# ADDED to get the add-on's path for font files
	addon_package = mw.addonManager.addonFromModule(__name__)
	# ADDED to generate the font-specific CSS
	font_css_block = generate_font_css(addon_package)

	effect_mode = mw.col.conf.get("onigiri_canvas_inset_effect_mode", "none")
	effect_intensity = mw.col.conf.get("onigiri_canvas_inset_effect_intensity", 50)

	def _apply_canvas_inset_effect(colors: dict):
		"""Applies opacity or glassmorphism effect to --canvas-inset color."""
		if "--canvas-inset" not in colors:
			return

		if effect_mode in ["opacity", "glassmorphism"]:
			original_hex = colors["--canvas-inset"]
			
			# Intensity to alpha mapping (0-100 -> 1.0-0.0)
			# For glassmorphism, higher intensity means more transparency.
			alpha = (100 - effect_intensity) / 100.0
			
			# For simple opacity, higher intensity means more opacity.
			if effect_mode == "opacity":
				alpha = effect_intensity / 100.0

			colors["--canvas-inset"] = _hex_to_rgba(original_hex, alpha)

	colors = conf.get("colors", {})
	light_colors = colors.get("light", {}).copy()
	dark_colors = colors.get("dark", {}).copy()

	# Apply effects if enabled
	_apply_canvas_inset_effect(light_colors)
	_apply_canvas_inset_effect(dark_colors)

	# --- START: Calculate Heatmap Colors (to avoid CSS color-mix) ---
	def _generate_heatmap_colors(colors_dict, is_night_mode):
		canvas_inset = colors_dict.get("--canvas-inset", "#ffffff")
		# Get user-defined heatmap colors
		heatmap_color = colors_dict.get("--heatmap-color", "#9be9a8")
		heatmap_color_zero = colors_dict.get("--heatmap-color-zero", "#f0f0f0" if not is_night_mode else "#3a3a3a")
		
		# Past/Due Level 0 - use the user-defined heatmap-color-zero
		colors_dict["--heatmap-level-0"] = heatmap_color_zero
		colors_dict["--heatmap-future-0"] = heatmap_color_zero

		# LEVELS 1-8 Loop
		for i in range(1, 9):
			# --- Past Colors ---
			# Use the user selected color as the maximum intensity (Level 8)
			# Interpolate towards the canvas background (inset) for lower levels.
			# This works for both Light Mode (White bg -> Blue) and Dark Mode (Dark bg -> Blue).
			
			# Use a slightly non-linear ratio to make lower levels visible
			ratio = (i / 8.0) ** 0.6
			
			# Determine the "faint" color limit.
			# We don't want Level 1 to be invisible (ratio 0), so we scale ratio to be, say, 0.2 to 1.0
			cleaned_ratio = 0.25 + (ratio * 0.75) 

			# Mix: Target Color (weight: cleaned_ratio) <-> Empty Day Color (weight: 1-cleaned_ratio)
			# We use heatmap_color_zero as the base to ensure a smooth transition from "Empty" to "Activity".
			# This also avoids issues where canvas_inset might be transparent (glassmorphism).
			colors_dict[f"--heatmap-level-{i}"] = _mix_colors(heatmap_color, heatmap_color_zero, cleaned_ratio)

			# --- Future Colors (blending from heatmap_color_zero -> black/white) ---
			# Future days: Level 8 = Strongest Contrast. Level 1 = Faint.
			if is_night_mode:
				# Dark mode: heatmap_color_zero (Gray) -> White
				future_ratio = 0.1 + (i / 8.0) * 0.5 # Mix in up to 60% white
				colors_dict[f"--heatmap-future-{i}"] = _mix_colors("#ffffff", heatmap_color_zero, future_ratio)
			else:
				# Light mode: heatmap_color_zero (Gray) -> Black
				future_ratio = 0.1 + (i / 8.0) * 0.5 # Mix in up to 60% black
				colors_dict[f"--heatmap-future-{i}"] = _mix_colors("#000000", heatmap_color_zero, future_ratio)

	_generate_heatmap_colors(light_colors, False)
	_generate_heatmap_colors(dark_colors, True)
	# --- END: Calculate Heatmap Colors ---

	# Keep all colors, we'll apply them with proper scoping
	light_rules = []
	dark_rules = []
	
	# Non-card related styles (applied globally)
	non_card_related = {
		"--bg", "--bg-elevated", "--bg-hover", "--bg-active",
		"--border", "--border-hover", "--border-active",
		"--shadow-small", "--shadow-medium", "shadow-large",
		"--canvas-inset"
	}
	
	# Add non-card related styles to global rules
	for key, value in light_colors.items():
		if key in non_card_related:
			light_rules.append(f"    {key}: {value} !important;")
		
	for key, value in dark_colors.items():
		if key in non_card_related:
			dark_rules.append(f"    {key}: {value} !important;")
	
	# Add scoped styles for Onigiri UI elements
	onigiri_ui_light = []
	onigiri_ui_dark = []
	
	text_related = {
		"--fg", "--fg-subtle", "--fg-faint", "--fg-on-accent",
		"--accent", "--accent-hover", "--accent-pressed",
		"--text-on-accent", "--text-on-accent-hover", "--text-on-accent-pressed",
		"--accent-light", "--accent-lighter", "--accent-dark", "--accent-darker"
	}
	
	for key, value in light_colors.items():
		if key in text_related:
			onigiri_ui_light.append(f"    {key}: {value} !important;")
			
	for key, value in dark_colors.items():
		if key in text_related:
			onigiri_ui_dark.append(f"    {key}: {value} !important;")
	
	# Convert lists to strings
	light_rules = "\n".join(light_rules)
	dark_rules = "\n".join(dark_rules)
	onigiri_ui_light = "\n".join(onigiri_ui_light)
	onigiri_ui_dark = "\n".join(onigiri_ui_dark)

	# Special case: One setting for two CSS variables
	if "--button-primary-bg" in light_colors:
		light_colors["--button-primary-bg"] = light_colors["--button-primary-bg"]
	if "--button-primary-bg" in dark_colors:
		dark_colors["--button-primary-bg"] = dark_colors["--button-primary-bg"]

	light_rules = "\n".join([f"    {key}: {value} !important;" for key, value in light_colors.items()])
	dark_rules = "\n".join([f"    {key}: {value} !important;" for key, value in dark_colors.items()])
	
	profile_light_color = mw.col.conf.get("modern_menu_profile_bg_color_light", "#EEEEEE")
	profile_dark_color = mw.col.conf.get("modern_menu_profile_bg_color_dark", "#3C3C3C")
	light_rules += f"\n    --profile-bg-custom-color: {profile_light_color} !important;"
	dark_rules += f"\n    --profile-bg-custom-color: {profile_dark_color} !important;"

	# --- New Glassmorphism Style Block ---
	glass_style_block = ""
	if effect_mode == "glassmorphism":
		# Map intensity (0-100) to blur radius (0-20px)
		blur_px = (effect_intensity / 100.0) * 20
		# --- FIX: Added heatmap container IDs to the selectors ---
		glass_selectors = ".stats-container, .congrats-card, .stat-card, #onigiri-heatmap-container, #onigiri-profile-heatmap-container"
		glass_style_block = f"""
        <style id="onigiri-glass-effect">
        {glass_selectors} {{
            backdrop-filter: blur({blur_px}px);
            -webkit-backdrop-filter: blur({blur_px}px);
        }}
        </style>
        """

	# MODIFIED to include scoped Onigiri UI styles and reset card styles
	return f"""
    {font_css_block}
    <style id="modern-menu-dynamic-styles">
    /* Global styles (non-text related) */
    :root {{ {light_rules} }}
    .night-mode {{ {dark_rules} }}
    
    /* Scoped Onigiri UI styles */
    .onigiri-ui, 
    [class*="onigiri-"],
    .modern-menu,
    .modern-menu *:not(.card, .card *),
    .onigiri-profile-page,
    .onigiri-profile-page *:not(.card, .card *),
    .onigiri-restaurant,
    .onigiri-restaurant *:not(.card, .card *) {{
        {onigiri_ui_light}
    }}
    
    .night-mode .onigiri-ui,
    .night-mode [class*="onigiri-"],
    .night-mode .modern-menu,
    .night-mode .modern-menu *:not(.card, .card *),
    .night-mode .onigiri-profile-page,
    .night-mode .onigiri-profile-page *:not(.card, .card *),
    .night-mode .onigiri-restaurant,
    .night-mode .onigiri-restaurant *:not(.card, .card *) {{
        {onigiri_ui_dark}
    }}
    </style>
    {glass_style_block}
    """
