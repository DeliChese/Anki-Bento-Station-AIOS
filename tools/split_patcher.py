"""
Hiện đại hóa P0 - A3: Tách cụm CSS khỏi patcher.py sang css_engine.py.

Cách hoạt động (an toàn):
  1. Đọc patcher.py, dùng `ast` lấy đúng (lineno..end_lineno) từng hàm CSS.
  2. Trích chính xác source của các hàm đó → ghi css_engine.py (kèm header import).
  3. Loại bỏ đúng các dòng đó khỏi patcher.py, chèn khối re-export.
  4. Ghi ra file tạm, py_compile, chỉ thay thế khi compile OK.

Chạy: python tools/split_patcher.py [--apply]
  - mặc định: dry-run, in kế hoạch + ghi css_engine.py (không đụng patcher.py)
  - --apply: thực hiện ghi đè patcher.py (sau khi compile tạm OK)
"""

import ast
import py_compile
import sys
import tempfile
import os

TARGET = "patcher.py"
CSS_ENGINE = "css_engine.py"

CSS_FUNCS = [
    "_render_background_css",
    "generate_profile_page_background_css",
    "generate_deck_browser_backgrounds",
    "generate_reviewer_background_css",
    "generate_overview_background_css",
    "generate_toolbar_background_css",
    "_generate_outer_background_css",
    "generate_reviewer_bottom_bar_background_css",
    "generate_profile_bar_fix_css",
    "generate_icon_size_css",
    "generate_icon_css",
    "generate_conditional_css",
    "generate_font_css",
    "_hex_to_rgba",
    "_mix_colors",
    "generate_dynamic_css",
    "generate_reviewer_buttons_css",
]

HEADER = '''"""
Hiện đại hóa P0 - A3: css_engine.py
Các hàm sinh CSS được tách nguyên vẹn từ patcher.py (giữ nguyên hành vi).
patcher.py re-export các tên này để mọi `from . import patcher` cũ không vỡ.
"""
import os
import re
import json
import html
import base64
import time
import math
from aqt import mw
from . import config
from . import fonts
from . import icon_registry
from .constants import COLOR_LABELS
from .fonts import get_all_fonts


'''

REEXPORT = '''# --- Re-export từ css_engine (Hiện đại hóa P0-A3) ---
# Giữ các tên CSS trong namespace patcher để mọi `patcher.X` cũ vẫn hoạt động.
from .css_engine import (
    _render_background_css,
    generate_profile_page_background_css,
    generate_deck_browser_backgrounds,
    generate_reviewer_background_css,
    generate_overview_background_css,
    generate_toolbar_background_css,
    _generate_outer_background_css,
    generate_reviewer_bottom_bar_background_css,
    generate_profile_bar_fix_css,
    generate_icon_size_css,
    generate_icon_css,
    generate_conditional_css,
    generate_font_css,
    _hex_to_rgba,
    _mix_colors,
    generate_dynamic_css,
    generate_reviewer_buttons_css,
)


'''


def extract_ranges(src, lines):
    tree = ast.parse(src)
    ranges = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in CSS_FUNCS:
            ranges[node.name] = (node.lineno, node.end_lineno)
    missing = [n for n in CSS_FUNCS if n not in ranges]
    return ranges, missing


def build_css_engine(lines, ranges):
    parts = []
    for name in CSS_FUNCS:
        s, e = ranges[name]
        end = e
        while end < len(lines) and lines[end].strip() == "":
            end += 1
        parts.append("".join(lines[s - 1:end]))
    return HEADER + "\n\n".join(parts)


def build_new_patcher(lines, ranges):
    drop = set()
    for s, e in ranges.values():
        end = e
        while end < len(lines) and lines[end].strip() == "":
            end += 1
        drop.update(range(s - 1, end))
    new_lines = [l for i, l in enumerate(lines) if i not in drop]

    # Tìm dòng đầu tiên bắt đầu 1 định nghĩa cấp cao (def/class) để chèn re-export trước nó
    insert_at = len(new_lines)
    for i, l in enumerate(new_lines):
        if l.startswith("def ") or l.startswith("class "):
            insert_at = i
            break
    new_lines[insert_at:insert_at] = [REEXPORT]
    return "".join(new_lines)


def main():
    apply = "--apply" in sys.argv
    with open(TARGET, encoding="utf-8") as f:
        src = f.read()
    lines = src.splitlines(keepends=True)

    ranges, missing = extract_ranges(src, lines)
    if missing:
        print("[ERR] không tìm thấy hàm:", missing)
        return 1

    css_engine_src = build_css_engine(lines, ranges)
    new_patcher_src = build_new_patcher(lines, ranges)

    with open(CSS_ENGINE, "w", encoding="utf-8") as f:
        f.write(css_engine_src)
    print(f"[OK] wrote {CSS_ENGINE} ({len(css_engine_src.splitlines())} lines)")

    # Verify compile của css_engine + patcher mới
    try:
        py_compile.compile(CSS_ENGINE, doraise=True)
        print(f"[OK] {CSS_ENGINE} compiles")
    except py_compile.PyCompileError as e:
        print(f"[ERR] {CSS_ENGINE} compile fail: {e}")
        return 1

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(new_patcher_src)
        tmp = tf.name
    try:
        py_compile.compile(tmp, doraise=True)
        print("[OK] patcher.py (new) compiles")
    except py_compile.PyCompileError as e:
        print(f"[ERR] patcher.py (new) compile fail: {e}")
        os.unlink(tmp)
        return 1

    if not apply:
        print("[DRY-RUN] patcher.py NOT overwritten - use --apply to apply.")
        os.unlink(tmp)
        return 0

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(new_patcher_src)
    os.unlink(tmp)
    print(f"[OK] overwrote {TARGET} ({len(new_patcher_src.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
