# 🍱 Bento Station AIOS — Kiến Trúc Tổng Thể

> Kế thừa & mở rộng **Onigiri Add-on**. Code mới dùng tên `Bento Station AIOS`; một số symbol cũ giữ tên `onigiri_*`/`modern_menu_*` vì tương thích ngược. Điểm vào cho AI: [`AGENTS.md`](AGENTS.md).

## Tổng Quan

Bento Station là add-on giao diện toàn diện cho Anki, thay thế hoàn toàn giao diện mặc định của Deck Browser, Overview, Reviewer và Congratulations page. Add-on hoạt động bằng cách **monkey-patch** và **hook** vào các class nội bộ của Anki (`DeckBrowser`, `Reviewer`, `Overview`) để inject HTML/CSS/JS tùy chỉnh. Module phụ **Bento Forge** (xưởng tạo thẻ AI) được nối qua [`bento_forge_bridge.py`](bento_forge_bridge.py) — xem [`BENTO_FORGE_INTEGRATION.md`](BENTO_FORGE_INTEGRATION.md).

## Luồng Khởi Động

```
Anki khởi động
  │
  ├─► __init__.py (top-level)
  │     ├─ patcher.patch_congrats_page()        ← Patch trang chúc mừng
  │     ├─ DeckBrowser._renderPage = bento_station_renderer.render_bento_station_deck_browser  ← Thay thế renderer
  │     └─ DeckBrowser._render_deck_node = patcher._onigiri_render_deck_node       ← Thay thế render node
  │
  ├─► gui_hooks.main_window_did_init
  │     └─► setup_global_hooks()
  │           ├─ patcher.apply_patches()         ← Patch toolbar, menu, overview
  │           └─ menu_buttons.setup_onigiri_menu() ← Thêm menu "Onigiri" vào thanh công cụ
  │
  └─► gui_hooks.profile_did_open
        └─► on_profile_did_open()
              ├─ patcher.patch_overview()        ← Patch overview (cần mw.col)
              ├─ apply_full_hide_mode()          ← Ẩn menu bar nếu bật
              ├─ maybe_show_welcome_popup()      ← Hiện popup chào mừng
              ├─ birthday_dialog.maybe_show_birthday_popup() ← Sinh nhật
              └─ patcher.apply_menu_styling()    ← Style cho QMenu
```

## Luồng Render Trang

### Deck Browser (`bento_station_renderer.py` → `templates.py` + JS)

```
render_onigiri_deck_browser()
  ├─ 1. Build Onigiri Widgets Grid (stats, heatmap, retention, favorites, level bar)
  │     ├─ widget_generators dict: studied, time, pace, retention, heatmap, favorites, level
  │     └─ Layout từ config: onigiriWidgetLayout.grid
  ├─ 2. Build External Add-on Widgets (cùng grid với Onigiri)
  │     ├─ patcher._get_external_hooks() → lấy hook từ add-on khác
  │     └─ Layout từ config: externalWidgetLayout.grid
  ├─ 3. Assemble Stats Block (CSS + HTML grid)
  ├─ 4. Build Deck Tree HTML
  │     └─ deck_tree_updater._render_deck_tree_html_only()
  ├─ 5. Populate Main Template (templates.py: custom_body_template)
  │     ├─ Thay {tree}, {stats}, {sidebar_buttons}, {profile_bar}...
  │     └─ Thêm mascot HTML nếu enabled
  └─ 6. Render Final Page
        └─ self.web.stdHtml(body, css, js, context)
```

### Reviewer (`__init__.py` → `inject_menu_files()`)

```
inject_menu_files(web_content, context) [isinstance Reviewer]
  ├─ CSS: notifications.css + notification position
  ├─ CSS: patcher.generate_reviewer_background_css()  ← Ảnh nền reviewer
  ├─ CSS: patcher.generate_reviewer_buttons_css()     ← Style nút Again/Hard/Good/Easy
  ├─ HTML: patcher.generate_reviewer_top_bar_html_and_css() ← Top bar (Decks, Add, Browse...)
  ├─ JS: injector (top bar insertion, header offset, mascot)
  ├─ JS: notifications.js
  └─ JS: animated_mascot (nếu enabled)
```

## Quan Hệ Module

```
__init__.py (entry point, hook registration)
  ├──► patcher.py (SHIM re-export — giữ namespace patcher.X cho các module cũ)
  ├──► patching.py (Patch registry + version-guard cho monkey-patch Anki internals)
  ├──► css/ (Sinh toàn bộ CSS — package: backgrounds.py, icons.py, reviewer.py, dynamic.py, fonts.py, utils.py; `css_engine.py` là SHIM re-export)
  ├──► toolbar_styling.py (Menu styling, QMenu patch, sync status, toolbar visibility)
  ├──► profile_page.py (ProfileDialog + HTML helpers + profile stats cache)
  ├──► webview_router.py (on_webview_js_message — xử lý pycmd từ mọi webview)
  ├──► bento_forge_bridge.py (Cầu nối 1 chiều tới Bento Forge — lazy import, config sync, chống lỗi)
  ├──► bento_station_renderer.py (Deck Browser render core, EXP, sidebar) + widgets/ (widget generators: levelbar, stats, heatmap, session, favorites)
  ├──► deck_tree_updater.py (Deck tree HTML rendering, collapse/expand, move decks)
  ├──► config.py (Config loader - đọc/ghi file JSON profile-specific)
  ├──► templates.py (HTML template cho deck browser)
  ├──► webview_handlers.py (Xử lý pycmd từ webview: collapse, favorite, transfer, move, set_mood)
  ├──► menu_buttons.py (Thêm nút "Onigiri" vào thanh menu Anki)
  ├──► settings/ (Giao diện settings dialog — package: dialog.py, widgets.py, pickers.py, color_widgets.py, search.py, dialogs.py, pixmap_utils.py; `__init__.py` re-export API cũ)
  ├──► animated_mascot.py (Engine nhân vật 2D: sprite/Lottie/Rive)
  ├──► heatmap.py (Dữ liệu heatmap + streak từ revlog database; effort_by_day)
  ├──► habit_engine.py (Habit Engine: telemetry theo ngày, effort score, session suggestion, streak tokens — cache TTL)
  ├──► study_tools/ (Study Planner, Quick Lookup, Flashcard Gallery, Focus Timer — package: shared/planner/lookup/gallery/timer + open_tool router)
  ├──► future_letter_dialog.py (Future Self Letter: milestone check + dialog viết/giao thư)
  ├──► fonts.py (Font loading: system fonts + user fonts)
  ├──► constants.py (COLOR_LABELS, ICON_DEFAULTS, theme keys)
  ├──► themes/ (Theme presets: `themes/definitions.py` chứa `THEMES` + `define_theme()`)
  ├──► welcome_dialog.py (Popup chào mừng lần đầu)
  ├──► birthday_dialog.py (Popup sinh nhật)
  ├──► icon_chooser.py (Dialog chọn icon cho deck)
  ├──► create_deck_dialog.py (Dialog tạo deck mới)
  ├──► credits_dialog.py (Dialog credits)
  ├──► favorites_cleanup.py (Dọn dẹp favorites)
  └──► coloris_picker.py (Color picker widget)

web/
  ├──► engine.js (OnigiriEngine: hover, collapse, mutation observer - 60FPS)
  ├──► injector.js (Sidebar resize, focus mode, edit mode, transfer buttons)
  ├──► animated_mascot.js (Mascot animation: sprite sheet canvas / Lottie / Rive)
  ├──► heatmap.js (Heatmap renderer)
  ├──► notifications.js (EXP toast notifications)
  ├──► profile_page.js (Profile page interactions)
  ├──► menu.css / overview.css / profile.css / heatmap.css / notifications.css / congrats.css
  └──► lib/html2canvas.min.js (Screenshot export cho profile)
```

## Cơ Chế Chính

### 1. Monkey-patching Anki (qua `patching.py` — version-guard, P0-A2)
- `patching.apply_congrats_patch()` / `apply_overview_patch()` / `apply_deck_browser_render_patches()`
- Mỗi patch có `hasattr` guard + try/except → nếu Anki đổi API thì bỏ qua, dùng mặc định (không crash); log qua `_safe_apply`.
- `DeckBrowser._renderPage` → `bento_station_renderer.render_bento_station_deck_browser`
- `DeckBrowser._render_deck_node` → `patcher._onigiri_render_deck_node`
- `Overview._table` → custom HTML
- `Overview._body` → custom HTML
- `Overview._show_finished_screen` → wrap với custom congrats

### 2. WebView Message Passing
- Python: `gui_hooks.webview_did_receive_js_message` → `patcher.on_webview_js_message` + `webview_handlers.handle_webview_cmd`
- JS → Python: `pycmd('command')` (Anki's built-in bridge)
- Python → JS: `webview.web.eval("JS code")`

### 3. EXP System (Sakura RPG)
- `_on_reviewer_did_answer_card()` hook: tính EXP dựa trên card type + ease + interval
- `award_exp()`: cập nhật `mw.col.conf["onigiri_exp"]`
- `_get_onigiri_level_bar_html()`: render level bar trong deck browser
- `_EXP_TOAST_JS` / `OnigiriExpToast`: hiển thị toast EXP trong reviewer

### 4. Config System
- File: `user_files/settings_{profile_name}.json`
- Load: `config.get_config()` → merge DEFAULTS + user config (deep-merge — lưu ý khi thêm widget vào DEFAULTS.grid sẽ tự xuất hiện cho user cũ). **Có cache TTL 1s** (P0-A1) — trả deepcopy, `invalidate_config_cache()` khi write/mở profile.
- Write: `config.write_config()`
- Cache: `mw.col.conf` cho các giá trị runtime (sidebar width, collapse state, EXP, session mood, streak tokens, letters...)

### 5. Habit Engine (GĐ1–GĐ4)
- **GĐ1 Effort Heatmap**: `habit_engine.get_effort_data()` → `heatmap_data["effort_by_day"]`; JS toggle Count/Effort trong `web/heatmap.js`. Công thức: effort 0-100 = tổ hợp (thời gian + độ đúng + độ khó) theo `heatmapEffortWeights`.
- **GĐ2 Suggested Session**: `get_session_suggestion()` = clamp(avg_volume × mood_multiplier). Widget `"session"` (opt-in qua widget editor) + pycmd `onigiri_set_mood`.
- **GĐ3 Streak Insurance**: `track_today_review()` (hook reviewer, không thêm setMod) cấp token khi vượt 120% khối lượng TB; `maybe_protect_streak()` (deck browser render) tự cứu streak khi lỡ ngày + notification.
- **GĐ4 Future Self Letter**: `future_letter_dialog.maybe_check_milestones()` (profile open, delay 1.6s) giao thư cũ + nhắc viết thư mới ở milestone.
- Hiệu suất: telemetry cache TTL 10s + `invalidate_cache()` khi review; avg cache theo ngày; tránh thêm `setMod()` mỗi lần bấm.

## Hiệu Xuất — Điểm Nghẽn Đã Biết

| Vị trí | Vấn đề | Mức độ |
|--------|--------|--------|
| `_on_reviewer_did_answer_card()` | 2 lần `mw.col.setMod()` mỗi lần bấm nút | **Cao** ⚡ |
| `render_onigiri_deck_browser()` | Nhiều DB query mỗi lần render | Trung bình |
| `inject_menu_files()` | Đọc file CSS từ disk mỗi lần navigate | Thấp |
| `update_sync_status_indicator()` | Gọi `web.eval()` quá thường xuyên | Thấp |
| `get_mascot_config()` | `deepcopy` + recursive merge mỗi lần | Thấp |
| `_get_onigiri_favorites_html()` | Gọi `mw.col.decks.get()` cho từng deck | Thấp |
