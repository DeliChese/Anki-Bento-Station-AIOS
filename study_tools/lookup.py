# Bento Station Study Tools (tách từ study_tools.py — Bước 4 refactor)
# Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.
import time
from aqt import mw
from aqt.qt import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFormLayout, QSpinBox, QCheckBox, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QTimer, QFrame,
    QSizePolicy, Qt,
)
from aqt.utils import tooltip

from .shared import get_tools_config

class QuickLookupDialog(QDialog):
    """Tra từ nhanh → tìm trong Anki / mở web / đúc thẻ Bento Forge 1 chạm."""

    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("🔍 Quick Lookup — Bento Station")
        self.setMinimumWidth(460)
        cfg = get_tools_config()["quick_lookup"]
        self._cfg = cfg

        root = QVBoxLayout(self)
        root.setSpacing(10)

        root.addWidget(QLabel("<h3>Tra từ nhanh</h3>"))

        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Nhập từ / cụm từ cần tra...")
        self.word_input.returnPressed.connect(self._on_lookup_web)
        root.addWidget(self.word_input)

        def _btn(text, slot):
            b = QPushButton(text)
            b.clicked.connect(slot)
            return b

        b1 = _btn("🌐 Tra cứu trên web (jisho/Google)", self._on_lookup_web)
        b2 = _btn("🔎 Tìm trong bộ sưu tập Anki", self._on_lookup_anki)
        b3 = _btn("🧪 Đúc thẻ nhanh bằng Bento Forge", self._on_forge)
        for b in (b1, b2, b3):
            root.addWidget(b)

        root.addWidget(self._make_separator())
        hint = QLabel(
            "💡 <b>Đúc thẻ nhanh:</b> mở Bento Forge, tự điền từ vào ô AI "
            "để trích xuất nghĩa + tạo thẻ ngay."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#777;font-size:11px;")
        root.addWidget(hint)

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#888;")
        return line

    def _word(self) -> str:
        return self.word_input.text().strip()

    def _on_lookup_web(self):
        word = self._word()
        if not word:
            tooltip("Nhập từ cần tra trước.")
            return
        url_tpl = self._cfg.get("dictionary_url") or "https://jisho.org/search/{word}"
        from aqt.qt import QDesktopServices, QUrl
        QDesktopServices.openUrl(QUrl(url_tpl.replace("{word}", word)))
        if self._cfg.get("open_browser_on_lookup", True):
            self.accept()

    def _on_lookup_anki(self):
        word = self._word()
        if not word:
            tooltip("Nhập từ cần tìm trước.")
            return
        try:
            if mw is not None and hasattr(mw, "onBrowse"):
                mw.onBrowse()
                self.accept()
        except Exception:
            pass

    def _on_forge(self):
        word = self._word()
        try:
            from . import bento_forge_bridge
            bento_forge_bridge.open_forge(mw)
            dlg = getattr(mw, "factory_dialog", None)
            if dlg is not None and hasattr(dlg, "ai_text_input"):
                if word:
                    dlg.ai_text_input.setPlainText(word)
                    if hasattr(dlg, "_analyze_content"):
                        dlg._analyze_content()
                dlg.raise_()
            self.accept()
        except Exception as e:
            tooltip(f"Không mở được Bento Forge: {e}")


def open_quick_lookup(parent=None):
    if not (get_tools_config()["quick_lookup"].get("enabled", True)):
        tooltip("Quick Lookup đang tắt (bật trong Bento Station Settings).")
        return
    QuickLookupDialog(parent).exec()


def get_lookup_widget_html() -> str:
    """Widget HTML Quick Lookup trên Dashboard (click → mở tra từ nhanh)."""
    try:
        cfg = get_tools_config()
        if not (cfg.get("enabled") and cfg["quick_lookup"].get("enabled", True)):
            return ""
        return """
        <div class="stat-card lookup-card" style="cursor:pointer" onclick="pycmd('openQuickLookup')">
            <h3>🔍 Quick Lookup</h3>
            <p>Tra từ nhanh → đúc thẻ Bento Forge</p>
            <p style="font-size:11px;opacity:.7">Bấm để mở</p>
        </div>
        """
    except Exception:
        return ""
