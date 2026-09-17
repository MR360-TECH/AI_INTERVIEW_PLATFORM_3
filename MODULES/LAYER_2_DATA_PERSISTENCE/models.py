from MODULES.LAYER_1_CORE_INFRASTRUCTURE.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    gender = db.Column(db.String(10))
    education = db.Column(db.String(50))
    course = db.Column(db.String(100))
    semester = db.Column(db.String(20))
    auth_provider = db.Column(db.String(20), default='local')
    email_verified = db.Column(db.Boolean, default=False)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    registered_at = db.Column(db.DateTime, server_default=db.func.now())
    user_type = db.Column(db.String(20), default='student')
    github_url = db.Column(db.String(200))
    linkedin_url = db.Column(db.String(200))
    skills = db.Column(db.Text)
    years_of_experience = db.Column(db.String(20))
    current_designation = db.Column(db.String(100))
    resume_text = db.Column(db.Text)
    resume_filename = db.Column(db.String(255))
    extra_allowed_interviews = db.Column(db.Integer, default=0)


class InterviewResult(db.Model):
    __tablename__ = 'interview_results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Numeric(4, 2))
    status = db.Column(db.String(50))
    strengths = db.Column(db.Text)
    improvements = db.Column(db.Text)
    summary = db.Column(db.Text)
    domain = db.Column(db.String(150))
    is_terminated = db.Column(db.Boolean, default=False)
    termination_reason = db.Column(db.Text)
    interview_datetime = db.Column(db.DateTime, server_default=db.func.now())

    # Statuses that should NOT consume a token slot:
    #   - anything with 'Practice' in name
    #   - 'Abandoned (Reset)' — user reset before finishing
    #   - 'Terminated (Breach)' — auto-terminated by proctoring
    NON_COUNTING_STATUSES = ['Abandoned (Reset)', 'Terminated (Breach)']

    @property
    def session_code(self):
        """Returns a standardized unique assessment session code, e.g. AIS-000042, scalable beyond 1,000,000+ users."""
        if self.id:
            return f"AIS-{self.id:06d}"
        return "AIS-000000"

    @classmethod
    def real_attempt_filter(cls):
        """Returns SQLAlchemy filter conditions for attempts that count against the token limit.
        Only completed assessments (passed, failed, selected, rejected) consume a token."""
        from sqlalchemy import and_
        return and_(
            ~cls.status.like('%Practice%'),
            ~cls.status.in_(cls.NON_COUNTING_STATUSES)
        )



class InterviewProgress(db.Model):
    __tablename__ = 'interview_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    chat_history = db.Column(db.Text, default='[]')
    q_count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


class AdminSettings(db.Model):
    __tablename__ = 'admin_settings'
    id = db.Column(db.Integer, primary_key=True)
    min_questions = db.Column(db.Integer, default=3)
    max_questions = db.Column(db.Integer, default=8)
    pass_score = db.Column(db.Integer, default=3)
    default_difficulty = db.Column(db.String(20), default='student')
    question_timer_seconds = db.Column(db.Integer, default=90)
    enable_attempt_limits = db.Column(db.Boolean, default=True)
    default_allowed_interviews = db.Column(db.Integer, default=2)
    enable_warning_strikes = db.Column(db.Boolean, default=True)


class SettingsSnapshot:
    def __init__(self, s=None):
        self.min_questions = getattr(s, 'min_questions', 3) or 3
        self.max_questions = getattr(s, 'max_questions', 8) or 8
        self.pass_score = getattr(s, 'pass_score', 3) or 3
        self.default_difficulty = getattr(s, 'default_difficulty', 'student') or 'student'
        self.question_timer_seconds = getattr(s, 'question_timer_seconds', 90) or 90
        self.enable_attempt_limits = getattr(s, 'enable_attempt_limits', True)
        if self.enable_attempt_limits is None:
            self.enable_attempt_limits = True
        self.default_allowed_interviews = getattr(s, 'default_allowed_interviews', 2) or 2
        self.enable_warning_strikes = getattr(s, 'enable_warning_strikes', True)
        if self.enable_warning_strikes is None:
            self.enable_warning_strikes = True
