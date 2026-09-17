import os
from flask import Flask, render_template, request, redirect, session, jsonify
from MODULES.LAYER_1_CORE_INFRASTRUCTURE.extensions import db, oauth
from MODULES.LAYER_1_CORE_INFRASTRUCTURE import config
from MODULES.LAYER_4_ROUTE_CONTROLLERS import register_blueprints

def create_app():
    # Set template and static folders relative to project root
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    template_folder = os.path.join(root_dir, 'templates')
    static_folder = os.path.join(root_dir, 'static')

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder
    )
    app.secret_key = config.SECRET_KEY

    # Session cookie security
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if config.IS_PRODUCTION:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["PREFERRED_URL_SCHEME"] = "https"

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    if config.SQLALCHEMY_ENGINE_OPTIONS:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = config.SQLALCHEMY_ENGINE_OPTIONS

    # Uploads configuration
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

    # Initialize extensions
    db.init_app(app)
    oauth.init_app(app)

    # Register Google OAuth provider
    if config.has_google_oauth:
        oauth.register(
            name='google',
            client_id=config.GOOGLE_CLIENT_ID,
            client_secret=config.GOOGLE_CLIENT_SECRET,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )

    # Performance optimization: static asset caching
    @app.after_request
    def add_performance_headers(response):
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=86400'
        return response

    # Security headers
    @app.after_request
    def apply_security_headers(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
        if config.IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Error handlers
    @app.errorhandler(413)
    def request_entity_too_large(error):
        if "user_id" in session:
            return redirect("/dashboard?error=file_too_large")
        return redirect("/login?error=file_too_large")

    @app.errorhandler(500)
    def internal_server_error(error):
        try:
            db.session.rollback()
        except Exception:
            pass
        print(f"[Internal Server Error]: {error}")
        if request.path == "/interview/submit" or request.headers.get("Content-Type", "").startswith("application/json"):
            return jsonify({
                "error": "server_error",
                "question": "Can you walk me through a challenging problem you solved recently?",
                "q_num": session.get("q_count", 0) + 1,
                "total": 10,
                "question_type": "text",
                "done": False
            }), 200
        back_url = "/dashboard" if "user_id" in session else "/login"
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Error</title>
        <style>body{{font-family:sans-serif;background:#0a0f1e;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;flex-direction:column;gap:16px}}
        h2{{color:#00ffff}}a{{color:#00ffff;font-weight:bold}}</style></head>
        <body><h2>⚠️ Something went wrong</h2>
        <p>A temporary server error occurred. Your interview progress is saved.</p>
        <a href="{back_url}">← Return to Dashboard</a></body></html>""", 500

    # Register blueprints
    register_blueprints(app)

    # Initialize tables and verify schema
    with app.app_context():
        try:
            db.create_all()
            try:
                engine = db.engine
                with engine.connect() as conn:
                    from sqlalchemy import inspect, text
                    inspector = inspect(engine)
                    if inspector.has_table('users'):
                        columns = [c['name'] for c in inspector.get_columns('users')]
                        if 'resume_text' not in columns:
                            conn.execute(text("ALTER TABLE users ADD COLUMN resume_text TEXT"))
                            conn.commit()
                            print("Added column 'resume_text' dynamically to users table.")
                        if 'resume_filename' not in columns:
                            conn.execute(text("ALTER TABLE users ADD COLUMN resume_filename VARCHAR(255)"))
                            conn.commit()
                            print("Added column 'resume_filename' dynamically to users table.")
                        if 'extra_allowed_interviews' not in columns:
                            conn.execute(text("ALTER TABLE users ADD COLUMN extra_allowed_interviews INT DEFAULT 0"))
                            conn.commit()
                            print("Added column 'extra_allowed_interviews' dynamically to users table.")
                    if inspector.has_table('interview_results'):
                        res_columns = [c['name'] for c in inspector.get_columns('interview_results')]
                        if 'is_terminated' not in res_columns:
                            conn.execute(text("ALTER TABLE interview_results ADD COLUMN is_terminated BOOLEAN DEFAULT 0"))
                            conn.commit()
                            print("Added column 'is_terminated' dynamically to interview_results table.")
                        if 'termination_reason' not in res_columns:
                            conn.execute(text("ALTER TABLE interview_results ADD COLUMN termination_reason TEXT"))
                            conn.commit()
                            print("Added column 'termination_reason' dynamically to interview_results table.")
            except Exception as schema_err:
                print(f"Schema check notice: {schema_err}")
            print("Database tables verified/created successfully.")
        except Exception as e:
            print(f"Error creating/verifying database tables: {e}")

    return app
