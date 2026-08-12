# 🎌 CREDITS — Ghi Nhận & Tri Ân Tác Giả Gốc

> **Bento Station AIOS is heavily inspired by and built upon the foundation of the
> Onigiri Add-on, created by [Peace — 'the original Onigiri creator'].**
>
> We express our deepest gratitude to the original author for laying the wonderful
> interface architecture that our community continues to build upon.

---

## 🇬🇧 English

### Our Sincere Thanks

**Bento Station AIOS** would not exist without the remarkable work of the original
author of the **Onigiri Add-on** for Anki Desktop.

Onigiri is not merely a theme — it is a complete, thoughtfully-engineered workspace
that reimagines how a learner interacts with Anki. Its clean architecture, its
beautiful deck-browser rendering engine, its modular hook system, and its attention
to visual detail provided the very foundation on which Bento Station AIOS stands
today.

We are honored to inherit, study, and expand upon that foundation. Wherever you see
beauty in Bento Station's interface, much of the credit belongs to the original
Onigiri creator. Our contributions are built with respect for their design
philosophy and in the true spirit of open-source software.

Thank you, Peace, for sharing your vision with the community. ❤️

### License

Bento Station AIOS continues to honor the original license of the Onigiri Add-on.
The original license file is preserved untouched — please read [`LICENSE`](LICENSE)
for the exact terms. Any code, structure, or design inherited from Onigiri remains
under its original license, and our modifications are released under the same terms
to keep the project truly open and collaborative.

If you enjoy Bento Station AIOS, please consider:

- Supporting the original **Onigiri** author and the broader Anki ecosystem.
- Respecting the `# Original code/structure from Onigiri Add-on` attribution
  comments found throughout the source code.

---

## 🇻🇳 Tiếng Việt

### Lời Tri Ân Chân Thành

**Bento Station AIOS** khó có thể tồn tại nếu không có công trình tuyệt vời của tác
giả gốc của **Add-on Onigiri** dành cho Anki Desktop.

Onigiri không đơn thuần là một giao diện — đó là một *không gian làm việc* hoàn
chỉnh, được thiết kế vô cùng tỉ mỉ, tái định nghĩa cách người học tương tác với
Anki. Kiến trúc sạch sẽ, engine hiển thị danh sách bộ bài đẹp mắt, hệ thống hook
mô-đun, cùng sự chăm chút từng chi tiết hình ảnh chính là nền móng mà Bento Station
AIOS đứng vững trên đó ngày hôm nay.

Chúng tôi vinh dự được kế thừa, nghiên cứu và phát triển mở rộng trên nền tảng ấy.
Bất cứ nơi nào bạn thấy vẻ đẹp trong giao diện của Bento Station, phần lớn công lao
thuộc về tác giả Onigiri gốc. Những đóng góp của chúng tôi được xây dựng với sự tôn
trọng triết lý thiết kế của họ và đúng tinh thần của phần mềm mã nguồn mở.

Cảm ơn Peace đã chia sẻ tầm nhìn của mình với cộng đồng. ❤️

### Giấy Phép (License)

Bento Station AIOS tiếp tục tôn trọng giấy phép gốc của Add-on Onigiri. File giấy
phép gốc được giữ nguyên vẹn, không chỉnh sửa — vui lòng đọc [`LICENSE`](LICENSE) để
biết điều khoản chính xác. Mọi mã nguồn, cấu trúc hoặc thiết kế kế thừa từ Onigiri
vẫn thuộc về giấy phép gốc của nó, và các tùy biến của chúng tôi được phát hành
theo cùng điều khoản để dự án luôn cởi mở và hợp tác.

Nếu bạn yêu thích Bento Station AIOS, hãy cân nhắc:

- Ủng hộ tác giả gốc của **Onigiri** và hệ sinh thái Anki nói chung.
- Tôn trọng các chú thích `# Original code/structure from Onigiri Add-on` xuất hiện
  khắp mã nguồn.

---

## 📜 Điểm Truy Cập & Kế Thừa / Inheritance Map

| Thành phần (Component) | Nguồn gốc (Origin) | Ghi chú (Notes) |
|---|---|---|
| Khung giao diện Workspace / Deck Browser renderer | Onigiri Add-on | `bento_station_renderer.py`, `templates.py` |
| Hệ thống Patch & Hook | Onigiri Add-on | `patcher.py`, `patching.py`, `webview_router.py` |
| Hệ thống Cấu hình & Settings | Onigiri Add-on | `config.py`, `settings/` (package), `menu_buttons.py` |
| CSS Engine & Themes | Onigiri Add-on | `css_engine.py` (SHIM), `themes/` (package), `toolbar_styling.py` |
| Bento Forge (Xưởng chế tạo thẻ từ vựng / AI) | Bento Forge (kế thừa từ add-on xưởng không tên) | `Bento Forge/` — được nối vào Bento Station qua `bento_forge_bridge.py` |

---

*Written with respect and gratitude — Ngày 12/08/2026.*
