# study_tools/__init__.py — re-export toàn bộ API (tách từ study_tools.py, Bước 4).
from .shared import (_defaults, get_tools_config, save_tools_config, _get_station_config,
                    _save_station_config, _deep_merge, cards_reviewed_today, cards_reviewed_week,
                    current_streak, is_tools_available)
from .planner import StudyPlannerDialog, open_study_planner, get_planner_widget_html
from .lookup import QuickLookupDialog, open_quick_lookup, get_lookup_widget_html
from .gallery import FlashcardGalleryDialog, ReviewDeckDialog, open_flashcard_gallery, get_gallery_widget_html
from .timer import FocusTimerDialog, open_focus_timer, get_timer_widget_html

def open_tool(tool: str, parent=None):
    """Mở công cụ theo tên: planner | lookup | gallery | timer."""
    fn = {
        "planner": open_study_planner,
        "lookup": open_quick_lookup,
        "gallery": open_flashcard_gallery,
        "timer": open_focus_timer,
    }.get(tool)
    if fn:
        fn(parent)
