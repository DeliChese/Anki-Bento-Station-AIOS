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

class DonationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Support Onigiri")
        self.setFixedWidth(300)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Choose a donation platform:")
        title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # --- Theme Detection for Base Button Style ---
        is_dark = theme_manager.night_mode
        
        if is_dark:
            btn_bg = "#3a3a3a"
            btn_text = "white"
            btn_border = "#555"
        else:
            btn_bg = "#f0f0f0"
            btn_text = "black"
            btn_border = "#ccc"

        base_style = f"""
            QPushButton {{
                padding: 12px;
                border-radius: 20px;
                background-color: {btn_bg};
                color: {btn_text};
                border: 1px solid {btn_border};
                font-weight: bold;
                font-size: 13px;
            }}
        """

        # BMC Button
        self.bmc_button = QPushButton("Buy Me A Coffee")
        self.bmc_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bmc_button.setStyleSheet(base_style + """
            QPushButton:hover {
                background-color: #FFDD04;
                border: 1px solid #FFDD04;
                color: black;
            }
        """)
        self.bmc_button.clicked.connect(lambda: self._open_url("https://buymeacoffee.com/peacemonk"))
        layout.addWidget(self.bmc_button)

        # Ko-Fi Button
        self.kofi_button = QPushButton("Ko-Fi")
        self.kofi_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.kofi_button.setStyleSheet(base_style + """
            QPushButton:hover {
                background-color: #FF5A16;
                border: 1px solid #FF5A16;
                color: white;
            }
        """)
        self.kofi_button.clicked.connect(lambda: self._open_url("https://ko-fi.com/peacemonk"))
        layout.addWidget(self.kofi_button)

    def _open_url(self, url):
        QDesktopServices.openUrl(QUrl(url))
        self.accept()
