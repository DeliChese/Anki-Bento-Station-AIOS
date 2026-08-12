# Bento Station AIOS + Bento Forge — Architecture Audit (Thực tế, không khen xã giao)

> Ngày: 2026-08-12 · Phạm vi: toàn bộ `addons21/Bento Station AIOS` + `addons21/Bento Forge`
> Phương pháp: đọc mã nguồn trực tiếp (không dựa vào README/ARCHITECTURE.md), đếm dòng thực tế, truy vết luồng khởi động, hook, patch, pipeline AI.

---

## 1. Quy mô codebase

### Số liệu thô (đã loại binary, .git, __pycache__, system_files, user_files)

| Thành phần | Bento Station AIOS | Bento Forge | Tổng |
|---|---|---|---|
| File Python | **70** | **57** | **127** |
| Dòng Python | **26.123** | **20.161** | **46.284** |
| Dòng CSS | 3.959 | 0 | 3.959 |
| Dòng template/HTML | 890 | 0 | 890 |
| Dòng JS | 2.711 | 0 | 2.711 |
| JSON | 4 (40 dòng) | 22 (12.921 dòng) | 26 (12.961) |
| Markdown | 11 (1.628) | 10 (1.087) | 21 (2.715) |
| **Tổng dòng** | **35.362** | **34.169** | **~69.500** |

### File test

| | Bento Station | Bento Forge |
|---|---|---|
| File test | 8 | 18 |
| Dòng test | 482 | 4.204 |
| Loại | smoke-test import/render gọi được | test logic thật (factory_selection, batch_processor) |

**Verdict:** Phần lớn test của Station là *smoke call* (`test_css_engine_call`, `test_renderer_widgets_call`) — không test hành vi. Test thật nằm ở Forge. Tỷ lệ dòng test/Python: Station 1.8%, Forge 20.8%.

### 10 file lớn nhất — Bento Station AIOS

| Dòng | File | Ghi chú |
|---|---|---|
| 9.323 | `settings/dialog.py` | 1 class `SettingsDialog` đơn khối khổng lồ |
| 1.686 | `web/menu.css` | CSS deck browser |
| 1.096 | `patcher.py` | Legacy patch + wrap + CSS generators mixed |
| 1.065 | `bento_station_renderer.py` | Renderer chính (chứa ~350 dòng CSS inline) |
| 989 | `css/backgrounds.py` | Sinh CSS nền |
| 911 | `themes/definitions.py` | 20+ theme palette |
| 800 | `settings/widgets.py` | Widget tùy chỉnh settings |
| 769 | `settings/pickers.py` | Color/file pickers |
| 754 | `web/icon_chooser.css` | Icon chooser |
| 726 | `web/icon_chooser.js` | Icon chooser JS |

### 10 file lớn nhất — Bento Forge

| Dòng | File | Ghi chú |
|---|---|---|
| 5.824 | `utils/factory_state.json` | **478 KB state runtime** nằm trong thư mục nguồn |
| 2.720 | `utils/ai_extractor.py` | Toàn bộ AI pipeline + HTTP + cache + history |
| 2.639 | `__init__.py` | 1 class `AnkiSmartFactory` 2.500 dòng |
| 1.744 | `utils/i18n.py` | i18n vi/en |
| 1.149 | `mode/templates.py` | Template thẻ 3 ngôn ngữ |
| 1.086 | `utils/import_history.json` | History import (data, không phải code) |
| 1.033 | `utils/batch_processor.py` | Batch AI |
| 683 | `tests/test_factory_selection.py` | |
| 611 | `tests/test_batch_processor.py` | |
| 539 | `ui/theme.py` | Glassmorphism theme |

---

## 2. Phân lớp kiến trúc (ước tính % dòng Python)

| Lớp | % | Dòng ước tính | Thành phần chính |
|---|---|---|---|
| Bento Station UI/Workspace | **~35%** | ~9.100 | `bento_station_renderer.py`, `deck_tree_updater.py`, `templates.py`, `widgets/`, `study_tools/`, `profile_page.py`, `animated_mascot.py`, `welcome/birthday/icon/credits/create` dialog |
| Settings & Config | **~22%** | ~5.700 | `settings/` (9.323 dòng), `config.py`, `coloris_picker.py`, `icon_chooser.py` |
| Theme/CSS Engine | **~12%** | ~3.100 | `css/` (989 nền + dynamic + reviewer + icons), `themes/`, `css_engine.py` (shim), `fonts.py`, `toolbar_styling.py` |
| Onigiri Foundation (legacy core) | **~11%** | ~2.900 | `patcher.py`, `onigiri_renderer.py` (shim), `menu_buttons.py`, phần Onigiri còn nguyên trong `__init__.py` (toast/level bar JS, inject) |
| Hook & Patching | **~3%** | ~800 | `patching.py`, patcher.apply_patches, hook registry trong `__init__.py` |
| Bento Forge AI | — | 20.161 riêng | `ai_extractor.py`, `batch_processor.py`, `workers/`, `hooks/` |
| Tests | — | 4.686 (cả 2) | 26 files |

> Lưu ý: `__init__.py` chỉ 674 dòng nhưng **gom 9 hook đăng ký + inject JS/CSS cho 5 loại webview + logic EXP game hóa + level-bar/toast JS inline**.

---

## 3. Mức độ kế thừa từ Onigiri

Đếm thực tế: **32 file** có header `Original code/structure from Onigiri Add-on`, 7 file nhắc Onigiri (không header), 31 file không nhắc.

| Thành phần | Đánh giá | Bằng chứng |
|---|---|---|
| **Renderer** | **Viết mới** | `bento_station_renderer.render_bento_station_deck_browser` thay thế hoàn toàn `_renderPage`; widget/layout grid là concept mới. Nhưng `_onigiri_render_deck_node` (patcher.py:786) vẫn là code Onigiri sửa nhẹ. |
| **Hook system** | **Giữ nguyên** | Cùng bộ hook cũ (`main_window_did_init`, `profile_did_open`, `webview_will_set_content`, `deck_browser_did_render`...). Thêm `reviewer_did_answer_card` (EXP) và `deck_browser_will_show_options_menu`. |
| **Patching** | **Sửa nhẹ** | `patching.py` mới (hasattr guard + `_safe_apply` registry) — cải thiện lớn so với Onigiri, nhưng `patch_congrats_page` vẫn `wrap` không guard. |
| **Settings** | **Tái cấu trúc sâu (bắt buộc)** | 9.323 dòng 1 class; không tách được logic khỏi Qt. Backlog `plans/` đã thừa nhận. |
| **Theme engine** | **Sửa nhẹ** | Tách `css/` package + `css_engine.py` shim (giữ API cũ). Nội dung vẫn là f-string CSS của Onigiri. |
| **Toolbar** | **Sửa nhẹ** | Tách `toolbar_styling.py`; vẫn patch QMenu + MainWebView event filter kiểu Onigiri. |
| **Webview router** | **Sửa nhẹ** | Tách `webview_router.py` + `webview_handlers.py` từ patcher; vẫn là 1 chuỗi `if cmd ==` khổng lồ. |
| **Templates** | **Sửa nhẹ** | `templates.py` là body template mới (custom_body_template) nhưng CSS inline trong renderer vẫn kiểu Onigiri. |
| **CSS** | **Sửa nhẹ** | `web/menu.css` 1.686 dòng gần như giữ nguyên; thêm heatmap/overview/notifications/css. |

**Tóm tắt:** Bento Station đã **thay renderer + đổi tên brand** nhưng **giữ nguyên xương sống hook/patch/theme-setup của Onigiri**. Đây là một rebrand + mở rộng, không phải rewrite.

---

## 4. Luồng khởi động

```
Anki khởi động
 │
 ├─ 1. Import __init__.py (module-level)
 │     • sys.path += addon_path
 │     • patching.apply_congrats_patch()          ← wrap Overview._show_finished_screen
 │     • patching.apply_deck_browser_render_patches() ← gán DeckBrowser._renderPage
 │         = bento_station_renderer.render_bento_station_deck_browser
 │         + DeckBrowser._render_deck_node = patcher._onigiri_render_deck_node
 │     • Đăng ký 11 gui_hooks (main_window_did_init, profile_did_open,
 │       webview_will_set_content, deck_browser_did_render, webview_did_receive_js_message×2,
 │       state_did_change, sync_will_start/did_finish, operation_did_execute,
 │       deck_browser_will_show_options_menu, theme_did_change, reviewer_did_answer_card)
 │
 ├─ 2. main_window_did_init → setup_global_hooks()
 │     • patcher.apply_patches() → apply_menu_styling, patch_qmenu, sync hooks, toolbar visibility
 │     • menu_buttons.setup_onigiri_menu()
 │     • bento_forge_bridge.initialize_forge() → import "Bento Forge" (importlib, có space)
 │         → Forge module-level: register_hooks() (reviewer) + register_overview_hooks()
 │
 ├─ 3. profile_did_open → on_profile_did_open()
 │     • patching.apply_overview_patch() → gán Overview._table/_body
 │     • config.invalidate_config_cache()
 │     • apply_full_hide_mode()
 │     • maybe_show_welcome_popup() (+ birthday 1s, future letter 1.6s qua QTimer)
 │     • bento_forge_bridge.ensure_config_sync() + configure_cache()
 │     • patcher.apply_menu_styling()
 │
 ├─ 4. webview_will_set_content → inject_menu_files(web_content, context)
 │     • DeckBrowser: generate_dynamic_css, menu.css, heatmap.css, profile-bar-fix,
 │       deck backgrounds, icon CSS, conditional CSS, notifications.css/js, injector.js,
 │       engine.js, heatmap.js, mascot
 │     • Reviewer: notifications.css, position CSS, reviewer bg, top-bar HTML/CSS, JS injector, mascot
 │     • Overview/BottomBar/TopToolbar: backgrounds + overview.css
 │     • (bẫy: inject_menu_files bị wrap lần 2 bởi inject_menu_files_with_level_bar — 2 lần chạy)
 │
 ├─ 5. deck_browser_did_render → on_deck_browser_did_render()
 │     • OnigiriHeatmap.render() qua web.eval
 │     • habit_engine.maybe_protect_streak() → toast JS
 │     • update_sync_status_indicator()
 │
 └─ 6. User tương tác → pycmd() → webview_router.on_webview_js_message
        → for each cmd: open settings / Forge / study tools / collapse / favorite...
```

**Điểm yếu của luồng:**
- **Hai lần patch renderer**: `patching.apply_deck_browser_render_patches()` chạy ở top-level, còn `apply_patches()` (trong `main_window_did_init`) cũng từng gọi nhưng đã comment — may mắn không double-patch nhưng là tiền sử bất ổn.
- **inject_menu_files bị wrap 2 lần** (dòng 643-652 `__init__.py`): mỗi webview sẽ chạy `_inject_menu_files_original` (chính là hàm đã đăng ký hook) cộng thêm level-bar — nếu thứ tự đăng ký thay đổi sẽ nhân đôi CSS.
- Forge init **chạy ngay lúc import module-level của Forge** (register_hooks được gọi ở top-level file Forge, không phải trong main_window_did_init) — nghĩa là lỗi import Forge sẽ crash Station nếu bridge không bọc try/except (có bọc).

---

## 5. Tích hợp Bento Forge (`bento_forge_bridge.py`, 464 dòng)

| Tiêu chí | Đánh giá |
|---|---|
| **Coupling** | **4/10** — thấp nhờ lazy import, sentinel attrs (`AnkiSmartFactory`/`start_smart_factory`), try/except toàn chỗ, cache import 1 lần, import qua `importlib.import_module("Bento Forge")` (vì thư mục có khoảng trắng). |
| **Tách repo riêng?** | **ĐƯỢC, và gần như đã là repo riêng.** Forge là add-on độc lập nằm trong `addons21/Bento Forge` với `__init__.py` riêng. Bridge chỉ cần đường dẫn + sentinel. Muốn tách hoàn toàn cần dọn 2 coupling trực tiếp: |
| **Dữ liệu trao đổi** | (1) Cấu hình AI/cache qua `_CONFIG_FIELD_MAP` (api_key, api_base, model, temperature, max_chars, chunk_size, reasoning_effort). (2) Lệnh mở dialog (open_forge/open_ai_settings/open_deck_manager). (3) Lệnh refresh UI (`mw.reset()` + `deckBrowser.refresh()`). (4) Invalidate cache từ vựng (`invalidate_deck_cache`). |
| **Signal/callback/direct?** | **Gọi trực tiếp + attribute mutation** — không dùng signal/callback. Đặc biệt: |
| | • `open_ai_settings()` dùng `from ui import show_ai_settings_dialog` **hard-coded** (dòng 197) — import trực tiếp không qua `_discover_forge()`, dễ crash nếu Forge lỗi. |
| | • `open_deck_manager()` dùng `from ui.deck_manager_dialog import DeckManagerDialog` (dòng 211) — cùng vấn đề. |
| | • `configure_cache()` **monkey-patch biến nội bộ của Forge**: `api_mod._CACHE_DIR = custom_dir` (dòng 400) — phá vỡ đóng gói; Forge đổi tên biến là hỏng. |
| | • Chiều Forge→Station: **không có** — Forge không import ngược (đúng nguyên tắc chống vòng lặp), nhưng nghĩa là Station không nhận được sự kiện "import xong" từ Forge; chỉ có `refresh_anki_ui()` gọi 1 chiều. |
| | • Chiều dữ liệu realtime: không có signal-based sync; chỉ sync config lúc `profile_did_open`. |

**Đánh giá:** Bridge là điểm sáng của codebase — thiết kế fail-safe tốt, chống circular import, xử lý tên module có khoảng trắng. Nhưng 2 import cứng trong `open_ai_settings`/`open_deck_manager` và monkey-patch `_CACHE_DIR` là 3 điểm nợ cần dọn để tách repo thực sự an toàn.

---

## 6. Hệ thống Hook & Patch (monkey patch quan trọng)

| Target | Method | Risk (1-10) | Has fallback |
|---|---|---|---|
| `DeckBrowser._renderPage` | Gán trực tiếp = `render_bento_station_deck_browser` | **9** — thay cả trang render | Có guard `hasattr(_renderPage)` nhưng **không có fallback render**; nếu guard fail → Anki default; nếu hàm mới lỗi runtime → Anki vỡ màn hình |
| `DeckBrowser._render_deck_node` | Gán trực tiếp = `_onigiri_render_deck_node` (Onigiri) | **8** — format HTML thủ công, dễ lệch khi Anki đổi cấu trúc node | Guard hasattr; không fallback |
| `DeckBrowser._render_deck_tree` | Gán = `_onigiri_render_deck_tree` (module-level, patcher.py:1088) | **7** — wrap có `_old_render_deck_tree` | Có fallback: nếu thiếu method chỉ print warning |
| `Overview._table` | Gán trực tiếp = `new_table` | **8** — Anki 2.1.x đổi API nhiều lần | Guard `hasattr(_table) or hasattr(_body)` trong `patching.apply_overview_patch` |
| `Overview._body` | Gán trực tiếp = f-string HTML | **8** | Cùng guard trên |
| `Overview._show_finished_screen` | `wrap(..., "around")` | **6** | Không guard — patcher.py:562 gán trực tiếp tại patch_congrats_page |
| `gui_hooks.deck_browser_will_render_content` | **Xóa hook của add-on khác** và giữ lại (take_control) | **10** — chiếm quyền add-on khác, vi phạm tôn chỉ "add-on không phá add-on" | Không |
| `QMenu` / `MainWebView.eventFilter` | wrap qua toolbar_styling | **5** | Có `_toolbar_patched` flag chống double |
| `gui_hooks.*` (11 hook) | append — API chính thức | 1 | N/A |

**Điểm rủi ro cao nhất:** `take_control_of_deck_browser_hook()` loại bỏ hook của add-on khác khỏi `deck_browser_will_render_content` rồi tự triệu hồi trong renderer — một cơ chế "độc quyền webview" kiểu dùng `_get_hook_name` so module. Hoạt động tốt khi chỉ có 1 theme add-on, nhưng **xung đột trực tiếp** với bất kỳ add-on nào khác muốn render vào deck browser.

---

## 7. Renderer & Theme

### Renderer chính
`bento_station_renderer.render_bento_station_deck_browser` (1.065 dòng) — thay thế **toàn bộ** `DeckBrowser._renderPage`:
1. Build widget grid (`onigiriWidgetLayout.grid`) — 12 widget generators (studied, time, pace, retention, heatmap, favorites, level, session, planner, timer, lookup, gallery).
2. Gọi **hook của add-on khác** (đã bị cướp ở `take_control_of_deck_browser_hook`) để lấy `stats` HTML → đặt vào grid.
3. Build deck tree: `col.sched.deck_due_tree()` + `_render_deck_tree_html_only()` (gọi `_render_deck_node` patched).
4. Đổ vào `templates.custom_body_template` + inject `OnigiriEngine` JS.
5. `self.web.stdHtml()`.

### Cách render HTML
Python f-string sinh HTML → `web.stdHtml()`; deck tree update (collapse/favorite) qua `web.eval(js)` với HTML được `json.dumps` escape — không cần reload cả trang (deck_tree_updater). Điểm tốt.

### Cách inject CSS/theme
- Hook `webview_will_set_content` → `inject_menu_files` append vào `web_content.head` (≤ 8 block CSS + 4-5 `<script>` cho deck browser).
- `patcher.generate_*_css` (re-export từ `css_engine` → `css/`) sinh CSS nền/icon/reviewer buttons động theo config.
- Theme palette: `themes/definitions.py` (911 dòng, 20+ theme) → CSS variables.

### Cache
| Cache | TTL | Vị trí |
|---|---|---|
| Config | 1s | `config.py:9-15` |
| Dashboard stats (cards_today/time) | 60s | `bento_station_renderer.py:136-138` |
| Profile stats | có (profile_page) | `_profile_stats_cache` |
| Deck tree | **KHÔNG cache** — `deck_due_tree()` gọi lại mỗi lần render | — |
| Enhanced stats | **KHÔNG cache** — SQL `select did, queue, count() from cards group by did, queue` mỗi render | — |
| Forge deck vocab | 30 phút (incremental) | `deck_cache.py` |

### 5 file CSS lớn nhất
1. `web/menu.css` — 1.686 dòng
2. `web/icon_chooser.css` — 754 dòng
3. `css/backgrounds.py` — 989 dòng (sinh CSS nền)
4. CSS inline trong `bento_station_renderer.py` — ~350 dòng
5. CSS inline trong `patcher.py` (reviewer top bar + exp toast) — ~280 dòng

### Bottleneck render
1. **`deck_due_tree()`**: dựng toàn bộ cây deck + count từ DB mỗi lần `_renderPage` — O(deck × card).
2. **Enhanced stats SQL**: quét toàn bộ bảng `cards` mỗi render (khi bật `enhancedDeckStats`).
3. **External hook widgets chạy đồng bộ**: mỗi add-on khác render `stats` HTML ngay trong render chính → chậm nếu add-on đó chậm.
4. **CSS inline khổng lồ + base64**: mỗi render dựng lại ~700 dòng CSS + icon base64.

---

## 8. AI Pipeline (Bento Forge)

```
Input (text/file/vocab list/grammar)
 │
 ├─ 1. PARSE        parse_word_list() — text/tab/CSV/colon/JSON array
 ├─ 2. FILTER       get_existing_vocab_from_deck() — deck_cache (incremental 30p)
 │                 existing_hash = _make_existing_hash() → tham gia cache key
 ├─ 3. CHUNK        smart_group_words() — theo level (N5→N1/HSK) + độ dài, batch 40-80 từ
 ├─ 4. PROMPT       _build_batch_user_prompt() — system prompt + JSON template + danh sách từ
 │                 + warning "TỪ ĐÃ CÓ TRONG DECK — ĐỪNG XUẤT" + custom instruction
 ├─ 5. PROVIDER     _call_ai_for_batch() → chat/completions (OpenAI-compatible)
 │                 DeepSeek / OpenAI / Claude-proxy / Ollama / LM Studio / OpenRouter
 ├─ 6. RETRY        _http_post_json() — retry 5×, exponential backoff, 429 → Retry-After + adaptive delay
 ├─ 7. CACHE        _batch_cache_get/set — cache 14 ngày, key = md5(batch|kind|lang|instruction|existing_hash|fronts)
 ├─ 8. VALIDATION   _parse_ai_json_with_comment() — JSON có comment; lọc trùng front/meaning/level
 ├─ 9. FIELD MAP    json_field_map (prompt_config.apply_field_map_to_cfg) — AI JSON → Anki fields
 ├─ 10. CARD RENDER mode/templates.py + mode/card_render.build_qfmt/afmt — template thẻ JA/ZH/KO × vocabulary/grammar/combo
 └─ 11. IMPORT      ImportWorker(QThread) → col.add_note → Phase 2: audio TTS song song 4 workers
                   → _on_import_finished → refresh_anki_ui() (mw.reset + deckBrowser.refresh)
```

**Bước tốn token nhất:** **#4 Prompt** — system prompt có sẵn + JSON template đầy đủ **được chèn 2 lần** (trong system prompt và trong user prompt `_build_batch_user_prompt`), cộng danh sách từ + danh sách từ đã trùng. Với batch 80 từ × template ~10 field → 1 request có thể 8-15k token; 80 từ/batch × N batch = tốn theo cấp số nhân với 100k từ.

**Bước tốn thời gian nhất:** **#6 + #11** — network wait (`timeout 300s` thường, `600s` cho model reasoner) + delay rate-limit giữa các batch (1.5-3.2s/batch × số batch) + audio TTS mạng (4 workers, mỗi file 0.5-2s). Với 1.000 từ = 13-25 batch → **20-80 giây** chỉ riêng delay + API, chưa kể TTS.

---

## 9. Hiệu năng (ước tính — không benchmark, dựa trên độ phức tạp thuật toán)

| Thao tác | 10k notes | 50k notes | 100k notes | Ghi chú |
|---|---|---|---|---|
| **Mở deck browser** | 300-600ms | 600ms-1.2s | 1.2-3s | `deck_due_tree()` + HTML build; enhanced_stats query `group by did,queue` O(cards) |
| **Render overview** | 50-150ms | 100-300ms | 200-500ms | Chỉ `sched.counts()` — nhẹ; congrats page nặng hơn |
| **Scan deck (Forge)** | 1-3s | 3-10s | 5-20s | Lần đầu full scan `find_notes` + SQL batch 200; lần sau cache 30p incremental rất nhanh |
| **Mở Forge** | < 1s | < 1s | < 1s | Dialog + `_init_history` chạy QThread async — tốt |

**Nút thắt thực sự:** Deck Browser với `enhancedDeckStats=True` ở 100k notes sẽ **treo UI 3s+** vì SQL scan toàn bảng cards đồng bộ trên main thread. Đây là điểm cần cache/incremental như Forge đã làm cho deck vocab.

---

## 10. Technical Debt — Top 5

| # | File/Site | Severity | Impact | Refactor effort | ROI |
|---|---|---|---|---|---|
| 1 | `settings/dialog.py` — 9.323 dòng, 1 class `SettingsDialog` | **9** | Bất kỳ thay đổi settings nào cũng chạm file khổng lồ; không test được từng tab | Cao (tách package theo tab: ~3-5 ngày) | Rất cao — file này là nơi sửa thường xuyên nhất |
| 2 | `patcher.take_control_of_deck_browser_hook()` — cướp hook add-on khác | **9** | Xung đột add-on; người dùng báo bug "deck browser vỡ" không debug được | Trung bình (dùng layout slot thay vì cướp hook) | Cực cao cho cộng đồng + maintenance |
| 3 | Config 2 nguồn (JSON profile `config.get_config` + `mw.col.conf`) + DEFAULTS trùng/chard | **8** | Mỗi key mới phải khai 2 nơi; cache TTL 1s; `config.py:18-24` còn block DEFAULTS rỗng + comment artifact | Trung bình | Cao — ngăn mọi refactor logic |
| 4 | HTML/CSS/JS nhúng trong Python f-string rải rác (`__init__.py` toast/level-bar, renderer ~350 dòng CSS, patcher reviewer top bar) | **7** | Không syntax-highlight, không test, rủi ro escape `{}`/`$` | Thấp-Trung bình (tách web/) | Cao |
| 5 | Forge: `factory_state.json` (478KB/5.824 dòng) + `import_history.json` (1.086 dòng) trong thư mục nguồn | **7** | Không thuộc về git, phình repo, rủi ro commit dữ liệu người dùng (English vocab list!) | Thấp (chuyển user_files/) | Cao — bảo mật + repo sạch |

> **Nợ bổ sung:** bridge monkey-patch `_CACHE_DIR` (S6), import cứng `from ui import` trong bridge (S5), `print()` debug còn lại trong `deck_tree_updater.py:102-116` (S3), comment lạc `# Located in patcher.py` trong `css/backgrounds.py:92` (S2).

---

## 11. 3 quyết định rất đúng

1. **`patching.py` version-guard registry** (`_safe_apply` + hasattr guard + danh sách patch đã áp). Đây là khác biệt lớn nhất so với Onigiri: khi Anki đổi API, add-on không crash mà tự bỏ patch. Chi phí: 78 dòng. Lợi ích: sống sót qua nhiều bản Anki.
2. **`bento_forge_bridge.py` fail-safe**: lazy import + sentinel attrs + cache lỗi import + try/except toàn chỗ. Bento Station **luôn khởi động nguyên vẹn dù Forge thiếu/lỗi**. Đây là mẫu "plugin host" đúng đắn trong một ecosystem add-on vốn dễ vỡ.
3. **Incremental deck vocab cache của Forge** (`deck_cache.py`): full scan 1 lần → cache 30p → chỉ query notes có `mod >= timestamp`. Đánh trúng bài toán token + thời gian thực tế của pipeline AI, đồng thời chuẩn SQL batch (tránh N+1).

> Bonus: atomic write config (`_save_config` tmp→rename) và tách `widgets/`, `css/`, `settings/` dù chưa đủ — đúng hướng modular hóa.

---

## 12. 3 quyết định sẽ hối hận sau 1 năm

1. **`take_control_of_deck_browser_hook` cướp hook của add-on khác.** Khi người dùng cài thêm bất kỳ add-on nào render deck browser (LearnAway, Heatmap add-on, custom stats...), sẽ có kẻ cướp người bị cướp. Bug kinh điển "add-on xung đột" mà dev không debug được vì hook bị xóa khỏi registry Anki. Sau 1 năm: hàng loạt issue "bị crash khi cài X".
2. **Đổ mọi thứ vào `__init__.py`**: 674 dòng vừa đăng ký 11 hooks, vừa inject JS/CSS 5 loại webview, vừa logic EXP game hóa, vừa toast/level-bar JS inline. Sau 1 năm: thêm tính năng nào cũng phải động vào file entry point → risk double-registration, order bug (đã thấy dấu hiệu: `inject_menu_files` bị wrap 2 lần ở dòng 643-652).
3. **Settings 9.323 dòng 1 class + config 2 nguồn.** Sau 1 năm: mỗi lần thêm setting mới = sửa 4 chỗ (DEFAULTS JSON, DEFAULTS col.conf, tab dialog, CONFIG_REFERENCE) — và mọi tab đều phải load cả class → mở settings chậm dần theo số tính năng.

---

## 13. 3 quyết định sẽ hối hận sau 3 năm

1. **Không có plugin/module registry**: 40+ tính năng (heatmap, mascot, habit engine, future letter, study tools, EXP, streak...) đều là code bê-tông gắn chặt vào renderer + hooks, không có interface để bật/tắt độc lập. Sau 3 năm: không thể tách "gamification layer" khỏi "theme layer" — mọi người dùng đều phải mang cả đống game hóa dù họ chỉ muốn theme. **Đây là sai lầm kiến trúc lớn nhất.**
2. **Chuỗi thông báo lỗi/UI hard-code tiếng Việt + emoji** trong toàn bộ Station (và Forge dù có i18n vi/en vẫn còn nhiều chuỗi Việt): `"❌ Không mở được Bento Forge"`, `"🎌 SAKURA RPG"`... Sau 3 năm: cộng đồng quốc tế không nhận nuôi được; add-on bị kẹt ở thị trường Việt. Forge đã có `utils/i18n.py` nhưng Station thì không.
3. **Monkey-patch toàn diện thay vì dùng API chính thức của Anki**: gán thẳng `_renderPage`, `_table`, `_body`, `_show_finished_screen`, cướp hook registry. Sau 3 năm: mỗi major Anki update (2.1.x → 2.2, lịch FSRS, engine rewrite) là một cuộc chiến lại — không bền vững như add-on dùng `AnkiWebView` + `gui_hooks` + add-on API.

---

## 14. 3 file quan trọng nhất để tái dựng Bento Station AIOS

1. **`patching.py`** (78 dòng) — Không phải vì nó lớn, mà vì nó chứa **mẫu kiến trúc sống còn**: mọi monkey-patch phải qua `_safe_apply` với guard `hasattr` + log + registry. Tái dựng từ file này = tái dựng được triết lý "không bao giờ crash khi Anki đổi API". Mọi thứ khác có thể viết lại, file này là bộ xương an toàn.
2. **`bento_station_renderer.py`** (1.065 dòng) — Chứa **toàn bộ mô hình UI**: widget grid, hook extern, deck tree build, profile bar, sidebar, mascot, OnigiriEngine JS. Đây là "trái tim" của trải nghiệm Bento Station. Nếu mất file này, Bento Station chỉ còn là một theme-set — mất toàn bộ bản sắc workspace.
3. **`bento_forge_bridge.py`** (464 dòng) — Chứa **mẫu tích hợp hệ thống con**: lazy import, sentinel, fallback, config sync 2 chiều không ghi đè, refresh UI an toàn. Đây là blueprint cho bất kỳ module AI/plugin nào muốn gắn vào mà không làm vỡ add-on chính — và chứng minh rằng Bento Station có thể trở thành một nền tảng thực sự.

> Lựa chọn thay thế hợp lý: `config.py` (trung tâm cấu hình) hoặc `templates.py` (skeleton trang). Nhưng config có thể viết lại dễ, còn patching.py là bài học đã trả giá bằng máu.

---

## Kết luận: "Bento Station AIOS thực chất là gì về mặt kiến trúc?"

**Bento Station AIOS là một *operating system wrapper* — không phải theme, không phải add-on đơn thuần, cũng chưa phải platform hoàn chỉnh.** Nó không chỉ đổi màu giao diện (theme làm được ít hơn), mà **chiếm quyền điều hành toàn bộ vòng đời Anki**: sở hữu renderer (`_renderPage`), sở hữu hook registry (cướp hook add-on khác), sở hữu config 2 tầng, sở hữu UI language riêng (sidebar, widget grid, gamification EXP/level/streak), và quản lý một hệ thống con AI (Bento Forge) như một "process" chạy trong kernel của nó — đúng nghĩa một thin OS chạy phía trên Anki. Tuy nhiên, đây là một OS **monolithic và độc quyền**: mọi thành phần (theme, habit, mascot, study tools, forge) đều được biên dịch cứng vào một lớp patch duy nhất, không có module registry, không có public API cho add-on thứ ba, và xây trên nền cát là monkey-patch internals Anki. Nói thẳng: nó là **một bản fork thực dụng của Onigiri, được mở rộng thành một "AnkiShell" đầy tham vọng** — tham vọng OS thì đúng, nhưng để trở thành platform đích thực, nó cần làm điều mà mọi OS thật đều làm: định nghĩa một **plugin contract** (interface + registry + sandbox) thay vì cướp hook của người khác.