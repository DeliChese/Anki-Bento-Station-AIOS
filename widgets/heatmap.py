# Bento Station Deck Browser Widgets (tách từ bento_station_renderer.py — Bước 3 refactor)
# Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.
import html
import json
import os
import math
import copy
from dataclasses import dataclass
from aqt import mw
from .. import patcher
from aqt.deckbrowser import DeckBrowser, RenderDeckNodeContext
from .. import config, heatmap, deck_tree_updater
from .. import study_tools
from ..templates import custom_body_template


def _get_onigiri_heatmap_html() -> str:
    skeleton_cells = "".join(["<div class='skeleton-cell'></div>" for _ in range(371)])
    return f"""
    <div id='onigiri-heatmap-container'>
        <div class="heatmap-header-skeleton"><div class="header-left-skeleton"><div class="skeleton-title"></div><div class="skeleton-nav"></div></div><div class="header-right-skeleton"><div class="skeleton-streak"></div><div class="skeleton-filters"></div></div></div>
        <div class="heatmap-grid-skeleton">{skeleton_cells}</div>
    </div>"""
