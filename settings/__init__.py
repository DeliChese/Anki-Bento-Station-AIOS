# settings/__init__.py — re-export toàn bộ API cũ (tách từ settings.py).
# Giữ tương thích: `from . import settings` / `from .settings import X` vẫn hoạt động.
from .pixmap_utils import create_circular_pixmap, create_rounded_pixmap
from .widgets import (FlowLayout, ThumbnailWorker, SelectionOverlay, CircularColorButton,
                      AnimatedToggleButton, ProfileBarWidget, SidebarToggleButton,
                      SectionGroup, ColorSwatch, BirthdayWidget, FontCardWidget,
                      SearchResultWidget)
from .color_widgets import (ColorMapWidget, GradientSlider, HueSlider, AlphaSlider,
                            FavoriteColorButton, ModernColorPickerDialog)
from .pickers import ThemeCardWidget, IconPickerDialog
from .search import SettingsSearchPage
from .dialogs import DonationDialog
from .dialog import (SettingsDialog, open_settings,
                     THUMBNAIL_STYLE, THUMBNAIL_STYLE_SELECTED, CUSTOM_GOAL_COOLDOWN_SECONDS)
# Lưu ý: ThumbnailWorker nằm trong .widgets (import ở trên), KHÔNG lặp lại ở đây.

__all__ = [
    'FlowLayout', 'ThumbnailWorker', 'SelectionOverlay', 'CircularColorButton',
    'AnimatedToggleButton', 'ProfileBarWidget', 'SidebarToggleButton', 'SectionGroup',
    'ColorSwatch', 'BirthdayWidget', 'FontCardWidget', 'SearchResultWidget',
    'ColorMapWidget', 'GradientSlider', 'HueSlider', 'AlphaSlider', 'FavoriteColorButton',
    'ModernColorPickerDialog', 'ThemeCardWidget', 'IconPickerDialog', 'SettingsSearchPage',
    'DonationDialog', 'SettingsDialog', 'open_settings', 'create_circular_pixmap',
    'create_rounded_pixmap', 'THUMBNAIL_STYLE', 'THUMBNAIL_STYLE_SELECTED',
    'CUSTOM_GOAL_COOLDOWN_SECONDS',
]
