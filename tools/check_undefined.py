"""
Công cụ kiểm tra tĩnh (Hiện đại hóa P0 - A3/A4).

Dùng `ast` để rà từng file .py, tìm các tên được DÙNG nhưng không được
ĐỊNH NGHĨA trong module (không phải local var/param/builtin/import).
Giúp phát hiện lỗi "gọi hàm chưa định nghĩa" khi tách module — chạy KHÔNG cần Anki.

Cách dùng:
    python tools/check_undefined.py [file1.py file2.py ...]   # mặc định: toàn bộ *.py
"""

import ast
import builtins
import os
import sys

# Tên Anki/aqt "quen thuộc" giảm nhiễu (coi như có sẵn trong môi trường runtime)
KNOWN_RUNTIME = {
    "mw", "gui_hooks", "tr", "isoDate", "anki", "aqt", "QDialog", "QVBoxLayout",
    "QHBoxLayout", "QLabel", "QLineEdit", "QPushButton", "QDialogButtonBox",
    "QCheckBox", "QWidget", "QTabWidget", "QColorDialog", "QColor", "QGroupBox",
    "QRadioButton", "QFileDialog", "QSpinBox", "QPlainTextEdit", "QFormLayout",
    "QScrollArea", "QGridLayout", "QPixmap", "Qt", "QEvent", "QPainter",
    "QPainterPath", "QMessageBox", "QMenu", "QFrame", "QTimer", "QToolBar",
    "QAction", "QAbstractButton", "QButtonGroup", "QLayout", "QSize", "QRect",
    "QLinearGradient", "QPushButton", "QDesktopServices", "QUrl", "QObject",
    "QAbstractButton", "QApplication", "QFont", "QFontMetrics", "QSvgRenderer",
    "pyqtSignal", "pyqtProperty", "CustomStudy", "Preferences", "readable", "time",
}


def get_builtins():
    return set(dir(builtins)) | KNOWN_RUNTIME | {
        "__file__", "__name__", "__path__", "__package__", "__doc__", "__all__",
    }


def collect_defined(node):
    """Trả về set tên được định nghĩa trong module (def/class/assign/import/param)."""
    defined = set()
    for sub in ast.walk(node):
        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(sub.name)
        elif isinstance(sub, ast.Name) and isinstance(sub.ctx, (ast.Store, ast.Del)):
            defined.add(sub.id)
        elif isinstance(sub, ast.arg):
            defined.add(sub.arg)
        elif isinstance(sub, ast.Import):
            for alias in sub.names:
                defined.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(sub, ast.ImportFrom):
            for alias in sub.names:
                # `from x import *` → không thể biết; coi như đã định nghĩa
                if alias.name != "*":
                    defined.add(alias.asname or alias.name)
        elif isinstance(sub, ast.ExceptHandler) and sub.name:
            defined.add(sub.name)
    return defined


def collect_used(node):
    """Trả về set tên được dùng trong ngữ cảnh Load."""
    used = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
            used.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            # Chỉ quan tâm phần gốc của chuỗi thuộc tính (vd patcher.foo → 'patcher')
            pass
    return used


def check_file(path):
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    defined = collect_defined(tree)
    used = collect_used(tree)
    built = get_builtins()

    # Các tên trong chain thuộc tính (a.b.c) — lấy phần gốc 'a'
    attr_roots = set()
    for sub in ast.walk(tree):
        if isinstance(sub, ast.Attribute):
            root = sub
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name):
                attr_roots.add(root.id)

    missing = set()
    for name in (used | attr_roots) - defined - built:
        # Lọc ra các tên module nội bộ (self.config, self.patcher...) đã có 'self'
        if name in {"self", "cls"}:
            continue
        missing.add(name)

    return sorted(missing)


def main():
    if len(sys.argv) > 1:
        files = [a for a in sys.argv[1:] if a.endswith(".py")]
    else:
        files = []
        for root, _, names in os.walk("."):
            if "system_files" in root or ".git" in root:
                continue
            for n in names:
                if n.endswith(".py"):
                    files.append(os.path.join(root, n))

    had_error = False
    for f in sorted(files):
        try:
            missing = check_file(f)
        except SyntaxError as e:
            print(f"[ERR] {f}: SyntaxError: {e}")
            had_error = True
            continue
        if missing:
            print(f"[WARN] {f}: undefined -> {', '.join(missing)}")
            had_error = True
        else:
            print(f"[OK] {f}")
    print("---")
    print("RESULT:", "HAS ISSUES" if had_error else "CLEAN (no missing names)")
    return 1 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
