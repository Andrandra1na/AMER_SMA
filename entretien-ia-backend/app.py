from flask import Flask
from flask_cors import CORS
from config import Config
from database.models import db
from extensions import jwt, celery, mail


def create_app(config_override=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    
    if config_override:
        app.config.update(config_override)
    
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    
    CORS(app, 
         resources={r"/api/*": {"origins": "http://localhost:5173"}}, 
         headers=['Content-Type', 'Authorization'], 
         supports_credentials=True
    )
    
    celery.conf.update(
        broker_url=app.config.get("CELERY_BROKER_URL"),
        result_backend=app.config.get("CELERY_RESULT_BACKEND")
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    with app.app_context():
          from routes.auth import auth_bp
          from routes.upload import upload_bp
          from routes.session import session_bp 
          from routes.report import report_bp
          from routes.user import user_bp
          from routes.question import question_bp
          from routes.admin import admin_bp
          from routes.recruiter_dashboard import recruiter_dashboard_bp
          from routes.admin_dashboard import admin_dashboard_bp
          
          app.register_blueprint(auth_bp)
          app.register_blueprint(upload_bp)
          app.register_blueprint(session_bp) 
          app.register_blueprint(report_bp)
          app.register_blueprint(user_bp)
          app.register_blueprint(question_bp)
          app.register_blueprint(admin_bp)
          app.register_blueprint(recruiter_dashboard_bp)
          app.register_blueprint(admin_dashboard_bp)

          from tasks import run_analysis_task

    return app
