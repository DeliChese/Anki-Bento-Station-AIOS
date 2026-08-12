"""
═══════════════════════════════════════════════════════════════
 onigiri_renderer.py  —  COMPATIBILITY SHIM (đã đổi tên)
 ===============================================================

 File renderer chính đã được đổi tên thành `bento_station_renderer.py`
 để đồng bộ hệ sinh thái "Bento Station AIOS".

 File này CHỈ tồn tại để giữ tương thích ngược: nếu addon/tool bên ngoài
 vẫn thực hiện `from onigiri_renderer import ...`, chúng sẽ tiếp tục hoạt
 động thay vì gây ModuleNotFoundError.

 Original code/structure from Onigiri Add-on. Customized and expanded
 for Bento Station AIOS.
═══════════════════════════════════════════════════════════════
"""
# Tái xuất toàn bộ API công khai từ module mới.
from .bento_station_renderer import *  # noqa: F401,F403
# Alias giữ tên hàm renderer cũ hoạt động với code lạc hậu.
from .bento_station_renderer import (
    render_bento_station_deck_browser as render_onigiri_deck_browser,
)  # noqa: F401
