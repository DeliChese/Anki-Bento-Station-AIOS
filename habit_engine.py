"""
Onigiri Habit Engine — tầng dữ liệu chung cho các tính năng duy trì thói quen.

GĐ1 (hiện tại): Effort-Adjusted Heatmap
  - get_daily_telemetry():  telemetry mỗi ngày từ bảng revlog (count, time, độ đúng, độ khó)
  - get_effort_data():       effort score 0-100 mỗi ngày (thời gian + độ đúng + độ khó)

Dùng chung logic timezone/rollover với heatmap.py để nhất quán giữa các widget.
Dữ liệu được cache với TTL ngắn để tránh query lại DB mỗi lần render deck browser.
"""

import time
from datetime import datetime
from aqt import mw
from . import config

# ── Cache ──────────────────────────────────────────────────────────────
_TELEMETRY_CACHE = {"data": None, "ts": 0.0}
_TELEMETRY_TTL = 10.0  # giây
_STREAK_CONF_CACHE = {"enabled": True, "ratio": 1.2, "ts": 0.0}
_STREAK_CONF_TTL = 20.0  # giây — tránh đọc config từ disk mỗi lần trả lời thẻ (hot path)

def invalidate_cache():
    """Xoá cache telemetry — gọi khi có review mới để dữ liệu hôm nay luôn tươi."""
    _TELEMETRY_CACHE["data"] = None
    _TELEMETRY_CACHE["ts"] = 0.0

def _streak_config():
    """Đọc streakInsuranceEnabled + streakTokenThresholdRatio với cache TTL ngắn."""
    now = time.time()
    if now - _STREAK_CONF_CACHE["ts"] > _STREAK_CONF_TTL:
        try:
            c = config.get_config()
            _STREAK_CONF_CACHE["enabled"] = c.get("streakInsuranceEnabled", True)
            _STREAK_CONF_CACHE["ratio"] = c.get("streakTokenThresholdRatio", 1.2)
        except Exception:
            _STREAK_CONF_CACHE["enabled"] = True
            _STREAK_CONF_CACHE["ratio"] = 1.2
        _STREAK_CONF_CACHE["ts"] = now
    return _STREAK_CONF_CACHE


# ── Bối cảnh thời gian (giống heatmap.py) ─────────────────────────────
def _get_rollover_context():
    """Trả về các giá trị thời gian dùng chung (rollover hour, offset, start of today)."""
    if not mw.col:
        return 4, 14400, 0
    rollover_hour = mw.col.conf.get("rollover", 4)
    offset_seconds = rollover_hour * 3600
    day_cutoff_seconds = mw.col.sched.day_cutoff
    today_start_seconds = day_cutoff_seconds - 86400
    return rollover_hour, offset_seconds, today_start_seconds


def get_today_date_key():
    """Ngày hôm nay theo localtime + rollover (YYYY-MM-DD)."""
    if not mw.col:
        return ""
    _, _, today_start_seconds = _get_rollover_context()
    return datetime.fromtimestamp(today_start_seconds).strftime('%Y-%m-%d')


# ── Telemetry theo ngày ────────────────────────────────────────────────
def get_daily_telemetry():
    """
    Truy vấn revlog JOIN cards, nhóm theo ngày local (theo rollover).

    Trả về: { "YYYY-MM-DD": { count, time_ms, correct, avg_ease } }
      - count:     số review (type IN 0,1,2,3 — lọc bỏ thao tác thủ công type 4)
      - time_ms:   tổng thời lượng review (cột `time`, đơn vị ms)
      - correct:   số lần trả lời đúng (ease > 1)
      - avg_ease:  ease factor trung bình của thẻ (cards.ease) — proxy độ khó
    """
    if not mw.col:
        return {}

    now = time.time()
    if _TELEMETRY_CACHE["data"] is not None and (now - _TELEMETRY_CACHE["ts"]) < _TELEMETRY_TTL:
        return _TELEMETRY_CACHE["data"]

    _, offset_seconds, _ = _get_rollover_context()

    query = """
        SELECT
            STRFTIME('%Y-%m-%d', r.id / 1000 - ?, 'unixepoch', 'localtime', 'start of day') AS day_key,
            COUNT() AS cnt,
            SUM(r.time) AS time_ms,
            SUM(CASE WHEN r.ease > 1 THEN 1 ELSE 0 END) AS correct,
            AVG(c.ease) AS avg_ease
        FROM revlog r
        JOIN cards c ON c.id = r.cid
        WHERE r.type IN (0,1,2,3)
        GROUP BY day_key
    """

    telemetry = {}
    try:
        rows = mw.col.db.all(query, offset_seconds)
        for day_key, cnt, time_ms, correct, avg_ease in rows:
            telemetry[day_key] = {
                "count": int(cnt or 0),
                "time_ms": int(time_ms or 0),
                "correct": int(correct or 0),
                "avg_ease": float(avg_ease) if avg_ease else 2500.0,
            }
    except Exception:
        telemetry = {}

    _TELEMETRY_CACHE["data"] = telemetry
    _TELEMETRY_CACHE["ts"] = now
    return telemetry


# ── Effort score ───────────────────────────────────────────────────────
# Khoảng ease factor hợp lý (Anki: ~1300 thấp, 2500 mặc định, ~5000 cao)
_EASE_MIN = 1300.0
_EASE_MAX = 5000.0

def ease_to_difficulty(avg_ease):
    """
    Ease factor càng thấp → thẻ càng khó → difficulty càng gần 1.
    Map avg_ease trong [1300, 5000] → difficulty trong [1, 0].
    """
    try:
        ease = max(_EASE_MIN, min(_EASE_MAX, float(avg_ease)))
    except (TypeError, ValueError):
        ease = 2500.0
    return round(1.0 - (ease - _EASE_MIN) / (_EASE_MAX - _EASE_MIN), 3)


def compute_effort_score(day, refs, weights):
    """
    Effort score 0-100 của một ngày = tổ hợp trọng số của:
      - Thời gian thực dùng (chuẩn hoá theo ngày điển hình của user)
      - Tỷ lệ trả lời đúng (học thực chất, không phải lướt qua)
      - Độ khó thẻ (thẻ khó = nỗ lực nhiều hơn)

    weights: {"time", "correct", "difficulty"} — tải trọng mỗi thành phần.
    refs: {"avg_time_ms"} — thời lượng trung bình ngày CÓ học (để chuẩn hoá).
    """
    count = day.get("count", 0) or 0
    if count <= 0:
        return 0.0

    w_time = float(weights.get("time", 1.0))
    w_correct = float(weights.get("correct", 1.0))
    w_diff = float(weights.get("difficulty", 0.5))
    w_sum = w_time + w_correct + w_diff
    if w_sum <= 0:
        w_sum = 1.0

    # Thời gian: đạt 150% ngày điển hình = điểm tối đa (tránh thưởng quá cho "cày cuốc" bất thường)
    time_ratio = day.get("time_ms", 0) / max(refs.get("avg_time_ms", 1), 1)
    time_comp = min(time_ratio / 1.5, 1.0)

    # Độ đúng: trả lời đúng nhiều = học thực chất
    correct_comp = day.get("correct", 0) / count

    # Độ khó: thẻ khó (ease thấp) = nỗ lực nhiều hơn
    diff_comp = ease_to_difficulty(day.get("avg_ease", 2500.0))

    score = 100.0 * (w_time * time_comp + w_correct * correct_comp + w_diff * diff_comp) / w_sum
    return round(max(0.0, min(100.0, score)), 1)


def _get_effort_weights():
    conf = config.get_config()
    return conf.get(
        "heatmapEffortWeights",
        config.DEFAULTS.get("heatmapEffortWeights", {"time": 1.0, "correct": 1.0, "difficulty": 0.5}),
    )


def get_effort_data(weights=None):
    """
    Effort score + breakdown mỗi ngày.

    Trả về: { "YYYY-MM-DD": { score, count, time_ms, correct, correct_ratio, difficulty } }
    """
    telemetry = get_daily_telemetry()
    if weights is None:
        weights = _get_effort_weights()

    active_times = [t["time_ms"] for t in telemetry.values() if t.get("count", 0) > 0]
    avg_time_ms = (sum(active_times) / max(len(active_times), 1)) if active_times else 1.0
    refs = {"avg_time_ms": avg_time_ms}

    effort = {}
    for day_key, day in telemetry.items():
        count = day.get("count", 0)
        effort[day_key] = {
            "score": compute_effort_score(day, refs, weights),
            "count": count,
            "time_ms": day.get("time_ms", 0),
            "correct": day.get("correct", 0),
            "correct_ratio": round(day.get("correct", 0) / count, 3) if count else 0.0,
            "difficulty": ease_to_difficulty(day.get("avg_ease", 2500.0)),
        }
    return effort


# ════════════════════════════════════════════════════════════════════
# GĐ2: Adaptive Session Length
# ════════════════════════════════════════════════════════════════════
# Ghi chú GĐ2-2: không cần hook riêng để ghi telemetry phiên — dữ liệu
# hôm nay (count + time) đã có trong revlog, và _on_reviewer_did_answer_card
# gọi invalidate_cache() mỗi lần trả lời thẻ nên dữ liệu luôn tươi khi render.

_MOOD_MULTIPLIERS = {"tired": 0.6, "normal": 1.0, "hype": 1.3}

def get_mood():
    """Mood hiện tại của user (lưu trong mw.col.conf — state runtime, không ghi file settings)."""
    if not mw.col:
        return "normal"
    return mw.col.conf.get("onigiri_session_mood", "normal")

def set_mood(mood):
    """Lưu mood user chọn (1 click). Chỉ chấp nhận giá trị hợp lệ."""
    if not mw.col or mood not in _MOOD_MULTIPLIERS:
        return
    mw.col.conf["onigiri_session_mood"] = mood

def get_review_speed_history(days=14):
    """Tốc độ ôn (thẻ/phút) của các ngày CÓ học trong N ngày gần đây."""
    telemetry = get_daily_telemetry()
    today = get_today_date_key()
    recent = [k for k in sorted(telemetry.keys()) if k <= today][-days:]
    speeds = []
    for k in recent:
        t = telemetry[k]
        if t.get("count", 0) > 0 and t.get("time_ms", 0) > 0:
            speeds.append((t["count"] * 60000.0) / t["time_ms"])
    return speeds

def get_rolling_avg_volume(days=14):
    """Số thẻ trung bình mỗi ngày (chỉ tính ngày có học) trong N ngày gần đây."""
    telemetry = get_daily_telemetry()
    today = get_today_date_key()
    recent = [k for k in sorted(telemetry.keys()) if k <= today][-days:]
    counts = [telemetry[k]["count"] for k in recent if telemetry[k].get("count", 0) > 0]
    if not counts:
        return 0.0
    return round(sum(counts) / len(counts), 1)

def get_session_suggestion():
    """
    GĐ2: Đề xuất số thẻ nên học hôm nay.
      target = clamp(avg_volume × mood_multiplier, min_ratio×avg, max_ratio×avg)

    Trả về dict: mood, target, avg_volume, speed_cpm, today_count.
    """
    conf = config.get_config()
    if not conf.get("sessionSuggestEnabled", True):
        return {"mood": get_mood(), "target": 0, "avg_volume": 0.0, "speed_cpm": 0.0, "today_count": 0}

    avg_volume = get_rolling_avg_volume(14)
    speeds = get_review_speed_history(14)
    mood = get_mood()
    multiplier = _MOOD_MULTIPLIERS.get(mood, 1.0)

    min_ratio = conf.get("sessionTargetMinRatio", 0.5)
    max_ratio = conf.get("sessionTargetMaxRatio", 1.5)
    min_target = max(5.0, avg_volume * min_ratio)
    max_target = max(min_target, avg_volume * max_ratio)
    target = int(round(max(min_target, min(max_target, avg_volume * multiplier))))

    today_count = 0
    telemetry = get_daily_telemetry()
    today = get_today_date_key()
    if today in telemetry:
        today_count = telemetry[today].get("count", 0)

    return {
        "mood": mood,
        "target": max(0, target),
        "avg_volume": round(avg_volume, 1),
        "speed_cpm": round(sum(speeds) / max(len(speeds), 1), 1) if speeds else 0.0,
        "today_count": today_count,
    }


# ════════════════════════════════════════════════════════════════════
# GĐ3: Streak Insurance (token bảo hiểm chuỗi ngày)
# ════════════════════════════════════════════════════════════════════

def _get_streak_tokens_state():
    """Trả về dict token (tự khởi tạo nếu chưa có)."""
    state = dict(mw.col.conf.get("onigiri_streak_tokens", {})) if mw.col else {}
    state.setdefault("count", 0)
    state.setdefault("awarded_day", "")
    state.setdefault("protected_day", "")
    return state

def get_streak_tokens():
    """Số token bảo hiểm hiện tại."""
    return _get_streak_tokens_state().get("count", 0)

def reset_streak_tokens():
    """GĐ3-4: Reset token về 0 (nút trong settings)."""
    if not mw.col:
        return
    mw.col.conf["onigiri_streak_tokens"] = {"count": 0, "awarded_day": "", "protected_day": ""}

def track_today_review():
    """
    GĐ3-1: Gọi mỗi lần trả lời thẻ (chung nhịp hook EXP — KHÔNG thêm setMod thừa).
      - Đếm số review hôm nay (lưu runtime, reset khi đổi ngày).
      - Vượt ngưỡng (ratio × avg_volume) → cộng 1 token (tối đa 1/ngày).
    Trả về số token hiện có.
    """
    if not mw.col:
        return 0
    conf = mw.col.conf
    streak_conf = _streak_config()
    if not streak_conf["enabled"]:
        return _get_streak_tokens_state().get("count", 0)

    today = get_today_date_key()

    # Reset bộ đếm khi đổi ngày
    if conf.get("onigiri_today_key") != today:
        conf["onigiri_today_key"] = today
        conf["onigiri_today_count"] = 0
    conf["onigiri_today_count"] = conf.get("onigiri_today_count", 0) + 1
    today_count = conf["onigiri_today_count"]

    tokens = _get_streak_tokens_state()

    # Cấp token 1 lần/ngày khi vượt ngưỡng; avg chỉ tính lại 1 lần/ngày để tránh query mỗi thẻ
    if tokens.get("awarded_day") != today:
        ratio = streak_conf["ratio"]
        avg_cache = conf.get("onigiri_avg_cache", {})
        if avg_cache.get("day") != today:
            avg = get_rolling_avg_volume(365)
            conf["onigiri_avg_cache"] = {"day": today, "value": avg}
        else:
            avg = avg_cache.get("value", 0.0)
        threshold = max(5.0, avg * ratio)
        if today_count >= threshold:
            tokens["count"] += 1
            tokens["awarded_day"] = today

    conf["onigiri_streak_tokens"] = tokens
    return tokens["count"]

def maybe_protect_streak():
    """
    GĐ3-2: Chạy khi render deck browser / mở profile.
    Nếu hôm qua KHÔNG có review và có token → tự "cứu" streak (trừ 1 token).
    Mỗi ngày chỉ xử lý 1 lần (đánh dấu protected_day).
    Trả về dict {protected, remaining} — hoặc None nếu không cần thông báo.
    """
    if not mw.col:
        return None
    conf = mw.col.conf
    if not _streak_config()["enabled"]:
        return None

    today = get_today_date_key()
    _, _, today_start_seconds = _get_rollover_context()
    yesterday_key = datetime.fromtimestamp(today_start_seconds - 86400).strftime('%Y-%m-%d')

    tokens = _get_streak_tokens_state()
    if tokens.get("protected_day") == today:
        return None

    # Hôm qua có review không? (telemetry cache TTL — miễn phí)
    telemetry = get_daily_telemetry()
    studied_yesterday = yesterday_key in telemetry and telemetry[yesterday_key].get("count", 0) > 0

    if studied_yesterday:
        tokens["protected_day"] = today
        conf["onigiri_streak_tokens"] = tokens
        return None

    if tokens.get("count", 0) > 0:
        tokens["count"] -= 1
        tokens["protected_day"] = today
        conf["onigiri_streak_tokens"] = tokens
        mw.col.setMod()
        return {"protected": True, "remaining": tokens["count"]}

    tokens["protected_day"] = today
    conf["onigiri_streak_tokens"] = tokens
    return {"protected": False, "remaining": 0}
