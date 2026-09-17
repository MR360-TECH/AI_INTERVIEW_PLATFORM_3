import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, session, send_from_directory, current_app
from MODULES.LAYER_1_CORE_INFRASTRUCTURE.extensions import db
from MODULES.LAYER_2_DATA_PERSISTENCE.models import User, InterviewResult, InterviewProgress
from MODULES.LAYER_2_DATA_PERSISTENCE.validators import profile_is_complete, allowed_resume_file
from MODULES.LAYER_2_DATA_PERSISTENCE.helpers import get_settings, clear_progress
from MODULES.LAYER_3_BUSINESS_SERVICES.ai_client import analyze_attachment

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    if session.get("is_admin"):
        return redirect("/admin")
    if "user_id" not in session:
        return redirect("/login")

    current_user = db.session.get(User, session["user_id"])
    if not current_user:
        session.clear()
        return redirect("/login")

    if not profile_is_complete(current_user):
        return redirect("/register")

    latest_res = InterviewResult.query.filter_by(user_id=session["user_id"]).order_by(InterviewResult.interview_datetime.desc()).first()
    if latest_res and latest_res.is_terminated:
        clear_progress(session["user_id"])
        has_progress = False
    else:
        progress = InterviewProgress.query.filter_by(user_id=session["user_id"]).first()
        has_progress = bool(progress and progress.q_count > 0)

    recent_results = InterviewResult.query.filter(
        InterviewResult.user_id == session["user_id"],
        InterviewResult.real_attempt_filter()
    ).order_by(InterviewResult.interview_datetime.desc()).limit(5).all()
    has_result = len(recent_results) > 0

    error_msg = None
    err_code = request.args.get("error")
    if err_code == "file_too_large":
        error_msg = "Uploaded file is too large. The maximum size limit is 10MB."
    elif err_code == "api_key_missing":
        error_msg = "AI Placement evaluation is not configured. Please set the GEMINI_API_KEY environment variable."

    # Check attempt limit status (for UI button state)
    settings = get_settings()
    is_locked = False
    attempts_used = 0
    extra_granted = current_user.extra_allowed_interviews or 0 if current_user else 0
    allowed_total = (settings.default_allowed_interviews or 2) + extra_granted
    remaining_tokens = allowed_total

    if settings.enable_attempt_limits:
        attempts_used = InterviewResult.query.filter(
            InterviewResult.user_id == session["user_id"],
            InterviewResult.real_attempt_filter()
        ).count()
        remaining_tokens = max(0, allowed_total - attempts_used)
        if attempts_used >= allowed_total:
            is_locked = True

    return render_template("dashboard.html", name=session["user_name"], user=current_user,
                           has_progress=has_progress, has_result=has_result,
                           recent_results=recent_results, error=error_msg,
                           is_locked=is_locked, attempts_used=attempts_used,
                           allowed_total=allowed_total, remaining_tokens=remaining_tokens,
                           settings=settings)


@dashboard_bp.route("/dashboard/update-resume", methods=["POST"])
def dashboard_update_resume():
    if "user_id" not in session:
        return redirect("/login")
    
    user = db.session.get(User, session["user_id"])
    if not user:
        return redirect("/dashboard")
        
    resume_file = request.files.get("resume_file")
    
    if resume_file and resume_file.filename:
        filename = resume_file.filename
        if allowed_resume_file(filename):
            try:
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                ext = filename.rsplit('.', 1)[1].lower()
                saved_filename = f"user_{user.id}_resume.{ext}"
                file_path = os.path.join(upload_folder, saved_filename)
                
                resume_file.seek(0)
                file_bytes = resume_file.read()
                with open(file_path, "wb") as f:
                    f.write(file_bytes)
                
                user.resume_filename = saved_filename

                resume_file.seek(0)
                extracted_text = analyze_attachment(
                    file_bytes, resume_file.mimetype,
                    context_hint="Extract the text content and structure from this resume as cleanly as possible. Provide only the text transcription."
                )
                user.resume_text = extracted_text
                db.session.commit()
            except Exception as e:
                print(f"Error extracting text from uploaded resume: {e}")
                return redirect("/dashboard?error=resume_extraction_failed")
        else:
            return redirect("/dashboard?error=invalid_file_type")
            
    return redirect("/dashboard")


@dashboard_bp.route("/dashboard/remove-resume", methods=["GET", "POST"])
def dashboard_remove_resume():
    if "user_id" not in session:
        return redirect("/login")
    user = db.session.get(User, session["user_id"])
    if user:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if user.resume_filename:
            file_path = os.path.join(upload_folder, user.resume_filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing resume file: {e}")
            user.resume_filename = None
        user.resume_text = None
        db.session.commit()
    return redirect("/dashboard")


@dashboard_bp.route("/uploads/resumes/<filename>")
def view_original_resume(filename):
    if not session.get("is_admin") and "user_id" not in session:
        return redirect("/login")
    if not session.get("is_admin"):
        user = db.session.get(User, session["user_id"])
        if not user or user.resume_filename != filename:
            return "Unauthorized", 403
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    return send_from_directory(upload_folder, filename)


@dashboard_bp.route("/latest-result")
def latest_result():
    if session.get("is_admin"):
        return redirect("/admin")
    if "user_id" not in session:
        return redirect("/login")

    result = InterviewResult.query.filter_by(user_id=session["user_id"]).order_by(InterviewResult.interview_datetime.desc(), InterviewResult.id.desc()).first()

    if not result:
        return redirect("/dashboard")

    is_term = bool(result.is_terminated or (result.status and "Terminated" in result.status))
    if is_term:
        label = "Disqualified"
        label_color = "#e74a3b"
        verdict = "Terminated (Breach)"
        verdict_message = "This assessment session was automatically terminated by the automated security proctoring system due to a breach of the Candidate Code of Conduct."
    else:
        label = "Excellent" if result.score and result.score >= 8 else "Good" if result.score and result.score >= 6 else "Fair" if result.score and result.score >= 4 else "Needs Work"
        label_color = "#1cc88a" if result.score and result.score >= 8 else "#4e73df" if result.score and result.score >= 6 else "#f6c23e" if result.score and result.score >= 4 else "#e74a3b"
        verdict = result.status
        verdict_message = "🎉 Congratulations! You have met the recruitment selection criteria and successfully passed the assessment." if result.status in ("Selected", "PASS") or (result.status and "WELL DONE" in result.status) else "Thank you for taking the assessment. We regret that you did not meet the selection threshold for this placement round. Keep developing your skills."

    return render_template(
        "interview_result.html",
        score=result.score,
        score_percent=min(int((float(result.score) / 10) * 100), 100) if result.score else 0,
        label=label,
        label_color=label_color,
        summary=result.summary,
        verdict=verdict,
        verdict_message=verdict_message,
        candidate_name=session.get("user_name", "Candidate"),
        report_date=result.interview_datetime.strftime("%B %d, %Y") if result.interview_datetime else datetime.now().strftime("%B %d, %Y"),
        domain=result.domain or "General",
        is_terminated=is_term,
        termination_reason=result.termination_reason or "Repeated window focus loss / tab switching detected during active assessment",
        session_code=result.session_code
    )


@dashboard_bp.route("/my-history")
def my_history():
    if session.get("is_admin"):
        return redirect("/admin")
    if "user_id" not in session:
        return redirect("/login")

    attempts = InterviewResult.query.filter_by(user_id=session["user_id"]).order_by(InterviewResult.interview_datetime.desc(), InterviewResult.id.desc()).all()

    chart_labels = [a.interview_datetime.strftime('%d %b') for a in reversed(attempts)]
    chart_scores = [float(a.score) if a.score is not None else 0 for a in reversed(attempts)]

    return render_template("my_history.html", attempts=attempts, chart_labels=chart_labels, chart_scores=chart_scores)


@dashboard_bp.route("/my-history/<int:result_id>")
def view_past_result(result_id):
    if session.get("is_admin"):
        return redirect("/admin")
    if "user_id" not in session:
        return redirect("/login")

    result = InterviewResult.query.filter_by(id=result_id, user_id=session["user_id"]).first()
    if not result:
        return redirect("/my-history")

    try:
        score_num = float(result.score)
    except:
        score_num = 0

    if score_num >= 8:
        label = "Excellent"
        label_color = "#1cc88a"
    elif score_num >= 6:
        label = "Good"
        label_color = "#4e73df"
    elif score_num >= 4:
        label = "Fair"
        label_color = "#f6c23e"
    else:
        label = "Needs Work"
        label_color = "#e74a3b"

    score_percent = min(int((score_num / 10) * 100), 100)
    verdict = result.status or "FAIL"
    is_terminated = bool(result.is_terminated or (result.status and "Terminated" in result.status))
    
    if is_terminated or "Terminated" in str(verdict):
        verdict = "Terminated (Breach)"
        label = "Disqualified"
        label_color = "#e74a3b"
        verdict_message = "This assessment session was automatically terminated by the automated security proctoring system due to a breach of the Candidate Code of Conduct."
    else:
        is_pass = verdict in ("PASS", "Selected") or "WELL DONE" in verdict
        if is_pass:
            verdict_message = "🎉 Congratulations! You have met the recruitment selection criteria and successfully passed the assessment."
        else:
            verdict_message = "Thank you for taking the assessment. We regret that you did not meet the selection threshold for this placement round. Keep developing your skills."

    return render_template(
        "interview_result.html",
        score=score_num,
        score_percent=score_percent,
        label=label,
        label_color=label_color,
        summary=result.summary,
        verdict=verdict,
        verdict_message=verdict_message,
        candidate_name=session.get("user_name", "Candidate"),
        report_date=result.interview_datetime.strftime("%B %d, %Y") if result.interview_datetime else datetime.now().strftime("%B %d, %Y"),
        domain=result.domain or "General",
        is_terminated=is_terminated,
        termination_reason=result.termination_reason or "Repeated window focus loss / tab switching detected during active assessment",
        session_code=result.session_code
    )
