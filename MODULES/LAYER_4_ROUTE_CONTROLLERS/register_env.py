import random
from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import generate_password_hash
from MODULES.LAYER_1_CORE_INFRASTRUCTURE.extensions import db
from MODULES.LAYER_1_CORE_INFRASTRUCTURE.config import has_google_oauth
from MODULES.LAYER_2_DATA_PERSISTENCE.models import User
from MODULES.LAYER_3_BUSINESS_SERVICES.mailer import send_otp_email

register_bp = Blueprint('register_bp', __name__)


@register_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email or "@" not in email:
            return render_template("signup.html", error="Please enter a valid email address.", has_google_oauth=has_google_oauth)

        if User.query.filter_by(email=email).first():
            return render_template("signup.html", error="An account with this email already exists. Please login.", has_google_oauth=has_google_oauth)

        otp = str(random.randint(100000, 999999))
        session["reg_otp"] = otp
        session["pending_signup_email"] = email

        if send_otp_email(email, otp):
            return redirect("/auth/register/verify-otp")
        else:
            return render_template("signup.html", error="Failed to send OTP email. Please try again.", has_google_oauth=has_google_oauth)

    return render_template("signup.html", has_google_oauth=has_google_oauth, error=None)


@register_bp.route("/auth/register/verify-otp", methods=["GET", "POST"])
def verify_register_otp():
    email = session.get("pending_signup_email") or session.get("email_otp_verified")
    if not email or "reg_otp" not in session:
        if session.get("email_otp_verified"):
            return redirect("/signup/set-password")
        return redirect("/signup")

    if request.method == "GET":
        return render_template("verify_otp.html", error=None, email=email, next_step="set_password")

    entered = (request.form.get("otp") or "").strip()
    if entered == session.get("reg_otp"):
        session.pop("reg_otp", None)
        session["email_otp_verified"] = email
        return redirect("/signup/set-password")

    return render_template("verify_otp.html", error="Invalid OTP. Please try again.", email=email, next_step="set_password")


@register_bp.route("/signup/set-password", methods=["GET", "POST"])
def signup_set_password():
    email = session.get("email_otp_verified") or session.get("pending_signup_email")
    if not email:
        return redirect("/signup")

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()

        if not password or len(password) < 6:
            return render_template("set_password.html", error="Password must be at least 6 characters.", email=email)
        if password != confirm:
            return render_template("set_password.html", error="Passwords do not match.", email=email)

        session["verified_signup_email"] = email
        session["verified_signup_password"] = generate_password_hash(password)
        return redirect("/register")

    return render_template("set_password.html", error=None, email=email)


@register_bp.route("/register", methods=["GET", "POST"])
def register():
    is_google = request.args.get("google") == "1"

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        gender = request.form.get("gender")
        education = request.form.get("education")
        course = request.form.get("course")
        semester = request.form.get("semester")
        user_type = request.form.get("user_type", "student")
        github_url = request.form.get("github_url", "").strip() or None
        linkedin_url = request.form.get("linkedin_url", "").strip() or None
        skills = request.form.get("skills", "").strip() or None
        years_of_experience = request.form.get("years_of_experience", "").strip() or None
        current_designation = request.form.get("current_designation", "").strip() or None

        email = session.get("pending_google_email") or session.get("verified_signup_email")
        password = session.get("verified_signup_password")

        def render_register_error(error_msg):
            return render_template("register.html", error=error_msg,
                                   is_google=is_google, prefill_name=full_name, prefill_email=email or "",
                                   prefill_gender=gender, prefill_education=education, prefill_course=course,
                                   prefill_semester=semester, prefill_user_type=user_type,
                                   prefill_github_url=github_url, prefill_linkedin_url=linkedin_url,
                                   prefill_skills=skills, prefill_years_of_experience=years_of_experience,
                                   prefill_current_designation=current_designation)

        if not full_name:
            return render_register_error("Please fill in your full name.")

        if not gender:
            return render_register_error("Please select your gender.")

        existing_name = User.query.filter(User.full_name.ilike(full_name)).first()
        if existing_name and ("user_id" not in session or session.get("user_id") != existing_name.id):
            return render_register_error("This name is already taken. Please use a different name.")

        if user_type == "student":
            if not education:
                return render_register_error("Please select your education level.")
            if not course:
                return render_register_error("Please enter your course/branch.")
            if not semester:
                return render_register_error("Please enter your semester/year.")
        elif user_type == "professional":
            if not current_designation:
                return render_register_error("Please enter your current designation.")
            if not years_of_experience:
                return render_register_error("Please enter your years of experience.")

        # Logged-in user updating their profile
        if "user_id" in session:
            user = db.session.get(User, session["user_id"])
            if user:
                user.full_name = full_name
                user.gender = gender
                user.education = education
                user.course = course
                user.semester = semester
                user.user_type = user_type
                user.github_url = github_url
                user.linkedin_url = linkedin_url
                user.skills = skills
                user.years_of_experience = years_of_experience
                user.current_designation = current_designation
                db.session.commit()
                session["user_name"] = user.full_name
                return redirect("/dashboard")

        # Google OAuth new user
        if session.get("pending_google_email"):
            g_email = session.pop("pending_google_email")
            google_id = session.pop("pending_google_id", None)
            session.pop("pending_google_name", None)
            new_user = User(
                full_name=full_name, email=g_email, password=None,
                gender=gender, education=education, course=course, semester=semester,
                auth_provider="google", google_id=google_id, email_verified=True,
                user_type=user_type, github_url=github_url, linkedin_url=linkedin_url,
                skills=skills, years_of_experience=years_of_experience,
                current_designation=current_designation
            )
            db.session.add(new_user)
            db.session.commit()
            session["user_id"] = new_user.id
            session["user_name"] = new_user.full_name
            session["user_email"] = new_user.email
            return redirect("/dashboard")

        # Local signup (email verified via OTP, password already set)
        if session.get("verified_signup_email"):
            new_user = User(
                full_name=full_name, email=email, password=password,
                gender=gender, education=education, course=course, semester=semester,
                auth_provider="local", email_verified=True,
                user_type=user_type, github_url=github_url, linkedin_url=linkedin_url,
                skills=skills, years_of_experience=years_of_experience,
                current_designation=current_designation
            )
            db.session.add(new_user)
            db.session.commit()
            session.pop("verified_signup_email", None)
            session.pop("verified_signup_password", None)
            session["user_id"] = new_user.id
            session["user_name"] = new_user.full_name
            session["user_email"] = new_user.email
            return redirect("/dashboard")

        return redirect("/login")

    # GET
    if "user_id" in session:
        user = db.session.get(User, session["user_id"])
        prefill_name = user.full_name if user else ""
        prefill_email = (user.email if user else "") or session.get("pending_google_email", "")
        if user and user.auth_provider == "google":
            is_google = True
    else:
        prefill_name = session.get("pending_google_name", "")
        prefill_email = session.get("pending_google_email") or session.get("verified_signup_email", "")
        if not prefill_email:
            return redirect("/login")

    return render_template("register.html", is_google=is_google,
                           prefill_name=prefill_name, prefill_email=prefill_email, error=None)


@register_bp.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():
    if session.get("is_admin"):
        return redirect("/admin")
    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])

    if not user:
        session.clear()
        return redirect("/login")

    if request.method == "POST":
        user.full_name = request.form.get("full_name")
        user.gender = request.form.get("gender")
        user.education = request.form.get("education")
        user.course = request.form.get("course")
        user.semester = request.form.get("semester")
        user.user_type = request.form.get("user_type", "student")
        user.github_url = request.form.get("github_url", "").strip() or None
        user.linkedin_url = request.form.get("linkedin_url", "").strip() or None
        user.skills = request.form.get("skills", "").strip() or None
        user.years_of_experience = request.form.get("years_of_experience", "").strip() or None
        user.current_designation = request.form.get("current_designation", "").strip() or None
        db.session.commit()
        session["user_name"] = user.full_name
        return render_template("edit_profile.html", user=user, success="Profile updated successfully.")

    return render_template("edit_profile.html", user=user)
