from flask import Blueprint, jsonify, request
from flask_login import current_user
from extensions import db
from models.models import (
    DisasterAlert, DisasterReport, Shelter, Hospital, PoliceStation,
    FireStation, RescueRequest, SOSRequest, Notification, User, Volunteer
)
from services.distance_service import find_nearest_shelters, find_nearest_hospitals, find_all_nearest_emergency
from services.weather_service import get_weather_for_city
from services.alert_service import refresh_forecast_alerts
from services.notification_service import create_notification, get_user_notifications

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/mobile-health')
def mobile_health():
    return jsonify({'status': 'ok'})


@api_bp.route('/map-data')
def map_data():
    """
    Consolidated REST API endpoint for Leaflet.js interactive live map.
    """
    refresh_forecast_alerts()
    alerts = DisasterAlert.query.filter(DisasterAlert.status.in_(['Active', 'Watch'])).all()
    verified_reports = DisasterReport.query.filter_by(verified=True).all()
    shelters = Shelter.query.all()
    hospitals = Hospital.query.all()
    police = PoliceStation.query.all()
    fire_stations = FireStation.query.all()

    return jsonify({
        'status': 'success',
        'alerts': [a.to_dict() for a in alerts],
        'verified_reports': [r.to_dict() for r in verified_reports],
        'shelters': [s.to_dict() for s in shelters],
        'hospitals': [h.to_dict() for h in hospitals],
        'police': [p.to_dict() for p in police],
        'fire_stations': [f.to_dict() for f in fire_stations]
    })


@api_bp.route('/sos', methods=['POST'])
def trigger_sos():
    """
    Trigger emergency SOS request with GPS geolocation.
    """
    data = request.get_json(silent=True) or request.form.to_dict()
    
    try:
        lat = float(data.get('latitude', 0.0))
        lon = float(data.get('longitude', 0.0))
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid GPS coordinates provided.'}), 400

    emergency_type = data.get('emergency_type', 'Immediate SOS Evacuation Assistance')
    
    user_id = None
    caller_name = data.get('caller_name', 'Citizen in Distress')
    caller_phone = data.get('caller_phone', 'N/A')

    if current_user.is_authenticated and not getattr(current_user, 'is_admin', False):
        user_id = current_user.id
        caller_name = current_user.full_name or current_user.username
        caller_phone = current_user.phone or caller_phone

    # 1. Create SOS Request record
    sos = SOSRequest(
        user_id=user_id,
        caller_name=caller_name,
        caller_phone=caller_phone,
        latitude=lat,
        longitude=lon,
        emergency_type=emergency_type,
        status='Pending'
    )
    db.session.add(sos)

    # 2. Also register as a Critical Rescue Request for operations dispatch
    if user_id:
        rescue = RescueRequest(
            user_id=user_id,
            emergency_type=f"🚨 SOS: {emergency_type}",
            description=f"CRITICAL SOS broadcast triggered by {caller_name} ({caller_phone}) at GPS [{lat:.5f}, {lon:.5f}]. Immediate dispatch required.",
            location=f"GPS: {lat:.5f}, {lon:.5f}",
            latitude=lat,
            longitude=lon,
            people_count=int(data.get('people_count', 1)),
            priority='Critical',
            status='Pending'
        )
        db.session.add(rescue)

    # 3. Create critical broadcast notification
    create_notification(
        title="🚨 SOS EMERGENCY SIGNAL RECEIVED",
        message=f"SOS alert triggered at coordinates [{lat:.4f}, {lon:.4f}]. Emergency response units notified.",
        level="danger",
        user_id=user_id
    )

    db.session.commit()

    # 4. Compute nearest emergency resources
    emergency_facilities = find_all_nearest_emergency(lat, lon)

    # Emergency contacts if logged in
    contacts = []
    if current_user.is_authenticated and not getattr(current_user, 'is_admin', False):
        contacts = [c.to_dict() for c in current_user.contacts]

    return jsonify({
        'status': 'success',
        'message': 'SOS Emergency signal transmitted successfully. Dispatchers and nearest rescue units have been alerted.',
        'sos_id': sos.id,
        'coordinates': {'latitude': lat, 'longitude': lon},
        'emergency_facilities': emergency_facilities,
        'emergency_contacts': contacts,
        'hotlines': {
            'national_emergency': '112',
            'ambulance': '108',
            'police': '100',
            'fire': '101',
            'disaster_helpline': '1078'
        }
    })


@api_bp.route('/nearest-shelter')
def get_nearest_shelter():
    """
    Given user lat and lon, return nearest safe shelters.
    """
    try:
        lat = float(request.args.get('latitude', request.args.get('lat', 0.0)))
        lon = float(request.args.get('longitude', request.args.get('lon', 0.0)))
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Valid latitude and longitude required.'}), 400

    limit = int(request.args.get('limit', 5))
    results = find_nearest_shelters(lat, lon, limit=limit)
    
    return jsonify({
        'status': 'success',
        'user_location': {'latitude': lat, 'longitude': lon},
        'shelters': results
    })


@api_bp.route('/weather')
def get_weather():
    """
    Fetch weather and hazard metrics for specified city.
    """
    city = request.args.get('city', 'Chennai')
    refresh_forecast_alerts([city])
    weather_data = get_weather_for_city(city)
    return jsonify({
        'status': 'success',
        'weather': weather_data
    })


@api_bp.route('/notifications')
def fetch_notifications():
    """
    Fetch notifications for the current user or global alerts.
    """
    user_id = current_user.id if current_user.is_authenticated and not getattr(current_user, 'is_admin', False) else None
    notifs = get_user_notifications(user_id=user_id, limit=8)
    return jsonify({
        'status': 'success',
        'notifications': [n.to_dict() for n in notifs]
    })


@api_bp.route('/stats')
def get_live_stats():
    """
    Fetch real-time KPI counts.
    """
    return jsonify({
        'status': 'success',
        'active_disasters': DisasterAlert.query.filter_by(status='Active').count(),
        'safe_shelters': Shelter.query.count(),
        'rescue_requests': RescueRequest.query.filter(RescueRequest.status != 'Resolved').count(),
        'verified_reports': DisasterReport.query.filter_by(verified=True).count(),
        'registered_volunteers': Volunteer.query.count()
    })
