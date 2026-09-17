# LAYER 4: ROUTE CONTROLLERS
def register_blueprints(app):
    from MODULES.LAYER_4_ROUTE_CONTROLLERS.login_env import login_bp
    from MODULES.LAYER_4_ROUTE_CONTROLLERS.register_env import register_bp
    from MODULES.LAYER_4_ROUTE_CONTROLLERS.dashboard import dashboard_bp
    from MODULES.LAYER_4_ROUTE_CONTROLLERS.admin_env import admin_bp
    from MODULES.LAYER_4_ROUTE_CONTROLLERS.interview_engine import interview_bp
    from MODULES.LAYER_4_ROUTE_CONTROLLERS.practicemode import practice_bp
    from MODULES.LAYER_4_ROUTE_CONTROLLERS.resources import resources_bp

    app.register_blueprint(login_bp)
    app.register_blueprint(register_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(practice_bp)
    app.register_blueprint(resources_bp)
