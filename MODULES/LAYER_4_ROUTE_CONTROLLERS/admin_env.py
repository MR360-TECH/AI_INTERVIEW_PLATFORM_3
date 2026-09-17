from datetime import date
from flask import Blueprint, render_template, request, redirect, session, jsonify, send_from_directory, current_app
from sqlalchemy import func
from MODULES.LAYER_1_CORE_INFRASTRUCTURE.extensions import db
from MODULES.LAYER_2_DATA_PERSISTENCE.models import User, InterviewResult, InterviewProgress, AdminSettings
from MODULES.LAYER_2_DATA_PERSISTENCE.helpers import get_settings, invalidate_settings_cache
from MODULES.LAYER_3_BUSINESS_SERVICES.mailer import send_slot_unlocked_email

admin_bp = Blueprint('admin_bp', __name__)


@admin_bp.route("/admin")
def admin():
    if "user_id" in session:
        return redirect("/dashboard")
    if not session.get("is_admin"):
        return redirect("/login")

    today = date.today()
    current_month = today.month
    current_year = today.year

    filter_type = request.args.get("filter", "all")

    all_results = db.session.query(InterviewResult, User).join(User, InterviewResult.user_id == User.id)\
        .filter(~InterviewResult.status.like('%Practice%'))\
        .order_by(InterviewResult.interview_datetime.desc(), InterviewResult.id.desc()).all()

    today_count = sum(1 for r, u in all_results if r.interview_datetime and r.interview_datetime.date() == today)
    month_count = sum(1 for r, u in all_results if r.interview_datetime and r.interview_datetime.year == current_year and r.interview_datetime.month == current_month)
    total_count = len(all_results)
    selected_count = sum(1 for r, u in all_results if (r.status in ["Selected", "PASS"] or (r.status and "WELL DONE" in r.status)) and not r.is_terminated)
    rejected_count = sum(1 for r, u in all_results if (r.status in ["Rejected", "FAIL"] or r.is_terminated or "Terminated" in (r.status or "")))

    if filter_type == "today":
        results = [(r, u) for r, u in all_results if r.interview_datetime and r.interview_datetime.date() == today]
    elif filter_type == "month":
        results = [(r, u) for r, u in all_results if r.interview_datetime and r.interview_datetime.year == current_year and r.interview_datetime.month == current_month]
    elif filter_type == "selected":
        results = [(r, u) for r, u in all_results if (r.status in ["Selected", "PASS"] or (r.status and "WELL DONE" in r.status)) and not r.is_terminated]
    elif filter_type == "rejected":
        results = [(r, u) for r, u in all_results if (r.status in ["Rejected", "FAIL"] or r.is_terminated or "Terminated" in (r.status or ""))]
    else:
        results = all_results

    settings = get_settings()

    attempt_counts_raw = db.session.query(
        InterviewResult.user_id, func.count(InterviewResult.id)
    ).filter(
        InterviewResult.real_attempt_filter()
    ).group_by(InterviewResult.user_id).all()
    user_attempt_counts = {u_id: count for u_id, count in attempt_counts_raw}

    return render_template(
        "admin.html",
        results=results,
        today_count=today_count,
        month_count=month_count,
        total_count=total_count,
        selected_count=selected_count,
        rejected_count=rejected_count,
        filter_type=filter_type,
        settings=settings,
        user_attempt_counts=user_attempt_counts
    )


@admin_bp.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if not session.get("is_admin"):
        return redirect("/login")

    if request.method == "POST":
        # Always work directly with the DB row — never modify the cached snapshot
        db_settings = AdminSettings.query.first()
        if not db_settings:
            # Row doesn't exist yet — create it with defaults
            db_settings = AdminSettings(
                min_questions=3,
                max_questions=8,
                pass_score=3,
                default_difficulty='student',
                question_timer_seconds=90,
                enable_attempt_limits=True,
                default_allowed_interviews=2
            )
            db.session.add(db_settings)

        try:
            db_settings.min_questions = int(float(request.form.get("min_questions", 3)))
        except (ValueError, TypeError):
            pass
        try:
            db_settings.max_questions = int(float(request.form.get("max_questions", 8)))
        except (ValueError, TypeError):
            pass
        try:
            db_settings.pass_score = int(float(request.form.get("pass_score", 3)))
        except (ValueError, TypeError):
            pass
        db_settings.default_difficulty = request.form.get("default_difficulty", "student")
        if "question_timer_seconds" in request.form:
            try:
                db_settings.question_timer_seconds = int(float(request.form["question_timer_seconds"]))
            except (ValueError, TypeError):
                pass

        # Checkbox: present = True, absent = False
        db_settings.enable_attempt_limits = bool(request.form.get("enable_attempt_limits"))
        if "default_allowed_interviews" in request.form:
            try:
                db_settings.default_allowed_interviews = int(float(request.form["default_allowed_interviews"]))
            except (ValueError, TypeError):
                pass

        db.session.commit()

        # ✅ Force-clear the in-memory cache so the new settings apply immediately
        invalidate_settings_cache()

        return redirect("/admin/settings?saved=1")

    settings = get_settings()
    return render_template("admin_settings.html", settings=settings, saved=request.args.get("saved"))


@admin_bp.route("/admin/guide")
@admin_bp.route("/admin/info")
def admin_guide():
    if not session.get("is_admin"):
        return redirect("/login")
    settings = get_settings()
    return render_template("admin_guide.html", settings=settings)


@admin_bp.route("/admin/delete/<int:result_id>")
def delete_result(result_id):
    if not session.get("is_admin"):
        return redirect("/login")

    record = db.session.get(InterviewResult, result_id)
    if record:
        db.session.delete(record)
        db.session.commit()

    return redirect("/admin")


@admin_bp.route("/admin/user/<int:user_id>/unlock-attempt", methods=["POST"])
def admin_unlock_attempt(user_id):
    if not session.get("is_admin"):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    user_obj = db.session.get(User, user_id)
    if not user_obj:
        return jsonify({"status": "error", "message": "User not found"}), 404

    settings = get_settings()
    default_allowed = settings.default_allowed_interviews or 2

    # Count actual token-consuming attempts (excludes Practice, Abandoned, Terminated)
    attempts_used = InterviewResult.query.filter(
        InterviewResult.user_id == user_id,
        InterviewResult.real_attempt_filter()
    ).count()

    # Calculate exactly how much extra we need so remaining = 1
    # remaining = (default_allowed + extra) - attempts_used = 1
    # => extra = attempts_used - default_allowed + 1
    # But extra must never go below 0
    required_extra = max(0, attempts_used - default_allowed + 1)
    user_obj.extra_allowed_interviews = required_extra
    db.session.commit()

    allowed_total = default_allowed + user_obj.extra_allowed_interviews
    remaining_tokens = max(0, allowed_total - attempts_used)  # will be exactly 1

    if user_obj.email:
        send_slot_unlocked_email(user_obj.email, user_obj.full_name)

    return jsonify({
        "status": "success",
        "message": f"Successfully granted 1 interview token for {user_obj.full_name or 'candidate'}.",
        "new_extra": user_obj.extra_allowed_interviews,
        "remaining_tokens": remaining_tokens,
        "allowed_total": allowed_total,
        "attempts_used": attempts_used
    })


@admin_bp.route("/admin/delete-user/<int:user_id>")
def delete_user(user_id):
    if not session.get("is_admin"):
        return redirect("/login")

    InterviewResult.query.filter_by(user_id=user_id).delete()
    InterviewProgress.query.filter_by(user_id=user_id).delete()

    user = db.session.get(User, user_id)
    if user:
        db.session.delete(user)

    db.session.commit()

    next_url = request.args.get("next") or "/admin"
    return redirect(next_url)


@admin_bp.route("/admin/users")
def admin_users():
    if not session.get("is_admin"):
        return redirect("/login")

    q = request.args.get("q", "").strip()
    if q:
        users = User.query.filter(
            (User.full_name.ilike(f"%{q}%")) |
            (User.email.ilike(f"%{q}%")) |
            (User.course.ilike(f"%{q}%")) |
            (User.skills.ilike(f"%{q}%"))
        ).order_by(User.registered_at.desc()).all()
    else:
        users = User.query.order_by(User.registered_at.desc()).all()
    settings = get_settings()

    attempt_counts_raw = db.session.query(
        InterviewResult.user_id, func.count(InterviewResult.id)
    ).filter(
        InterviewResult.real_attempt_filter()
    ).group_by(InterviewResult.user_id).all()
    user_attempt_counts = {u_id: count for u_id, count in attempt_counts_raw}

    return render_template("admin_users.html", users=users, q=q, settings=settings, user_attempt_counts=user_attempt_counts)


@admin_bp.route("/admin/user/<int:user_id>")
def admin_user_detail(user_id):
    if not session.get("is_admin"):
        return redirect("/login")

    user = db.session.get(User, user_id)
    if not user:
        return redirect("/admin")

    interviews = InterviewResult.query.filter(
        InterviewResult.user_id == user_id,
        ~InterviewResult.status.like('%Practice%')
    ).order_by(InterviewResult.interview_datetime.desc(), InterviewResult.id.desc()).all()

    settings = get_settings()
    attempts_used = sum(1 for inv in interviews if inv.status not in InterviewResult.NON_COUNTING_STATUSES)
    extra_granted = user.extra_allowed_interviews or 0
    allowed_total = (settings.default_allowed_interviews or 2) + extra_granted
    remaining_tokens = max(0, allowed_total - attempts_used)
    is_locked = bool(settings.enable_attempt_limits and remaining_tokens <= 0)

    return render_template(
        "admin_user_detail.html",
        user=user,
        interviews=interviews,
        settings=settings,
        attempts_used=attempts_used,
        extra_granted=extra_granted,
        allowed_total=allowed_total,
        remaining_tokens=remaining_tokens,
        is_locked=is_locked
    )


@admin_bp.route("/admin/user/<int:user_id>/resume")
def admin_view_user_resume(user_id):
    if not session.get("is_admin"):
        return redirect("/login")
    user = db.session.get(User, user_id)
    if not user or not user.resume_filename:
        return redirect(f"/admin/user/{user_id}")
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    return send_from_directory(upload_folder, user.resume_filename)


@admin_bp.route("/admin/interview/<int:result_id>")
def admin_interview_detail(result_id):
    if not session.get("is_admin"):
        return redirect("/login")

    result = db.session.get(InterviewResult, result_id)
    if not result:
        return redirect("/admin")

    candidate = db.session.get(User, result.user_id)

    try:
        score_percent = min(int((float(result.score) / 10) * 100), 100)
    except:
        score_percent = 0

    return render_template("admin_interview_detail.html", result=result, candidate=candidate, score_percent=score_percent)
