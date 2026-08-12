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
from .pixmap_utils import create_circular_pixmap, create_rounded_pixmap

class FlowLayout(QLayout):
    """A responsive layout that arranges widgets horizontally when space permits, vertically otherwise."""
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            widget = item.widget()
            if widget is None:
                continue
            
            space_x = spacing
            space_y = spacing
            next_x = x + item.sizeHint().width() + space_x
            
            # If this item doesn't fit and we're not at the start of a line, move to next line
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class ThumbnailWorker(QObject):
    thumbnail_ready = pyqtSignal(str, int, QPixmap, str)
    finished = pyqtSignal()

    def __init__(self, key, full_folder_path, image_files, shape='rounded'):
        super().__init__()
        self.key = key
        self.full_folder_path = full_folder_path
        self.image_files = image_files
        self.is_cancelled = False
        self.shape = shape

    def run(self):
        # --- MODIFIED: Reduced dimensions to create padding ---
        # Original was 110x62. New dimensions are 10px smaller.
        thumb_width = 100
        thumb_height = 55 # Kept aspect ratio close to 16:9

        for index, filename in enumerate(self.image_files):
            if self.is_cancelled:
                break
            try:
                pixmap_path = os.path.join(self.full_folder_path, filename)
                final_pixmap = QPixmap()

                if self.shape == 'circular':
                    source_image = QImage(pixmap_path)
                    if not source_image.isNull():
                        final_pixmap = create_circular_pixmap(source_image, 100)
                else: # 'rounded'
                    pixmap = QPixmap(pixmap_path)
                    if not pixmap.isNull():
                        # Scale the image to cover the smaller target rectangle
                        scaled_pixmap = pixmap.scaled(
                            thumb_width, thumb_height, 
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                            Qt.TransformationMode.SmoothTransformation
                        )
                        
                        # Crop from the center
                        crop_x = (scaled_pixmap.width() - thumb_width) / 2
                        crop_y = (scaled_pixmap.height() - thumb_height) / 2
                        
                        cropped_pixmap = scaled_pixmap.copy(int(crop_x), int(crop_y), thumb_width, thumb_height)
                        
                        final_pixmap = create_rounded_pixmap(cropped_pixmap, 10)
                
                if not final_pixmap.isNull():
                    self.thumbnail_ready.emit(self.key, index, final_pixmap, filename)
            except Exception as e:
                print(f"Onigiri ThumbnailWorker Error for '{filename}': {e}")
        self.finished.emit()

    def cancel(self):
        self.is_cancelled = True


class SelectionOverlay(QWidget):
    def __init__(self, parent=None, accent_color="#D65DB1"):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self._checked = False
        self.accent_color = QColor(accent_color)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) # Let clicks pass through

    def setChecked(self, checked):
        self._checked = checked
        self.update()

    def isChecked(self):
        return self._checked

    def paintEvent(self, event):
        if not self._checked:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw white circle
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())
        
        # Draw checkmark
        path = QPainterPath()
        path.moveTo(7, 12)
        path.lineTo(10, 15)
        path.lineTo(17, 8)
        
        # Use the accent color for the checkmark
        pen = QPen(self.accent_color) 
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)


class CircularColorButton(QPushButton):
    def __init__(self, color=QColor("white"), parent=None):
        super().__init__("", parent)
        self.setFixedSize(26, 26)
        self._color = QColor(color)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Choose Color")

    def color(self):
        return self._color

    def setColor(self, color):
        qcolor = QColor(color)
        if self._color != qcolor:
            self._color = qcolor
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect)
        border_color = QColor("#888888")
        pen = QPen(border_color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)


class AnimatedToggleButton(QAbstractButton):
    def __init__(self, parent=None, accent_color="#007bff"):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.accent_color = QColor(accent_color)
        self.track_color_off = QColor("#cccccc") if not theme_manager.night_mode else QColor("#555555")
        self.thumb_color = QColor("#ffffff")
        
        self.setFixedSize(38, 20)
        
        self._thumb_x_pos = 3.0

        self.animation = QPropertyAnimation(self, b"thumb_x_pos", self)
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.toggled.connect(self._start_animation)

    @pyqtProperty(float)
    def thumb_x_pos(self):
        return self._thumb_x_pos

    @thumb_x_pos.setter
    def thumb_x_pos(self, value):
        self._thumb_x_pos = value
        self.update()

    def _start_animation(self, checked):
        end_pos = self.width() - self.height() + 3 if checked else 3
        self.animation.setStartValue(self.thumb_x_pos)
        self.animation.setEndValue(end_pos)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        height = self.height()
        radius = height / 2.0
        
        painter.setPen(Qt.PenStyle.NoPen)
        track_color = self.accent_color if self.isChecked() else self.track_color_off
        painter.setBrush(track_color)
        painter.drawRoundedRect(self.rect(), radius, radius)

        thumb_radius = radius - 3
        painter.setBrush(self.thumb_color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        thumb_y = radius
        painter.drawEllipse(QPointF(self._thumb_x_pos + thumb_radius, thumb_y), thumb_radius, thumb_radius)

    def showEvent(self, event):
        super().showEvent(event)
        self._thumb_x_pos = self.width() - self.height() + 3 if self.isChecked() else 3
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._thumb_x_pos = self.width() - self.height() + 3 if self.isChecked() else 3
        self.update()


class ProfileBarWidget(QWidget):
    clicked = pyqtSignal()

    def __init__(self, user_name, pic_path, bg_mode, bg_config, accent_color, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(50)
        self.setToolTip("Open Profile Settings")

        self._bg_mode = bg_mode
        self._bg_image_path = bg_config.get('image')
        self._bg_color = QColor(bg_config.get('color', '#555555'))
        self._accent_color = QColor(accent_color)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 15, 5)
        layout.setSpacing(10)

        self.pic_label = QLabel()
        self.pic_label.setStyleSheet("background: transparent;")
        self.pic_label.setFixedSize(40, 40)
        
        if pic_path and os.path.exists(pic_path):
            source_image = QImage(pic_path)
        else:
            # Use default profile image
            default_pic = os.path.join(os.path.dirname(__file__), "system_files", "profile_default", "bento_station-san.png")
            source_image = QImage(default_pic)
            
        if not source_image.isNull():
            circular_pixmap = create_circular_pixmap(source_image, 40)
            self.pic_label.setPixmap(circular_pixmap)

        self.name_label = QLabel(user_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: white; background: transparent;")

        layout.addWidget(self.pic_label)
        layout.addWidget(self.name_label)
        layout.addStretch()

    def paintEvent(self, event):
        painter = QPainter()
        if not painter.begin(self):
            return

        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            path = QPainterPath()
            rect = self.rect().adjusted(0, 0, -1, -1)
            rect_f = QRectF(rect)
            path.addRoundedRect(rect_f, 24, 24)

            paint_color = self._accent_color
            if self._bg_mode == 'custom':
                paint_color = self._bg_color
            elif self._bg_mode == 'image':
                paint_color = QColor("#333333") 
            
            painter.fillPath(path, paint_color)

            if self._bg_mode == 'image':
                bg_image_path = self._bg_image_path
                if not bg_image_path or not os.path.exists(bg_image_path):
                    # Use default background image
                    bg_image_path = os.path.join(os.path.dirname(__file__), "system_files", "profile_default", "bento_station-bg.png")
                
                if os.path.exists(bg_image_path):
                    image = QImage(bg_image_path)
                    if not image.isNull():
                        source_pixmap = QPixmap.fromImage(image)
                        scaled_pixmap = source_pixmap.scaled(
                            self.size(), 
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                            Qt.TransformationMode.SmoothTransformation
                        )
                        x_pos = (self.width() - scaled_pixmap.width()) / 2
                        y_pos = (self.height() - scaled_pixmap.height()) / 2
                        painter.setClipPath(path)
                        painter.drawPixmap(int(x_pos), int(y_pos), scaled_pixmap)
                        overlay_color = QColor(0, 0, 0, 100)
                        painter.fillRect(self.rect(), overlay_color)
        finally:
            painter.end()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class SidebarToggleButton(QWidget):
    page_selected = pyqtSignal(str)

    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.items = items
        self.title = title
        self.is_open = False
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.toggle_button = QPushButton(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setObjectName("mainItemButton")
        self.toggle_button.clicked.connect(self._toggle_content)
        main_layout.addWidget(self.toggle_button)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 5, 0, 5)
        self.content_layout.setSpacing(4)
        
        self.sub_button_group = QButtonGroup()
        self.sub_button_group.setExclusive(True)

        self.sub_buttons = {}
        for item in items:
            button = QPushButton(item)
            button.setCheckable(True)
            button.setObjectName("subItemButton")
            button.clicked.connect(lambda _, name=item: self.page_selected.emit(name))
            self.sub_buttons[item] = button
            self.content_layout.addWidget(button)
            self.sub_button_group.addButton(button)

        main_layout.addWidget(self.content_widget)
        self.content_widget.hide()

    def _toggle_content(self, checked):
        self.is_open = checked
        self.content_widget.setVisible(checked)
        if not checked:
            if btn := self.sub_button_group.checkedButton():
                btn.blockSignals(True)
                btn.setChecked(False)
                btn.blockSignals(False)
                self.page_selected.emit("")

    def select_page(self, page_name):
        if page_name in self.sub_buttons:
            if not self.is_open:
                self.toggle_button.click()
            self.sub_buttons[page_name].setChecked(True)
            return True
        return False

    def deselect_all(self):
        self.toggle_button.setChecked(False)
        self.is_open = False
        self.content_widget.hide()
        if btn := self.sub_button_group.checkedButton():
             btn.blockSignals(True)
             btn.setChecked(False)
             btn.blockSignals(False)


class SectionGroup(QWidget):
    def __init__(self, title="", parent=None, border=True, description=""):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(0, 5, 0, 0)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 20px; margin-bottom: 5px;")
        main_layout.addWidget(title_label)

        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("font-size: 11px; color: #888; margin-bottom: 5px;")
            desc_label.setWordWrap(True)
            main_layout.addWidget(desc_label)

        self.content_area = QWidget()
        if border:
            self.content_area.setObjectName("innerGroup")
        
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout.setSpacing(10)
        main_layout.addWidget(self.content_area)

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)


class ColorSwatch(QWidget):
    """A simple widget to display a circle of a solid color."""
    def __init__(self, color_hex, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.color = QColor(color_hex)
        self.setToolTip(color_hex.upper())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())


class BirthdayWidget(QWidget):
    def __init__(self, accent_color="#007bff", parent=None):
        super().__init__(parent)
        
        # Resolve real accent color from theme to match accurately
        current_theme = mw.col.conf.get("modern_menu_theme", "Tokyo Drift")
        if current_theme in THEMES:
            mode = "dark" if theme_manager.night_mode else "light"
            accent_color = THEMES[current_theme][mode].get("--accent-color", accent_color)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        self.accent_color = accent_color

        # Common style for input fields
        if theme_manager.night_mode:
            bg_color = "#3a3a3a"
            text_color = "#e0e0e0"
            border_color = "#555"
            hover_border_color = "#777"
        else:
            bg_color = "white"
            text_color = "#333"
            border_color = "#e0e0e0"
            hover_border_color = "#b0b0b0"

        input_style = f"""
            QLineEdit {{
                padding: 7px 11px;
                border: 2px solid {border_color};
                border-radius: 8px;
                background-color: {bg_color};
                color: {text_color};
                font-size: 13px;
                selection-background-color: {accent_color};
                outline: none;
            }}
            QLineEdit:hover {{
                border-color: {hover_border_color};
            }}
            QLineEdit:focus {{
                border: 2px solid {accent_color};
                background-color: {bg_color};
            }}
        """

        # Day Input
        self.day_input = QLineEdit()
        self.day_input.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        self.day_input.setPlaceholderText("Day")
        self.day_input.setValidator(QIntValidator(1, 31))
        self.day_input.setFixedWidth(70)
        self.day_input.setStyleSheet(input_style)
        self.day_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Month Input
        self.month_input = QLineEdit()
        self.month_input.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        self.month_input.setPlaceholderText("Month")
        self.month_input.setValidator(QIntValidator(1, 12))
        self.month_input.setFixedWidth(70)
        self.month_input.setStyleSheet(input_style)
        self.month_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Year Input
        self.year_input = QLineEdit()
        self.year_input.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        self.year_input.setPlaceholderText("Year")
        self.year_input.setValidator(QIntValidator(1900, 2100))
        self.year_input.setFixedWidth(80)
        self.year_input.setStyleSheet(input_style)
        self.year_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.day_input)
        layout.addWidget(self.month_input)
        layout.addWidget(self.year_input)
        layout.addStretch()

    def setDate(self, date):
        if not date.isValid():
            return
        
        # Set Day
        self.day_input.setText(str(date.day()))
        
        # Set Month
        self.month_input.setText(str(date.month()))
        
        # Set Year
        self.year_input.setText(str(date.year()))

    def date(self):
        try:
            if not self.day_input.text() or not self.month_input.text() or not self.year_input.text():
                return QDate()
            
            day = int(self.day_input.text())
            month = int(self.month_input.text())
            year = int(self.year_input.text())
            
            return QDate(year, month, day)
        except:
            return QDate()


class FontCardWidget(QPushButton):
    """A custom button widget to display and select a font."""
    # <<< START NEW CODE >>>
    delete_requested = pyqtSignal(str) # Signal with font_key (filename)
    # <<< END NEW CODE >>>

    def __init__(self, font_key, accent_color, parent=None, is_system_card=False, delete_icon=None):
        super().__init__(parent)
        self.font_key = font_key
        all_fonts = get_all_fonts(os.path.dirname(__file__))
        font_info = all_fonts.get(font_key)
        
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if is_system_card:
            self.setFixedHeight(50)
            layout = QHBoxLayout(self) # Horizontal layout
            layout.setContentsMargins(15, 10, 15, 10)
            
            name_label = QLabel(font_info["name"])
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(name_label)
        else:
            self.setFixedSize(140, 80)
            layout = QVBoxLayout(self) # Vertical layout
            layout.setContentsMargins(10, 10, 10, 10)

            aa_label = QLabel("Aa")
            aa_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            name_label = QLabel(font_info["name"])
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            layout.addWidget(aa_label, 1)
            layout.addWidget(name_label, 0)
        
        if font_info and font_info.get("file"):
            addon_path = os.path.dirname(__file__)
            # Correctly handles user-uploaded fonts
            if font_info.get("user"):
                font_path = os.path.join(addon_path, "user_files", "fonts", font_info["file"])
            # Correctly handles the built-in system fonts
            else:
                # FIX: Corrected the path to the system_fonts subfolder
                font_path = os.path.join(addon_path, "system_files", "fonts", "system_fonts", font_info["file"])

            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        font_size = 14 if is_system_card else 12
                        name_label.setFont(QFont(font_families[0], font_size))
                        if not is_system_card:
                            aa_label.setFont(QFont(font_families[0], 20))

        self.delete_button = None
        if font_info.get("user"):
            self.delete_button = QPushButton(self)
            self.delete_button.setFixedSize(22, 22)
            if delete_icon:
                self.delete_button.setIcon(delete_icon)
                self.delete_button.setIconSize(QSize(14, 14))
            else:
                self.delete_button.setText("✕")
            self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.delete_button.setToolTip("Delete this font")
            self.delete_button.clicked.connect(self._on_delete_clicked)
            self.delete_button.setStyleSheet(f"""
                QPushButton {{
                    font-size: 14px;
                    font-weight: bold;
                    color: hsl(0, 0, 63, 0.5);
                    background: transparent; 
                    border: none;
                    border-radius: 11px;
                }}
                QPushButton:hover {{ 
                    background: transparent; 
                    color: hsl(0, 0, 63);
                }}
            """)

        if theme_manager.night_mode:
            self.setStyleSheet(f"""
                QPushButton {{ background-color: #3a3a3a; border: 2px solid #4a4a4a; border-radius: 12px; color: #e0e0e0; }}
                QPushButton:hover {{ border-color: #5a5a5a; }}
                QPushButton:checked {{ border-color: {accent_color}; }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{ background-color: #e9e9e9; border: 2px solid #e0e0e0; border-radius: 12px; color: #212121; }}
                QPushButton:hover {{ border-color: #d0d0d0; }}
                QPushButton:checked {{ border-color: {accent_color}; }}
            """)
    
    # <<< START NEW CODE >>>
    def _on_delete_clicked(self):
        self.delete_requested.emit(self.font_key)

    def resizeEvent(self, event):
        """Ensure the delete button stays in the top-right corner."""
        super().resizeEvent(event)
        if self.delete_button:
            self.delete_button.move(self.width() - self.delete_button.width() - 5, 5)


class SearchResultWidget(QPushButton):
    def __init__(self, title, subtitle, target_page, parent=None):
        super().__init__(parent)
        self.target_page = target_page
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(70)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(4)
        
        # Determine colors based on theme
        if theme_manager.night_mode:
            bg_color = "#3a3a3a"
            text_color = "#e0e0e0"
            sub_text_color = "#aaaaaa"
            hover_bg = "#4a4a4a"
            border_color = "#3a3a3a"
        else:
            bg_color = "#dddddd"
            text_color = "#212121"
            sub_text_color = "#555555"
            hover_bg = "#e0e0e0"
            border_color = "#dddddd"

        # Resolve real accent color from theme
        current_theme = mw.col.conf.get("modern_menu_theme", "Tokyo Drift")
        accent_color = "#007bff"
        if current_theme in THEMES:
            mode = "dark" if theme_manager.night_mode else "light"
            accent_color = THEMES[current_theme][mode].get("--accent-color", accent_color)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {text_color}; background: transparent;")
        layout.addWidget(title_label)
        
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet(f"font-size: 12px; color: {sub_text_color}; background: transparent;")
            layout.addWidget(sub_label)
            
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 2px solid {border_color};
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                border: 2px solid {accent_color};
            }}
        """)
