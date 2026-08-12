# Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.
"""Tách từ settings.py (Bước 1 refactor) — di chuyển nguyên vẹn, không đổi logic."""
import os
import copy
import shutil
import urllib.parse
import json
import functools
import time
from datetime import datetime
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QDialogButtonBox, QWidget, QTabWidget, QColorDialog, QColor, QCheckBox,
    QGroupBox, QRadioButton, QFileDialog, QSpinBox, QPlainTextEdit, QFormLayout, QScrollArea,
    QGridLayout, QPixmap, Qt, QEvent, QPainter, QPainterPath, QMessageBox,
    QListWidget, QStackedWidget, QListWidgetItem, QFrame, QSizePolicy,
    QComboBox,
    QIcon, QPen, QBrush, QInputDialog, QAbstractButton, QDoubleSpinBox,
    QButtonGroup, QAbstractSpinBox,
    QDrag, QMimeData, QPoint,
    QMenu, QAction, QActionGroup,
    QListWidget, QListWidgetItem, QAbstractItemView, QDateEdit, QLayout
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtProperty, QPointF, QSignalBlocker, QSize, QTimer, QDate, QLocale
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QUrl, QPropertyAnimation, QEasingCurve, QRegularExpression
from PyQt6.QtGui import QDesktopServices, QLinearGradient, QRegularExpressionValidator, QMouseEvent, QRegion, QGuiApplication, QCursor, QIntValidator
from typing import Union
from aqt import mw
from aqt import mw, gui_hooks
from aqt.theme import theme_manager
from aqt.qt import QRectF
from aqt.utils import showInfo
from PyQt6.QtGui import QImage, QFontDatabase, QFont
from PyQt6.QtCore import QRect, QSize, QPoint
from ..config import DEFAULTS
from ..constants import COLOR_LABELS, ICON_DEFAULTS, DEFAULT_ICON_SIZES, ALL_THEME_KEYS, REVIEWER_THEME_KEYS
from ..themes import THEMES
from .. import icon_registry
from ..fonts import FONTS, get_all_fonts
from .widgets import SearchResultWidget

class SettingsSearchPage(QWidget):
    page_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # --- Search Bar ---
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search settings...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border-radius: 15px;
                border: 1px solid #ccc;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #007bff;
            }
        """)
        self.search_bar.textChanged.connect(self._filter_cards)
        self.layout.addWidget(self.search_bar)

        # --- Scroll Area for Cards ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")
        
        self.content_wrapper = QWidget()
        self.wrapper_layout = QVBoxLayout(self.content_wrapper)
        self.wrapper_layout.setContentsMargins(0, 0, 0, 0)
        self.wrapper_layout.setSpacing(0)

        # Cards Container (List)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.wrapper_layout.addWidget(self.cards_container)

        # Results Container (List)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setSpacing(10)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.wrapper_layout.addWidget(self.results_container)
        self.results_container.hide()
        
        self.scroll_area.setWidget(self.content_wrapper)
        self.layout.addWidget(self.scroll_area)

        self.cards = []
        self._create_cards()

    def _create_cards(self):
        # Format: (Title, Description, [Pages], [Keywords])
        sections = [
            ("Profile", "Manage your profile settings.", ["Profile"],
             ["User Details", "Profile Picture", "Profile Bar Background"]),
            ("General", "Customize appearance, fonts, and themes.", ["Modes", "Fonts", "Palette", "Themes", "Gallery"],
             ["Modes", "Hide", "Pro", "Max", "Fonts", "Accent Color", "General Palette", "Boxes Color Effect", "Light Mode", "Dark Mode", "Official Themes", "Your Themes", "Gallery", "Colors Gallery", "Images Gallery"]),
            ("Menu", "Configure main menu and sidebar options.", ["Main menu", "Sidebar"],
             ["Organize", "Main Background", "Heatmap", "Visibility", "Congratulations", "Sidebar Customization", "Organize Sidebar", "Sidebar Background", "Action Buttons", "Deck", "Icon Sizing"]),
            ("Study Pages", "Settings for Overviewer and Reviewer.", ["Overviewer", "Reviewer"],
             ["Overviewer Background", "Overview Style", "Congratulations", "Reviewer Background", "Bottom Bar Background"]),
        ]

        for title, desc, pages, settings in sections:
            card = self._create_card_widget(title, desc, pages)
            self.cards.append((card, title, desc, pages, settings))
            self.cards_layout.addWidget(card)
        
        self.cards_layout.addStretch()

    def _create_card_widget(self, title, desc, pages):
        card = QFrame()
        card.setObjectName("searchCard")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setFixedHeight(80)
        
        # Determine background color based on theme
        if theme_manager.night_mode:
            bg_color = "#3a3a3a"
            text_color = "#e0e0e0"
            desc_color = "#aaaaaa"
            hover_bg = "#4a4a4a"
            match_text_color = "#bbbbbb"
        else:
            bg_color = "#dddddd"
            text_color = "#212121"
            desc_color = "#555555"
            hover_bg = "#e0e0e0"
            match_text_color = "#555555"

        # Resolve real accent color from theme
        current_theme = mw.col.conf.get("modern_menu_theme", "Tokyo Drift")
        accent_color = "#007bff"
        if current_theme in THEMES:
            mode = "dark" if theme_manager.night_mode else "light"
            accent_color = THEMES[current_theme][mode].get("--accent-color", accent_color)

        card.setStyleSheet(f"""
            QFrame#searchCard {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 2px solid transparent;
            }}
            QFrame#searchCard:hover {{
                background-color: {hover_bg};
                border: 2px solid {accent_color};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {text_color}; background: transparent;")
        layout.addWidget(title_lbl)
        
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {desc_color}; background: transparent;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # Container for matches (initially hidden)
        matches_container = QWidget()
        matches_layout = QVBoxLayout(matches_container)
        matches_layout.setContentsMargins(0, 5, 0, 0)
        matches_layout.setSpacing(2)
        matches_container.hide()
        layout.addWidget(matches_container)
        
        # Store references for dynamic updates
        card.title_label = title_lbl
        card.desc_label = desc_lbl
        card.matches_container = matches_container
        card.matches_layout = matches_layout
        card.match_text_color = match_text_color
        card.current_target_page = pages[0]
        
        # Use a method for the click handler to access the current target
        card.mousePressEvent = lambda event: self.page_requested.emit(card.current_target_page)
        
        return card

    def _filter_cards(self, text):
        text = text.lower().strip()
        
        if not text:
            self.results_container.hide()
            self.cards_container.show()
            
            # Clear results to free memory
            while self.results_layout.count():
                child = self.results_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            return

        self.cards_container.hide()
        self.results_container.show()
        
        # Clear previous results
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        results_found = False
        
        for card, title, desc, pages, settings in self.cards:
            # Check for Title/Desc match
            if text in title.lower() or text in desc.lower():
                # Add the main section as a result
                widget = SearchResultWidget(title, desc, pages[0])
                widget.clicked.connect(lambda _, p=pages[0]: self.page_requested.emit(p))
                self.results_layout.addWidget(widget)
                results_found = True

            # Check for Settings match
            for setting in settings:
                if text in setting.lower():
                    # Add the setting as a result
                    # Try to map setting to a specific page if possible, otherwise default to first page
                    target_page = pages[0]
                    # Simple heuristic: if setting name contains page name
                    for p in pages:
                        if p.lower() in setting.lower():
                            target_page = p
                            break
                    
                    widget = SearchResultWidget(setting, f"In {title}", target_page)
                    widget.clicked.connect(lambda _, p=target_page: self.page_requested.emit(p))
                    self.results_layout.addWidget(widget)
                    results_found = True

        if not results_found:
            no_results = QLabel("No results found.")
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_results.setStyleSheet("color: #888; font-size: 14px; margin-top: 20px;")
            self.results_layout.addWidget(no_results)
        
        self.results_layout.addStretch()
