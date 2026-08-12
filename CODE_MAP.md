# 🍱 Bento Station AIOS — Code Map (Bản Đồ Mã Nguồn)

> Liệt kê mọi file + số dòng (đã xác minh) giúp AI định vị nhanh code cần sửa mà không đọc trọn file.
> Quy trình tiết kiệm token: xem [`AGENTS.md`](AGENTS.md).

---

## 📂 Python (Gốc)

| File | Dòng | Mô tả |
|------|------|-------|
| [`__init__.py`](__init__.py) | 674 | **Entry point.** Đăng ký mọi `gui_hooks` (dòng 654-674): `setup_global_hooks()`, `on_profile_did_open()`, `inject_menu_files()` (inject CSS/JS), `_on_reviewer_did_answer_card()` (EXP + habit), `update_sync_status_indicator()`, `_on_webview_cmd`. Chứa `_EXP_TOAST_JS`/`_LEVEL_BAR_JS`. |
| [`patcher.py`](patcher.py) | 1096 | **SHIM re-export.** Giữ namespace `patcher.X`; code thật đã tách sang `patching/css_engine/toolbar_styling/profile_page/webview_router`. Còn giữ: `patch_overview`, `patch_congrats_page`, `take_control_of_deck_browser_hook`, `_onigiri_render_deck_node`, `_get_external_hooks`, `apply_patches`. |
| [`patching.py`](patching.py) | 78 | **Patch registry + version-guard.** `_safe_apply()` (hasattr + try/except); `apply_overview_patch()`, `apply_congrats_patch()`, `apply_deck_browser_render_patches()`, `applied_patches()`. |
| [`css/`](css/) | — | **CSS engine — PACKAGE** (tách từ `css_engine.py` 2k; `css_engine.py` giờ là SHIM re-export). |
| [`css/backgrounds.py`](css/backgrounds.py) | 989 | Sinh CSS nền: `generate_*_background_css` (profile/deck browser/reviewer/overview/toolbar/bottom bar), `_render_background_css`, `_generate_outer_background_css`. |
| [`css/icons.py`](css/icons.py) | 410 | `generate_icon_css`, `generate_icon_size_css`, `generate_conditional_css`, `generate_profile_bar_fix_css`. |
| [`css/reviewer.py`](css/reviewer.py) | 322 | `generate_reviewer_buttons_css` (nút Again/Hard/Good/Easy). |
| [`css/dynamic.py`](css/dynamic.py) | 208 | `generate_dynamic_css` (CSS biến theo config). |
| [`css/fonts.py`](css/fonts.py) | 110 | `generate_font_css`. |
| [`css/utils.py`](css/utils.py) | 58 | `_hex_to_rgba`, `_mix_colors`. |
| [`toolbar_styling.py`](toolbar_styling.py) | 230 | **Toolbar/menu styling.** `apply_menu_styling`, `patch_qmenu`, `get_sync_status`, `_new_MainWebView_eventFilter`, `_update_toolbar_visibility`, `_on_sync_did_finish`. |
| [`profile_page.py`](profile_page.py) | 384 | **Profile page.** `ProfileDialog`, `open_profile`, `_generate_profile_html_body`, `_profile_stats_cache`. |
| [`webview_router.py`](webview_router.py) | 240 | **Webview router.** `on_webview_js_message` — xử lý pycmd từ mọi webview. |
| [`icon_registry.py`](icon_registry.py) | 555 | **🎌 Thư viện icon trung tâm.** 60+ icon Lucide style. `get_icon()`, `get_icon_url()`, `list_icons()`. |
| [`bento_station_renderer.py`](bento_station_renderer.py) | 1064 | **Deck Browser render engine (core).** `render_bento_station_deck_browser`, sidebar builder, `BUTTON_HTML`, dashboard stats cache — widget generators tách sang `widgets/`. |
| [`widgets/`](widgets/) | — | **Widget generators — PACKAGE** (tách từ renderer, Bước 3). |
| [`widgets/levelbar.py`](widgets/levelbar.py) | 119 | EXP/level bar: `_get_exp_data`, `award_exp`, `_get_onigiri_level_bar_html`, `_get_level_bar_js_refresh`. |
| [`widgets/stats.py`](widgets/stats.py) | 79 | `_get_onigiri_stat_card_html`, `_get_sakura_stat_card_html`, `_get_onigiri_retention_html` (+ retention cache). |
| [`widgets/favorites.py`](widgets/favorites.py) | 112 | `_get_onigiri_favorites_html`. |
| [`widgets/session.py`](widgets/session.py) | 70 | `_get_onigiri_session_widget_html`. |
| [`widgets/heatmap.py`](widgets/heatmap.py) | 23 | `_get_onigiri_heatmap_html`. |
| [`config.py`](config.py) | 568 | **Config loader.** `get_config()`/`write_config()` cache TTL 1s + `invalidate_config_cache()`. Section `bentoForge` (API key/cache), Habit Engine, icon registry. |
| [`templates.py`](templates.py) | 458 | **HTML template** deck browser. CSS edit mode/favorite/sidebar; JS `OnigiriEditor`, `SyncStatusManager`. |
| [`constants.py`](constants.py) | 167 | **Hằng số.** `COLOR_LABELS`, `ICON_DEFAULTS`, `ALL_THEME_KEYS`, `REVIEWER_THEME_KEYS`. |
| [`deck_tree_updater.py`](deck_tree_updater.py) | 191 | **Deck tree operations.** `_render_deck_tree_html_only()`, `on_deck_collapse()`, `on_decks_move()`, `refresh_deck_tree_state()`. |
| [`webview_handlers.py`](webview_handlers.py) | 106 | **WebView command handler.** `pycmd`: `onigiri_create_deck`, `onigiri_collapse:`, `onigiri_toggle_favorite:`, `onigiri_show_transfer_window:`, `onigiri_move_decks:`, `onigiri_set_mood:`. |
| [`animated_mascot.py`](animated_mascot.py) | 399 | **Mascot engine.** `get_mascot_config()`, `generate_mascot_html/css/js()`, `get_mascot_head_content()/body_content()`. |
| [`heatmap.py`](heatmap.py) | 177 | **Heatmap data provider.** `get_heatmap_data()` (query revlog), `get_heatmap_and_config()`, streak. Gắn `effort_by_day` từ `habit_engine`. |
| [`habit_engine.py`](habit_engine.py) | 385 | **Habit Engine.** Telemetry theo ngày, effort score 0-100, rolling avg, session suggestion, streak tokens, cache TTL 10s. |
| [`future_letter_dialog.py`](future_letter_dialog.py) | 264 | **Future Self Letter.** Milestone check + dialog viết/giao thư (`mw.col.conf["onigiri_letters"]`). |
| [`study_tools/`](study_tools/) | — | **Study tools — PACKAGE** (tách từ study_tools.py, Bước 4). |
| [`study_tools/shared.py`](study_tools/shared.py) | 154 | Cấu hình + thống kê: `get_tools_config`, `save_tools_config`, `cards_reviewed_today/week`, `current_streak`. |
| [`study_tools/planner.py`](study_tools/planner.py) | 126 | `StudyPlannerDialog`, `open_study_planner`, `get_planner_widget_html`. |
| [`study_tools/lookup.py`](study_tools/lookup.py) | 125 | `QuickLookupDialog`, `open_quick_lookup`, `get_lookup_widget_html`. |
| [`study_tools/gallery.py`](study_tools/gallery.py) | 224 | `FlashcardGalleryDialog`, `ReviewDeckDialog`, `open_flashcard_gallery`, `get_gallery_widget_html`. |
| [`study_tools/timer.py`](study_tools/timer.py) | 193 | `FocusTimerDialog`, `open_focus_timer`, `get_timer_widget_html`. |
| [`bento_forge_bridge.py`](bento_forge_bridge.py) | 456 | **Cầu nối Bento Forge.** Lazy import 1 chiều, `open_forge()`, `ensure_config_sync()`, `configure_cache()`, `refresh_anki_ui()`. |
| [`settings/`](settings/) | — | **Settings dialog — PACKAGE** (tách từ `settings.py` 11.6k, giữ nguyên API qua `__init__.py`). |
| [`settings/dialog.py`](settings/dialog.py) | 9321 | **`SettingsDialog` + `open_settings()`** — dialog chính (còn lớn 9.3k). |
| [`settings/widgets.py`](settings/widgets.py) | 799 | Widget lá: FlowLayout, ThumbnailWorker, ProfileBarWidget, SidebarToggleButton, SectionGroup, ColorSwatch, FontCardWidget, BirthdayWidget, SearchResultWidget... |
| [`settings/pickers.py`](settings/pickers.py) | 768 | `ThemeCardWidget`, `IconPickerDialog`. |
| [`settings/color_widgets.py`](settings/color_widgets.py) | 534 | `ColorMapWidget`, `GradientSlider`/`HueSlider`/`AlphaSlider`, `FavoriteColorButton`, `ModernColorPickerDialog`. |
| [`settings/search.py`](settings/search.py) | 250 | `SettingsSearchPage`. |
| [`settings/dialogs.py`](settings/dialogs.py) | 108 | `DonationDialog`. |
| [`settings/pixmap_utils.py`](settings/pixmap_utils.py) | 49 | `create_circular_pixmap()`, `create_rounded_pixmap()`. |
| [`fonts.py`](fonts.py) | 115 | **Font loader.** System fonts + user fonts; `generate_font_css()`. |
| [`menu_buttons.py`](menu_buttons.py) | 116 | **Menu integration.** Thêm menu "Onigiri"/"Bento Station" + submenu (Settings, Profile, Bento Forge, Study Tools). |
| [`themes/`](themes/) | — | **Theme presets — PACKAGE** (tách từ themes.py, Bước 4). |
| [`themes/definitions.py`](themes/definitions.py) | 911 | `THEMES` dict + `define_theme()` (Tokyo Drift, Midnight...). |
| [`welcome_dialog.py`](welcome_dialog.py) | 110 | **Welcome popup.** Lần đầu hoặc khi có phiên bản mới. |
| [`birthday_dialog.py`](birthday_dialog.py) | 218 | **Birthday popup.** Nếu hôm nay là sinh nhật user. |
| [`icon_chooser.py`](icon_chooser.py) | 242 | **Icon chooser dialog.** Chọn icon cho từng deck. |
| [`create_deck_dialog.py`](create_deck_dialog.py) | 106 | **Create deck dialog.** Tạo deck mới. |
| [`credits_dialog.py`](credits_dialog.py) | 57 | **Credits dialog.** Tác giả, phiên bản. |
| [`coloris_picker.py`](coloris_picker.py) | 134 | **Color picker.** Tích hợp Coloris. |
| [`favorites_cleanup.py`](favorites_cleanup.py) | 163 | **Favorites cleanup.** Dọn deck favorites đã xóa. |
| [`onigiri_renderer.py`](onigiri_renderer.py) | 22 | **SHIM tương thích ngược.** Re-export `bento_station_renderer` dưới tên cũ. |

## 📂 Web (HTML/CSS/JS)

| File | Mô tả |
|------|-------|
| [`web/engine.js`](web/engine.js) | **Onigiri Performance Engine.** Hover row, collapse click, mutation observer, `updateDeckTree()` không reload trang. |
| [`web/injector.js`](web/injector.js) | **Sidebar UI.** Resize handle (60FPS rAF), focus mode, edit mode, transfer, collapse toggle. |
| [`web/animated_mascot.js`](web/animated_mascot.js) | **Mascot animation JS.** Canvas 2D sprite sheet / Lottie / Rive; click/hover/drag. |
| [`web/heatmap.js`](web/heatmap.js) | **Heatmap renderer.** `OnigiriHeatmap.render()`, tooltip, toggle Count/Effort. |
| [`web/notifications.js`](web/notifications.js) | **Notification system.** Stack toast (thành công/lỗi/info), streak protection. |
| [`web/profile_page.js`](web/profile_page.js) | **Profile page JS.** Tab navigation, export (html2canvas). |
| [`web/menu.css`](web/menu.css) | CSS deck browser: sidebar, stats grid, heatmap, level bar, session widget, mode toggle. |
| [`web/overview.css`](web/overview.css) | CSS overview page. |
| [`web/heatmap.css`](web/heatmap.css) | CSS heatmap widget. |
| [`web/profile.css`](web/profile.css) | CSS profile page. |
| [`web/notifications.css`](web/notifications.css) | CSS notification toast. |
| [`web/congrats.css`](web/congrats.css) | CSS congratulations page. |
| [`web/icon_chooser.*`](web/icon_chooser.html) | HTML/CSS/JS icon chooser dialog. |
| [`web/welcome.html`](web/welcome.html) | HTML welcome dialog. |
| [`web/birthday.html`](web/birthday.html) | HTML birthday dialog. |
| [`web/credits.html`](web/credits.html) | HTML credits dialog. |
| [`web/lib/html2canvas.min.js`](web/lib/html2canvas.min.js) | Thư viện html2canvas (screenshot export). |

## 📂 System / User Files

| Thư mục | Mô tả |
|---------|-------|
| `system_files/coloris/` | Thư viện Coloris color picker (CSS + JS). |
| `system_files/fonts/system_fonts/` | Font hệ thống (.ttf). |
| `system_files/heatmap_system_icons/` | SVG icons cho heatmap shape. |
| `system_files/system_icons/` | SVG icons cho UI. |
| `system_files/profile_default/` | Ảnh mặc định (`bento_station-bg.png`, `bento_station-san.png`). |
| `user_files/settings_{profile}.json` | Config profile-specific. |
| `user_files/{main_bg,sidebar_bg,reviewer_bg,reviewer_bar_bg,profile,profile_bg}/` | Ảnh nền + avatar. |
| `user_files/sprites/` | Sprite sheet mascot. · `user_files/fonts/` · `user_files/icons/` · `user_files/user_themes/` | Asset tùy chỉnh. |

## 🔗 Hook Flow (`__init__.py:654-674`)

| Hook | Hàm đăng ký | Context |
|------|------------|---------|
| `main_window_did_init` | `setup_global_hooks()` | Toàn cục |
| `profile_did_open` | `on_profile_did_open()` | Toàn cục |
| `webview_will_set_content` | `inject_menu_files()` | DeckBrowser, Reviewer, Overview, Toolbar |
| `deck_browser_did_render` | `on_deck_browser_did_render()` | DeckBrowser |
| `webview_did_receive_js_message` | `patcher.on_webview_js_message()` + `_on_webview_cmd()` | Tất cả webview |
| `reviewer_did_answer_card` | `_on_reviewer_did_answer_card()` | Reviewer |
| `state_did_change` | `on_state_change()` | Toàn cục |
| `sync_did_finish` / `sync_will_start` / `operation_did_execute` | `update_sync_status_indicator()` | Toàn cục |
| `deck_browser_will_show_options_menu` | `on_deck_options_shown()` | DeckBrowser |
| `theme_did_change` | `patcher.apply_menu_styling()` | Toàn cục |
