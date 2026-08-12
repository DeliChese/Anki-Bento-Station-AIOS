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


def _hex_to_rgba(hex_str: str, alpha: float) -> str:
	"""Converts a hex color string to an rgba string."""
	hex_str = hex_str.lstrip('#')
	if len(hex_str) != 6:
		return f"rgba(0,0,0,{alpha})" # Return a default for invalid hex
	try:
		r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
		return f"rgba({r}, {g}, {b}, {alpha})"
	except ValueError:
		return f"rgba(0,0,0,{alpha})"


def _mix_colors(c1, c2, ratio):
	"""Mixes two colors (hex or rgba) with a given ratio (0.0 to 1.0).
	ratio is the weight of c1.
	"""
	def parse_color(c):
		if not c: return (0, 0, 0, 1.0)
		if c.startswith('#'):
			c = c.lstrip('#')
			if len(c) == 6:
				return tuple(int(c[i:i+2], 16) for i in (0, 2, 4)) + (1.0,)
			elif len(c) == 3:
				return tuple(int(c[i]*2, 16) for i in (0, 1, 2)) + (1.0,)
		elif c.startswith('rgba'):
			parts = c[5:-1].split(',')
			return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
		elif c.startswith('rgb'):
			parts = c[4:-1].split(',')
			return float(parts[0]), float(parts[1]), float(parts[2]), 1.0
		return (0, 0, 0, 1.0) # Fallback

	r1, g1, b1, a1 = parse_color(c1)
	r2, g2, b2, a2 = parse_color(c2)

	r = r1 * ratio + r2 * (1 - ratio)
	g = g1 * ratio + g2 * (1 - ratio)
	b = b1 * ratio + b2 * (1 - ratio)
	a = a1 * ratio + a2 * (1 - ratio)

	return f"rgba({int(r)}, {int(g)}, {int(b)}, {a:.2f})"
