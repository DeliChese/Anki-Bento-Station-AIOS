# 📋 Các Prompt Đã Soạn Sẵn — Copy-Paste Là Dùng

> Dành cho người dùng không rành kỹ thuật: **chọn đúng phase bạn đang làm, copy cả khối prompt, dán vào Codex/ChatGPT, nhấn Enter.** Không cần sửa gì (trừ khi có dòng ghi "TÙY CHỈNH").
> Nhớ: bạn đã dán instruction cá nhân hóa 1 lần trong phần Personalization — phần này chỉ là prompt gõ mỗi phiên.

---

## ▶️ PROMPT PHASE 1 — Định ranh giới module

```text
[Phase 1] — Định ranh giới các module theo ARCHITECT.md

- Mục tiêu: tạo tài liệu interface cho từng module (trách nhiệm + được phép import ai), không sửa code
- Module đích: Station, Dynamo, Forge, Express, Archives
- Loại: docs
- Phạm vi đề xuất: cập nhật ARCHITECT.md và/hoặc tạo file docs/interface-*.md
- Restart Anki: không
- Verify: không cần chạy check; chỉ đối chiếu với CODE_MAP.md cho đúng
- Tiến hành luôn, không cần confirm lại scope.
```

---

## ▶️ PROMPT PHASE 2 — Tạo Module Manager

```text
[Phase 2] — Tạo module_manager.py và cho phép bật/tắt module qua Settings

- Mục tiêu: tạo registry BentoModule (id, name, enabled, restart_required, load, unload); thêm config enabledModules; __init__.py chỉ nạp module đang bật (lazy import qua importlib)
- Module đích: Station
- Loại: feature (giữ mọi hook hiện tại, không đổi hành vi)
- Phạm vi đề xuất: station/module_manager.py (file mới), config.py, __init__.py, CONFIG_REFERENCE.md
- Restart Anki: có (thay đổi cách khởi động)
- Verify: check_undefined.py + pytest + restart Anki xác nhận không crash
- Tiến hành luôn, không cần confirm lại scope.
```

---

## ▶️ PROMPT PHASE 3 — Cho Forge tùy chọn (chạy được khi không có Forge)

```text
[Phase 3] — Đảm bảo Bento Station chạy bình thường khi tắt hoặc không có add-on Bento Forge

- Mục tiêu: bento_forge_bridge.py kiểm tra enabledModules.forge; không import gì từ Forge khi tắt/thiếu; menu Forge ẩn hoặc disabled
- Module đích: Station (cầu nối Forge)
- Loại: refactor nhỏ (guard + lazy import), không đổi logic Forge
- Phạm vi đề xuất: bento_forge_bridge.py, __init__.py (chỗ khởi tạo Forge), có thể settings/ để hiện công tắc
- Restart Anki: có (đổi khởi động)
- Verify: check_undefined.py + check_patcher_refs.py + pytest; nếu có thể, gỡ tạm thư mục Bento Forge và khởi động Anki kiểm tra
- Tiến hành luôn, không cần confirm lại scope.
```

---

## ▶️ PROMPT PHASE 4 — Tách Dynamo (toàn bộ phần UI)

```text
[Phase 4] — Gom toàn bộ phần giao diện vào package dynamo/

- Mục tiêu: di chuyển renderer, templates, deck_tree, css, themes, fonts, toolbar_styling, profile_page, mascot, icon_registry, widgets, web/* vào dynamo/; các file cũ giữ làm SHIM re-export
- Module đích: Dynamo
- Loại: move+SHIM (KHÔNG đổi logic render)
- Phạm vi đề xuất: tạo dynamo/, di chuyển theo bảng trong ARCHITECT.md, giữ SHIM ở file gốc
- Restart Anki: có (đổi import + inject)
- Verify: check_undefined.py + pytest + restart Anki kiểm tra Deck Browser/Reviewer/Overview hiển thị đúng
- Trình scope trước khi sửa (task rủi ro ở renderer), sau khi tôi duyệt thì tiến hành.
```

---

## ▶️ PROMPT PHASE 5 — Tách Express (học tập hằng ngày)

```text
[Phase 5] — Gom study tools, habit engine, heatmap, future letter và hệ EXP vào package express/

- Mục tiêu: di chuyển study_tools/, habit_engine.py, heatmap.py, future_letter_dialog.py, levelbar (EXP) vào express/; dời logic EXP ra khỏi __init__.py; giữ SHIM
- Module đích: Bento Express
- Loại: move+SHIM (KHÔNG đổi logic)
- Phạm vi đề xuất: tạo express/, di chuyển theo bảng trong ARCHITECT.md; __init__.py chỉ còn hook registry + bootstrap
- Restart Anki: có
- Verify: check_undefined.py + pytest + restart Anki kiểm tra level bar/heatmap/study tools vẫn hoạt động
- Trình scope trước khi sửa (đụng __init__.py và inject), sau khi tôi duyệt thì tiến hành.
```

---

## ▶️ PROMPT PHASE 6 — Tách Archives (lưu trữ)

```text
[Phase 6] — Gom phần lưu trữ vào package archives/

- Mục tiêu: tạo archives/ chứa AI history, templates, prompt presets, field-map presets, import/export, backup; tách dữ liệu khỏi UI; đảm bảo favorites_cleanup.py và dữ liệu user_files nằm gọn
- Module đích: Bento Archives
- Loại: move+SHIM + thêm helper import/export/backup
- Phạm vi đề xuất: tạo archives/, di chuyển theo bảng trong ARCHITECT.md
- Restart Anki: không chắc — yêu cầu xác nhận
- Verify: check_undefined.py + pytest; kiểm tra import/export preset đúng định dạng
- Tiến hành luôn, không cần confirm lại scope.
```

---

## ▶️ PROMPT PHASE 7 — Public beta (an toàn tổng thể)

```text
[Phase 7] — Chuẩn bị public beta: rà soát an toàn khi tắt từng module

- Mục tiêu: với mỗi module (Dynamo, Forge, Express, Archives), kiểm tra Bento Station vẫn khởi động và hoạt động khi module đó bị tắt; xử lý hook-cướp take_control_of_deck_browser_hook nếu còn; rà soát không commit dữ liệu runtime
- Module đích: tất cả
- Loại: kiểm tra + sửa rủi ro
- Phạm vi đề xuất: module_manager.py, bento_forge_bridge.py, patcher.py (hook-cướp), .gitignore
- Restart Anki: có
- Verify: check_undefined.py + check_patcher_refs.py + pytest + restart Anki tắt từng module
- Trình scope trước khi sửa (nhiều phần rủi ro), sau khi tôi duyệt thì tiến hành.
```

---

## ▶️ PROMPT SỬA LỖI (dùng khi gặp bug)

```text
[Fix] — <mô tả ngắn lỗi đang gặp, ví dụ: Deck Browser bị vỡ giao diện, settings không mở được...>

- Mục tiêu: sửa lỗi trên, giữ nguyên các tính năng khác
- Module đích: <tên module liên quan, nếu không chắc thì để AI tự xác định>
- Loại: bugfix
- Phạm vi đề xuất: <để trống, yêu cầu AI tìm phạm vi tối thiểu>
- Restart Anki: chưa chắc — yêu cầu xác nhận
- Verify: check_undefined.py + pytest + restart Anki kiểm tra lỗi hết
- Trình scope trước khi sửa.
```

---

## ▶️ PROMPT CẬP NHẬT TÀI LIỆU

```text
[Docs] — Cập nhật tài liệu sau khi đã tách module

- Mục tiêu: cập nhật CODE_MAP.md (file + số dòng thực tế), ARCHITECTURE.md, AGENTS.md, và CONFIG_REFERENCE.md nếu có config mới
- Module đích: — (không đụng code)
- Loại: docs
- Phạm vi đề xuất: CODE_MAP.md, ARCHITECTURE.md, AGENTS.md, CONFIG_REFERENCE.md
- Restart Anki: không
- Verify: đối chiếu số dòng thực tế bằng search_files
- Tiến hành luôn, không cần confirm lại scope.
```

---

## 💡 Cách dùng (3 bước, cho người không rành kỹ thuật)

1. **Chọn đúng khối prompt** của phase bạn đang làm (ví dụ đang làm Phase 2 thì copy khối `PROMPT PHASE 2`).
2. **Dán nguyên khối** vào Codex/ChatGPT, nhấn Enter.
3. **Trả lời nếu AI hỏi** — AI sẽ hỏi 1-2 câu đơn giản hoặc trình scope cho bạn duyệt; bạn chỉ cần nói **"ok, tiến hành"** hoặc **"đúng vậy"**.

**Lưu ý nhỏ:**
- Sau khi AI xong 1 phase → chạy lại khối `PROMPT CẬP NHẬT TÀI LIỆU` để docs luôn đúng.
- Gặp lỗi bất kỳ → dùng khối `PROMPT SỬA LỖI`, chỉ cần gõ 1 câu mô tả lỗi vào chỗ `<>`.
- Mỗi phiên chỉ làm 1 việc. Xong việc này hãy mở phiên mới làm việc kế tiếp.
