from datetime import datetime

from extensions import db
from models.models import DisasterAlert
from services.weather_service import CITY_COORDINATES, get_forecasts_for_cities


def _severity_for_rain(rainfall, probability):
    if rainfall >= 80:
        return 'Critical'
    if rainfall >= 50:
        return 'High'
    if rainfall >= 25:
        return 'Moderate'
    if rainfall >= 10 and probability >= 70:
        return 'Low'
    return None


def _severity_for_wind(wind_speed):
    if wind_speed >= 90:
        return 'Critical'
    if wind_speed >= 70:
        return 'High'
    if wind_speed >= 50:
        return 'Moderate'
    if wind_speed >= 35:
        return 'Low'
    return None


def refresh_forecast_alerts(city_names=None):
    """Upsert forecast advisories while leaving authority-issued alerts untouched."""
    city_names = city_names or list(CITY_COORDINATES)
    forecasts = get_forecasts_for_cities(city_names)
    if not forecasts:
        return {'available': False, 'updated': 0}

    updated = 0
    for forecast in forecasts:
        city = forecast['location']
        city_info = CITY_COORDINATES[city]
        rainfall = float(forecast['rainfall_mm'] or 0)
        probability = float(forecast['precipitation_probability'] or 0)
        wind_speed = float(forecast['wind_speed_kmh'] or 0)
        desired = {}

        rain_severity = _severity_for_rain(rainfall, probability)
        if rain_severity:
            title = f'Weather forecast: Flood risk - {city}'
            desired[title] = {
                'disaster_type': 'Flood',
                'severity': rain_severity,
                'description': (
                    f"The next 24-hour forecast indicates peak hourly rainfall of {rainfall:.1f} mm "
                    f"with up to {probability:.0f}% precipitation probability in {city}."
                ),
                'recommended_action': 'Avoid flood-prone roads and monitor local emergency instructions.'
            }

        wind_severity = _severity_for_wind(wind_speed)
        if wind_severity:
            hazard_type = 'Cyclone' if wind_speed >= 90 else 'Storm'
            title = f'Weather forecast: {hazard_type} risk - {city}'
            desired[title] = {
                'disaster_type': hazard_type,
                'severity': wind_severity,
                'description': (
                    f"The next 24-hour forecast indicates peak winds or gusts of {wind_speed:.1f} km/h "
                    f"in {city}."
                ),
                'recommended_action': 'Secure loose outdoor objects and follow official wind and evacuation advisories.'
            }

        existing = DisasterAlert.query.filter(
            DisasterAlert.location == city,
            DisasterAlert.title.like('Weather forecast:%')
        ).all()
        existing_by_title = {alert.title: alert for alert in existing}

        for alert in existing:
            if alert.title not in desired and alert.status != 'Resolved':
                alert.status = 'Resolved'
                alert.created_at = datetime.utcnow()
                updated += 1

        for title, details in desired.items():
            alert = existing_by_title.get(title)
            status = 'Active' if details['severity'] in {'High', 'Critical'} else 'Watch'
            if alert is None:
                alert = DisasterAlert(title=title, location=city)
                db.session.add(alert)

            alert.disaster_type = details['disaster_type']
            alert.description = details['description']
            alert.severity = details['severity']
            alert.latitude = city_info['lat']
            alert.longitude = city_info['lon']
            alert.affected_radius_km = 15.0
            alert.status = status
            alert.recommended_action = details['recommended_action']
            alert.created_at = datetime.utcnow()
            updated += 1

    db.session.commit()
    return {'available': True, 'updated': updated}