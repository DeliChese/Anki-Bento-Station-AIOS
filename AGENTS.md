# AGENTS.md — Bento Station AIOS

> Điểm vào cho mọi AI agent. Đọc file này (~1k token) → chọn đúng mục → **chỉ đọc đúng file/dòng cần sửa**.
> Đừng đọc trọn file lớn (ví dụ `settings/dialog.py` = 9.3k dòng). Dùng `file:line` từ bảng bên dưới.

## QUY TRÌNH BẮT BUỘC (tiết kiệm token)

1. Xác định **nhiệm vụ thuộc module nào**: Bento Station (workspace này) hay Bento Forge (add-on riêng).
2. Tra bảng **Nhiệm vụ → File** bên dưới, đọc đúng file với `offset/limit` (dùng số dòng có sẵn).
3. Nếu sửa **Bento Forge**: đó là **add-on độc lập** nằm ngay trong `addons21/Bento Forge/` (ngoài workspace này) — đọc `addons21/Bento Forge/AGENTS.md` → hệ thống skill `.claude/`.
4. Sửa xong → kiểm tra tính nhất quán (Anki restart để verify UI).

## Nhiệm vụ → File

| Nhiệm vụ | File (dòng) |
|---|---|
| Entry point, đăng ký hooks, EXP, inject JS/CSS | [`__init__.py`](__init__.py:654) |
| Render Deck Browser (widget, EXP, sidebar) | [`bento_station_renderer.py`](bento_station_renderer.py) · [`widgets/`](widgets/) (widget generators) |
| Deck tree HTML (collapse, move, favorite) | [`deck_tree_updater.py`](deck_tree_updater.py) |
| Sinh CSS (nền, icon, reviewer buttons) | [`css/`](css/) · [`css_engine.py`](css_engine.py) (SHIM) |
| Config đọc/ghi (cache TTL 1s) | [`config.py`](config.py:454) · `invalidate_config_cache()` (`config.py:12`) |
| Settings UI (package `settings/`) | [`settings/dialog.py`](settings/dialog.py) · [`settings/widgets.py`](settings/widgets.py) · [`settings/pickers.py`](settings/pickers.py) |
| Toolbar/menu styling, sync status | [`toolbar_styling.py`](toolbar_styling.py) · [`menu_buttons.py`](menu_buttons.py) |
| Profile page dialog | [`profile_page.py`](profile_page.py) |
| Xử lý `pycmd` từ JS | [`webview_router.py`](webview_router.py) · [`webview_handlers.py`](webview_handlers.py) |
| Study tools (planner, lookup, gallery, timer) | [`study_tools/`](study_tools/) |
| Habit Engine (effort, streak, session) | [`habit_engine.py`](habit_engine.py) |
| Future Self Letter | [`future_letter_dialog.py`](future_letter_dialog.py) |
| Animated Mascot | [`animated_mascot.py`](animated_mascot.py) · [`web/animated_mascot.js`](web/animated_mascot.js) |
| Heatmap data | [`heatmap.py`](heatmap.py) · [`web/heatmap.js`](web/heatmap.js) |
| Theme presets | [`themes/`](themes/) |
| Icon library | [`icon_registry.py`](icon_registry.py) |
| HTML template deck browser | [`templates.py`](templates.py) |
| Cầu nối Bento Forge | [`bento_forge_bridge.py`](bento_forge_bridge.py) |
| Patch Anki API (version-guard) | [`patching.py`](patching.py) · [`patcher.py`](patcher.py) (SHIM) |
| Dialog phụ (welcome/birthday/icon/create/credits) | `welcome_dialog.py` · `birthday_dialog.py` · `icon_chooser.py` · `create_deck_dialog.py` · `credits_dialog.py` |

## Các Hook Chính (`__init__.py:654-674`)

| Hook | Handler |
|---|---|
| `main_window_did_init` | `setup_global_hooks()` |
| `profile_did_open` | `on_profile_did_open()` |
| `webview_will_set_content` | `inject_menu_files()` |
| `deck_browser_did_render` | `on_deck_browser_did_render()` |
| `webview_did_receive_js_message` | `patcher.on_webview_js_message` + `_on_webview_cmd` |
| `reviewer_did_answer_card` | `_on_reviewer_did_answer_card()` (EXP + habit) |
| `state_did_change` / `sync_*` / `operation_did_execute` | `on_state_change()` / `update_sync_status_indicator()` |
| `theme_did_change` | `patcher.apply_menu_styling()` |

## Luật Vàng

1. **Monkey-patch Anki** luôn qua `patching._safe_apply()` (hasattr + try/except) — không bao giờ crash nếu Anki đổi API.
2. Config runtime: `config.get_config()` (file JSON profile) + `mw.col.conf` (sidebar width, EXP, collapse…). Sau khi `write_config()` gọi `invalidate_config_cache()`.
3. Không import ngược: Forge **không bao giờ** import Bento Station (chống vòng lặp).
4. Mọi JS→Python đi qua `pycmd('...')`; Python→JS qua `web.eval("...")`.
5. Giữ nguyên header tri ân `# Original code/structure from Onigiri Add-on.` ở đầu file (compliance).
6. Khi thêm config key mới → cập nhật [`CONFIG_REFERENCE.md`](CONFIG_REFERENCE.md).

## Tài liệu liên quan

- Bản đồ file chi tiết: [`CODE_MAP.md`](CODE_MAP.md) · Kiến trúc: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Config: [`CONFIG_REFERENCE.md`](CONFIG_REFERENCE.md) · Tích hợp Forge: [`BENTO_FORGE_INTEGRATION.md`](BENTO_FORGE_INTEGRATION.md)
- Bento Forge (add-on độc lập): `addons21/Bento Forge/AGENTS.md` — nằm ngoài workspace này, kết nối qua [`bento_forge_bridge.py`](bento_forge_bridge.py).
