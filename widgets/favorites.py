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


def _get_onigiri_favorites_html() -> str:
    """
    Generates the HTML for the favorites widget.
    Automatically cleans up deleted decks from the favorites list.
    """
    try:
        favorite_dids = mw.col.conf.get("onigiri_favorite_decks", [])
        if not favorite_dids:
            return """
            <div class="onigiri-favorites-widget">
                <h3>Favorites</h3>
                <div class="favorites-placeholder">
                    No favorite decks selected.
                    <br>
                    <span>(Select decks in Edit Mode)</span>
                </div>
            </div>
            """

        links_html = []
        valid_dids = []  # Track valid deck IDs
        
        # Get all existing deck IDs for validation
        all_deck_ids = mw.col.decks.all_names_and_ids()
        existing_deck_ids = {str(deck.id) for deck in all_deck_ids}
        
        for did in favorite_dids:
            # Convert to string for consistent comparison
            did_str = str(did)
            
            # Check if deck actually exists in the collection
            if did_str not in existing_deck_ids:
                print(f"Onigiri: Skipping deleted deck ID {did_str}")
                continue
            
            # Get the deck object
            deck = mw.col.decks.get(did)
            if not deck:
                print(f"Onigiri: Skipping invalid deck ID {did_str}")
                continue
            
            # Get the deck name
            deck_name = deck.get("name", "")
            if not deck_name:
                print(f"Onigiri: Skipping deck with no name, ID {did_str}")
                continue
            
            # Deck is valid - add to valid list and create HTML
            valid_dids.append(did)
            
            # Get the short name
            short_name = deck_name.split("::")[-1]
            
            # Create a clickable link
            links_html.append(
                f"""<a class="favorite-deck-link"
                      href=# onclick="pycmd('open:{did}'); return false;"
                      title="Open {html.escape(deck_name, quote=True)}">
                    <span class="fav-deck-icon"></span>
                    <span class="fav-deck-name">{html.escape(short_name)}</span>
                </a>"""
            )
        
        # Clean up deleted decks from favorites if any were found
        if len(valid_dids) != len(favorite_dids):
            mw.col.conf["onigiri_favorite_decks"] = valid_dids
            mw.col.setMod()
            removed_count = len(favorite_dids) - len(valid_dids)
            print(f"Onigiri: Cleaned up {removed_count} deleted/ghost deck(s) from favorites")
        
        # If no valid favorites remain after cleanup, show placeholder
        if not links_html:
            return """
            <div class="onigiri-favorites-widget">
                <h3>Favorites</h3>
                <div class="favorites-placeholder">
                    No favorite decks selected.
                    <br>
                    <span>(Select decks in Edit Mode)</span>
                </div>
            </div>
            """
        
        return f"""
        <div class="onigiri-favorites-widget">
            <h3>Favorites</h3>
            <div class="favorites-list">
                {''.join(links_html)}
            </div>
        </div>
        """
    except Exception as e:
        print(f"Onigiri: Error building favorites widget: {e}")
        import traceback
        traceback.print_exc()
        return "<div class='onigiri-favorites-widget'>Error loading favorites.</div>"
