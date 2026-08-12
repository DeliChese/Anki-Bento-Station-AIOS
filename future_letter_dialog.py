"""
GĐ4: Future Self Letter — nhắn tin tương lai gắn với milestone (self-continuity).

Cơ chế:
  - Ở mốc học đạt được (streak 30/90/180, tổng thẻ 1000/5000...), nhắc người dùng
    viết một lá thư ngắn cho "bạn của tương lai".
  - Lá thư được giao lại đúng mốc kế tiếp khi người dùng đạt được nó.

Lưu trữ: mw.col.conf["onigiri_letters"] = {
    "letters": { "<milestone_key>": {"text": str, "written_at": iso, "deliver_at": "<next_key>"} },
    "delivered": ["<milestone_key>", ...],     # mốc đã giao thư
    "acknowledged": ["<milestone_key>", ...],  # mốc đã xử lý nhắc viết thư
    "last_check_day": "YYYY-MM-DD"
}
"""

from datetime import datetime
from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QDialogButtonBox, QScrollArea, QWidget, Qt,
)
from . import config


# ── Trạng thái ─────────────────────────────────────────────────────────
def _get_state():
    if not mw.col:
        return {}
    return dict(mw.col.conf.get("onigiri_letters", {}))

def _save_state(state):
    if mw.col:
        mw.col.conf["onigiri_letters"] = state
        mw.col.setMod()

def _today_key():
    from . import habit_engine
    return habit_engine.get_today_date_key()

def _get_milestones():
    conf = config.get_config()
    return conf.get("futureLetterMilestones", [])

def _label_for_key(key):
    for m in _get_milestones():
        if m.get("key") == key:
            return m.get("label", key)
    return key


# ── Tiến trình ─────────────────────────────────────────────────────────
def _get_milestone_progress():
    """Trả về (streak, total_cards) hiện tại."""
    streak = 0
    total_cards = 0
    try:
        from . import heatmap
        streak = heatmap.get_heatmap_data().get("streak", 0) or 0
    except Exception:
        pass
    try:
        if mw.col:
            total_cards = mw.col.db.scalar("SELECT COUNT() FROM cards WHERE queue != -1") or 0
    except Exception:
        pass
    return streak, total_cards

def _reached_keys(streak, total_cards):
    keys = []
    for m in _get_milestones():
        mtype = m.get("type")
        value = int(m.get("value", 0))
        if mtype == "streak" and streak >= value:
            keys.append(m["key"])
        elif mtype == "total_cards" and total_cards >= value:
            keys.append(m["key"])
    return keys

def _next_milestone_after(key):
    milestones = _get_milestones()
    keys = [m["key"] for m in milestones]
    if key in keys and keys.index(key) + 1 < len(keys):
        return keys[keys.index(key) + 1]
    return None


# ── Dialog giao thư ────────────────────────────────────────────────────
class DeliveryDialog(QDialog):
    """Hiện lá thư người dùng đã viết ở mốc trước."""

    def __init__(self, letter, milestone_key, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💌 A letter from your past self")
        self.setMinimumSize(480, 360)
        self.setModal(True)

        vbox = QVBoxLayout(self)

        title = QLabel(f"✨ You reached: {_label_for_key(milestone_key)}")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        vbox.addWidget(title)

        subtitle = QLabel("Your past self left this for you:")
        subtitle.setStyleSheet("color: #6b6b6b; font-size: 12px;")
        vbox.addWidget(subtitle)

        body = QLabel(letter.get("text", "") or "(empty letter)")
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        body.setStyleSheet(
            "background: #2d2d3a; color: #e6e6e6; border-radius: 10px;"
            "padding: 14px; font-size: 14px; line-height: 1.6;"
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(body)
        scroll.setWidget(wrapper)
        vbox.addWidget(scroll, 1)

        if letter.get("written_at"):
            date_label = QLabel(f"Written {letter['written_at'][:10]}")
            date_label.setStyleSheet("color: #888; font-size: 11px;")
            vbox.addWidget(date_label)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Got it")
        button_box.accepted.connect(self.accept)
        vbox.addWidget(button_box)


# ── Dialog viết thư ────────────────────────────────────────────────────
class WriteDialog(QDialog):
    """Viết thư cho bạn của tương lai ở mốc kế tiếp."""

    def __init__(self, milestone_key, deliver_at, parent=None):
        super().__init__(parent)
        self.milestone_key = milestone_key
        self.deliver_at = deliver_at
        self.setWindowTitle("📮 Write to your future self")
        self.setMinimumSize(480, 380)
        self.setModal(True)

        vbox = QVBoxLayout(self)

        title = QLabel(f"🎉 Milestone reached: {_label_for_key(milestone_key)}")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        vbox.addWidget(title)

        hint = QLabel(
            "Write a short note to your future self. "
            "It will be delivered when you reach the next milestone."
            if deliver_at else
            "Write a short note to your future self. It will be saved as a memory."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #6b6b6b; font-size: 12px;")
        vbox.addWidget(hint)

        if deliver_at:
            deliver_label = QLabel(f"Will be delivered at: {_label_for_key(deliver_at)}")
            deliver_label.setStyleSheet("color: #c77dff; font-size: 12px; font-weight: 600;")
            vbox.addWidget(deliver_label)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Dear future me...")
        self.editor.setStyleSheet(
            "background: #2d2d3a; color: #e6e6e6; border: 1px solid #444;"
            "border-radius: 10px; padding: 10px; font-size: 14px;"
        )
        vbox.addWidget(self.editor, 1)

        btn_row = QHBoxLayout()
        skip_btn = QPushButton("Not now")
        skip_btn.clicked.connect(self.reject)
        btn_row.addWidget(skip_btn)
        btn_row.addStretch()
        save_btn = QPushButton("Save letter")
        save_btn.setStyleSheet(
            "background: #c77dff; color: #1a1a2e; font-weight: 700;"
            "border: none; border-radius: 10px; padding: 8px 16px;"
        )
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        vbox.addLayout(btn_row)

    def _on_save(self):
        text = self.editor.toPlainText().strip()
        state = _get_state()
        letters = state.setdefault("letters", {})
        letters[self.milestone_key] = {
            "text": text,
            "written_at": datetime.now().isoformat(timespec="seconds"),
            "deliver_at": self.deliver_at,
        }
        _save_state(state)
        self.accept()


# ── Entry points ───────────────────────────────────────────────────────
def show_delivery_dialog(letter, milestone_key):
    if not mw:
        return
    dlg = DeliveryDialog(letter, milestone_key, mw)
    dlg.exec()

def show_write_dialog(milestone_key, deliver_at):
    if not mw:
        return
    dlg = WriteDialog(milestone_key, deliver_at, mw)
    dlg.exec()

def maybe_check_milestones():
    """
    GĐ4-3: Chạy khi mở profile (gọi từ __init__.on_profile_did_open).
    Chỉ xử lý 1 lần/ngày. Ưu tiên giao thư cũ trước, sau đó nhắc viết thư mới.
    """
    conf = config.get_config()
    if not conf.get("futureLetterEnabled", True):
        return
    if not mw.col:
        return

    state = _get_state()
    today = _today_key()
    if state.get("last_check_day") == today:
        return
    state["last_check_day"] = today

    streak, total_cards = _get_milestone_progress()
    reached = _reached_keys(streak, total_cards)
    if not reached:
        _save_state(state)
        return

    letters = state.setdefault("letters", {})
    delivered = set(state.get("delivered", []))

    # 1) Giao thư cũ: mốc đang đạt có thư (deliver_at == key) chưa giao
    for key in reached:
        for letter_key, letter in list(letters.items()):
            if letter.get("deliver_at") == key and key not in delivered:
                delivered.add(key)
                state["delivered"] = sorted(delivered)
                _save_state(state)
                show_delivery_dialog(letter, key)
                return

    # 2) Nhắc viết thư cho mốc vừa đạt chưa viết/chưa xử lý
    acknowledged = set(state.get("acknowledged", []))
    for key in reached:
        if key not in acknowledged and key not in letters:
            acknowledged.add(key)
            state["acknowledged"] = sorted(acknowledged)
            _save_state(state)
            show_write_dialog(key, _next_milestone_after(key))
            return

    _save_state(state)
