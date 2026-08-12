"""
Hiện đại hóa P0 - A3: tách toolbar_styling / profile_page / webview_router khỏi patcher.py.

Chế độ: --apply để ghi đè patcher.py (sau khi compile OK); mặc định dry-run.
Xử lý: hàm/class (AST) + biến module-level (Assign) + alias.
"""

import ast
import os
import py_compile
import sys
import tempfile

TARGET = "patcher.py"

HEADER_TOOLBAR = '''"""
Hiện đại hóa P0 - A3: toolbar_styling.py
Menu styling, QMenu patch, sync status, toolbar visibility — tách từ patcher.py.
"""
import os
import re
import time
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.main import MainWebView
from . import config


'''

HEADER_PROFILE = '''"""
Hiện đại hóa P0 - A3: profile_page.py
Profile page (ProfileDialog + HTML helpers) — tách từ patcher.py.
"""
import os
import json
import html
import base64
import time
import math
from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView
from . import config
from . import settings
from . import heatmap
from .css_engine import (
    generate_dynamic_css,
    generate_profile_page_background_css,
    generate_deck_browser_backgrounds,
    generate_profile_bar_fix_css,
    generate_icon_css,
)
from .constants import COLOR_LABELS
from .fonts import get_all_fonts


'''

HEADER_ROUTER = '''"""
Hiện đại hóa P0 - A3: webview_router.py
Xử lý pycmd từ webview (on_webview_js_message) — tách từ patcher.py.
"""
import os
import json
import base64
import html
import time
from aqt import mw
from aqt.deckbrowser import DeckBrowser
from aqt.overview import Overview
from aqt.reviewer import Reviewer
from aqt.qt import *
from aqt.utils import tooltip
from . import config
from . import settings
from . import profile_page
from .profile_page import open_profile
from .toolbar_styling import get_sync_status


'''

REEXPORT = '''# --- Re-export từ toolbar_styling / profile_page / webview_router (P0-A3) ---
from .toolbar_styling import (
    apply_menu_styling,
    patch_qmenu,
    get_sync_status,
    _new_MainWebView_eventFilter,
    _update_toolbar_visibility,
    _on_sync_did_finish,
    _toolbar_patched,
    _original_MainWebView_eventFilter,
)
from .profile_page import (
    _get_profile_pic_html,
    _get_profile_pill_html,
    _get_theme_colors_html,
    _get_backgrounds_html,
    _get_heatmap_data_and_config_for_profile,
    _get_stats_html,
    _get_profile_header_html,
    _generate_profile_html_body,
    open_profile,
    show_profile_page,
    ProfileDialog,
    _profile_dialog,
    _profile_stats_cache,
)
from .webview_router import on_webview_js_message


'''

CLUSTERS = [
    {"module": "toolbar_styling.py", "header": HEADER_TOOLBAR,
     "members": [
         ("func", "apply_menu_styling"),
         ("func", "patch_qmenu"),
         ("assign", "_toolbar_patched"),
         ("assign", "_original_MainWebView_eventFilter"),
         ("func", "get_sync_status"),
         ("func", "_new_MainWebView_eventFilter"),
         ("func", "_update_toolbar_visibility"),
         ("func", "_on_sync_did_finish"),
     ]},
    {"module": "profile_page.py", "header": HEADER_PROFILE,
     "members": [
         ("func", "_get_profile_pic_html"),
         ("func", "_get_profile_pill_html"),
         ("func", "_get_theme_colors_html"),
         ("func", "_get_backgrounds_html"),
         ("func", "_get_heatmap_data_and_config_for_profile"),
         ("assign", "_profile_dialog"),
         ("assign", "_profile_stats_cache"),
         ("func", "_get_stats_html"),
         ("func", "_get_profile_header_html"),
         ("func", "_generate_profile_html_body"),
         ("class", "ProfileDialog"),
         ("func", "open_profile"),
         ("assign", "show_profile_page"),
     ]},
    {"module": "webview_router.py", "header": HEADER_ROUTER,
     "members": [("func", "on_webview_js_message")]},
]


def collect_ranges(tree):
    """(name, kind) -> (lineno, end_lineno) cho các node cấp cao trong tree.body."""
    ranges = {}
    for node in tree.body:
        kind = None
        name = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "func" if isinstance(node, ast.FunctionDef) else "class"
            name = node.name
            ranges[name] = (kind, node.lineno, node.end_lineno)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    ranges[t.id] = ("assign", node.lineno, node.end_lineno)
    return ranges


def build_module(lines, cluster, ranges):
    parts = [cluster["header"]]
    for kind, name in cluster["members"]:
        if name not in ranges:
            raise SystemExit(f"[ERR] {cluster['module']}: missing member {name}")
        k, s, e = ranges[name]
        end = e
        while end < len(lines) and lines[end].strip() == "":
            end += 1
        parts.append("".join(lines[s - 1:end]))
    return "".join(parts)


def build_new_patcher(lines, all_ranges):
    drop = set()
    for cluster in CLUSTERS:
        for kind, name in cluster["members"]:
            k, s, e = all_ranges[name]
            end = e
            while end < len(lines) and lines[end].strip() == "":
                end += 1
            drop.update(range(s - 1, end))
    new_lines = [l for i, l in enumerate(lines) if i not in drop]
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
    tree = ast.parse(src)
    ranges = collect_ranges(tree)

    # Xây các module
    for cluster in CLUSTERS:
        module_src = build_module(lines, cluster, ranges)
        if cluster["module"] == "webview_router.py":
            # `_profile_dialog` là mutable state của profile_page — phải truy cập qua
            # module attribute để không bị stale khi profile_page gán dialog mới.
            import re as _re
            module_src = _re.sub(r"(?<![.\w])_profile_dialog", "profile_page._profile_dialog", module_src)
        with open(cluster["module"], "w", encoding="utf-8") as f:
            f.write(module_src)
        try:
            py_compile.compile(cluster["module"], doraise=True)
            print(f"[OK] {cluster['module']} ({len(module_src.splitlines())} lines) compiles")
        except py_compile.PyCompileError as e:
            print(f"[ERR] {cluster['module']} compile fail: {e}")
            return 1

    new_patcher_src = build_new_patcher(lines, ranges)
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
        print("[DRY-RUN] patcher.py NOT overwritten - use --apply.")
        os.unlink(tmp)
        return 0

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(new_patcher_src)
    os.unlink(tmp)
    print(f"[OK] overwrote {TARGET} ({len(new_patcher_src.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
