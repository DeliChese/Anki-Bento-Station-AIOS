# 🎌 Hướng Dẫn Tạo Sprite Assets Bằng AI (Gemini, ChatGPT, Imagen...)

Tài liệu này hướng dẫn cách dùng AI tạo sprite sheet cho nhân vật 2D chuyển động trong Onigiri Nakama.

---

## ⚠️ Quan Trọng: Cách AI Tạo Animation

Các model AI hiện tại (kể cả Gemini 2.5 Pro, ChatGPT-4o, Imagen) **KHÔNG tạo được video** hay **file Lottie JSON** trực tiếp từ prompt. Nhưng chúng **CÓ THỂ** tạo **sprite sheet** — một ảnh PNG chứa nhiều frame.

### Nguyên lý: `1 ảnh = 1 animation`

Mỗi animation (idle, happy, sad...) là **MỘT ảnh PNG** chứa tất cả các frame xếp theo hàng ngang.

```  
Ảnh idle:  [frame0][frame1][frame2][frame3][frame4][frame5][frame6][frame7]
            ←────────────── 1024px ──────────────────────────────────→
            Mỗi frame = 128×128px
```

---

## 📝 Prompt Mẫu (Tiếng Anh — cho AI)

> **Lưu ý:** Dùng tiếng Anh cho prompt sẽ cho kết quả tốt hơn. Dịch tiếng Việt bên dưới.

### Prompt #1: Nhân vật Onigiri (cơm nắm) — Idle Animation

```
Generate a horizontal sprite sheet with exactly 8 frames for a cute kawaii anime-style 
onigiri (rice ball) mascot character in an idle bouncing animation.

TECHNICAL REQUIREMENTS (MUST FOLLOW EXACTLY):
- Total image size: exactly 1024×128 pixels
- Each frame: exactly 128×128 pixels (8 frames × 128px = 1024px wide)
- Frames must be arranged in a single horizontal row, touching edge-to-edge with NO gaps
- Background must be TRANSPARENT (no white background)
- The spacing between frames must be ZERO pixels

ART STYLE:
- Cute kawaii anime chibi style
- Pastel colors: soft pink, light cream, and gentle blue
- Clean cel-shaded outlines (thin, consistent line art)
- Soft gradient shading, not flat colors
- The character should have: a cute face (^_^ eyes), small blush marks, tiny arms/legs
- Wrapped in a small green nori (seaweed) band

ANIMATION (idle/bouncing):
- Frame 0: Neutral standing pose
- Frame 1: Slight squash down (preparing to bounce)
- Frame 2: Stretched upward (rising)
- Frame 3: Peak of bounce (slightly airborne, ears flapping)
- Frame 4: Floating at max height
- Frame 5: Starting to fall
- Frame 6: Landing with squash
- Frame 7: Recovering back to neutral

The animation should loop seamlessly: frame 7 should flow back into frame 0 naturally.
```

### Prompt #2: Nhân vật Onigiri — Happy Animation

```
Generate a horizontal sprite sheet with exactly 8 frames for the SAME cute onigiri mascot 
character in a HAPPY/excited celebration animation.

TECHNICAL REQUIREMENTS (MUST FOLLOW EXACTLY):
- Total image size: exactly 1024×128 pixels
- Each frame: exactly 128×128 pixels (8 frames in a single horizontal row)
- NO gaps between frames
- Background must be TRANSPARENT
- Same art style and character design as the idle sprite

HAPPY ANIMATION (celebrating):
- Frame 0: Character looking up with sparkle eyes
- Frame 1: Arms raised halfway, slight smile
- Frame 2: Arms fully raised, big open-mouth smile, small hearts floating
- Frame 3: Jumping up slightly, arms waving
- Frame 4: Mid-air, star particles around, biggest smile
- Frame 5: Landing with arms spread wide
- Frame 6: Bouncing on heels, hands on cheeks blushing
- Frame 7: Settling back, arms down but still big smile
```

### Prompt #3: Nhân vật Onigiri — Sad Animation

```
Generate a horizontal sprite sheet with exactly 8 frames for the SAME cute onigiri mascot 
character in a SAD/disappointed animation.

TECHNICAL REQUIREMENTS:
- Total image size: exactly 1024×128 pixels
- Each frame: exactly 128×128 pixels, single horizontal row, NO gaps
- Background: TRANSPARENT
- Same art style and character as idle/happy sprites

SAD ANIMATION:
- Frame 0: Neutral/slightly worried, sweat drop visible
- Frame 1: Head tilting down, eyes half-closed
- Frame 2: Shoulders drooping, small tear forming
- Frame 3: Full sad face, tear rolling down, trembling slightly
- Frame 4: Looking down at ground, arms limp, tear drop falling
- Frame 5: Small sniffle, rubbing eye with tiny hand
- Frame 6: Slight recovery, still teary-eyed but looking up
- Frame 7: Back to worried/neutral but with residual tear marks
```

### Prompt #4: Nhân Vật Anime (Pet/Familiar) — Tổng Quát

```
Generate a horizontal sprite sheet for a 2D pixel-art / chibi anime pet character.

CHARACTER: [MÔ TẢ NHÂN VẬT CỦA BẠN]
- Ví dụ: "a small fox spirit with nine tails and glowing blue eyes"
- Ví dụ: "a chibi dragon with round body and tiny wings"
- Ví dụ: "a cat familiar wearing a witch hat"

TECHNICAL:
- Exactly 8 frames in one horizontal row
- Total: 1024×128 pixels, each frame 128×128px
- No gaps between frames
- TRANSPARENT background

ANIMATION STATE: [idle/happy/sad/celebrate]
- [Mô tả chuyển động bạn muốn, như các prompt trên]
```

---

## 🇻🇳 Prompt Mẫu (Tiếng Việt)

### Prompt #1 — Idle (tiếng Việt)

```
Tạo một sprite sheet ngang với đúng 8 khung hình cho nhân vật linh vật onigiri 
(cơm nắm) phong cách anime kawaii dễ thương, đang thực hiện animation đứng yên nhún nhảy.

YÊU CẦU KỸ THUẬT (PHẢI TUÂN THỦ CHÍNH XÁC):
- Kích thước tổng: chính xác 1024×128 pixel
- Mỗi khung hình: chính xác 128×128 pixel (8 khung × 128px = 1024px chiều rộng)
- Các khung hình xếp thành 1 hàng ngang duy nhất, liền kề không khoảng cách
- Nền PHẢI TRONG SUỐT (transparent), không được có nền trắng
- Khoảng cách giữa các khung hình: 0 pixel

PHONG CÁCH:
- Anime chibi kawaii dễ thương
- Màu pastel nhẹ nhàng
- Đường viền mảnh, sạch sẽ
- Nhân vật có: mặt dễ thương (^_^), má hồng, tay chân nhỏ xíu
- Có dải rong biển (nori) xanh bọc quanh

ANIMATION (đứng yên nhún nhảy):
- Khung 0: Đứng thẳng bình thường
- Khung 1: Hơi nén xuống chuẩn bị nhún
- Khung 2: Vươn lên
- Khung 3: Đỉnh nhún (hơi bay lên)
- Khung 4: Lơ lửng ở độ cao nhất
- Khung 5: Bắt đầu rơi xuống
- Khung 6: Tiếp đất, nén xuống
- Khung 7: Hồi phục về trạng thái bình thường

Animation phải mượt và lặp lại liền mạch.
```

---

## 🔧 Tool Hỗ Trợ Xử Lý Sprite

### 1. Kiểm tra sprite sheet
Mở ảnh bằng bất kỳ tool xem ảnh nào, zoom vào để kiểm tra:
- Các frame có đều nhau không?
- Có khoảng trắng giữa các frame không?
- Nền có trong suốt không?

### 2. Cắt/gộp sprite sheet
- **ImageMagick** (dòng lệnh): `convert input.png -crop 128x128 frame_%d.png`
- **Aseprite** (trả phí): Tool chuyên cho pixel art & sprite
- **Piskel** (miễn phí, online): https://www.piskelapp.com/
- **SpriteSheetPacker** (miễn phí): Gộp nhiều frame thành 1 sheet

### 3. Tạo Lottie animation
- **After Effects** + plugin **Bodymovin** (xuất JSON)
- **LottieFiles** (online editor): https://lottiefiles.com/
- **Rive** (online, miễn phí): https://rive.app/ — tạo animation vector tương tác

---

## 🚀 Pipeline Khuyến Nghị

```
Bước 1: Dùng Gemini/ChatGPT tạo sprite sheet PNG
        ↓
Bước 2: Kiểm tra ảnh (cắt đều, nền trong suốt, đủ frame)
        ↓
Bước 3: Lưu vào user_files/sprites/ với tên phù hợp
        (VD: mascot_idle.png, mascot_happy.png)
        ↓
Bước 4: Vào Onigiri Settings → Animated Mascot → Bật + chọn file
        ↓
Bước 5: Mở Anki → Nhìn mascot chuyển động! 🎉
```

---

## ❓ FAQ

**Q: Tại sao AI không tạo được file video/GIF/Lottie?**
A: Các model hiện tại sinh ảnh tĩnh (static image generation). Chúng không có khả năng xuất video, JSON animation, hay GIF. Sprite sheet là giải pháp thay thế: bạn mô tả tất cả frame chuyển động trong prompt, AI vẽ chúng thành 1 ảnh.

**Q: Tôi có thể dùng GIF có sẵn không?**
A: Có! Dùng tool như `ezgif.com/split` để tách GIF thành các frame, rồi dùng ImageMagick hoặc SpriteSheetPacker để gộp thành sprite sheet ngang.

**Q: Làm sao để tạo Lottie/Rive?**
A: AI không tạo được Lottie JSON. Bạn cần dùng After Effects + Bodymovin, hoặc Rive editor (rive.app — miễn phí). Đây là tool thiết kế animation chuyên dụng, không phải AI.

**Q: Sprite sheet của tôi bị "nhảy" khi chuyển frame?**
A: Đảm bảo tất cả frame có kích thước bằng nhau, vị trí nhân vật nhất quán giữa các frame, và không có khoảng trắng giữa các frame.

**Q: Tôi muốn tạo nhiều nhân vật khác nhau thì sao?**
A: Tạo các sprite sheet riêng cho từng nhân vật, đặt tên file khác nhau (VD: `cat_idle.png`, `fox_idle.png`), và chuyển đổi qua settings.
