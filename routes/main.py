import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename
from extensions import db
from models.models import (
    DisasterAlert, DisasterReport, Shelter, Hospital, PoliceStation,
    FireStation, RescueRequest, Volunteer, WeatherData, RiskPrediction, Notification
)
from services.weather_service import get_weather_for_city, CITY_COORDINATES
from services.alert_service import refresh_forecast_alerts
from services.notification_service import create_notification

main_bp = Blueprint('main', __name__, template_folder='../templates')

@main_bp.route('/mobile-entry')
def mobile_entry():
    if current_user.is_authenticated:
        logout_user()
    session['mobile_app'] = True
    return redirect(url_for('auth.login'))


def allowed_file(filename):
    allowed = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


@main_bp.route('/')
def index():
    refresh_forecast_alerts()
    alerts = DisasterAlert.query.filter_by(status='Active').order_by(DisasterAlert.created_at.desc()).limit(6).all()
    critical_alerts = DisasterAlert.query.filter_by(status='Active', severity='Critical').all()
    stats = {
        'active_disasters': DisasterAlert.query.filter_by(status='Active').count(),
        'safe_shelters': Shelter.query.count(),
        'rescue_requests': RescueRequest.query.filter(RescueRequest.status != 'Resolved').count(),
        'verified_reports': DisasterReport.query.filter_by(verified=True).count()
    }
    recent_reports = DisasterReport.query.filter_by(verified=True).order_by(DisasterReport.created_at.desc()).limit(4).all()
    return render_template('index.html', alerts=alerts, critical_alerts=critical_alerts, stats=stats, recent_reports=recent_reports)


@main_bp.route('/alerts')
def alerts():
    refresh_forecast_alerts()
    category = request.args.get('category', '').strip()
    severity = request.args.get('severity', '').strip()
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    query = DisasterAlert.query

    if category and category != 'All':
        query = query.filter_by(disaster_type=category)
    if severity and severity != 'All':
        query = query.filter_by(severity=severity)
    if status and status != 'All':
        query = query.filter_by(status=status)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (DisasterAlert.title.ilike(search_pattern)) |
            (DisasterAlert.location.ilike(search_pattern)) |
            (DisasterAlert.description.ilike(search_pattern))
        )

    alerts_list = query.order_by(DisasterAlert.created_at.desc()).all()
    return render_template('alerts.html', alerts=alerts_list, selected_category=category, selected_severity=severity, selected_status=status, search_query=search)


@main_bp.route('/live-map')
def live_map():
    shelters = Shelter.query.all()
    return render_template('map.html', shelters=shelters)


@main_bp.route('/emergency')
def emergency():
    return render_template('emergency.html')


@main_bp.route('/shelters')
def shelters():
    all_shelters = Shelter.query.order_by(Shelter.name).all()
    return render_template('shelters.html', shelters=all_shelters)


@main_bp.route('/services')
def services():
    hospitals = Hospital.query.all()
    police = PoliceStation.query.all()
    fire_stations = FireStation.query.all()
    return render_template('services.html', hospitals=hospitals, police=police, fire_stations=fire_stations)


@main_bp.route('/weather')
def weather():
    city = request.args.get('city', 'Chennai')
    refresh_forecast_alerts([city])
    weather_data = get_weather_for_city(city)
    latest_prediction = RiskPrediction.query.filter_by(location=city).order_by(RiskPrediction.created_at.desc()).first()
    if not latest_prediction:
        latest_prediction = RiskPrediction.query.order_by(RiskPrediction.created_at.desc()).first()
    
    available_cities = list(CITY_COORDINATES.keys())
    return render_template('weather.html', weather=weather_data, risk=latest_prediction, current_city=city, cities=available_cities)


@main_bp.route('/preparedness')
def preparedness():
    return render_template('preparedness.html')


@main_bp.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        # If user is logged in use their id, else allow guest submissions
        user_id = current_user.id if current_user.is_authenticated and not getattr(current_user, 'is_admin', False) else None
        
        # If user is not logged in, we can either link to demo user or allow anonymous report
        if not user_id:
            from models.models import User
            demo_user = User.query.filter_by(username='citizen').first()
            user_id = demo_user.id if demo_user else 1

        disaster_type = request.form.get('disaster_type', 'Flood')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        
        try:
            lat = float(request.form.get('latitude')) if request.form.get('latitude') else None
            lon = float(request.form.get('longitude')) if request.form.get('longitude') else None
        except (ValueError, TypeError):
            lat, lon = None, None

        if not title or not description or not location:
            flash('Please complete all required fields (Title, Location, Description).', 'danger')
            return render_template('report.html')

        image_filename = None
        video_filename = None

        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        os.makedirs(upload_folder, exist_ok=True)

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                unique_name = f"img_{uuid.uuid4().hex[:10]}.{ext}"
                file.save(os.path.join(upload_folder, unique_name))
                image_filename = unique_name

        if 'video' in request.files:
            vfile = request.files['video']
            if vfile and vfile.filename != '' and allowed_file(vfile.filename):
                ext = vfile.filename.rsplit('.', 1)[1].lower()
                unique_name = f"vid_{uuid.uuid4().hex[:10]}.{ext}"
                vfile.save(os.path.join(upload_folder, unique_name))
                video_filename = unique_name

        report_obj = DisasterReport(
            user_id=user_id,
            disaster_type=disaster_type,
            title=title,
            description=description,
            location=location,
            latitude=lat,
            longitude=lon,
            image=image_filename,
            video=video_filename,
            status='Pending Verification',
            verified=False
        )
        db.session.add(report_obj)

        create_notification(
            title="Citizen Disaster Report Submitted",
            message=f"A new report '{title}' in {location} was submitted and is pending verification.",
            level="info"
        )

        db.session.commit()
        flash('Your disaster report has been submitted successfully! It will appear on the Live Map once verified by emergency administrators.', 'success')
        return redirect(url_for('main.user_reports'))

    return render_template('report.html')


@main_bp.route('/reports')
@login_required
def user_reports():
    if getattr(current_user, 'is_admin', False):
        return redirect(url_for('admin.reports'))
        
    reports = DisasterReport.query.filter_by(user_id=current_user.id).order_by(DisasterReport.created_at.desc()).all()
    user_rescues = RescueRequest.query.filter_by(user_id=current_user.id).order_by(RescueRequest.created_at.desc()).all()
    return render_template('user_reports.html', reports=reports, rescues=user_rescues)


@main_bp.route('/volunteer', methods=['GET', 'POST'])
def volunteer():
    if request.method == 'POST':
        user_id = current_user.id if current_user.is_authenticated and not getattr(current_user, 'is_admin', False) else None
        
        if not user_id:
            flash('Please log in or create an account to register as an emergency volunteer.', 'info')
            return redirect(url_for('auth.login', next=url_for('main.volunteer')))

        skills_list = request.form.getlist('skills')
        other_skills = request.form.get('other_skills', '').strip()
        if other_skills:
            skills_list.append(other_skills)
        skills = ", ".join(skills_list) if skills_list else "General Disaster Relief"

        location = request.form.get('location', '').strip() or current_user.address or 'City Center'
        contact_number = request.form.get('contact_number', '').strip() or current_user.phone or 'N/A'
        availability = request.form.get('availability', 'Available')

        vol = Volunteer.query.filter_by(user_id=user_id).first()
        if not vol:
            vol = Volunteer(
                user_id=user_id,
                skills=skills,
                location=location,
                available=(availability == 'Available'),
                status=availability,
                contact_number=contact_number
            )
            db.session.add(vol)
        else:
            vol.skills = skills
            vol.location = location
            vol.status = availability
            vol.available = (availability == 'Available')
            vol.contact_number = contact_number

        current_user.is_volunteer = True
        current_user.volunteer_status = availability
        db.session.commit()

        flash('Thank you! Your volunteer profile has been registered. Operations coordinators will contact you during emergencies in your area.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('volunteer.html')


@main_bp.route('/request-rescue', methods=['GET', 'POST'])
def request_rescue():
    if request.method == 'POST':
        user_id = current_user.id if current_user.is_authenticated and not getattr(current_user, 'is_admin', False) else None
        if not user_id:
            from models.models import User
            demo_user = User.query.filter_by(username='citizen').first()
            user_id = demo_user.id if demo_user else 1

        emergency_type = request.form.get('emergency_type', 'Stranded Evacuation')
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        
        try:
            lat = float(request.form.get('latitude')) if request.form.get('latitude') else None
            lon = float(request.form.get('longitude')) if request.form.get('longitude') else None
            people_count = int(request.form.get('people_count', 1))
        except (ValueError, TypeError):
            lat, lon = None, None
            people_count = 1

        priority = request.form.get('priority', 'High')

        image_filename = None
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        os.makedirs(upload_folder, exist_ok=True)

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                unique_name = f"rescue_{uuid.uuid4().hex[:10]}.{ext}"
                file.save(os.path.join(upload_folder, unique_name))
                image_filename = unique_name

        rescue = RescueRequest(
            user_id=user_id,
            emergency_type=emergency_type,
            description=description,
            location=location,
            latitude=lat,
            longitude=lon,
            people_count=people_count,
            priority=priority,
            image=image_filename,
            status='Pending'
        )
        db.session.add(rescue)

        create_notification(
            title=f"🚨 New Rescue Request ({priority} Priority)",
            message=f"{people_count} person(s) need assistance for '{emergency_type}' at {location}.",
            level="danger" if priority == 'Critical' else "warning"
        )

        db.session.commit()
        flash('Rescue assistance request submitted immediately! Emergency response teams have received your coordinates.', 'success')
        return redirect(url_for('main.user_reports'))

    return render_template('request_rescue.html')
