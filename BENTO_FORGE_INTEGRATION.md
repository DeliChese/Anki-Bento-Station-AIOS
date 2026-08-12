# 🧩 Tích Hợp Bento Forge vào Bento Station AIOS — Tài Liệu Kỹ Thuật

> Bento Station AIOS: **Trạm học tập All-In-One** trên Anki Desktop.
> Bento Forge: **Xưởng chế tạo thẻ từ vựng/ngữ pháp** với AI DeepSeek, lọc trùng, cache.

Tài liệu này mô tả **cách hai module được nối lại thành một hệ thống duy nhất** —
không mở nhiều app, không xung đột Python Runtime / Qt Engine, không cần khởi động lại
Anki khi thẻ mới được đúc xong.

---

## 1. Kiến trúc Tổng Quan

```
┌─────────────────────────────────────────────────────────────────────┐
│              BENTO STATION AIOS (add-on chính)                      │
│                                                                     │
│  ┌──────────────┐   ┌────────────────────────────────────────────┐  │
│  │  __init__.py  │   │  Sidebar (bento_station_renderer.py)       │  │
│  │ setup_global │   │   ▸ Bento Forge  ◄── nút mới                 │  │
│  │ _hooks()     │   │   ▸ More / Settings / ...                   │  │
│  │ profile_open │   └───────────────┬────────────────────────────┘  │
│  └──────┬───────┘                   │ pycmd('openBentoForge')        │
│         │                            ▼                              │
│         │                 ┌─────────────────────┐                  │
│         │                 │ webview_router.py   │                  │
│         │                 │ (xử lý pycmd)       │                  │
│         │                 └──────────┬──────────┘                  │
│         │                            ▼                              │
│         │        ┌──────────────────────────────────────────────┐  │
│         └──────► │   🧩 bento_forge_bridge.py  (BRIDGE SCRIPT)    │  │
│                  │   importlib.import_module("Bento Forge")       │  │
│                  └────────────────────┬─────────────────────────┘  │
│                                       │ (chỉ 1 chiều — không vòng) │
│                                       ▼                            │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  BENTO FORGE  (add-on Anki ĐỘC LẬP — addons21/Bento Forge/)  │  │
│  │  __init__.py → AnkiSmartFactory (Xưởng chế biến)              │  │
│  │  utils/ai_config.json   (API Key / model / cache)             │  │
│  │  utils/ai_cache/        (cache AI)                            │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Vì sao dùng `importlib.import_module`?
Thư mục **"Bento Forge"** chứa **khoảng trắng** trong tên → cú pháp `from Bento Forge import ...`
không hợp lệ trong Python. Bridge dùng `importlib.import_module("Bento Forge")` —
đã kiểm chứng hoạt động bằng `importlib.util.find_spec("Bento Forge")` (resolve đúng
`Bento Forge/__init__.py`).

---

## 2. Các File Đã Tạo & Sửa Đổi

### ✨ Tạo mới
| File | Vai trò |
|---|---|
| [`CREDITS.md`](CREDITS.md) | Lời tri ân tác giả Onigiri gốc (EN + VI), bảng kế thừa |
| [`bento_forge_bridge.py`](bento_forge_bridge.py) | **Bridge script** — import trễ, mở dialog, đồng bộ config, quản lý cache, refresh UI |
| [`BENTO_FORGE_INTEGRATION.md`](BENTO_FORGE_INTEGRATION.md) | Tài liệu tích hợp này |

### 🔧 Sửa đổi
| File | Thay đổi |
|---|---|
| [`__init__.py`](__init__.py) | Header tri ân; import bridge; `initialize_forge()` trong `setup_global_hooks()`; `ensure_config_sync()` + `configure_cache()` trong `on_profile_did_open()` |
| [`menu_buttons.py`](menu_buttons.py) | Header tri ân; submenu **🧪 Bento Forge** (Open / AI Settings / Deck Manager / Clear Cache) |
| [`webview_router.py`](webview_router.py) | Header tri ân; handler `openBentoForge`, `openBentoForgeAI`, `openBentoForgeDecks`, `clearBentoForgeCache` |
| [`bento_station_renderer.py`](bento_station_renderer.py) | Header tri ân; nút `forge` trong `BUTTON_HTML`; tôn trọng `bentoForge.enabled`/`sidebar_button` |
| [`config.py`](config.py) | Header tri ân; thêm `"forge"` vào `sidebarButtonLayout.visible`; section `bentoForge` (API key / cache) trong `DEFAULTS` |
| [`settings/`](settings/) | Header tri ân; đăng ký `"forge"` vào `SidebarLayoutEditor.BUTTON_MAP` + `action_icons_to_configure` |
| [`patcher.py`](patcher.py) | Header tri ân |
| [`templates.py`](templates.py) | Header tri ân |
| [`css_engine.py`](css_engine.py) | Header tri ân |
| [`toolbar_styling.py`](toolbar_styling.py) | Header tri ân |

---

## 3. Điểm Truy Cập (Entrypoints)

### 3.1 Nút trên Sidebar (thanh điều hướng chính)
Khi mở Deck Browser, mục **"Bento Forge"** xuất hiện trên sidebar với các lệnh:

| Lệnh `pycmd` | Chức năng |
|---|---|
| `openBentoForge` | Mở **Xưởng chế biến** (tạo thẻ, AI DeepSeek, lọc trùng, cache) |
| `openBentoForgeAI` | Mở **Cài Đặt AI** (API key, model, temperature, độ dài chunk) |
| `openBentoForgeDecks` | Mở **Deck Manager** (tạo/đổi tên/xóa deck, tự refresh UI) |
| `clearBentoForgeCache` | Xoá toàn bộ cache AI |

### 3.2 Menu chính "Onigiri" → "🧪 Bento Forge"
Tương tự các lệnh trên, được thêm vào menu top-level qua [`menu_buttons.py`](menu_buttons.py).

### 3.3 Phím tắt
Bento Forge vẫn giữ phím tắt **`Ctrl+Shift+I`** (được Forge tự đăng ký khi import qua bridge).

---

## 4. Đồng Bộ Cấu Hình (Một Nơi Duy Nhất)

### Nơi chỉnh sửa
- **Bento Station** đọc config từ `user_files/settings_<profile>.json` (hàm `config.get_config()`).
- Bridge đưa section **`bentoForge`** vào config này → **người dùng chỉnh API key/cache tại một nơi**:
  ```json
  {
    "bentoForge": {
      "enabled": true,
      "sidebar_button": true,
      "api_key": "sk-...",
      "api_base": "https://api.deepseek.com/v1",
      "model": "deepseek-chat",
      "temperature": 0.2,
      "max_tokens": 8192,
      "max_chars": 45000,
      "chunk_size": 8000,
      "reasoning_effort": "",
      "cache_enabled": true,
      "cache_dir": ""
    }
  }
  ```

### Chiến lược đồng bộ (`ensure_config_sync`)
| Trường hợp | Hành vi |
|---|---|
| Station có `api_key` (khác rỗng) | **PUSH** toàn bộ section lên `Bento Forge/utils/ai_config.json` (qua `save_api_config` — giữ nguyên mã hoá Fernet/XOR của Forge) |
| Station **chưa** đặt key | **PULL** cấu hình thật của Forge về Station (chỉ để "thấy một nơi"), KHÔNG đẩy ngược → không ghi đè cấu hình user đã chỉnh trong Cài Đặt AI |

> ⚠️ **Không ghi đè mất dữ liệu:** Nếu bạn từng cấu hình OpenAI/Ollama trong Cài Đặt AI
> của Forge và **chưa** đặt key ở Station, cấu hình đó vẫn nguyên vẹn và được kéo về Station.

### Cache
- `cache_enabled`: bật/tắt việc tạo cache AI.
- `cache_dir`: nếu để trống → dùng mặc định `Bento Forge/utils/ai_cache/`; nếu đặt đường dẫn
  tùy chỉnh → bridge gán vào `ai_extractor._CACHE_DIR` khi mở profile.

---

## 5. Luồng Dữ Liệu — Thẻ Mới Không Cần Restart

Khi người dùng "đúc" xong thẻ trong Xưởng chế biến:

```
AnkiSmartFactory → ImportWorker (Bento Forge/__init__.py)
        │
        ├─► mw.col.addNote(...)   (ghi thẳng vào collection Anki)
        │
        ├─► invalidate_deck_cache()   (xoá cache từ vựng deck)
        │
        └─► mw.reset()  ← Forge TỰ gọi sau import (_on_import_finished)
                │
                └─► Deck Browser + Review cập nhật NGAY, không cần restart
```

Bridge bổ sung thêm `refresh_anki_ui()` (gọi `mw.reset()` + `mw.deckBrowser.refresh()`)
để chắc chắn danh sách deck + số thẻ hiển thị tức thì. Bạn có thể gọi thủ công:

```python
import bento_forge_bridge
bento_forge_bridge.refresh_anki_ui()
```

---

## 6. Chống Lỗi Import Vòng (Circular Import) & ModuleNotFoundError

- **Import 1 chiều duy nhất:** Station → Forge. Forge **không bao giờ** import ngược Bento Station.
- **Lazy import:** `bento_forge_bridge.py` chỉ import Forge khi thực sự cần
  (`open_forge`, `initialize_forge`, ...) — không import ở module load.
- **Chống sập:** mọi lời gọi Forge đều bọc `try/except`; nếu Forge thiếu hoặc lỗi,
  Bento Station vẫn khởi động bình thường, menu Forge bị ẩn và hiện thông báo thân thiện.
- **Đảm bảo sys.path:** bridge chèn thư mục `addons21` vào `sys.path` để
  `importlib.import_module("Bento Forge")` resolve được — dù Forge là add-on độc lập
  (Anki cũng tự thêm thư mục add-on vào sys.path khi load).

---

## 7. Khắc Phục Sự Cố (Troubleshooting)

| Vấn đề | Nguyên nhân / Cách xử lý |
|---|---|
| Không thấy menu/nút "Bento Forge" | Forge không import được → kiểm tra thư mục `Bento Forge` tồn tại đúng tên, có `__init__.py`, không thiếu dependency (`edge-tts`, `gtts`). Mở Anki Console (Tools → Debug) để xem lỗi. |
| Bento Station không khởi động được | Không liên quan bridge (bridge đã chống lỗi). Kiểm tra log Anki (`Help → Debug`) cho các lỗi khác. |
| API key không có tác dụng | Mở **Cài Đặt AI** (menu Bento Forge) và đặt key; hoặc đặt `api_key` trong section `bentoForge` của `user_files/settings_<profile>.json` rồi khởi động lại Anki. |
| Thẻ mới không hiện trong deck | Thẻ đã ghi vào collection nhưng UI chưa refresh → bấm **Clear AI Cache** rồi mở lại Deck Browser, hoặc gọi `bento_forge_bridge.refresh_anki_ui()` từ console. |
| Xung đột phím tắt `Ctrl+Shift+I` | Nếu addon khác chiếm phím này, đổi shortcut trong `Bento Forge/__init__.py` (dòng tạo `action`). |

---

## 8. Ghi Nhận Tác Giả (Compliance)
- File [`CREDITS.md`](CREDITS.md) ghi rõ nguồn gốc Onigiri và lời tri ân (EN + VI).
- Các file kế thừa Onigiri đều có header:
  `# Original code/structure from Onigiri Add-on. Customized and expanded for Bento Station AIOS.`
- Giữ nguyên giấy phép gốc (xem [`LICENSE`](LICENSE) — file Onigiri gốc không bị chỉnh sửa).
