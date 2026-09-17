import os
import json
import smtplib
import threading
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def _otp_html_body(otp):
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px; background: #080e1e; color: #e2e8f0; border-radius: 16px; border: 1px solid rgba(0, 255, 255, 0.25);">
      <div style="text-align: center; margin-bottom: 24px;">
        <span style="background: rgba(0, 255, 255, 0.12); color: #00ffff; border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 100px; padding: 6px 18px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;">
          Platform Access Code
        </span>
      </div>
      <h2 style="color: #ffffff; font-size: 22px; font-weight: 800; margin-bottom: 8px; text-align: center;">
        Your Temporary Login Code
      </h2>
      <p style="color: #94a3b8; font-size: 15px; line-height: 1.6; margin-bottom: 24px; text-align: center;">
        Hi there, <br><br>
        You recently requested to access the AI Assessment Studio. Please use the secure code below to complete your login securely.
      </p>
      <div style="background: rgba(0, 255, 255, 0.06); border: 1.5px solid rgba(0, 255, 255, 0.3); border-radius: 14px; text-align: center; padding: 28px 0; margin-bottom: 24px;">
        <span style="font-size: 42px; font-weight: 900; letter-spacing: 12px; color: #00ffff;">{otp}</span>
      </div>
      <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 28px;">
        <div style="color: #00ffff; font-weight: 700; font-size: 14px; margin-bottom: 6px;">
          ✓ Important Security Note
        </div>
        <div style="color: #cbd5e1; font-size: 13px; line-height: 1.6;">
          This code will expire in 10 minutes. If you did not request this code, you can safely ignore this email.
        </div>
      </div>
      <p style="color: #475569; font-size: 11px; text-align: center; margin: 0;">
        This is an automated notification from AI Assessment Studio. Please do not reply.
      </p>
    </div>
    """
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 0; background: #080e1e; border-radius: 16px; border: 1px solid rgba(0, 255, 255, 0.25); overflow: hidden;">
      <div style="background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(2, 132, 199, 0.1)); padding: 28px 32px 18px; text-align: center; border-bottom: 1px solid rgba(0, 255, 255, 0.15);">
        <div style="font-size: 28px; font-weight: 900; color: #ffffff; letter-spacing: 0.02em; margin-bottom: 4px;">AI Assessment <span style="color: #00ffff;">Studio</span></div>
        <div style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.15em;">Secure Authentication</div>
      </div>
      <div style="padding: 32px;">
        <div style="text-align: center; margin-bottom: 8px;">
          <span style="background: rgba(0, 255, 255, 0.12); color: #00ffff; border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 100px; padding: 6px 18px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;">
            One-Time Passcode
          </span>
        </div>
        <h2 style="color: #ffffff; font-size: 20px; font-weight: 800; margin: 16px 0 8px; text-align: center;">Your Verification Code</h2>
        <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin-bottom: 24px; text-align: center;">
          Enter this code to securely access your <strong style="color: #e2e8f0;">AI Assessment Studio</strong> workspace.
        </p>
        <div style="background: rgba(0, 255, 255, 0.06); border: 1.5px solid rgba(0, 255, 255, 0.3); border-radius: 14px; text-align: center; padding: 28px 0; margin-bottom: 24px;">
          <span style="font-size: 42px; font-weight: 900; letter-spacing: 12px; color: #00ffff;">{otp}</span>
        </div>
        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 16px; margin-bottom: 20px;">
          <div style="color: #94a3b8; font-size: 13px; line-height: 1.6;">
            &#8987; Valid for <strong style="color: #e2e8f0;">10 minutes</strong> &nbsp;|&nbsp; &#128274; Do not share this code with anyone
          </div>
        </div>
        <div style="text-align: center;">
          <a href="https://ai-interview-platform-3-vdic.onrender.com" style="color: #00ffff; font-size: 13px; font-weight: 600; text-decoration: none;">Visit AI Assessment Studio &rarr;</a>
        </div>
      </div>
      <div style="padding: 16px 32px; border-top: 1px solid rgba(255, 255, 255, 0.06); text-align: center;">
        <p style="color: #475569; font-size: 11px; margin: 0;">This is an automated message from AI Assessment Studio. Please do not reply.</p>
      </div>
    </div>
    """

def _send_via_resend(to_email, otp, api_key):
    """Send via Resend HTTP API (port 443 - works on Render free tier)."""
    from_addr = os.environ.get("MAIL_FROM", f"AI Assessment Studio <onboarding@{os.environ.get('RESEND_DOMAIN', 'resend.dev')}>")
    payload = json.dumps({
        "from": from_addr,
        "to": [to_email],
        "subject": "Your AI Assessment Studio login code",
        "html": _otp_html_body(otp),
        "text": f"Hi there,\n\nYou recently requested to access the AI Assessment Studio. Please use the secure code below to complete your login securely.\n\nCode: {otp}\n\nThis code will expire in 10 minutes. If you did not request this code, you can safely ignore this email.\n\nVisit: https://ai-interview-platform-3-vdic.onrender.com"
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
            print(f"[OTP] Resend response: {resp.status} {body[:120]}")
            return resp.status in (200, 201)
    except urllib.error.HTTPError as http_err:
        err_body = http_err.read().decode() if http_err.fp else ""
        print(f"[OTP] Resend HTTP error {http_err.code}: {err_body[:200]}")
        return False
    except urllib.error.URLError as url_err:
        print(f"[OTP] Resend URL error: {url_err.reason}")
        return False


def _send_via_sendgrid(to_email, otp, api_key):
    """Send via SendGrid HTTP API (port 443 - works on Render free tier)."""
    from_addr = os.environ.get("MAIL_FROM", "noreply@yourdomain.com")
    payload = json.dumps({
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_addr, "name": "AI Assessment Studio"},
        "subject": "Your AI Assessment Studio login code",
        "content": [
            {"type": "text/plain", "value": f"Hi there,\n\nYou recently requested to access the AI Assessment Studio. Please use the secure code below to complete your login securely.\n\nCode: {otp}\n\nThis code will expire in 10 minutes. If you did not request this code, you can safely ignore this email.\n\nVisit: https://ai-interview-platform-3-vdic.onrender.com"},
            {"type": "text/html",  "value": _otp_html_body(otp)},
        ]
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[OTP] SendGrid response: {resp.status}")
            return resp.status == 202
    except urllib.error.HTTPError as http_err:
        err_body = http_err.read().decode() if http_err.fp else ""
        print(f"[OTP] SendGrid HTTP error {http_err.code}: {err_body[:200]}")
        return False
    except urllib.error.URLError as url_err:
        print(f"[OTP] SendGrid URL error: {url_err.reason}")
        return False


def _send_via_smtp(to_email, otp, mail_user, mail_pass):
    """SMTP fallback - may be blocked on Render free tier."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your AI Assessment Studio login code"
    msg["From"] = f"AI Assessment Studio <{mail_user}>"
    msg["To"] = to_email
    msg.attach(MIMEText(f"Hi there,\n\nYou recently requested to access the AI Assessment Studio. Please use the secure code below to complete your login securely.\n\nCode: {otp}\n\nThis code will expire in 10 minutes. If you did not request this code, you can safely ignore this email.\n\nVisit: https://ai-interview-platform-3-vdic.onrender.com", "plain"))
    msg.attach(MIMEText(_otp_html_body(otp), "html"))

    import socket
    result = {"ok": False}

    def _smtp_thread():
        try:
            old_to = socket.getdefaulttimeout()
            socket.setdefaulttimeout(15)
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(mail_user, mail_pass)
                server.sendmail(mail_user, [to_email], msg.as_string())
            result["ok"] = True
            print(f"[OTP] SMTP sent to {to_email} successfully.")
        except Exception as exc:
            print(f"[OTP] SMTP error: {exc}")
        finally:
            socket.setdefaulttimeout(old_to if 'old_to' in dir() else None)

    t = threading.Thread(target=_smtp_thread, daemon=True)
    t.start()
    t.join(timeout=8)
    return result["ok"]


def send_slot_unlocked_email(to_email, candidate_name):
    """Send an automated HTML notification email when candidate slot is unlocked."""
    subject = "🎉 Your Assessment Slot Has Been Unlocked - AI Assessment Studio"
    candidate_display = (candidate_name or "Candidate").strip()
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px; background: #080e1e; color: #e2e8f0; border-radius: 16px; border: 1px solid rgba(0, 255, 255, 0.25);">
      <div style="text-align: center; margin-bottom: 24px;">
        <span style="background: rgba(0, 255, 255, 0.12); color: #00ffff; border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 100px; padding: 6px 18px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;">
          Assessment Status Update
        </span>
      </div>
      <h2 style="color: #ffffff; font-size: 22px; font-weight: 800; margin-bottom: 8px; text-align: center;">
        New Interview Slot Authorized!
      </h2>
      <p style="color: #94a3b8; font-size: 15px; line-height: 1.6; margin-bottom: 24px; text-align: center;">
        Great news, <strong>{candidate_display}</strong>! An additional standard evaluation slot has been unlocked for your account on AI Assessment Studio.
      </p>
      <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 28px;">
        <div style="color: #00ffff; font-weight: 700; font-size: 14px; margin-bottom: 6px;">
          ✓ What's Next?
        </div>
        <div style="color: #cbd5e1; font-size: 13px; line-height: 1.6;">
          Log in to your workspace dashboard to launch your new assessment session. Ensure your camera, microphone, and quiet environment are ready.
        </div>
      </div>
      <div style="text-align: center; margin-bottom: 24px;">
        <a href="https://ai-interview-platform-3-vdic.onrender.com" style="background: linear-gradient(135deg, #00ffff, #0284c7); color: #020510; text-decoration: none; padding: 12px 32px; border-radius: 10px; font-weight: 800; font-size: 15px; display: inline-block;">
          Open AI Assessment Studio &rarr;
        </a>
      </div>
      <p style="color: #475569; font-size: 11px; text-align: center; margin: 0;">
        This is an automated notification from AI Assessment Studio. Please do not reply.
      </p>
    </div>
    """
    
    text_content = f"Hello {candidate_display},\n\nYour standard assessment slot has been unlocked! Log in to your workspace to begin your new evaluation session.\n\nOpen AI Assessment Studio: https://ai-interview-platform-3-vdic.onrender.com"

    def _dispatch():
        mail_user = (os.environ.get("MAIL_USERNAME") or "").strip()
        mail_pass = (os.environ.get("MAIL_PASSWORD") or "").replace(" ", "").strip()
        if mail_user and mail_pass:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"AI Assessment Studio <{mail_user}>"
                msg["To"] = to_email
                msg["Auto-Submitted"] = "auto-generated"
                msg.attach(MIMEText(text_content, "plain"))
                msg.attach(MIMEText(html_content, "html"))
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(mail_user, mail_pass)
                    server.sendmail(mail_user, [to_email], msg.as_string())
                print(f"[UNLOCK EMAIL] SMTP sent to {to_email}")
                return
            except Exception as exc:
                print(f"[UNLOCK EMAIL] SMTP error: {exc}")

        resend_key = (os.environ.get("RESEND_API_KEY") or "").strip()
        if resend_key:
            try:
                from_addr = os.environ.get("MAIL_FROM", f"AI Assessment Studio <{mail_user if mail_user else 'onboarding@resend.dev'}>")
                payload = json.dumps({
                    "from": from_addr,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content,
                    "text": text_content
                }).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.resend.com/emails",
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {resend_key}",
                        "Content-Type": "application/json",
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    print(f"[UNLOCK EMAIL] Resend status: {resp.status}")
                    return
            except Exception as e:
                print(f"[UNLOCK EMAIL] Resend error: {e}")

    t = threading.Thread(target=_dispatch, daemon=True)
    t.start()


def send_otp_email(to_email, otp):
    """
    Send OTP email. Tries providers in priority order:
      1. Gmail SMTP (MAIL_USERNAME + MAIL_PASSWORD - primary sender)
      2. Resend  (fallback - set RESEND_API_KEY)
      3. SendGrid (fallback - set SENDGRID_API_KEY)
    If none are configured, prints OTP to logs (dev/local fallback).
    """
    print(f"[OTP] ── Sending OTP to {to_email} ──")

    # 1. Gmail SMTP (primary)
    mail_user = (os.environ.get("MAIL_USERNAME") or "").strip()
    mail_pass = (os.environ.get("MAIL_PASSWORD") or "").replace(" ", "").strip()
    if mail_user and mail_pass:
        print(f"[OTP] Trying Gmail SMTP ({mail_user})...")
        try:
            result = _send_via_smtp(to_email, otp, mail_user, mail_pass)
            if result:
                print(f"[OTP] ✓ Gmail SMTP: sent to {to_email}")
                return True
            else:
                print(f"[OTP] ✗ Gmail SMTP returned False, trying next provider...")
        except Exception as e:
            print(f"[OTP] ✗ Gmail SMTP exception: {e}")

    # 2. Resend (fallback)
    resend_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    if resend_key:
        print(f"[OTP] Trying Resend...")
        try:
            ok = _send_via_resend(to_email, otp, resend_key)
            if ok:
                print(f"[OTP] ✓ Resend: sent to {to_email}")
                return True
            else:
                print(f"[OTP] ✗ Resend returned False, trying next provider...")
        except Exception as e:
            print(f"[OTP] ✗ Resend exception: {e}")

    # 3. SendGrid (fallback)
    sg_key = (os.environ.get("SENDGRID_API_KEY") or "").strip()
    if sg_key:
        print(f"[OTP] Trying SendGrid...")
        try:
            ok = _send_via_sendgrid(to_email, otp, sg_key)
            if ok:
                print(f"[OTP] ✓ SendGrid: sent to {to_email}")
                return True
            else:
                print(f"[OTP] ✗ SendGrid returned False")
        except Exception as e:
            print(f"[OTP] ✗ SendGrid exception: {e}")

    # Dev fallback
    print(f"[OTP] No email provider configured. OTP for {to_email}: {otp}")
    return True
