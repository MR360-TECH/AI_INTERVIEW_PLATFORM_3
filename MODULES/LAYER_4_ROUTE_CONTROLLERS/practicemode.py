from flask import Blueprint, render_template, request, redirect, session, jsonify, url_for
from MODULES.LAYER_1_CORE_INFRASTRUCTURE.extensions import db
from MODULES.LAYER_2_DATA_PERSISTENCE.models import InterviewResult
from MODULES.LAYER_2_DATA_PERSISTENCE.helpers import clear_progress

practice_bp = Blueprint('practice_bp', __name__)


@practice_bp.route("/practice-setup")
def practice_setup():
    if session.get("is_admin"):
        return redirect("/admin")
    if "user_id" not in session:
        return redirect("/login")
    return render_template("practice_setup.html")


@practice_bp.route("/practice-start", methods=["POST"])
def practice_start():
    if "user_id" not in session:
        return redirect("/login")
    
    mode = request.form.get("mode")
    viva_subject = request.form.get("viva_subject", "").strip()
    drill_subject = request.form.get("drill_subject", "").strip()
    
    session["interview_mode"] = mode
    if mode == "viva" and viva_subject:
        session["practice_topic"] = viva_subject
    elif mode == "drill" and drill_subject:
        session["practice_topic"] = drill_subject
    elif mode == "lang":
        lang_target = request.form.get("lang_target", "").strip()
        lang_focus = request.form.get("lang_focus", "conversation").strip()
        lang_level = request.form.get("lang_level", "intermediate").strip()
        
        session["lang_target"] = lang_target or "English"
        session["lang_focus"] = lang_focus
        session["lang_level"] = lang_level
        session["practice_topic"] = f"{session['lang_target']} ({lang_focus.capitalize()})"
    else:
        session["practice_topic"] = "General English Speaking"

    return redirect(url_for("interview_bp.interview", restart="1", practice="1"))


@practice_bp.route("/quit-interview")
def quit_interview():
    if "user_id" not in session:
        return redirect("/login")
    session.pop("chat_history", None)
    session.pop("q_count", None)
    session.pop("interview_mode", None)
    session.pop("practice_topic", None)
    session.pop("lang_target", None)
    session.pop("lang_focus", None)
    session.pop("lang_level", None)
    session.pop("interview_domain", None)
    session.pop("interview_difficulty", None)
    session.pop("resume_summary", None)
    clear_progress(session["user_id"])
    return redirect("/dashboard")


@practice_bp.route("/reset-assessment", methods=["POST"])
def reset_assessment():
    if "user_id" not in session:
        return jsonify({"status": "error", "reason": "not_logged_in"}), 401
    user_id = session["user_id"]
    is_practice = bool(session.get("interview_mode"))
    domain_val = session.get("interview_domain", "General")

    # Check DB for actual progress (more reliable than session q_count)
    db_progress = InterviewProgress.query.filter_by(user_id=user_id).first()
    has_real_progress = bool(db_progress and db_progress.q_count and db_progress.q_count > 0)

    if not is_practice and has_real_progress:
        try:
            res_rec = InterviewResult(
                user_id=user_id,
                score=0.0,
                status="Abandoned (Reset)",
                summary="Candidate initiated a fresh session reset mid-assessment.",
                domain=domain_val
            )
            db.session.add(res_rec)
            db.session.commit()
        except Exception as e:
            print(f"[RESET ASSESSMENT LOG ERROR] {e}")
            db.session.rollback()

    session.pop("chat_history", None)
    session.pop("q_count", None)
    session.pop("interview_mode", None)
    session.pop("practice_topic", None)
    session.pop("lang_target", None)
    session.pop("lang_focus", None)
    session.pop("lang_level", None)
    session.pop("interview_domain", None)
    session.pop("interview_difficulty", None)
    session.pop("resume_summary", None)
    session.pop("resume_choice", None)
    session.modified = True
    clear_progress(user_id)
    return jsonify({"status": "ok"})


@practice_bp.route("/terminate-proctoring", methods=["POST"])
def terminate_proctoring():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "unauthorized"}), 401
    
    user_id = session["user_id"]
    domain_val = session.get("interview_domain", "General")
    
    reason = "Repeated window focus loss / tab switching detected during active assessment"
    summary_msg = (
        "OFFICIAL DISQUALIFICATION NOTICE:\n\n"
        "This assessment session was automatically terminated by the automated security proctoring system "
        "due to a breach of the Candidate Code of Conduct. Specifically, unauthorized application tab switching "
        "or window focus loss was detected on multiple occasions during an active examination session.\n\n"
        "In accordance with evaluation security standards, all progress has been recorded as terminated "
        "and flagged for administrator audit review."
    )
    
    try:
        result_record = InterviewResult(
            user_id=user_id,
            score=0.0,
            status="Terminated (Breach)",
            summary=summary_msg,
            domain=domain_val,
            is_terminated=True,
            termination_reason=reason
        )
        db.session.add(result_record)
        db.session.commit()
    except Exception as db_err:
        print(f"Error recording proctoring termination: {db_err}")
        db.session.rollback()

    session.pop("chat_history", None)
    session.pop("q_count", None)
    session.pop("resume_choice", None)
    session.pop("resume_summary", None)
    session.pop("interview_domain", None)
    session.pop("interview_difficulty", None)
    session.pop("interview_mode", None)
    session.pop("practice_topic", None)
    session.modified = True
    clear_progress(user_id)

    return jsonify({"status": "terminated", "redirect": "/interview-result?terminated=1"})
