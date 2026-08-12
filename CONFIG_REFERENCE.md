# 🍱 Bento Station AIOS — Config Reference (Tham Chiếu Cấu Hình)

> Nguồn chân lý: `DEFAULTS` trong [`config.py`](config.py). Thêm config key mới → cập nhật file này + xem [`AGENTS.md`](AGENTS.md).

Tài liệu này liệt kê **tất cả** config key trong `config.py:DEFAULTS` và các key được lưu trong `mw.col.conf`.

---

## 📂 Cấu trúc config

- **File:** `user_files/settings_{profile_name}.json`
- **Loader:** [`config.py:get_config()`](config.py:366) — merge `DEFAULTS` + file JSON
- **Runtime values:** Một số key lưu trong `mw.col.conf` thay vì file JSON (sidebar width, collapse state, EXP...)

---

## 🔧 Config Keys (`config.py:DEFAULTS`)

### 👤 General

| Key | Type | Default | Mô tả |
|-----|------|---------|--------|
| `userName` | `str` | `"USER"` | Tên hiển thị trên profile bar |
| `statsTitle` | `str` | `"Today's Stats"` | Tiêu đề stats block |
| `studyNowText` | `str` | `"Study Now"` | Text nút "Study Now" trên overview |
| `hideWelcomeMessage` | `bool` | `False` | Ẩn "WELCOME {name}" trong sidebar |
| `userBirthday` | `str` | `""` | Sinh nhật user (YYYY-MM-DD) |
| `lastBirthdayShown` | `str` | `""` | Năm cuối cùng hiển thị birthday popup |

### 🎨 Theme Colors

| Key | Type | Mô tả |
|-----|------|-------|
| `colors.light.{var}` | `str` | Màu cho theme sáng. Variables: `--accent-color`, `--bg`, `--fg`, `--icon-color`, `--fg-subtle`, `--border`, `--highlight-bg`, `--canvas-inset`, `--button-primary-bg`, `--new/learn/review-count-bubble-bg/fg`, `--heatmap-color`, `--star-color`... (xem [`constants.py:ALL_THEME_KEYS`](constants.py:75)) |
| `colors.dark.{var}` | `str` | Màu cho theme tối (cùng variables) |

### 🖼️ Layout

| Key | Type | Mô tả |
|-----|------|-------|
| `hideAllDeckCounts` | `bool` | Ẩn tất cả count cards |
| `hideDeckCounts` | `bool` | Ẩn count cards trong deck list |
| `hideNativeHeaderAndBottomBar` | `bool` | Ẩn header/bottom bar gốc của Anki |
| `proHide` | `bool` | Pro hide mode |
| `maxHide` | `bool` | Max hide mode |
| `flowMode` | `bool` | Flow mode |
| `fullHideMode` | `bool` | Ẩn cả menu bar (Windows/Linux) |
| `sidebarCollapsed` | `bool` | Sidebar collapsed mặc định |

### 📊 Widgets

| Key | Type | Mô tả |
|-----|------|-------|
| `onigiriWidgetLayout.grid` | `dict` | Layout grid cho Onigiri widgets. Key = widget ID (`studied`, `time`, `pace`, `retention`, `heatmap`, `level`, `favorites`), value = `{pos, row, col}` |
| `onigiriWidgetLayout.archive` | `list` | Widgets bị ẩn (vd: `["favorites"]`) |
| `externalWidgetLayout` | `dict` | Layout cho widgets từ add-on khác |
| `sidebarButtonLayout.visible` | `list` | Thứ tự nút sidebar: `["profile","add","browse","stats","sync","settings","more"]` |
| `sidebarButtonLayout.archived` | `list` | Nút bị ẩn |

### 🎌 EXP / Sakura RPG

| Key | Type | Default | Mô tả |
|-----|------|---------|--------|
| `expBarEnabled` | `bool` | `True` | Bật/tắt level bar |
| `expBarTitle` | `str` | `"Onigiri Mastery"` | Tiêu đề level bar |
| `expBarLevelLabel` | `str` | `"LV"` | Nhãn level |
| `expBarNextLevelText` | `str` | `"Next level:"` | Text "Next level" |
| `expBarShowRemaining` | `bool` | `True` | Hiện EXP còn lại |
| `expBarShowPercent` | `bool` | `True` | Hiện phần trăm |

### 🏆 Achievements

| Key | Type | Default | Mô tả |
|-----|------|---------|--------|
| `achievements.enabled` | `bool` | `False` | Bật/tắt achievements |
| `achievements.earned` | `dict` | `{}` | Achievement đã đạt |
| `achievements.history` | `list` | `[]` | Lịch sử |
| `achievements.custom_goals.daily` | `dict` | `{enabled:False, target:100}` | Mục tiêu hàng ngày |
| `achievements.custom_goals.weekly` | `dict` | `{enabled:False, target:700}` | Mục tiêu hàng tuần |

### 🎌 Icon Registry

| Key | Type | Default | Mô tả |
|-----|------|---------|--------|
| `iconSource` | `str` | `"registry"` | `"registry"` (dùng [`icon_registry.py`](icon_registry.py)) hoặc `"file"` (SVG cũ) |
| `iconOverrides` | `dict` | `{}` | Override icon: `{"add":"plus-circle", "browse":"compass"}` |

> **60+ icon:** social (fb, twitter, github, discord...), tech (vscode, figma, docker...), media (spotify, twitch...), UI (home, user, settings, bell, heart...), action (share, download, edit, trash...), navigation, file, commerce, security.
> Xem: [`icon_registry.py`](icon_registry.py) hoặc `icon_registry.list_icons()`.

### 🔥 Heatmap

| Key | Type | Default | Mô tả |
|-----|------|---------|--------|
| `heatmapShape` | `str` | `"square.svg"` | Hình dạng heatmap cell (file SVG trong `system_files/heatmap_system_icons/`) |
| `heatmapShowStreak` | `bool` | `True` | Hiện streak counter |
| `heatmapShowMonths` | `bool` | `True` | Hiện tên tháng |
| `heatmapShowWeekdays` | `bool` | `True` | Hiện thứ trong tuần |
| `heatmapShowWeekHeader` | `bool` | `True` | Hiện header tuần |
| `heatmapDefaultView` | `str` | `"year"` | View mặc định |
| `hideRetentionStars` | `bool` | `False` | Ẩn sao retention |
| `showHeatmapOnProfile` | `bool` | `True` | Hiện heatmap trên profile page |

### 🎌 Animated Mascot

| Key | Type | Default | Mô tả |
|-----|------|---------|--------|
| `animatedMascot.enabled` | `bool` | `False` | Bật/tắt mascot |
| `animatedMascot.mode` | `str` | `"sprite"` | `"sprite"` / `"lottie"` / `"rive"` |
| `animatedMascot.position` | `str` | `"bottom-right"` | Vị trí |
| `animatedMascot.scale` | `float` | `1.0` | Tỉ lệ (0.5-3.0) |
| `animatedMascot.size` | `int` | `150` | Kích thước (px) |
| `animatedMascot.sprite.*` | — | — | Sprite sheet config (idle/happy/sad/celebrate/curious file names, frame_count, frame_width/height, fps) |
| `animatedMascot.lottie.*` | — | — | Lottie file names |
| `animatedMascot.rive.*` | — | — | Rive config |
| `animatedMascot.auto_reactions` | `bool` | `True` | Tự động phản ứng |
| `animatedMascot.click_reaction` | `bool` | `True` | Phản ứng khi click |
| `animatedMascot.hover_reaction` | `bool` | `True` | Phản ứng khi hover |
| `animatedMascot.draggable` | `bool` | `True` | Kéo thả được |
| `animatedMascot.show_in_deck_browser` | `bool` | `True` | Hiện trong deck browser |
| `animatedMascot.show_in_reviewer` | `bool` | `True` | Hiện trong reviewer |
| `animatedMascot.show_in_overview` | `bool` | `True` | Hiện trong overview |

### 🖼️ Reviewer Background

| Key | Type | Default | Mô tả |
|-----|------|---------|--------|
| `onigiri_reviewer_bg_mode` | `str` | `"main"` | `"main"` / `"color"` / `"image_color"` |
| `onigiri_reviewer_bg_main_blur` | `int` | `0` | Blur khi dùng main bg |
| `onigiri_reviewer_bg_main_opacity` | `int` | `100` | Opacity khi dùng main bg |
| `onigiri_reviewer_bg_light_color` | `str` | `"#f2f2f2"` | Màu nền sáng |
| `onigiri_reviewer_bg_dark_color` | `str` | `"#2C2C2C"` | Màu nền tối |
| `onigiri_reviewer_bg_image_mode` | `str` | `"single"` | `"single"` / `"separate"` |
| `onigiri_reviewer_bg_image` | `str` | `""` | Ảnh nền |
| `onigiri_reviewer_bg_image_light` | `str` | `""` | Ảnh nền sáng |
| `onigiri_reviewer_bg_image_dark` | `str` | `""` | Ảnh nền tối |
| `onigiri_reviewer_bg_blur` | `int` | `0` | Blur |
| `onigiri_reviewer_bg_opacity` | `int` | `100` | Opacity |
| `onigiri_reviewer_notification_position` | `str` | `"top-center"` | Vị trí notification |

### 🎯 Reviewer Buttons

| Key | Type | Mô tả |
|-----|------|-------|
| `onigiri_reviewer_btn_custom_enabled` | `bool` | Bật style tùy chỉnh cho nút |
| `onigiri_reviewer_btn_border_size` | `int` | Độ dày border |
| `onigiri_reviewer_btn_radius` | `int` | Bo góc (px) |
| `onigiri_reviewer_btn_padding` | `int` | Padding (px) |
| `onigiri_reviewer_btn_height` | `int` | Chiều cao nút (px) |
| `onigiri_reviewer_bar_height` | `int` | Chiều cao bar (px) |
| `onigiri_reviewer_btn_interval_color_{light,dark}` | `str` | Màu text interval |
| `onigiri_reviewer_btn_border_color_{light,dark}` | `str` | Màu border |
| `onigiri_reviewer_btn_{again,hard,good,easy}_bg_{light,dark}` | `str` | Màu nền nút Again/Hard/Good/Easy |
| `onigiri_reviewer_btn_{again,hard,good,easy}_text_{light,dark}` | `str` | Màu text nút Again/Hard/Good/Easy |
| `onigiri_reviewer_other_btn_{bg,text,hover_bg,hover_text}_{light,dark}` | `str` | Màu cho nút khác (Show Answer, Edit...) |
| `onigiri_reviewer_stattxt_color_{light,dark}` | `str` | Màu text stat (interval) |

### 📝 Reviewer Bottom Bar

| Key | Type | Mô tả |
|-----|------|-------|
| `onigiri_reviewer_bottom_bar_bg_mode` | `str` | `"main"` / `"color"` / `"image"` / `"image_color"` / `"match_reviewer_bg"` |
| `onigiri_reviewer_bottom_bar_bg_{light,dark}_color` | `str` | Màu nền |
| `onigiri_reviewer_bottom_bar_bg_image` | `str` | Ảnh nền |
| `onigiri_reviewer_bottom_bar_bg_blur` | `int` | Blur |
| `onigiri_reviewer_bottom_bar_bg_opacity` | `int` | Opacity |
| `onigiri_reviewer_bottom_bar_match_main_{blur,opacity}` | `int` | Blur/opacity khi match main bg |
| `onigiri_reviewer_bottom_bar_match_reviewer_bg_{blur,opacity}` | `int` | Blur/opacity khi match reviewer bg |

### 🗺️ Overview Background

| Key | Type | Default | Mô tả |
|-----|------|---------|--------|
| `onigiri_overview_bg_mode` | `str` | `"main"` | `"main"` / `"color"` / `"image_color"` |
| `onigiri_overview_bg_main_blur` | `int` | `0` | Blur khi dùng main bg |
| `onigiri_overview_bg_main_opacity` | `int` | `100` | Opacity khi dùng main bg |
| `onigiri_overview_bg_{light,dark}_color` | `str` | — | Màu nền |
| `onigiri_overview_bg_image` | `str` | `""` | Ảnh nền |
| `onigiri_overview_bg_{blur,opacity}` | `int` | `0` / `100` | |

### 🔤 Fonts

| Key | Type | Default | Mô tả |
|-----|------|---------|--------|
| `onigiri_font_main` | `str` | `"system"` | Font chính |
| `onigiri_font_subtle` | `str` | `"system"` | Font phụ |
| `onigiri_font_small_title` | `str` | `"system"` | Font tiêu đề nhỏ |
| `onigiri_font_size_main` | `int` | `14` | Cỡ chữ chính |
| `onigiri_font_size_subtle` | `int` | `20` | Cỡ chữ phụ |
| `onigiri_font_size_small_title` | `int` | `15` | Cỡ chữ tiêu đề nhỏ |

### 🌲 Deck Indentation

| Key | Type | Default | Mô tả |
|-----|------|---------|--------|
| `deck_indentation_mode` | `str` | `"default"` | `"default"` / `"smaller"` / `"bigger"` / `"custom"` |
| `deck_indentation_custom_px` | `int` | `20` | Indent tùy chỉnh (px/level) |

---

## 📦 `mw.col.conf` Keys (Runtime Values)

Các giá trị này được lưu trong Anki collection config, **không** nằm trong file JSON của add-on.

| Key | Type | Mô tả |
|-----|------|-------|
| `modern_menu_sidebar_width` | `int` | Chiều rộng sidebar (px) |
| `onigiri_sidebar_collapsed` | `bool` | Sidebar đang collapsed? |
| `onigiri_deck_focus_mode` | `bool` | Focus mode đang bật? |
| `onigiri_favorite_decks` | `list[int]` | Danh sách deck ID yêu thích |
| `onigiri_exp` | `int` | EXP hiện tại của user |
| `onigiri_pending_exp` | `dict` | EXP pending từ review session |
| `modern_menu_profile_picture` | `str` | Tên file ảnh đại diện |
| `modern_menu_profile_bg_mode` | `str` | `"accent"` / `"image"` / `"custom"` |
| `modern_menu_profile_bg_image` | `str` | Tên file ảnh nền profile bar |
| `modern_menu_background_mode` | `str` | `"color"` / `"image"` / `"image_color"` / `"slideshow"` / `"accent"` |
| `modern_menu_background_image` | `str` | Ảnh nền chính |
| `modern_menu_bg_color_{light,dark}` | `str` | Màu nền chính |
| `modern_menu_background_blur` | `int` | Blur nền chính |
| `modern_menu_background_opacity` | `int` | Opacity nền chính |
| `modern_menu_slideshow_images` | `list[str]` | Ảnh slideshow |
| `modern_menu_slideshow_interval` | `int` | Interval slideshow (giây) |
| `modern_menu_sidebar_bg_mode` | `str` | `"main"` / `"custom"` |
| `modern_menu_sidebar_bg_type` | `str` | `"color"` / `"image"` / `"image_color"` / `"accent"` |
| `modern_menu_sidebar_bg_color_{light,dark}` | `str` | Màu nền sidebar |
| `modern_menu_sidebar_bg_image` | `str` | Ảnh nền sidebar |
| `modern_menu_statsTitle` | `str` | Tiêu đề stats (override) |
| `modern_menu_studyNowText` | `str` | Text "Study Now" (override) |
| `onigiri_overview_style` | `str` | `"pro"` / `"mini"` |
| `onigiri_toolbar_bg_mode` | `str` | `"main"` / `"color"` / ... |
| `onigiri_profile_page_bg_mode` | `str` | `"color"` / `"gradient"` |
| `onigiri_canvas_inset_effect_mode` | `str` | `"none"` / `"opacity"` / `"glassmorphism"` |
| `onigiri_canvas_inset_effect_intensity` | `int` | 0-100 |
| `onigiri_sidebar_main_bg_effect_mode` | `str` | `"opaque"` / `"glassmorphism"` |
| `restaurant_countdown_hour` | `int` | Giờ reset (4 AM mặc định) |
| `restaurant_countdown_minute` | `int` | Phút reset |
