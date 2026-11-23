from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.models import (
    Admin, User, DisasterAlert, DisasterReport, Shelter, Hospital,
    PoliceStation, FireStation, Volunteer, RescueRequest, Notification, RiskPrediction
)
from services.notification_service import create_notification

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../templates/admin')

def admin_required(func):
    """
    Decorator to ensure user is logged in as an administrator.
    """
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            flash('Administrator authentication required.', 'danger')
            return redirect(url_for('admin.login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        admin = Admin.query.filter(
            (Admin.username == username) | (Admin.email == username.lower())
        ).first()

        if admin and admin.check_password(password):
            login_user(admin, remember=True)
            flash(f'Admin command console initialized. Welcome, {admin.username}.', 'success')
            return redirect(url_for('admin.dashboard'))

        flash('Invalid administrator credentials.', 'danger')

    return render_template('login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    if getattr(current_user, 'is_admin', False):
        logout_user()
        flash('Administrator logged out successfully.', 'info')
    return redirect(url_for('admin.login'))


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_users': User.query.count(),
        'active_disasters': DisasterAlert.query.filter_by(status='Active').count(),
        'pending_reports': DisasterReport.query.filter_by(status='Pending Verification').count(),
        'verified_reports': DisasterReport.query.filter_by(verified=True).count(),
        'active_rescue_requests': RescueRequest.query.filter(RescueRequest.status != 'Resolved').count(),
        'available_shelters': Shelter.query.count(),
        'registered_volunteers': Volunteer.query.count(),
        'hospitals_count': Hospital.query.count()
    }

    # Chart Analytics Data
    # 1. Disasters by type
    all_alerts = DisasterAlert.query.all()
    disaster_types_count = {}
    for a in all_alerts:
        disaster_types_count[a.disaster_type] = disaster_types_count.get(a.disaster_type, 0) + 1

    # 2. Rescue requests by status
    rescue_status_count = {
        'Pending': RescueRequest.query.filter_by(status='Pending').count(),
        'Assigned': RescueRequest.query.filter_by(status='Assigned').count(),
        'In Progress': RescueRequest.query.filter_by(status='In Progress').count(),
        'Resolved': RescueRequest.query.filter_by(status='Resolved').count()
    }

    # 3. Report verification status
    report_status_count = {
        'Pending': DisasterReport.query.filter_by(status='Pending Verification').count(),
        'Verified': DisasterReport.query.filter_by(status='Verified').count(),
        'Rejected': DisasterReport.query.filter_by(status='Rejected').count()
    }

    recent_pending_reports = DisasterReport.query.filter_by(status='Pending Verification').order_by(DisasterReport.created_at.desc()).limit(5).all()
    critical_rescues = RescueRequest.query.filter(RescueRequest.status != 'Resolved').order_by(RescueRequest.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        stats=stats,
        disaster_types_count=disaster_types_count,
        rescue_status_count=rescue_status_count,
        report_status_count=report_status_count,
        recent_pending_reports=recent_pending_reports,
        critical_rescues=critical_rescues
    )


# -------------------- DISASTER ALERTS CRUD --------------------
@admin_bp.route('/alerts')
@login_required
@admin_required
def alerts():
    all_alerts = DisasterAlert.query.order_by(DisasterAlert.created_at.desc()).all()
    return render_template('disasters.html', alerts=all_alerts)


@admin_bp.route('/alerts/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_alert():
    if request.method == 'POST':
        try:
            lat = float(request.form.get('latitude')) if request.form.get('latitude') else None
            lon = float(request.form.get('longitude')) if request.form.get('longitude') else None
            radius = float(request.form.get('affected_radius_km', 15.0))
        except (ValueError, TypeError):
            lat, lon, radius = None, None, 15.0

        alert = DisasterAlert(
            disaster_type=request.form.get('disaster_type', 'Flood'),
            title=request.form.get('title', '').strip(),
            description=request.form.get('description', '').strip(),
            severity=request.form.get('severity', 'Moderate'),
            location=request.form.get('location', '').strip(),
            latitude=lat,
            longitude=lon,
            affected_radius_km=radius,
            status=request.form.get('status', 'Active'),
            recommended_action=request.form.get('recommended_action', '').strip()
        )
        db.session.add(alert)
        
        # Broadcast notification for High/Critical alerts
        if alert.severity in ['High', 'Critical']:
            create_notification(
                title=f"🚨 {alert.severity.upper()} ALERT: {alert.title}",
                message=f"Disaster advisory issued for {alert.location}. Recommended action: {alert.recommended_action}",
                level="danger"
            )

        db.session.commit()
        flash('Disaster alert published successfully.', 'success')
        return redirect(url_for('admin.alerts'))

    return render_template('create_alert.html')


@admin_bp.route('/alerts/edit/<int:alert_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_alert(alert_id):
    alert = DisasterAlert.query.get_or_404(alert_id)
    if request.method == 'POST':
        try:
            lat = float(request.form.get('latitude')) if request.form.get('latitude') else None
            lon = float(request.form.get('longitude')) if request.form.get('longitude') else None
            radius = float(request.form.get('affected_radius_km', 15.0))
        except (ValueError, TypeError):
            lat, lon, radius = alert.latitude, alert.longitude, 15.0

        alert.disaster_type = request.form.get('disaster_type')
        alert.title = request.form.get('title')
        alert.description = request.form.get('description')
        alert.severity = request.form.get('severity')
        alert.location = request.form.get('location')
        alert.latitude = lat
        alert.longitude = lon
        alert.affected_radius_km = radius
        alert.status = request.form.get('status')
        alert.recommended_action = request.form.get('recommended_action')

        db.session.commit()
        flash('Disaster alert updated successfully.', 'success')
        return redirect(url_for('admin.alerts'))

    return render_template('edit_alert.html', alert=alert)


@admin_bp.route('/alerts/delete/<int:alert_id>', methods=['POST', 'GET'])
@login_required
@admin_required
def delete_alert(alert_id):
    alert = DisasterAlert.query.get_or_404(alert_id)
    db.session.delete(alert)
    db.session.commit()
    flash('Disaster alert removed.', 'info')
    return redirect(url_for('admin.alerts'))


# -------------------- REPORTS VERIFICATION --------------------
@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    status_filter = request.args.get('status', 'All')
    query = DisasterReport.query
    if status_filter != 'All':
        query = query.filter_by(status=status_filter)
    all_reports = query.order_by(DisasterReport.created_at.desc()).all()
    return render_template('reports.html', reports=all_reports, current_filter=status_filter)


@admin_bp.route('/reports/verify/<int:report_id>', methods=['POST', 'GET'])
@login_required
@admin_required
def verify_report(report_id):
    report = DisasterReport.query.get_or_404(report_id)
    report.status = 'Verified'
    report.verified = True
    report.admin_notes = request.form.get('admin_notes', 'Verified by emergency command center.')
    
    create_notification(
        title="Report Verified & Broadcasted",
        message=f"Report '{report.title}' in {report.location} has been verified and pinned on the Live Disaster Map.",
        level="success",
        user_id=report.user_id
    )

    db.session.commit()
    flash(f"Report #{report.id} verified and added to Live Disaster Map.", 'success')
    return redirect(url_for('admin.reports'))


@admin_bp.route('/reports/reject/<int:report_id>', methods=['POST', 'GET'])
@login_required
@admin_required
def reject_report(report_id):
    report = DisasterReport.query.get_or_404(report_id)
    report.status = 'Rejected'
    report.verified = False
    report.admin_notes = request.form.get('admin_notes', 'Declined: Duplicate or unverified incident report.')
    
    create_notification(
        title="Report Update",
        message=f"Report '{report.title}' could not be verified by field monitors.",
        level="warning",
        user_id=report.user_id
    )

    db.session.commit()
    flash(f"Report #{report.id} marked as rejected / false report.", 'warning')
    return redirect(url_for('admin.reports'))


# -------------------- SHELTER MANAGEMENT --------------------
@admin_bp.route('/shelters', methods=['GET', 'POST'])
@login_required
@admin_required
def shelters():
    if request.method == 'POST':
        try:
            lat = float(request.form.get('latitude'))
            lon = float(request.form.get('longitude'))
            cap = int(request.form.get('capacity', 100))
            occ = int(request.form.get('occupancy', 0))
        except (ValueError, TypeError):
            flash('Invalid coordinates or capacity values.', 'danger')
            return redirect(url_for('admin.shelters'))

        shelter = Shelter(
            name=request.form.get('name', '').strip(),
            address=request.form.get('address', '').strip(),
            latitude=lat,
            longitude=lon,
            capacity=cap,
            occupancy=occ,
            food_available=bool(request.form.get('food_available')),
            water_available=bool(request.form.get('water_available')),
            medical_support=bool(request.form.get('medical_support')),
            power_backup=bool(request.form.get('power_backup')),
            contact_number=request.form.get('contact_number', '').strip()
        )
        db.session.add(shelter)
        db.session.commit()
        flash(f"Safe shelter '{shelter.name}' added successfully.", 'success')
        return redirect(url_for('admin.shelters'))

    all_shelters = Shelter.query.order_by(Shelter.name).all()
    return render_template('shelters.html', shelters=all_shelters)


@admin_bp.route('/shelters/edit/<int:shelter_id>', methods=['POST'])
@login_required
@admin_required
def edit_shelter(shelter_id):
    shelter = Shelter.query.get_or_404(shelter_id)
    shelter.name = request.form.get('name')
    shelter.address = request.form.get('address')
    shelter.capacity = int(request.form.get('capacity', shelter.capacity))
    shelter.occupancy = int(request.form.get('occupancy', shelter.occupancy))
    shelter.food_available = bool(request.form.get('food_available'))
    shelter.water_available = bool(request.form.get('water_available'))
    shelter.medical_support = bool(request.form.get('medical_support'))
    shelter.power_backup = bool(request.form.get('power_backup'))
    shelter.contact_number = request.form.get('contact_number')

    db.session.commit()
    flash(f"Shelter '{shelter.name}' updated.", 'success')
    return redirect(url_for('admin.shelters'))


@admin_bp.route('/shelters/delete/<int:shelter_id>', methods=['POST', 'GET'])
@login_required
@admin_required
def delete_shelter(shelter_id):
    shelter = Shelter.query.get_or_404(shelter_id)
    db.session.delete(shelter)
    db.session.commit()
    flash('Shelter removed.', 'info')
    return redirect(url_for('admin.shelters'))


# -------------------- EMERGENCY SERVICES --------------------
@admin_bp.route('/services', methods=['GET', 'POST'])
@login_required
@admin_required
def services():
    if request.method == 'POST':
        service_type = request.form.get('service_type')
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        contact = request.form.get('contact_number', '').strip()
        try:
            lat = float(request.form.get('latitude'))
            lon = float(request.form.get('longitude'))
        except (ValueError, TypeError):
            flash('Invalid coordinates.', 'danger')
            return redirect(url_for('admin.services'))

        if service_type == 'Hospital':
            h = Hospital(
                name=name, address=address, latitude=lat, longitude=lon,
                contact_number=contact,
                beds_total=int(request.form.get('beds_total', 100)),
                beds_available=int(request.form.get('beds_available', 20)),
                ambulance_available=bool(request.form.get('ambulance_available')),
                emergency_department=bool(request.form.get('emergency_department'))
            )
            db.session.add(h)
        elif service_type == 'Police':
            p = PoliceStation(
                name=name, address=address, latitude=lat, longitude=lon,
                contact_number=contact,
                jurisdiction=request.form.get('jurisdiction', 'City Division')
            )
            db.session.add(p)
        elif service_type == 'Fire':
            f = FireStation(
                name=name, address=address, latitude=lat, longitude=lon,
                contact_number=contact,
                fire_trucks=int(request.form.get('fire_trucks', 4)),
                rescue_boats=int(request.form.get('rescue_boats', 2))
            )
            db.session.add(f)

        db.session.commit()
        flash(f"{service_type} '{name}' registered successfully.", 'success')
        return redirect(url_for('admin.services'))

    hospitals = Hospital.query.all()
    police = PoliceStation.query.all()
    fire_stations = FireStation.query.all()
    return render_template('services.html', hospitals=hospitals, police=police, fire_stations=fire_stations)


@admin_bp.route('/services/delete/<string:service_type>/<int:item_id>', methods=['POST', 'GET'])
@login_required
@admin_required
def delete_service(service_type, item_id):
    if service_type == 'hospital':
        item = Hospital.query.get_or_404(item_id)
    elif service_type == 'police':
        item = PoliceStation.query.get_or_404(item_id)
    elif service_type == 'fire':
        item = FireStation.query.get_or_404(item_id)
    else:
        flash('Invalid service entity.', 'danger')
        return redirect(url_for('admin.services'))

    db.session.delete(item)
    db.session.commit()
    flash(f"Emergency service removed.", 'info')
    return redirect(url_for('admin.services'))


# -------------------- VOLUNTEERS & RESCUE OPERATIONS --------------------
@admin_bp.route('/volunteers')
@login_required
@admin_required
def volunteers():
    all_volunteers = Volunteer.query.order_by(Volunteer.created_at.desc()).all()
    return render_template('volunteers.html', volunteers=all_volunteers)


@admin_bp.route('/volunteers/status/<int:vol_id>', methods=['POST'])
@login_required
@admin_required
def update_volunteer_status(vol_id):
    vol = Volunteer.query.get_or_404(vol_id)
    new_status = request.form.get('status', 'Available')
    vol.status = new_status
    vol.available = (new_status == 'Available')
    if vol.user_rel:
        vol.user_rel.volunteer_status = new_status

    db.session.commit()
    flash(f"Volunteer {vol.user_rel.full_name or 'volunteer'} status updated to '{new_status}'.", 'success')
    return redirect(url_for('admin.volunteers'))


@admin_bp.route('/rescue-requests')
@login_required
@admin_required
def rescue_requests():
    requests_list = RescueRequest.query.order_by(RescueRequest.created_at.desc()).all()
    available_volunteers = Volunteer.query.filter_by(status='Available').all()
    return render_template('rescue_requests.html', requests=requests_list, volunteers=available_volunteers)


@admin_bp.route('/rescue-requests/update/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def update_rescue_request(request_id):
    rescue = RescueRequest.query.get_or_404(request_id)
    new_status = request.form.get('status', rescue.status)
    vol_id = request.form.get('assigned_volunteer_id')

    rescue.status = new_status

    if vol_id and vol_id != 'none':
        vid = int(vol_id)
        rescue.assigned_volunteer_id = vid
        vol = Volunteer.query.get(vid)
        if vol:
            vol.status = 'Assigned'
            vol.assigned_request_id = rescue.id

    if new_status == 'Resolved':
        if rescue.assigned_volunteer:
            rescue.assigned_volunteer.status = 'Available'
            rescue.assigned_volunteer.assigned_request_id = None

    create_notification(
        title=f"Rescue Request #{rescue.id} Status: {new_status}",
        message=f"Your rescue request for '{rescue.emergency_type}' is now marked as {new_status}.",
        level="success" if new_status == 'Resolved' else "info",
        user_id=rescue.user_id
    )

    db.session.commit()
    flash(f"Rescue request #{rescue.id} updated successfully.", 'success')
    return redirect(url_for('admin.rescue_requests'))
