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

class FocusTimerDialog(QDialog):
    """Đồng hồ tập trung Pomodoro (cấu hình sâu trong Settings)."""

    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("⏱️ Focus Timer — Bento Station")
        self.setMinimumWidth(360)
        # Non-modal + luôn nổi trên Anki → vừa đếm giờ vừa BẤM HỌC THẺ được bình thường
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowMinMaxButtonsHint
        )
        cfg = get_tools_config()["focus_timer"]
        self._work_min = int(cfg.get("work_min") or 25)
        self._break_min = int(cfg.get("break_min") or 5)
        self._long_break_min = int(cfg.get("long_break_min") or 15)
        self._sessions_before_long = int(cfg.get("sessions_before_long") or 4)
        self._auto_break = bool(cfg.get("auto_start_break", True))

        self._remaining = self._work_min * 60
        self._is_break = False
        self._sessions_done = 0
        self._running = False

        root = QVBoxLayout(self)
        root.setSpacing(10)

        self.mode_label = QLabel("🍅 Tập trung (Focus)")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.mode_label)

        self.time_label = QLabel("25:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-size:64px;font-weight:bold;")
        root.addWidget(self.time_label)

        self.session_label = QLabel(f"Phiên: {self._sessions_done}")
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.session_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, self._work_min * 60)
        self.progress.setValue(self._remaining)
        root.addWidget(self.progress)

        btns = QHBoxLayout()
        self.start_btn = QPushButton("▶ Bắt đầu")
        self.start_btn.clicked.connect(self._toggle)
        self.reset_btn = QPushButton("↺ Đặt lại")
        self.reset_btn.clicked.connect(self._reset)
        close_btn = QPushButton("Đóng")
        close_btn.clicked.connect(self.close)  # → closeEvent → ẩn, giữ trạng thái timer
        btns.addWidget(self.start_btn)
        btns.addWidget(self.reset_btn)
        btns.addWidget(close_btn)
        root.addLayout(btns)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

    def _fmt(self, s: int) -> str:
        return f"{s // 60:02d}:{s % 60:02d}"

    def _update_label(self):
        self.time_label.setText(self._fmt(self._remaining))
        self.progress.setValue(self._remaining)
        if self._is_break:
            self.mode_label.setText("☕ Nghỉ giải lao (Break)")
        else:
            self.mode_label.setText("🍅 Tập trung (Focus)")
        self.session_label.setText(f"Phiên: {self._sessions_done}")

    def _toggle(self):
        if self._running:
            self.timer.stop()
            self._running = False
            self.start_btn.setText("▶ Tiếp tục")
        else:
            self.timer.start()
            self._running = True
            self.start_btn.setText("⏸ Tạm dừng")

    def _tick(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self._phase_end()
        self._update_label()

    def _phase_end(self):
        self.timer.stop()
        self._running = False
        self.start_btn.setText("▶ Bắt đầu")
        if self._is_break:
            # Kết thúc break → quay lại focus
            self._is_break = False
            self._remaining = self._work_min * 60
            tooltip("✅ Nghỉ xong! Quay lại tập trung nhé.")
        else:
            self._sessions_done += 1
            if self._sessions_done % self._sessions_before_long == 0:
                self._is_break = True
                self._remaining = self._long_break_min * 60
                tooltip(f"🎉 Hoàn thành {self._sessions_done} phiên! Nghỉ dài {self._long_break_min} phút.")
            else:
                self._is_break = True
                self._remaining = self._break_min * 60
                tooltip(f"🍅 Xong 1 phiên! Nghỉ {self._break_min} phút.")
        self.progress.setRange(0, self._remaining)
        if self._auto_break and not self._is_break:
            pass
        self._update_label()

    def _reset(self):
        self.timer.stop()
        self._running = False
        self._is_break = False
        self._remaining = self._work_min * 60
        self.progress.setRange(0, self._remaining)
        self.start_btn.setText("▶ Bắt đầu")
        self._update_label()

    def closeEvent(self, event):
        """Đóng = ẩn cửa sổ, GIỮ NGUYÊN trạng thái timer (không mất khi mở lại)."""
        self.hide()
        event.ignore()

    def reload_config(self):
        """Nạp lại thời gian từ Settings — áp dụng khi timer đang RẢNH."""
        if self._running:
            return
        cfg = get_tools_config()["focus_timer"]
        self._work_min = int(cfg.get("work_min") or 25)
        self._break_min = int(cfg.get("break_min") or 5)
        self._long_break_min = int(cfg.get("long_break_min") or 15)
        self._sessions_before_long = int(cfg.get("sessions_before_long") or 4)
        self._auto_break = bool(cfg.get("auto_start_break", True))
        if not self._is_break:
            self._remaining = self._work_min * 60
            self.progress.setRange(0, self._remaining)
        self._update_label()


def open_focus_timer(parent=None):
    if not (get_tools_config()["focus_timer"].get("enabled", True)):
        tooltip("Focus Timer đang tắt (bật trong Bento Station Settings).")
        return
    # Một cửa sổ Pomodoro duy nhất, NON-MODAL → không chặn thao tác học thẻ,
    # đồng bộ trên cả Study page lẫn giao diện chính, giữ trạng thái khi đóng/mở lại.
    dlg = getattr(mw, "focus_timer_dialog", None)
    if dlg is None or not isinstance(dlg, FocusTimerDialog):
        dlg = FocusTimerDialog(mw)
        mw.focus_timer_dialog = dlg
    else:
        dlg.reload_config()  # cập nhật thời gian mới từ Settings khi rảnh
    if dlg.isMinimized():
        dlg.showNormal()
    dlg.show()
    dlg.raise_()
    dlg.activateWindow()


def get_timer_widget_html() -> str:
    """Widget HTML Focus Timer trên Dashboard (click → mở đồng hồ)."""
    try:
        cfg = get_tools_config()
        if not (cfg.get("enabled") and cfg["dashboard_widgets"].get("timer", True)):
            return ""
        work = int(cfg["focus_timer"].get("work_min") or 25)
        return f"""
        <div class="stat-card timer-card" style="cursor:pointer" onclick="pycmd('openFocusTimer')">
            <h3>⏱️ Focus Timer</h3>
            <p>🍅 Pomodoro {work} phút / phiên</p>
            <p style="font-size:11px;opacity:.7">Bấm để bắt đầu tập trung</p>
        </div>
        """
    except Exception:
        return ""
