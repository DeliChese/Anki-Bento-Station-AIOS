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

from .shared import cards_reviewed_today, cards_reviewed_week, current_streak, get_tools_config, save_tools_config

class StudyPlannerDialog(QDialog):
    """Lịch/mục tiêu học hằng ngày + theo dõi tiến độ thực tế."""

    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("📅 Study Planner — Bento Station")
        self.setMinimumWidth(480)
        cfg = get_tools_config()["planner"]
        self._cfg = cfg

        root = QVBoxLayout(self)
        root.setSpacing(12)

        # ── Thẻ tổng quan ──
        today = cards_reviewed_today()
        week = cards_reviewed_week()
        streak = current_streak()
        daily_goal = int(cfg.get("daily_goal_cards") or 50)
        weekly_goal = int(cfg.get("weekly_goal_cards") or 350)

        summary = QLabel(
            f"<h3>Hôm nay: <b style='color:#27ae60'>{today}</b> / {daily_goal} thẻ</h3>"
            f"<p>Tuần này: <b>{week}</b> / {weekly_goal} thẻ · "
            f"Streak: <b>{streak} 🔥</b> ngày</p>"
        )
        summary.setWordWrap(True)
        root.addWidget(summary)

        # Thanh tiến độ hôm nay
        pct = min(100, int(today / daily_goal * 100)) if daily_goal else 0
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(pct)
        bar.setFormat(f"Tiến độ hôm nay: {pct}%")
        root.addWidget(bar)

        root.addWidget(self._make_separator())

        # ── Thiết lập mục tiêu ──
        form = QFormLayout()
        self.daily_spin = QSpinBox()
        self.daily_spin.setRange(1, 10000)
        self.daily_spin.setValue(daily_goal)
        self.daily_spin.setSuffix(" thẻ/ngày")
        form.addRow("Mục tiêu hằng ngày:", self.daily_spin)

        self.weekly_spin = QSpinBox()
        self.weekly_spin.setRange(1, 100000)
        self.weekly_spin.setValue(weekly_goal)
        self.weekly_spin.setSuffix(" thẻ/tuần")
        form.addRow("Mục tiêu hằng tuần:", self.weekly_spin)

        self.widget_cb = QCheckBox("Hiển thị widget Study Planner trên Dashboard")
        self.widget_cb.setChecked(bool(cfg.get("show_dashboard_widget", True)))
        form.addRow("Dashboard:", self.widget_cb)
        root.addLayout(form)

        # ── Nút ──
        btns = QHBoxLayout()
        save_btn = QPushButton("💾 Lưu mục tiêu")
        save_btn.clicked.connect(self._save)
        close_btn = QPushButton("Đóng")
        close_btn.clicked.connect(self.accept)
        btns.addWidget(save_btn)
        btns.addStretch()
        btns.addWidget(close_btn)
        root.addLayout(btns)

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#888;")
        return line

    def _save(self):
        cfg = get_tools_config()
        cfg["planner"]["daily_goal_cards"] = self.daily_spin.value()
        cfg["planner"]["weekly_goal_cards"] = self.weekly_spin.value()
        cfg["planner"]["show_dashboard_widget"] = self.widget_cb.isChecked()
        save_tools_config(cfg)
        tooltip("✅ Đã lưu mục tiêu Study Planner.")
        self.accept()


def open_study_planner(parent=None):
    if not (get_tools_config()["planner"].get("enabled", True)):
        tooltip("Study Planner đang tắt (bật trong Bento Station Settings).")
        return
    StudyPlannerDialog(parent).exec()


def get_planner_widget_html() -> str:
    """Widget HTML hiển thị trên Dashboard (click → mở Study Planner)."""
    try:
        cfg = get_tools_config()
        if not (cfg.get("enabled") and cfg["planner"].get("show_dashboard_widget", True)):
            return ""
        today = cards_reviewed_today()
        goal = int(cfg["planner"].get("daily_goal_cards") or 50)
        pct = min(100, int(today / goal * 100)) if goal else 0
        return f"""
        <div class="stat-card planner-card" style="cursor:pointer" onclick="pycmd('openStudyPlanner')">
            <h3>📅 Study Planner</h3>
            <p>{today} / {goal} thẻ hôm nay</p>
            <div style="background:#e0e0e0;border-radius:8px;height:10px;overflow:hidden;margin:4px 0;">
                <div style="width:{pct}%;height:100%;background:#27ae60;border-radius:8px;"></div>
            </div>
            <p style="font-size:11px;opacity:.7">Bấm để mở & chỉnh mục tiêu</p>
        </div>
        """
    except Exception:
        return ""
