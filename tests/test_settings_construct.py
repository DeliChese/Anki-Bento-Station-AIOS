"""Runtime smoke test cho SettingsDialog sau khi tách settings/ package.

Bắt lỗi NameError/import thiếu KIỂU RUNTIME (khi __init__ chạy) — loại lỗi mà
check_undefined (tĩnh) có thể bỏ sót (vd `from ..config import DEFAULTS` không
bind tên module `config`, nhưng code gọi `config.get_config()`).

Chỉ chạy khi dùng STUB (môi trường không có PyQt thật): với PyQt thật, việc
dựng QDialog cần QApplication — nên bỏ qua (verify bằng Anki thật).
"""
from __future__ import annotations

import importlib.util

import pytest

def _has_real_qt() -> bool:
    """PyQt thật có sẵn? (stub trong sys.modules có __spec__=None → find_spec lỗi)."""
    for name in ("PyQt6", "PyQt5"):
        try:
            if importlib.util.find_spec(name) is not None:
                return True
        except ValueError:
            pass  # module stub (__spec__ None)
    return False


USING_STUBS = not _has_real_qt()


@pytest.mark.skipif(not USING_STUBS, reason="Cần stub Qt — verify bằng Anki thật")
def test_settings_dialog_constructs():
    import importlib

    s = importlib.import_module("bento_station.settings")
    # Dựng toàn bộ dialog (__init__ chạy mọi config.get_config()/widget builder)
    dlg = s.SettingsDialog(None, ".")
    assert hasattr(dlg, "current_config")
