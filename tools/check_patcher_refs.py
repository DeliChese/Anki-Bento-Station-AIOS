"""
Kiểm tra chéo: mọi `patcher.<name>` được dùng trong codebase (ngoài patcher.py)
có tồn tại trong namespace patcher.py (def/class/assign/import/re-export) không.

Chạy: python tools/check_patcher_refs.py
"""

import ast
import sys

TARGET = "patcher.py"
# Các module có thể dùng `patcher.<name>` (đã xác định từ grep)
FILES = [
    "__init__.py", "bento_station_renderer.py", "settings/__init__.py", "settings/dialog.py",
    "settings/widgets.py", "settings/color_widgets.py", "settings/pickers.py",
    "settings/search.py", "settings/dialogs.py", "settings/pixmap_utils.py",
    "menu_buttons.py",
    "deck_tree_updater.py", "patching.py", "welcome_dialog.py",
    "birthday_dialog.py", "icon_chooser.py", "create_deck_dialog.py",
    "credits_dialog.py", "favorites_cleanup.py", "animated_mascot.py",
    "webview_handlers.py", "future_letter_dialog.py", "habit_engine.py",
    "heatmap.py", "toolbar_styling.py", "profile_page.py", "webview_router.py",
    "css_engine.py", "coloris_picker.py", "themes/definitions.py",
    "constants.py", "fonts.py", "templates.py", "deck_tree_updater.py",
]


def defined_names(src):
    tree = ast.parse(src)
    defined = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    defined.add(t.id)
        elif isinstance(node, ast.Import):
            for a in node.names:
                defined.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.name != "*":
                    defined.add(a.asname or a.name)
    return defined


def patcher_uses(src):
    tree = ast.parse(src)
    uses = set()
    for sub in ast.walk(tree):
        if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id == "patcher":
            uses.add(sub.attr)
    return uses


def main():
    with open(TARGET, encoding="utf-8") as f:
        patcher_src = f.read()
    defined = defined_names(patcher_src)

    all_uses = {}
    for path in FILES:
        try:
            with open(path, encoding="utf-8") as f:
                src = f.read()
            uses = patcher_uses(src)
        except (OSError, SyntaxError) as e:
            print(f"[skip] {path}: {e}")
            continue
        if uses:
            all_uses[path] = uses

    missing = {}
    for path, uses in all_uses.items():
        for name in sorted(uses):
            if name not in defined:
                missing.setdefault(path, []).append(name)

    for path in sorted(all_uses):
        print(f"[{len(all_uses[path])}] {path}: {sorted(all_uses[path])}")
    if missing:
        print("---")
        for path, names in sorted(missing.items()):
            print(f"[MISSING] {path}: {names}")
        print("RESULT: MISSING REFS - FIX NEEDED")
        return 1
    print("---")
    print("RESULT: ALL patcher.* REFERENCES RESOLVE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
