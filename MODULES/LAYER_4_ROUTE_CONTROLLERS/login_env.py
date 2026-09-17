import os
import random
from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from MODULES.LAYER_1_CORE_INFRASTRUCTURE.extensions import db, oauth
from MODULES.LAYER_1_CORE_INFRASTRUCTURE.config import ADMIN_EMAIL, ADMIN_PASSWORD, has_google_oauth
from MODULES.LAYER_2_DATA_PERSISTENCE.models import User
from MODULES.LAYER_2_DATA_PERSISTENCE.validators import is_valid_email, profile_is_complete
from MODULES.LAYER_3_BUSINESS_SERVICES.mailer import send_otp_email

login_bp = Blueprint('login_bp', __name__)


@login_bp.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    if session.get("is_admin"):
        return redirect("/admin")
    return render_template("index.html")


@login_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not is_valid_email(email):
            return render_template("login.html", error="Please enter a valid email address.", prefill_email=email, has_google_oauth=has_google_oauth)

        if not password:
            return render_template("login.html", error="Please enter your password.", prefill_email=email, has_google_oauth=has_google_oauth)

        # Admin check
        if ADMIN_EMAIL and email == ADMIN_EMAIL.strip().lower():
            if ADMIN_PASSWORD and password == ADMIN_PASSWORD.strip():
                session.clear()
                session["is_admin"] = True
                session["user_name"] = "Admin"
                return redirect("/admin")
            else:
                return render_template("login.html", error="Wrong password. Please check your password and try again.", prefill_email=email, has_google_oauth=has_google_oauth)

        user = User.query.filter_by(email=email).first()

        if not user:
            return render_template("login.html", show_signup_prompt=True, prefill_email=email, has_google_oauth=has_google_oauth)

        # Check if user registered via Google OAuth without a password
        if user.auth_provider == "google" and not user.password:
            return render_template("login.html", error="This account was registered with Google. Please click 'Continue with Google' above.", prefill_email=email, has_google_oauth=has_google_oauth)

        if user.password and check_password_hash(user.password, password):
            session.clear()
            session["user_id"] = user.id
            session["user_name"] = user.full_name
            session["user_email"] = user.email
            session["is_admin"] = False
            if not profile_is_complete(user):
                return redirect("/register")
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Wrong password. Please check your password and try again.", prefill_email=email, has_google_oauth=has_google_oauth)

    error_msg = None
    err_code = request.args.get("error")
    if err_code == "file_too_large":
        error_msg = "Uploaded file is too large. The maximum size limit is 10MB."
    elif err_code == "google_not_configured":
        error_msg = "Google Sign-in is not configured on this server."
    return render_template("login.html", error=error_msg, has_google_oauth=has_google_oauth)


@login_bp.route("/auth/google")
def auth_google():
    if not has_google_oauth:
        return redirect("/login?error=google_not_configured")
    redirect_uri = url_for("login_bp.auth_google_callback", _external=True)
    google_client = getattr(oauth, 'google', None) or oauth.create_client('google')
    return google_client.authorize_redirect(redirect_uri)


@login_bp.route("/auth/google/callback")
def auth_google_callback():
    if not has_google_oauth:
        return redirect("/login")
    google_client = getattr(oauth, 'google', None) or oauth.create_client('google')
    token = google_client.authorize_access_token()
    user_info = token.get("userinfo")

    if not user_info:
        return redirect("/login")

    google_id = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name", email.split("@")[0])

    user = User.query.filter_by(google_id=google_id).first()

    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
            user.auth_provider = "google"
            user.email_verified = True
            db.session.commit()

    if user:
        session.clear()
        session["user_id"] = user.id
        session["user_name"] = user.full_name
        session["user_email"] = user.email
        if not profile_is_complete(user):
            session["pending_google_email"] = user.email
            return redirect("/register?google=1")
        return redirect("/dashboard")
    else:
        session["pending_google_email"] = email
        session["pending_google_name"] = name
        session["pending_google_id"] = google_id
        return redirect("/register?google=1")


@login_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email or "@" not in email:
            return render_template("forgot_password.html", error="Please enter a valid email address.")

        user = User.query.filter_by(email=email).first()
        if not user:
            return render_template("forgot_password.html", error="No account found with this email address.")

        otp = str(random.randint(100000, 999999))
        session["fp_otp"] = otp
        session["fp_email"] = email

        if send_otp_email(email, otp):
            return redirect("/forgot-password/verify")
        else:
            return render_template("forgot_password.html", error="Failed to send OTP. Please try again.")

    return render_template("forgot_password.html", error=None)


@login_bp.route("/forgot-password/verify", methods=["GET", "POST"])
def forgot_password_verify():
    if "fp_otp" not in session or "fp_email" not in session:
        return redirect("/forgot-password")

    email = session["fp_email"]
    if request.method == "GET":
        return render_template("verify_otp.html", error=None, email=email, next_step="reset_password")

    entered = (request.form.get("otp") or "").strip()
    if entered == session.get("fp_otp"):
        session.pop("fp_otp", None)
        session["fp_verified_email"] = email
        session.pop("fp_email", None)
        return redirect("/forgot-password/reset")

    return render_template("verify_otp.html", error="Invalid OTP. Please try again.", email=email, next_step="reset_password")


@login_bp.route("/forgot-password/reset", methods=["GET", "POST"])
def forgot_password_reset():
    email = session.get("fp_verified_email")
    if not email:
        return redirect("/forgot-password")

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()

        if not password or len(password) < 6:
            return render_template("set_password.html", error="Password must be at least 6 characters.", email=email, is_reset=True)
        if password != confirm:
            return render_template("set_password.html", error="Passwords do not match.", email=email, is_reset=True)

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(password)
            db.session.commit()
        session.pop("fp_verified_email", None)
        return redirect("/login?msg=password_reset")

    return render_template("set_password.html", error=None, email=email, is_reset=True)


@login_bp.route("/auth/otp/send", methods=["GET", "POST"])
def send_otp():
    if request.method == "GET":
        return render_template("send_otp.html", error=None)

    try:
        email = (request.form.get("email") or "").strip().lower()
        if not email or "@" not in email:
            return render_template("send_otp.html", error="Please enter a valid email address.")

        user = User.query.filter_by(email=email).first()
        if not user:
            user_name = email.split("@")[0].capitalize()
            user = User(
                full_name=user_name,
                email=email,
                password=generate_password_hash(os.urandom(24).hex()),
                auth_provider="otp",
                email_verified=True
            )
            db.session.add(user)
            try:
                db.session.commit()
                print(f"[OTP] Auto-created user account for {email}")
            except Exception as e:
                db.session.rollback()
                print(f"[OTP] Error auto-creating user account: {e}")

        otp = str(random.randint(100000, 999999))
        session["otp_code"] = otp
        session["otp_email"] = email

        if send_otp_email(email, otp):
            return redirect("/auth/otp/verify")
        else:
            return render_template("send_otp.html", error="Failed to send OTP email. Please try again or use password login.")

    except Exception as e:
        print(f"[send_otp] Unexpected error: {e}")
        db.session.rollback()
        return render_template("send_otp.html", error="Something went wrong. Please try again.")


@login_bp.route("/auth/otp/verify", methods=["GET", "POST"])
def verify_otp():
    if "otp_code" not in session:
        return redirect("/auth/otp/send")

    if request.method == "GET":
        return render_template("verify_otp.html", error=None, email=session.get("otp_email", ""))

    entered = (request.form.get("otp") or "").strip()
    if entered == session.get("otp_code"):
        email = session.pop("otp_email", None)
        session.pop("otp_code", None)
        user = User.query.filter_by(email=email).first()
        if user:
            session.clear()
            session["user_id"] = user.id
            session["user_name"] = user.full_name
            session["user_email"] = user.email
            if not profile_is_complete(user):
                return redirect("/register")
            return redirect("/dashboard")
    return render_template("verify_otp.html", error="Invalid OTP. Please try again.", email=session.get("otp_email", ""))


@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
