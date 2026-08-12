# 🍱 Bento Station AIOS

> **Trạm học tập All-In-One trên Anki Desktop** — giao diện hiện đại + Xưởng chế tạo thẻ từ vựng bằng AI.

Bento Station AIOS gồm **2 add-on** nối liền trong cùng runtime Anki:

| Module | Vai trò |
|---|---|
| **Bento Station** (add-on chính — repo này) | Thay thế giao diện mặc định Anki: Deck Browser, Overview, Reviewer, Congratulations. Kế thừa & mở rộng add-on **Onigiri** (xem [`CREDITS.md`](CREDITS.md)). |
| **Bento Forge** (add-on độc lập) | Xưởng chế tạo thẻ từ vựng/ngữ pháp **Nhật–Trung–Hàn**: AI trích xuất, TTS, lọc trùng, cache. Là **add-on Anki riêng** nằm tại `addons21/Bento Forge/`, được Station nối qua [`bento_forge_bridge.py`](bento_forge_bridge.py) (xem [`BENTO_FORGE_INTEGRATION.md`](BENTO_FORGE_INTEGRATION.md)). |

**Version:** `1.0.9-beta` · **Anki:** ≥ 2.1.50 · **Python:** ≥ 3.9 · **Thư mục cài đặt:** `%APPDATA%/Anki2/addons21/Bento Station AIOS`

---

## ✨ Tính năng chính

- 🎨 **Giao diện hiện đại hoàn toàn**: sidebar, profile bar, stats grid, heatmap, level bar (EXP), widget linh hoạt theo layout config.
- 🍙 **Animated Mascot**: nhân vật 2D (sprite sheet / Lottie / Rive) — xem [`PROMPT_TEMPLATES.md`](PROMPT_TEMPLATES.md) để tự tạo sprite bằng AI.
- 🎌 **Hệ thống EXP (Sakura RPG)**: cộng EXP khi trả lời thẻ, level bar + toast.
- 🏆 **Habit Engine**: heatmap nỗ lực, gợi ý phiên học, bảo hiểm streak, thư gửi tương lai.
- 🧩 **Bento Forge**: tạo thẻ 3 ngôn ngữ với AI DeepSeek/OpenAI/Ollama, TTS đa engine, Combo Mode (1 từ = 1 card, 5 chế độ học), batch xử lý 50k+ ký tự, Deck Manager, lịch sử AI.
- ⚙️ **Cấu hình theo profile**: `user_files/settings_<profile>.json`.

---

## 🏗️ Cấu trúc dự án (tóm tắt)

```
Bento Station AIOS/           # Add-on chính (repo này)
├── __init__.py              # Entry point — đăng ký toàn bộ gui_hooks
├── bento_station_renderer.py# Engine render Deck Browser (EXP, widget, sidebar)
├── patcher.py / patching.py # SHIM + Patch registry (version-guard Anki API)
├── css/                     # Sinh toàn bộ CSS (package: backgrounds, icons, reviewer, dynamic...)
├── css_engine.py            # SHIM re-export từ css/
├── config.py                # Config loader (cache TTL 1s, profile-specific)
├── settings/                # Settings dialog (package: dialog, widgets, pickers, color_widgets...)
├── study_tools/             # Study Planner, Quick Lookup, Flashcard Gallery, Focus Timer (package)
├── habit_engine.py          # Telemetry, effort score, streak insurance
├── bento_forge_bridge.py    # Cầu nối 1 chiều → Bento Forge (lazy import)
├── webview_router.py        # Xử lý pycmd từ mọi webview
├── web/                     # JS/CSS/HTML inject vào Anki
├── user_files/              # Ảnh nền, avatar, config, sprites, fonts
├── system_files/            # Icons, fonts hệ thống, Coloris, ảnh mặc định
├── tools/                   # Script kiểm tra tham chiếu (patcher)
└── plans/                   # Kế hoạch tính năng

addons21/Bento Forge/         # Add-on ĐỘC LẬP — Xưởng chế tạo thẻ (ngoài repo này)
```

> 📌 Tài liệu phát triển nội bộ (AGENTS.md, CODE_MAP.md, ARCHITECTURE.md, CONFIG_REFERENCE.md, plans/…) **không được publish** trong repo public này.
> Xem thêm: [`Bento Forge/README.md`](Bento%20Forge/README.md).

---

## 📚 Tài liệu (Docs Index)

| File | Nội dung |
|---|---|
| [`Bento Forge/README.md`](Bento%20Forge/README.md) | Docs Bento Forge — Xưởng chế tạo thẻ từ vựng/ngữ pháp. |

---

## 🚀 Cài đặt & sử dụng

1. Đặt thư mục `Bento Station AIOS` vào `%APPDATA%/Anki2/addons21/`.
2. Khởi động lại Anki → menu **"Bento Station"** / **"Onigiri"** trên toolbar.
3. Cấu hình trong **Settings**; cấu hình AI của Forge tại **🧪 Bento Forge → Cài Đặt AI**.
4. Lưu ý: `Bento Forge/utils/ai_config.json` chứa API key **mã hóa** — không commit (chỉ commit `ai_config.example.json`).

---

## 🧪 Kiểm thử

- **Bento Forge**: 344 test (17 file) — `python -m pytest "Bento Forge/tests" -v`.
- **Bento Station (root)**: 35 smoke test (import + runtime call, chạy không cần Anki) — `python -m pytest tests/ -v`.

---

## 📄 License & Ghi nhận

Kế thừa & mở rộng **Onigiri Add-on** (tác giả gốc: Peace). Mã nguồn kế thừa Onigiri giữ nguyên header tri ân.
Phần Bento Forge phát hành theo **MIT** — xem [`Bento Forge/LICENSE`](Bento%20Forge/LICENSE).
