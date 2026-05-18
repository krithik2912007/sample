"""
Academic Performance Evaluation System
Main Flask Application Entry Point
"""

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from datetime import timedelta
import os
from dotenv import load_dotenv
from models import db

load_dotenv()
jwt = JWTManager()
mail = Mail()


def create_app(config_name='development'):
    app = Flask(__name__)

    # ── Configuration ──────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rec-academic-eval-secret-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://root:password@localhost/academic_eval'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-rec-2024')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    # Mail config (update with real SMTP for production)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@rec.edu')

    # ── Extensions ─────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:5000'])

    # ── Blueprints ─────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes import admin_bp
    from routes import mentor_bp
    from routes import student_bp
    from routes import evaluation_bp
    from routes import subjects_bp
    from routes.marks import marks_bp
    from routes import reports_bp
    from routes import pages_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(mentor_bp, url_prefix='/api/mentor')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(evaluation_bp, url_prefix='/api/evaluation')
    app.register_blueprint(subjects_bp, url_prefix='/api/subjects')
    app.register_blueprint(marks_bp, url_prefix='/api/marks')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
