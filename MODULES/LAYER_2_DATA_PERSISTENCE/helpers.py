import json
import time
from MODULES.LAYER_1_CORE_INFRASTRUCTURE.extensions import db
from MODULES.LAYER_2_DATA_PERSISTENCE.models import AdminSettings, SettingsSnapshot, InterviewProgress

_cached_settings = None
_cached_settings_time = 0


def invalidate_settings_cache():
    """Force-clear the in-memory settings cache so the next call to get_settings()
    fetches fresh data from the database. Call this immediately after saving AdminSettings."""
    global _cached_settings, _cached_settings_time
    _cached_settings = None
    _cached_settings_time = 0


def get_settings():
    global _cached_settings, _cached_settings_time
    now = time.time()
    if _cached_settings and (now - _cached_settings_time) < 5:
        return _cached_settings

    try:
        settings_row = AdminSettings.query.first()
        if not settings_row:
            settings_row = AdminSettings(
                min_questions=3,
                max_questions=8,
                pass_score=3,
                default_difficulty='student',
                question_timer_seconds=90,
                enable_attempt_limits=True,
                default_allowed_interviews=2,
                enable_warning_strikes=True
            )
            db.session.add(settings_row)
            db.session.commit()
        snapshot = SettingsSnapshot(settings_row)
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
        snapshot = SettingsSnapshot()

    _cached_settings = snapshot
    _cached_settings_time = now
    return snapshot


def save_progress(user_id, chat_history, q_count):
    try:
        progress = InterviewProgress.query.filter_by(user_id=user_id).first()
        if not progress:
            progress = InterviewProgress(user_id=user_id)
            db.session.add(progress)
        progress.chat_history = json.dumps(chat_history)
        progress.q_count = q_count
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        try:
            progress = InterviewProgress.query.filter_by(user_id=user_id).first()
            if progress:
                progress.chat_history = json.dumps(chat_history)
                progress.q_count = q_count
                db.session.commit()
        except Exception:
            db.session.rollback()


def clear_progress(user_id):
    try:
        InterviewProgress.query.filter_by(user_id=user_id).delete()
        db.session.commit()
    except Exception:
        db.session.rollback()
