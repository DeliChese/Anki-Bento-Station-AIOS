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
from .pixmap_utils import create_rounded_pixmap
from .widgets import ColorSwatch

class ThemeCardWidget(QFrame):
    """A clickable card widget to display and select a theme."""
    theme_selected = pyqtSignal(dict)
    delete_requested = pyqtSignal(str) # Signal to request deletion

    def __init__(self, theme_name, theme_data, parent=None, deletable=False, delete_icon=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self.theme_data = theme_data

        self.setObjectName("themeCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        main_layout = QVBoxLayout(self)

        # --- Top row with title and delete button ---
        top_layout = QHBoxLayout()
        name_label = QLabel(theme_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; background: transparent;")
        top_layout.addWidget(name_label)
        top_layout.addStretch()

        if deletable:
            self.delete_button = QPushButton()
            self.delete_button.setFixedSize(30, 30)
            self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.delete_button.setToolTip("Delete this theme")
            if delete_icon:
                self.delete_button.setIcon(delete_icon)
                self.delete_button.setIconSize(self.delete_button.size() * 0.6)
            
            # Style it to be subtle
            self.delete_button.setStyleSheet("""
                QPushButton { background: transparent; border: none; border-radius: 4px; }
                QPushButton:hover { background: rgba(128, 128, 128, 0.2); }
            """)
            self.delete_button.clicked.connect(self._on_delete_clicked)
            top_layout.addWidget(self.delete_button)

        # --- Bottom row with color swatches ---
        swatch_layout = QHBoxLayout()
        swatch_layout.setSpacing(6)

        # 1. Colors
        preview_colors = theme_data['light']
        color_count = 0
        for key in ["--accent-color", "--fg", "--fg-subtle", "--border", "--canvas-inset", "--bg"]:
            if key in preview_colors:
                swatch_layout.addWidget(ColorSwatch(preview_colors[key]))
                color_count += 1
                if color_count >= 5: break # Limit to 5 colors
        swatch_layout.addStretch()

        main_layout.addLayout(top_layout)
        main_layout.addLayout(swatch_layout)

        # --- Asset Previews (New) ---
        assets = theme_data.get("assets", {})
        if assets:
            asset_layout = QHBoxLayout()
            asset_layout.setSpacing(8)
            
            # Images
            if "images" in assets:
                unique_paths = set()
                unique_images = []
                for img_path in assets["images"].values():
                    # Ensure path is valid before adding
                    if img_path and os.path.exists(img_path) and img_path not in unique_paths:
                        unique_paths.add(img_path)
                        unique_images.append(img_path)
                
                for img_path in unique_images[:3]: 
                    thumb = QLabel()
                    thumb.setFixedSize(26, 26)
                    thumb.setScaledContents(False) # We will scale manually
                    thumb.setStyleSheet(f"border: none; background-color: transparent;")
                    
                    pix = QPixmap(img_path)
                    if not pix.isNull():
                         # Scale to target size keeping usage of create_rounded_pixmap
                         # If we want 26x26
                         scaled = pix.scaled(26, 26, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                         # Crop center 26x26
                         x = (scaled.width() - 26) // 2
                         y = (scaled.height() - 26) // 2
                         cropped = scaled.copy(x, y, 26, 26)
                         
                         rounded = create_rounded_pixmap(cropped, 6)
                         thumb.setPixmap(rounded)
                         thumb.setToolTip(f"Image included: {os.path.basename(img_path)}")
                         asset_layout.addWidget(thumb)

            # Fonts - show configured fonts (from font_config) even if not portable files
            font_config = assets.get("font_config", {})
            fonts_dict = assets.get("fonts", {})
            
            # Combine both sources: portable files and configured selections
            all_fonts_to_show = set()
            if fonts_dict:
                all_fonts_to_show.update(fonts_dict.keys())
            if font_config:
                all_fonts_to_show.update(font_config.values())
            
            if all_fonts_to_show:
                # Import fonts module to access already-loaded fonts
                from .fonts import get_all_fonts
                all_available_fonts = get_all_fonts(os.path.dirname(__file__))
                
                font_count = 0
                for font_key in list(all_fonts_to_show)[:2]:
                    font_label = QLabel("Aa")
                    font_label.setFixedSize(26, 26)
                    font_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Auto-detect theme mode
                    bg_color = preview_colors.get('--bg', '#ffffff')
                    try:
                        bg_hex = bg_color.lstrip('#')
                        r, g, b = int(bg_hex[0:2], 16), int(bg_hex[2:4], 16), int(bg_hex[4:6], 16)
                        brightness = (r * 299 + g * 587 + b * 114) / 1000
                        is_dark = brightness < 128
                    except:
                        is_dark = False
                    
                    if is_dark:
                        border_col = '#aaaaaa'
                        text_col = '#ffffff'
                        bg_col = '#3a3a3a'
                    else:
                        border_col = '#cccccc'
                        text_col = '#333333'
                        bg_col = '#f5f5f5'
                    
                    # Load font the same way FontCardWidget does
                    font_info = all_available_fonts.get(font_key)
                    if font_info and font_info.get("file"):
                        addon_path = os.path.dirname(__file__)
                        # Handle user-uploaded fonts
                        if font_info.get("user"):
                            font_path = os.path.join(addon_path, "user_files", "fonts", font_info["file"])
                        # Handle built-in system fonts
                        else:
                            font_path = os.path.join(addon_path, "system_files", "fonts", "system_fonts", font_info["file"])
                        
                        if os.path.exists(font_path):
                            font_id = QFontDatabase.addApplicationFont(font_path)
                            if font_id != -1:
                                font_families = QFontDatabase.applicationFontFamilies(font_id)
                                if font_families:
                                    # Apply the font to the label
                                    font_label.setFont(QFont(font_families[0], 13))
                    
                    # Set stylesheet (font is already set via setFont)
                    font_label.setStyleSheet(
                        f"border: 1px solid {border_col}; "
                        f"border-radius: 6px; "
                        f"color: {text_col}; "
                        f"background-color: {bg_col}; "
                        f"font-weight: bold;"
                    )
                    
                    font_label.setToolTip(f"Font: {font_key}")
                    asset_layout.addWidget(font_label)
                    font_count += 1
            
            # Icons - show all configured icons including defaults
            icons_dict = assets.get("icons", {})
            icon_config = assets.get("icon_config", {})
            
            # Use icons_dict primarily, fall back to icon_config
            icons_to_show = []
            if icons_dict:
                icons_to_show = list(icons_dict.items())[:2]
            elif icon_config:
                icons_to_show = list(icon_config.items())[:2]
            
            if icons_to_show:
                for icon_key, icon_value in icons_to_show:
                    # icon_value could be a filename or a path
                    # Try to find the icon file
                    possible_paths = [
                        os.path.join(os.path.dirname(__file__), "user_files", "icons", os.path.basename(icon_value)),
                        os.path.join(os.path.dirname(__file__), "user_files", "icons", icon_value),
                    ]
                    
                    full_path = None
                    for path in possible_paths:
                        if os.path.exists(path):
                            full_path = path
                            break
                    
                    # If not found in user_files, check if it's a default icon
                    if not full_path and icon_key in ICON_DEFAULTS:
                        # Use default icon data
                        default_svg_data = ICON_DEFAULTS[icon_key]
                        
                        thumb = QLabel()
                        thumb.setFixedSize(26, 26)
                        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        thumb.setStyleSheet("background: transparent; border: none;")
                        
                        icon_color = preview_colors.get("--icon-color", preview_colors.get("--fg", "#888"))
                        
                        try:
                            # Default icons are data URIs: "data:image/svg+xml,<svg>..."
                            if default_svg_data.startswith("data:image/svg+xml,"):
                                svg_xml = default_svg_data.replace("data:image/svg+xml,", "")
                                import urllib.parse
                                svg_xml = urllib.parse.unquote(svg_xml)
                                
                                # Color the SVG
                                if 'stroke="currentColor"' in svg_xml:
                                    colored_svg = svg_xml.replace('stroke="currentColor"', f'stroke="{icon_color}"')
                                elif 'fill="currentColor"' in svg_xml:
                                    colored_svg = svg_xml.replace('fill="currentColor"', f'fill="{icon_color}"')
                                else:
                                    colored_svg = svg_xml.replace('<svg', f'<svg fill="{icon_color}" stroke="{icon_color}"', 1)
                                
                                renderer = QSvgRenderer(colored_svg.encode('utf-8'))
                                pixmap = QPixmap(26, 26)
                                pixmap.fill(Qt.GlobalColor.transparent)
                                painter = QPainter(pixmap)
                                renderer.render(painter)
                                painter.end()
                                
                                thumb.setPixmap(pixmap)
                                thumb.setToolTip(f"Icon: {icon_key} (default)")
                                asset_layout.addWidget(thumb)
                        except Exception as e:
                            print(f"Default icon preview error for {icon_key}: {e}")
                        continue
                    
                    if full_path:
                        thumb = QLabel()
                        thumb.setFixedSize(26, 26)
                        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        thumb.setStyleSheet("background: transparent; border: none;")
                        
                        icon_color = preview_colors.get("--icon-color", preview_colors.get("--fg", "#888"))
                        
                        pixmap = QPixmap(26, 26)
                        pixmap.fill(Qt.GlobalColor.transparent)
                        
                        loaded = False
                        if full_path.lower().endswith(".svg"):
                            try:
                                with open(full_path, 'r', encoding='utf-8') as f: svg_xml = f.read()
                                
                                if 'stroke="currentColor"' in svg_xml:
                                    colored_svg = svg_xml.replace('stroke="currentColor"', f'stroke="{icon_color}"')
                                elif 'fill="currentColor"' in svg_xml:
                                    colored_svg = svg_xml.replace('fill="currentColor"', f'fill="{icon_color}"')
                                else:
                                    colored_svg = svg_xml.replace('<svg', f'<svg fill="{icon_color}" stroke="{icon_color}"', 1)
                                
                                renderer = QSvgRenderer(colored_svg.encode('utf-8'))
                                painter = QPainter(pixmap)
                                renderer.render(painter)
                                painter.end()
                                loaded = True
                            except Exception as e:
                                print(f"Icon preview error: {e}")
                        
                        if not loaded:
                            temp_pix = QPixmap(full_path)
                            if not temp_pix.isNull():
                                temp_pix = temp_pix.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                painter = QPainter(pixmap)
                                x = (26 - temp_pix.width()) // 2
                                y = (26 - temp_pix.height()) // 2
                                painter.drawPixmap(x, y, temp_pix)
                                painter.end()
                                loaded = True
                        
                        if loaded:
                            thumb.setPixmap(pixmap)
                            thumb.setToolTip(f"Icon: {icon_key}")
                            asset_layout.addWidget(thumb)

            asset_layout.addStretch()
            if asset_layout.count() > 1: # Only add if we added widgets (stretch is 1)
                div = QFrame()
                div.setFrameShape(QFrame.Shape.HLine)
                div.setFrameShadow(QFrame.Shadow.Sunken)
                div.setStyleSheet("color: #ddd;")
                main_layout.addWidget(div)
                main_layout.addLayout(asset_layout)

    def _on_delete_clicked(self):
        # Stop the event from propagating to the mousePressEvent
        self.block_card_click = True
        self.delete_requested.emit(self.theme_name)

    def mousePressEvent(self, event):
        # A small mechanism to prevent card selection when delete is clicked
        if hasattr(self, 'block_card_click') and self.block_card_click:
            self.block_card_click = False
            return
            
        self.theme_selected.emit(self.theme_data)
        super().mousePressEvent(event)


class IconPickerDialog(QDialog):
    iconSelected = pyqtSignal(str)

    def __init__(self, current_filename, addon_path, parent=None):
        super().__init__(parent)
        self.addon_path = addon_path
        self.current_filename = current_filename
        self.setWindowTitle("Select Icon")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.container = QFrame()
        self.container.setObjectName("IconPickerContainer")
        if theme_manager.night_mode:
             self.container.setStyleSheet("QFrame#IconPickerContainer { background-color: #2c2c2c; border-radius: 12px; border: 1px solid #4a4a4a; }")
        else:
             self.container.setStyleSheet("QFrame#IconPickerContainer { background-color: #ffffff; border-radius: 12px; border: 1px solid #e0e0e0; }")

        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(15)
        
        # --- Header ---
        header_layout = QHBoxLayout()
        title_label = QLabel("Select Icon")
        if theme_manager.night_mode:
            title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #e0e0e0;")
        else:
            title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #212121;")
            
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        
        # Load xmark.svg
        xmark_path = os.path.join(os.path.dirname(__file__), "system_files", "system_icons", "xmark.svg")
        
        if theme_manager.night_mode:
            close_btn.setStyleSheet("""
                QPushButton { background-color: transparent; border: none; border-radius: 12px; }
                QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }
            """)
            icon_color = "#e0e0e0"
        else:
            close_btn.setStyleSheet("""
                QPushButton { background-color: transparent; border: none; border-radius: 12px; }
                QPushButton:hover { background-color: rgba(0, 0, 0, 0.05); }
            """)
            icon_color = "#555555"

        if os.path.exists(xmark_path):
            self._render_svg_to_icon(xmark_path, close_btn, icon_color)
        else:
            close_btn.setText("x")
            close_btn.setStyleSheet(close_btn.styleSheet() + f"color: {icon_color}; font-weight: bold; font-size: 16px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        container_layout.addLayout(header_layout)
        
        # --- Search & Add ---
        tools_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search icons...")
        self.search_input.textChanged.connect(self._filter_icons)
        if theme_manager.night_mode:
            self.search_input.setStyleSheet("QLineEdit { background-color: #3a3a3a; border: 1px solid #555; border-radius: 6px; padding: 4px; color: #e0e0e0; } QLineEdit:focus { border-color: #777; }")
        else:
            self.search_input.setStyleSheet("QLineEdit { background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 6px; padding: 4px; color: #212121; } QLineEdit:focus { border-color: #aaa; }")
            
        add_btn = QPushButton("Add Icon")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_icon_from_file)
        if theme_manager.night_mode:
            add_btn.setStyleSheet("QPushButton { background-color: #3a3a3a; border: 1px solid #555; border-radius: 6px; padding: 4px 10px; color: #e0e0e0; } QPushButton:hover { background-color: #4a4a4a; }")
        else:
            add_btn.setStyleSheet("QPushButton { background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 6px; padding: 4px 10px; color: #212121; } QPushButton:hover { background-color: #e0e0e0; }")
            
        tools_layout.addWidget(self.search_input)
        tools_layout.addWidget(add_btn)

        # Use Default Button
        default_btn = QPushButton("Use Default")
        default_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        default_btn.clicked.connect(lambda: (self.iconSelected.emit(""), self.close()))
        if theme_manager.night_mode:
            default_btn.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #555; border-radius: 6px; padding: 4px 10px; color: #e0e0e0; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.05); }")
        else:
            default_btn.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ccc; border-radius: 6px; padding: 4px 10px; color: #212121; } QPushButton:hover { background-color: rgba(0, 0, 0, 0.02); }")
        
        tools_layout.addWidget(default_btn)
        container_layout.addLayout(tools_layout)
        
        # --- Tab Widget: Your Icons | Registry ---
        self.icon_tabs = QTabWidget()
        self.icon_tabs.setStyleSheet("QTabWidget::pane { border: none; background: transparent; }")
        
        # Tab 1: User file icons
        self.file_tab = QWidget()
        self.file_scroll = QScrollArea()
        self.file_scroll.setWidgetResizable(True)
        self.file_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.file_grid_widget = QWidget()
        self.file_grid_layout = QGridLayout(self.file_grid_widget)
        self.file_grid_layout.setSpacing(10)
        self.file_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.file_scroll.setWidget(self.file_grid_widget)
        file_tab_layout = QVBoxLayout(self.file_tab)
        file_tab_layout.setContentsMargins(0,0,0,0)
        file_tab_layout.addWidget(self.file_scroll)
        self.icon_tabs.addTab(self.file_tab, "📁 Your Icons")
        
        # Tab 2: Registry icons (by category)
        self.reg_tab = QWidget()
        self.reg_scroll = QScrollArea()
        self.reg_scroll.setWidgetResizable(True)
        self.reg_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.reg_container = QWidget()
        self.reg_layout = QVBoxLayout(self.reg_container)
        self.reg_layout.setSpacing(15)
        self.reg_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.reg_scroll.setWidget(self.reg_container)
        reg_tab_layout = QVBoxLayout(self.reg_tab)
        reg_tab_layout.setContentsMargins(0,0,0,0)
        reg_tab_layout.addWidget(self.reg_scroll)
        self.icon_tabs.addTab(self.reg_tab, "🎌 Registry")
        
        container_layout.addWidget(self.icon_tabs)
        
        self.icons = [] # List of (filename, widget)
        self._load_icons()
        self._load_registry_icons()
        
        layout.addWidget(self.container)

    def _render_svg_to_icon(self, filepath, button, color_hex):
        try:
            with open(filepath, 'r', encoding='utf-8') as f: svg_xml = f.read()
            if 'stroke="currentColor"' in svg_xml: colored_svg = svg_xml.replace('stroke="currentColor"', f'stroke="{color_hex}"')
            elif 'fill="currentColor"' in svg_xml: colored_svg = svg_xml.replace('fill="currentColor"', f'fill="{color_hex}"')
            else: colored_svg = svg_xml.replace('<svg', f'<svg fill="{color_hex}" stroke="{color_hex}"', 1)
            
            renderer = QSvgRenderer(colored_svg.encode('utf-8'))
            pixmap = QPixmap(renderer.defaultSize())
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            # Simple scaling if needed, but for icon button usually best to let QIcon handle or pre-scale
            scaled = pixmap.scaled(12, 12, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            button.setIcon(QIcon(scaled))
            button.setIconSize(QSize(12, 12))
        except:
             button.setText("x")

    def _load_icons(self):
        # Clear existing
        while self.file_grid_layout.count():
            item = self.file_grid_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.icons = []

        icons_dir = os.path.join(self.addon_path, "user_files/icons")
        if not os.path.exists(icons_dir):
            os.makedirs(icons_dir)
            
        files = sorted([f for f in os.listdir(icons_dir) if f.lower().endswith(".svg")])
        
        row, col = 0, 0
        num_cols = 4
        
        for filename in files:
            container = QWidget()
            container.setFixedSize(70, 70)
            container.setObjectName("IconItem")
            
            # Highlight if selected
            is_selected = (filename == self.current_filename)
            
            # Style
            bg_normal = "transparent"
            bg_hover = "rgba(255,255,255,0.1)" if theme_manager.night_mode else "rgba(0,0,0,0.05)"
            bg_selected = "rgba(255,255,255,0.2)" if theme_manager.night_mode else "rgba(0,0,0,0.1)"
            border_selected = "#777" if theme_manager.night_mode else "#aaa"
            
            container.setStyleSheet(f"""
                QWidget#IconItem {{
                    background-color: {bg_selected if is_selected else bg_normal};
                    border-radius: 8px;
                    border: {("1px solid " + border_selected) if is_selected else "1px solid transparent"};
                }}
                QWidget#IconItem:hover {{
                    background-color: {bg_hover};
                    border: 1px solid {border_selected};
                }}
            """)
            
            # Image
            layout = QVBoxLayout(container)
            layout.setContentsMargins(5, 5, 5, 5)
            
            preview = QLabel()
            preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Load SVG
            filepath = os.path.join(icons_dir, filename)
            # Render SVG
            self._render_svg_to_label(filepath, preview)
            
            layout.addWidget(preview)
            
            # Clickable overlay for selection
            btn = QPushButton(container)
            btn.setStyleSheet("background: transparent; border: none;")
            btn.setFixedSize(70, 70)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, f=filename: self._select_icon(f))
            btn.move(0, 0)
            
            # Delete Button (Top Right)
            del_btn = QPushButton(container)
            del_btn.setFixedSize(20, 20)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setToolTip("Delete Icon")
            del_btn.move(45, 5) # Position top-right
            
            # Load xmark icon
            xmark_path = os.path.join(os.path.dirname(__file__), "system_files", "system_icons", "xmark.svg")
            
            # Style for delete button: No background, no hover effect as requested
            btn_style = "QPushButton { background-color: transparent; border: none; }"
            
            if theme_manager.night_mode:
                del_btn.setStyleSheet(btn_style)
                icon_color = "#e0e0e0"
            else:
                del_btn.setStyleSheet(btn_style)
                icon_color = "#555555"

            if os.path.exists(xmark_path):
                self._render_svg_to_icon(xmark_path, del_btn, icon_color)
            else:
                del_btn.setText("×")
                del_btn.setStyleSheet(del_btn.styleSheet() + f"color: {icon_color}; font-weight: bold; padding-bottom: 2px;")

            del_btn.clicked.connect(lambda _, f=filename: self._delete_icon_file(f))
            del_btn.raise_() # Ensure it's on top of the selection buttton
            
            self.file_grid_layout.addWidget(container, row, col)
            self.icons.append((filename, container))
            
            col += 1
            if col >= num_cols:
                col = 0
                row += 1

    def _delete_icon_file(self, filename):
        confirm = QMessageBox.question(self, "Delete Icon", f"Are you sure you want to delete '{filename}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                os.remove(os.path.join(self.addon_path, "user_files/icons", filename))
                self._load_icons() # Reload grid
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete file: {e}")

    def _load_registry_icons(self):
        """Load all icons from icon_registry, grouped by category."""
        # Clear existing registry items
        while self.reg_layout.count():
            item = self.reg_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        categories = icon_registry.get_icons_by_category()
        category_labels = icon_registry.list_categories()
        icon_color = "#e0e0e0" if theme_manager.night_mode else "#212121"
        
        for cat_key, icon_names in categories.items():
            cat_label_text = category_labels.get(cat_key, cat_key)
            
            # Category header
            header = QLabel(cat_label_text)
            header.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {'#aaa' if theme_manager.night_mode else '#666'}; margin-top: 5px;")
            self.reg_layout.addWidget(header)
            
            # Grid for this category
            grid = QGridLayout()
            grid.setSpacing(8)
            row, col = 0, 0
            num_cols = 5
            
            for icon_name in icon_names:
                icon_data = icon_registry.get_icon(icon_name)
                if not icon_data: continue
                
                container = QWidget()
                container.setFixedSize(56, 56)
                container.setToolTip(icon_name)
                
                is_selected = (f"registry:{icon_name}" == self.current_filename)
                bg_selected = "rgba(255,255,255,0.2)" if theme_manager.night_mode else "rgba(0,0,0,0.1)"
                container.setStyleSheet(f"""
                    QWidget {{ background-color: {bg_selected if is_selected else 'transparent'}; border-radius: 8px; border: {'1px solid #777' if is_selected else '1px solid transparent'}; }}
                    QWidget:hover {{ background-color: {'rgba(255,255,255,0.1)' if theme_manager.night_mode else 'rgba(0,0,0,0.05)'}; border: 1px solid {'#777' if theme_manager.night_mode else '#aaa'}; }}
                """)
                
                # Preview label
                preview = QLabel()
                preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
                svg_xml = icon_data["svg"]
                if 'stroke="currentColor"' in svg_xml: colored_svg = svg_xml.replace('stroke="currentColor"', f'stroke="{icon_color}"')
                elif 'fill="currentColor"' in svg_xml: colored_svg = svg_xml.replace('fill="currentColor"', f'fill="{icon_color}"')
                else: colored_svg = svg_xml.replace('<svg', f'<svg fill="{icon_color}" stroke="{icon_color}"', 1)
                try:
                    renderer = QSvgRenderer(colored_svg.encode('utf-8'))
                    pixmap = QPixmap(renderer.defaultSize()); pixmap.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(pixmap); renderer.render(painter); painter.end()
                    preview.setPixmap(pixmap.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                except: preview.setText("?")
                
                layout = QVBoxLayout(container); layout.setContentsMargins(4,4,4,4); layout.addWidget(preview)
                
                btn = QPushButton(container); btn.setStyleSheet("background: transparent; border: none;"); btn.setFixedSize(56, 56)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                reg_filename = f"registry:{icon_name}"
                btn.clicked.connect(lambda _, f=reg_filename: self._select_icon(f))
                btn.move(0, 0)
                
                grid.addWidget(container, row, col)
                col += 1
                if col >= num_cols: col = 0; row += 1
            
            self.reg_layout.addLayout(grid)

    def _render_svg_to_label(self, filepath, label):
        color = "#e0e0e0" if theme_manager.night_mode else "#212121"
        try:
            with open(filepath, 'r', encoding='utf-8') as f: svg_xml = f.read()
            if 'stroke="currentColor"' in svg_xml: colored_svg = svg_xml.replace('stroke="currentColor"', f'stroke="{color}"')
            elif 'fill="currentColor"' in svg_xml: colored_svg = svg_xml.replace('fill="currentColor"', f'fill="{color}"')
            else: colored_svg = svg_xml.replace('<svg', f'<svg fill="{color}" stroke="{color}"', 1)
            
            renderer = QSvgRenderer(colored_svg.encode('utf-8'))
            pixmap = QPixmap(renderer.defaultSize())
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            label.setPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except:
             label.setText("?")

    def _filter_icons(self, text):
        text = text.lower()
        # Clear file grid
        while self.file_grid_layout.count():
            item = self.file_grid_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        files = [f for f, _ in self.icons] # We are effectively just using self.icons as a cache of available files + widgets? 
        # Re-read files probably easier or reuse logic.
        
        icons_dir = os.path.join(self.addon_path, "user_files/icons")
        all_files = sorted([f for f in os.listdir(icons_dir) if f.lower().endswith(".svg")])
        filtered_files = [f for f in all_files if text in f.lower()]
        
        row, col = 0, 0
        num_cols = 4
        
        for filename in filtered_files:
            container = QWidget()
            container.setFixedSize(70, 70)
            is_selected = (filename == self.current_filename)
            
            bg_normal = "transparent"
            bg_hover = "rgba(255,255,255,0.1)" if theme_manager.night_mode else "rgba(0,0,0,0.05)"
            bg_selected = "rgba(255,255,255,0.2)" if theme_manager.night_mode else "rgba(0,0,0,0.1)"
            border_selected = "#777" if theme_manager.night_mode else "#aaa"
            
            container.setStyleSheet(f"QWidget {{ background-color: {bg_selected if is_selected else bg_normal}; border-radius: 8px; border: {('1px solid ' + border_selected) if is_selected else '1px solid transparent'}; }} QWidget:hover {{ background-color: {bg_hover}; border: 1px solid {border_selected}; }}")
            
            layout = QVBoxLayout(container); layout.setContentsMargins(5, 5, 5, 5)
            preview = QLabel(); preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._render_svg_to_label(os.path.join(icons_dir, filename), preview)
            layout.addWidget(preview)
            
            btn = QPushButton(container)
            btn.setStyleSheet("background: transparent; border: none;")
            btn.setFixedSize(70, 70); btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, f=filename: self._select_icon(f))
            btn.move(0, 0)
            
            self.file_grid_layout.addWidget(container, row, col)
            col += 1
            if col >= num_cols: col = 0; row += 1

    def _select_icon(self, filename):
        self.iconSelected.emit(filename)
        self.close()

    def _add_icon_from_file(self):
        icons_dir = os.path.join(self.addon_path, "user_files/icons")
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Icon", os.path.expanduser("~"), "SVG Files (*.svg)")
        if filepath:
            filename = os.path.basename(filepath)
            dest_path = os.path.join(icons_dir, filename)
            if not os.path.exists(dest_path) or not os.path.samefile(filepath, dest_path):
                try: shutil.copy(filepath, dest_path)
                except Exception as e: QMessageBox.warning(self, "Error", f"Could not copy icon: {e}"); return
            
            self._load_icons() # Reload grid
            # self.search_input.setText("")

    def focusOutEvent(self, event):
        self.close()
