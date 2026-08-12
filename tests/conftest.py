"""Smoke-test harness cho Bento Station AIOS (root).

Cho phép import các module gốc của addon KHÔNG cần chạy Anki, để bắt lỗi
"import vỡ / thiếu re-export" ngay khi refactor (tách file theo SHIM).

Cơ chế:
1. Nếu môi trường không có `aqt`/`anki`/`PyQt6` thật → cài stub tối thiểu.
2. Mọi `aqt.X` / `anki.X` / `PyQt6.*` là module stub có `__getattr__` trả
   **dummy class** (metaclass) cho bất kỳ tên nào:
   - Dùng được làm base class (`class Foo(QDialog)`).
   - Call được (`QColor(255,0,0)` → dummy instance).
   - Truy cập enum lồng nhau (`Qt.AlignmentFlag.AlignCenter` → dummy).
3. Đăng ký thư mục addon thành package `bento_station` → relative import
   (`from . import config`) hoạt động.

Lưu ý: đây là smoke test import-only — KHÔNG đảm bảo hành vi Qt thật.
Module gắn sâu runtime Qt nên được verify thêm bằng Anki thật.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

ADDON_ROOT = pathlib.Path(__file__).resolve().parents[1]

# ── Tên Qt phổ biến (đủ cho `from aqt.qt import *` đi qua `__dir__`) ──────────
_QT_NAMES = [
    "QDialog", "QVBoxLayout", "QHBoxLayout", "QLabel", "QLineEdit", "QPushButton",
    "QDialogButtonBox", "QWidget", "QTabWidget", "QColorDialog", "QColor", "QCheckBox",
    "QGroupBox", "QRadioButton", "QFileDialog", "QSpinBox", "QPlainTextEdit",
    "QFormLayout", "QScrollArea", "QGridLayout", "QPixmap", "Qt", "QEvent", "QPainter",
    "QPainterPath", "QMessageBox", "QListWidget", "QStackedWidget", "QListWidgetItem",
    "QFrame", "QSizePolicy", "QComboBox", "QIcon", "QPen", "QBrush", "QInputDialog",
    "QAbstractButton", "QDoubleSpinBox", "QButtonGroup", "QAbstractSpinBox", "QDrag",
    "QMimeData", "QPoint", "QMenu", "QAction", "QActionGroup", "QAbstractItemView",
    "QDateEdit", "QLayout", "QRectF", "QImage", "QFont", "QFontDatabase", "QRect",
    "QSize", "QApplication", "QObject", "QThread", "pyqtSignal", "pyqtProperty",
    "QPointF", "QSignalBlocker", "QTimer", "QDate", "QLocale", "QSvgRenderer", "QUrl",
    "QPropertyAnimation", "QEasingCurve", "QRegularExpression", "QDesktopServices",
    "QLinearGradient", "QRegularExpressionValidator", "QMouseEvent", "QRegion",
    "QGuiApplication", "QCursor", "QIntValidator", "QStandardItemModel",
    "QStandardItem", "QHeaderView", "QTextEdit", "QToolButton", "QToolBar",
    "QMainWindow", "QShortcut", "QKeySequence", "QStatusBar", "QScrollBar",
    "QSlider", "QTabBar", "QStackedLayout", "QSplitter", "QProgressBar",
    "QListView", "QTableView", "QTreeView", "QTreeWidget", "QTreeWidgetItem",
    "QAbstractItemModel", "QItemSelectionModel", "QDir", "QFileInfo", "QFile",
    "QTextStream", "QByteArray", "QBuffer", "QVariant", "QModelIndex",
    "QPainterPathStroker", "QPolygonF", "QTransform", "QMatrix4x4", "QVector3D",
    "pyqtSlot", "pyqtBoundSignal", "QSignalMapper", "QGraphicsScene",
    "QGraphicsView", "QGraphicsItem", "QGraphicsPixmapItem", "QGraphicsDropShadowEffect",
    "QPropertyAnimation", "QSequentialAnimationGroup", "QParallelAnimationGroup",
    "QTimerEvent", "QCloseEvent", "QResizeEvent", "QKeyEvent", "QMouseEvent",
    "QDragEnterEvent", "QDragMoveEvent", "QDropEvent", "QFocusEvent", "QShowEvent",
    "QHideEvent", "QWheelEvent", "QContextMenuEvent", "QEnterEvent", "QLayoutItem",
    "QSpacerItem", "QMargins", "QFontMetrics", "QFontMetricsF", "QScreen", "QPalette",
]


class _DummyBase:
    """Instance dummy: mọi thuộc tính/call đều trả dummy khác."""

    def __getattr__(self, name: str):
        return _make_dummy(name)

    def __call__(self, *args, **kwargs):
        return self


class _DummyMeta(type):
    """Class dummy: truy cập thuộc tính trên CLASS (enum lồng nhau) trả dummy."""

    def __getattr__(cls, name: str):
        return _make_dummy(name)

    def __call__(cls, *args, **kwargs):
        # Mọi `Class(...)` (vd QColor("white") trong default arg, @pyqtSlot(result=str))
        # đều trả dummy instance — không bị lỗi "takes no arguments".
        return _DummyBase()


def _make_dummy(name: str):
    """Class giả có metaclass — subclass được, call được, enum lồng nhau OK."""
    return _DummyMeta(name, (_DummyBase,), {})


def _make_signal_factory(name: str):
    """Function giả cho pyqtSignal/pyqtSlot/pyqtProperty (call nhiều kiểu được)."""
    def _factory(*args, **kwargs):
        return _make_dummy(name)
    _factory.__name__ = name
    return _factory


def _module_getattr(name: str):
    if name.startswith("__"):
        raise AttributeError(name)  # để Python dùng mặc định (__all__, __path__...)
    if name.startswith("pyqt"):     # pyqtSignal/Slot/Property/BoundSignal
        return _make_signal_factory(name)
    return _make_dummy(name)


def _stub_module(fqname: str) -> types.ModuleType:
    if fqname in sys.modules:
        return sys.modules[fqname]
    pkg = types.ModuleType(fqname)
    pkg.__path__ = []
    pkg.__all__ = list(_QT_NAMES)  # cơ chế `from aqt.qt import *` dùng __all__ (đáng tin hơn __dir__)
    pkg.__getattr__ = _module_getattr
    sys.modules[fqname] = pkg
    return pkg


_AQT_SUBMODULES = [
    "qt", "theme", "utils", "deckbrowser", "overview", "reviewer", "webview",
    "main", "toolbar", "profiles", "editor", "browser", "addcards", "importing",
    "gui_hooks", "preferences", "mediasrv",
]
_ANKI_SUBMODULES = [
    "hooks", "decks", "utils", "collection", "models", "notes", "cards", "sound",
    "stats", "consts", "lang", "version", "find", "template", "rsbackend",
    "importing", "hooks_gen",
]
_PYQT6_SUBMODULES = [
    "QtCore", "QtGui", "QtWidgets", "QtSvg", "QtNetwork", "QtMultimedia",
    "QtWebEngineCore", "QtWebEngineWidgets", "QtWebChannel", "QtOpenGL",
    "QtPrintSupport", "QtXml", "QtSql", "QtTest", "QtQuick", "QtQml",
    "QtMultimediaWidgets", "QtWebSockets", "QtSvgWidgets", "QtCharts",
    "QtPdf", "QtPdfWidgets", "QtDesigner", "QtHelp", "QtLocation",
    "QtPositioning", "QtBluetooth", "QtNfc", "QtSerialPort", "QtSerialBus",
]


class _FakePm:
    name = "default"

    def __getattr__(self, n):
        return None


class _FakeCol:
    def __init__(self):
        self.conf = {}

    def __getattr__(self, n):
        return None


class _FakeAddonManager:
    def getConfig(self, *a, **k):
        return None

    def addonFromModule(self, *a, **k):
        return "Bento Station AIOS"

    def setWebExports(self, *a, **k):
        return None

    def __getattr__(self, n):
        return None


class _FakeMw:
    """mw giả: col.conf là dict THẬT → config.get_config() trả DEFAULTS (dict)."""

    def __init__(self):
        self.col = _FakeCol()
        self.pm = _FakePm()
        self.addonManager = _FakeAddonManager()

    def reset(self):
        return None

    def __getattr__(self, n):
        return None

    def __call__(self, *a, **k):
        return self


def _install_stubs() -> None:
    if importlib.util.find_spec("aqt") is None:
        aqt = _stub_module("aqt")
        aqt.mw = _FakeMw()
        aqt.gui_hooks = _make_dummy("gui_hooks")
        for sub in _AQT_SUBMODULES:
            _stub_module(f"aqt.{sub}")
    if importlib.util.find_spec("anki") is None:
        anki = _stub_module("anki")
        for sub in _ANKI_SUBMODULES:
            _stub_module(f"anki.{sub}")
    if importlib.util.find_spec("PyQt6") is None:
        _stub_module("PyQt6")
        for sub in _PYQT6_SUBMODULES:
            _stub_module(f"PyQt6.{sub}")


def _install_addon_package() -> None:
    if "bento_station" in sys.modules:
        return
    pkg = types.ModuleType("bento_station")
    pkg.__path__ = [str(ADDON_ROOT)]
    sys.modules["bento_station"] = pkg
    if str(ADDON_ROOT) not in sys.path:
        sys.path.insert(0, str(ADDON_ROOT))


def pytest_configure() -> None:
    _install_stubs()
    _install_addon_package()
