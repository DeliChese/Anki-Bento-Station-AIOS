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

class FlashcardGalleryDialog(QDialog):
    """Duyệt thẻ trong bộ sưu tập + xem nhanh + ôn tập mini."""

    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("🗂️ Flashcard Gallery — Bento Station")
        self.resize(780, 560)
        cfg = get_tools_config()["gallery"]
        self._per_page = int(cfg.get("per_page") or 200)

        root = QVBoxLayout(self)
        root.setSpacing(8)

        # Thanh tìm kiếm
        bar = QHBoxLayout()
        self.search_input = QLineEdit(cfg.get("default_query") or "deck:*")
        self.search_input.setPlaceholderText("Truy vấn Anki (VD: deck:Tiếng Nhật tag:vocab)")
        self.search_input.returnPressed.connect(self._load)
        go = QPushButton("🔎 Lọc")
        go.clicked.connect(self._load)
        bar.addWidget(self.search_input, 1)
        bar.addWidget(go)
        root.addLayout(bar)

        # Bảng thẻ
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["#", "Deck", "Mặt trước", "Mặt sau"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.itemDoubleClicked.connect(lambda _i: self._start_review())
        root.addWidget(self.table)

        # Preview
        self.preview = QLabel("Chọn một thẻ để xem trước (hoặc bấm đúp để ôn tập).")
        self.preview.setWordWrap(True)
        self.preview.setMinimumHeight(90)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.preview.setStyleSheet("background:#f5f5f5;border-radius:8px;padding:8px;")
        root.addWidget(self.preview)

        # Nút
        btns = QHBoxLayout()
        review_btn = QPushButton("▶ Ôn tập nhanh")
        review_btn.clicked.connect(self._start_review)
        close_btn = QPushButton("Đóng")
        close_btn.clicked.connect(self.accept)
        btns.addWidget(review_btn)
        btns.addStretch()
        btns.addWidget(close_btn)
        root.addLayout(btns)

        self._notes = []
        self._load()

    def _load(self):
        query = self.search_input.text().strip() or "deck:*"
        try:
            if mw is None or mw.col is None:
                return
            note_ids = mw.col.find_notes(query)
            self._notes = note_ids[: self._per_page]
        except Exception as e:
            tooltip(f"Lỗi truy vấn: {e}")
            self._notes = []
        self._populate()

    def _populate(self):
        self.table.setRowCount(0)
        try:
            for i, nid in enumerate(self._notes):
                note = mw.col.get_note(nid)
                deck = mw.col.decks.name(note.note_type()["did"])
                fields = list(note.fields.values())
                front = fields[0] if fields else ""
                back = fields[1] if len(fields) > 1 else fields[0] if fields else ""
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(i + 1)))
                self.table.setItem(row, 1, QTableWidgetItem(deck))
                self.table.setItem(row, 2, QTableWidgetItem(self._clean(front)))
                self.table.setItem(row, 3, QTableWidgetItem(self._clean(back)))
        except Exception:
            pass

    @staticmethod
    def _clean(text: str) -> str:
        import re
        text = re.sub(r"<[^>]+>", " ", text or "")
        text = re.sub(r"\s+", " ", text).strip()
        return text[:80]

    def _on_select(self):
        idxs = self.table.selectionModel().selectedRows()
        if not idxs:
            return
        row = idxs[0].row()
        try:
            note = mw.col.get_note(self._notes[row])
            fields = list(note.fields.values())
            front = fields[0] if fields else ""
            back = fields[1] if len(fields) > 1 else ""
            self.preview.setText(
                f"<b>Mặt trước:</b> {front}<br><br><b>Mặt sau:</b> {back}"
            )
        except Exception:
            pass

    def _start_review(self):
        if not self._notes:
            tooltip("Không có thẻ nào để ôn tập.")
            return
        ReviewDeckDialog(self._notes, self).exec()


class ReviewDeckDialog(QDialog):
    """Ôn tập nhanh: hiện mặt trước → bấm lật → mặt sau → thẻ kế tiếp."""

    def __init__(self, note_ids, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("▶ Ôn tập nhanh — Flashcard Gallery")
        self.resize(600, 380)
        self._ids = list(note_ids)
        self._idx = 0
        self._flipped = False

        root = QVBoxLayout(self)
        self.card_label = QLabel("")
        self.card_label.setWordWrap(True)
        self.card_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_label.setStyleSheet(
            "font-size:22px;background:#fff;border:1px solid #ddd;border-radius:12px;padding:24px;"
        )
        root.addWidget(self.card_label, 1)

        self.count_label = QLabel("")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.count_label)

        btns = QHBoxLayout()
        flip_btn = QPushButton("🔄 Lật thẻ")
        flip_btn.clicked.connect(self._flip)
        next_btn = QPushButton("⏭ Thẻ tiếp theo")
        next_btn.clicked.connect(self._next)
        prev_btn = QPushButton("⏮ Thẻ trước")
        prev_btn.clicked.connect(self._prev)
        btns.addWidget(prev_btn)
        btns.addWidget(flip_btn)
        btns.addWidget(next_btn)
        root.addLayout(btns)

        self._show()

    def _current(self):
        try:
            note = mw.col.get_note(self._ids[self._idx])
            fields = list(note.fields.values())
            return (fields[0] if fields else "", fields[1] if len(fields) > 1 else (fields[0] if fields else ""))
        except Exception:
            return ("", "")

    def _show(self):
        front, back = self._current()
        text = back if self._flipped else front
        hint = " (mặt sau)" if self._flipped else " (mặt trước)"
        self.card_label.setText(f"{text}{hint}")
        self.count_label.setText(f"Thẻ {self._idx + 1} / {len(self._ids)}")

    def _flip(self):
        self._flipped = not self._flipped
        self._show()

    def _next(self):
        if self._ids:
            self._idx = (self._idx + 1) % len(self._ids)
        self._flipped = False
        self._show()

    def _prev(self):
        if self._ids:
            self._idx = (self._idx - 1) % len(self._ids)
        self._flipped = False
        self._show()


def open_flashcard_gallery(parent=None):
    if not (get_tools_config()["gallery"].get("enabled", True)):
        tooltip("Flashcard Gallery đang tắt (bật trong Bento Station Settings).")
        return
    FlashcardGalleryDialog(parent).exec()


def get_gallery_widget_html() -> str:
    """Widget HTML Flashcard Gallery trên Dashboard (click → mở duyệt/ôn thẻ)."""
    try:
        cfg = get_tools_config()
        if not (cfg.get("enabled") and cfg["gallery"].get("enabled", True)):
            return ""
        return """
        <div class="stat-card gallery-card" style="cursor:pointer" onclick="pycmd('openFlashcardGallery')">
            <h3>🗂️ Flashcard Gallery</h3>
            <p>Duyệt & ôn tập thẻ đã đúc</p>
            <p style="font-size:11px;opacity:.7">Bấm để mở</p>
        </div>
        """
    except Exception:
        return ""
