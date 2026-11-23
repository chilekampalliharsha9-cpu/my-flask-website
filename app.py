import os
from flask import Flask, render_template, send_file, request, redirect, url_for, session
from config import Config
from extensions import db, migrate, login_manager, bcrypt
from flask_login import current_user, logout_user

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Ensure upload directory exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/uploads'), exist_ok=True)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    from routes.ai_routes import ai_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(ai_bp)

    @app.before_request
    def enforce_mobile_app_access():
        if not session.get('mobile_app'):
            return None

        if request.endpoint == 'main.mobile_entry':
            return None

        if request.blueprint == 'admin':
            destination = 'main.index' if current_user.is_authenticated else 'auth.login'
            return redirect(url_for(destination))

        if request.endpoint in {'auth.login', 'auth.register', 'static', 'download_apk'}:
            return None

        if not current_user.is_authenticated or getattr(current_user, 'is_admin', False):
            if current_user.is_authenticated:
                logout_user()
            return redirect(url_for('auth.login'))

        return None

    # Enable CORS for Mobile App and API clients
    @app.before_request
    def handle_options():
        from flask import request, Response
        if request.method == 'OPTIONS':
            res = Response()
            res.headers['Access-Control-Allow-Origin'] = '*'
            res.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
            res.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
            return res

    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
        return response

    # Global context processors for template rendering
    @app.context_processor
    def inject_global_data():
        from models.models import DisasterAlert
        active_critical_count = DisasterAlert.query.filter_by(status='Active', severity='Critical').count()
        return {
            'system_name': 'Smart Disaster Management System',
            'critical_alerts_count': active_critical_count
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('base.html', content_error="404 - Requested page or disaster resource was not found."), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('base.html', content_error="500 - Internal Server Error. Emergency operations center is investigating."), 500

    return app

app = create_app()

@app.route('/download-apk')
def download_apk():
    apk_path = os.path.join(app.root_path, 'SmartDisasterOps-debug.apk')
    return send_file(
        apk_path,
        mimetype='application/vnd.android.package-archive',
        as_attachment=True,
        download_name='SmartDisasterOps.apk'
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Automatically populate sample data if database is empty
        from models.models import Admin
        if not Admin.query.first():
            from seed_data import seed_database
            seed_database()
            
    app.run(host='0.0.0.0', port=5000, debug=True)
