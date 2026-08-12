# 🏗️ Plan: Tái cấu trúc Bento Station AIOS — "Gọn & Có Tổ Chức" với Rủi Ro Thấp

> Quan điểm: **CÓ nên refactor**, nhưng theo kiểu **"di chuyển + SHIM" giữ nguyên hành vi**, KHÔNG viết lại logic, KHÔNG big-bang.

## 1. Vì sao cách này an toàn

- Pattern **"extract → re-export SHIM"** đã có sẵn trong codebase:
  - [`patcher.py`](patcher.py) (1,096) → SHIM cho `css_engine`/`toolbar_styling`/`profile_page`/`webview_router`.
  - [`onigiri_renderer.py`](onigiri_renderer.py) → SHIM cho `bento_station_renderer`.
  - `settings_helpers.py` → đã tách sẵn 1 phần `SettingsDialog` (mixin).
- Có **công cụ kiểm tra tĩnh chạy không cần Anki**: [`tools/check_undefined.py`](tools/check_undefined.py) + [`tools/check_patcher_refs.py`](tools/check_patcher_refs.py).
- Bento Forge đã refactor monolith 2.5k dòng thành công, có 344 test.

## 2. Định nghĩa "Gọn" (mục tiêu đo được)

| Tiêu chí | Hiện tại | Mục tiêu |
|---|---|---|
| File lớn nhất | `settings.py` 11,609 dòng | ≤ ~2,500 dòng |
| File > 1,000 dòng | 4 (`settings`, `css_engine`, `bento_station_renderer`, `patcher`) | 0 |
| 1 module = 1 trách nhiệm | Không rõ | Rõ ràng |

**KHÔNG làm:** gộp file, xóa code, đổi tên symbol, sửa logic trong lúc refactor. **Có làm:** giữ `settings.py`/`css_engine.py` làm SHIM nhẹ để mọi `from .X import ...` cũ vẫn chạy.

---

## 3. Bước 0 — Smoke-test import harness (bắt buộc trước khi tách)

**Lý do:** root không có test tự động → đây là lớp bảo vệ rẻ nhất.
- Tạo `tests/` ở root: `conftest.py` mock `aqt`, `anki`, `mw` (giống Bento Forge) + `test_import_all.py` import từng module, assert không `ImportError`.
- Tách riêng: module thuần (config/themes/constants) test được ngay; module Qt/Anki cần mock.
- **Chấp nhận:** 1 số module gắn chặt `mw`/Qt sẽ cần mock mạnh — nếu quá khó, chí ít đảm bảo chạy được `check_undefined.py` + smoke import cho các module thuần.

---

## 4. Bước 1 — `settings.py` (11,609) → package `settings/`

Phân tích cấu trúc thực tế (đã verify):

| Nhóm | Class/Function (dòng) | Module đích |
|---|---|---|
| Widget nền | `FlowLayout`(49), `ThumbnailWorker`(179), `SelectionOverlay`(235), `CircularColorButton`(276), `AnimatedToggleButton`(307), `ProfileBarWidget`(371), `SidebarToggleButton`(460), `SectionGroup`(527), `ColorSwatch`(559), `FontCardWidget`(984), `SearchResultWidget`(2008) | `settings/widgets.py` |
| Color | `ColorMapWidget`(1093), `GradientSlider`(1176), `HueSlider`(1216), `AlphaSlider`(1226), `FavoriteColorButton`(1254), `ModernColorPickerDialog`(1291) | `settings/color_widgets.py` |
| Picker/Thẻ | `IconPickerDialog`(1585), `ThemeCardWidget`(574), `BirthdayWidget`(877) | `settings/pickers.py` |
| Tìm kiếm | `SettingsSearchPage`(2062) | `settings/search.py` |
| Dialog phụ | `DonationDialog`(2272) | `settings/dialogs.py` |
| **Main** | `SettingsDialog`(2341), `open_settings`(11596) | `settings/dialog.py` |
| Pixel helpers | `create_circular_pixmap`(134), `create_rounded_pixmap`(165) | `settings/pixmap_utils.py` |

- `settings/__init__.py` re-export toàn bộ → mọi `from . import settings` / `from .settings import ...` không đổi.
- **`settings_helpers.py`:** là fragment ORPHAN (không được import, lỗi indent từ trước) → đã XÓA trong cleanup; `SettingsDialog` chứa sẵn các method `_create_*` inline.
- **Verify:** `check_undefined.py` 0 lỗi mới + mở Settings UI trên Anki (đủ 5 tab + search).

---

## 5. Bước 2 — `css_engine.py` (2,041) → package `css/`

Phân tích thực tế:

| Nhóm | Function (dòng) | Module đích |
|---|---|---|
| Background | `_render_background_css`(23), `_generate_outer_background_css`(799), `generate_profile_page_background_css`(176), `generate_deck_browser_backgrounds`(211), `generate_reviewer_background_css`(484), `generate_overview_background_css`(659), `generate_toolbar_background_css`(772), `generate_reviewer_bottom_bar_background_css`(880) | `css/backgrounds.py` |
| Icon | `generate_icon_css`(1099), `generate_icon_size_css`(1064), `generate_conditional_css`(1384), `generate_profile_bar_fix_css`(1004) | `css/icons.py` |
| Font | `generate_font_css`(1403) | `css/fonts.py` |
| Reviewer buttons | `generate_reviewer_buttons_css`(1737) | `css/reviewer.py` |
| Dynamic | `generate_dynamic_css`(1545) | `css/dynamic.py` |
| Utils | `_hex_to_rgba`(1499), `_mix_colors`(1513) | `css/utils.py` |

- `css/__init__.py` re-export toàn bộ; giữ `css_engine.py` SHIM. `patcher.py` (SHIM cũ) vẫn re-export từ `css_engine` → không phải sửa `patcher`.
- **⚠️ Phụ thuộc chéo:** `dynamic.py` có thể dùng `fonts`/helpers → import nội bộ package; tránh circular bằng cách để `utils.py` (pure) import cuối.
- **Verify:** `check_undefined.py` 0 lỗi + Deck Browser/Reviewer/Overview hiển thị đúng.

---

## 6. Bước 3 — `bento_station_renderer.py` (1,387) → tách widget generators

Phân tích thực tế:

| Nhóm | Function (dòng) | Module đích |
|---|---|---|
| EXP/Level bar | `_get_exp_data`(21), `award_exp`(30), `_get_onigiri_level_bar_html`(43), `_get_level_bar_js_refresh`(114) | `widgets/levelbar.py` |
| Stat/Retention | `_get_onigiri_stat_card_html`(280), `_get_sakura_stat_card_html`(284), `_get_onigiri_retention_html`(298) | `widgets/stats.py` |
| Heatmap | `_get_onigiri_heatmap_html`(343) | `widgets/heatmap.py` |
| Session | `_get_onigiri_session_widget_html`(351) | `widgets/session.py` |
| Favorites | `_get_onigiri_favorites_html`(407) | `widgets/favorites.py` |
| **Giữ lại** | `render_bento_station_deck_browser`(507), `_build_sidebar_html`(240), `_get_profile_pic_html`(269), `RenderData`(123) | `bento_station_renderer.py` |

- `bento_station_renderer.py` import các hàm từ `widgets/*` và re-export (giữ namespace cũ cho `__init__.py`/JS pycmd).
- **Verify:** `check_undefined.py` + Deck Browser render đủ widget (EXP, heatmap, favorites, session).

---

## 7. Bước 4 (tùy chọn, rủi ro rất thấp)

- `themes.py` (912) → `themes/` package (dữ liệu thuần `THEMES`, không cần mock).
- `study_tools.py` (840) → tách 4 công cụ thành `study_tools/` (planner/lookup/gallery/timer) nếu muốn gọn hơn nữa.

---

## 8. Quy trình & Rủi ro (bắt buộc mỗi bước)

1. Chạy `tools/check_undefined.py` **trước** (baseline) và **sau** (0 lỗi mới).
2. Chạy `tools/check_patcher_refs.py` nếu bước đụng `patcher.*`.
3. Không đụng phần đăng ký hook trong [`__init__.py`](__init__.py:654).
4. 1 bước = 1 commit; restart Anki + verify UI liên quan trước khi sang bước kế.
5. Cập nhật [`CODE_MAP.md`](CODE_MAP.md) / [`ARCHITECTURE.md`](ARCHITECTURE.md) / [`AGENTS.md`](AGENTS.md) (số dòng/đường dẫn) ngay trong cùng bước.

---

## 9. Todo tổng

- [x] Bước 0: smoke-test import harness (mock aqt/mw) — 33/33 pass
- [x] Bước 1: tách `settings.py` → `settings/` (7 module) + test runtime + sửa lỗi config
- [ ] Bước 1.5 (đề xuất): tách `SettingsDialog` 9.3k dòng → mixin (cần verify Anki thật)
- [x] Bước 2: tách `css_engine.py` → `css/` (6 module, SHIM) + call-test 15 hàm
- [x] Bước 3: tách widget generators → `widgets/` (5 module) — khôi phục BUTTON_HTML từ pyc + call-test sidebar
- [x] Bước 4: tách `themes.py` → `themes/` + `study_tools.py` → `study_tools/` (5 module + router) + call-test
- [x] Cập nhật docs theo từng bước (settings/, css/, widgets/, study_tools/, themes/ đã xong)

## 10. Bài học Bước 3 (rủi ro khi dùng script AST để tách)

Khi tách file bằng script AST cần lưu ý 2 lỗi hệ thống:
1. **Biến module-level bị rơi** (script chỉ trích def/class): mất `BUTTON_HTML`/`_DASHBOARD_*`.
   → Khôi phục từ `__pycache__/*.pyc` cũ (marshal) — chuỗi fragment byte-exact.
2. **Decorator bị rơi** (`node.lineno` của class trỏ tới dòng `class`, KHÔNG phải dòng `@decorator`):
   mất `@dataclass` của `RenderData` → `RenderData()` lỗi "takes no arguments".
   → Sửa thủ công + thêm test instantiate.

Cách tránh: khi tách bằng script, dùng `node.decorator_list` để giữ decorator,
và trích các module-level Assign trước khi ghi đè source.
- Verify: `_build_sidebar_html()` + `RenderData("x")` trong test.
