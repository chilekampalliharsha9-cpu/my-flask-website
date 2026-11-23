import os
import requests
import random
from datetime import datetime, timedelta, timezone
from models.models import WeatherData
from extensions import db

# Predefined realistic city coordinates & baseline climatology
CITY_COORDINATES = {
    'Chennai': {'lat': 13.0827, 'lon': 80.2707, 'base_temp': 31.0, 'base_humidity': 78.0},
    'Mumbai': {'lat': 19.0760, 'lon': 72.8777, 'base_temp': 29.5, 'base_humidity': 82.0},
    'Visakhapatnam': {'lat': 17.6868, 'lon': 83.2185, 'base_temp': 30.2, 'base_humidity': 76.0},
    'Kolkata': {'lat': 22.5726, 'lon': 88.3639, 'base_temp': 32.0, 'base_humidity': 80.0},
    'Kochi': {'lat': 9.9312, 'lon': 76.2673, 'base_temp': 28.5, 'base_humidity': 85.0},
    'Hyderabad': {'lat': 17.3850, 'lon': 78.4867, 'base_temp': 33.0, 'base_humidity': 60.0},
    'Bengaluru': {'lat': 12.9716, 'lon': 77.5946, 'base_temp': 26.5, 'base_humidity': 65.0},
    'Delhi': {'lat': 28.6139, 'lon': 77.2090, 'base_temp': 34.0, 'base_humidity': 55.0},
    'Bhubaneswar': {'lat': 20.2961, 'lon': 85.8245, 'base_temp': 31.5, 'base_humidity': 79.0}
}

def calculate_risk_level(rainfall, wind_speed, humidity):
    """
    Calculate risk classification based on meteorological readings.
    """
    score = 0
    if rainfall > 150: score += 4
    elif rainfall > 80: score += 3
    elif rainfall > 35: score += 2
    elif rainfall > 10: score += 1

    if wind_speed > 90: score += 4
    elif wind_speed > 60: score += 3
    elif wind_speed > 40: score += 2
    elif wind_speed > 25: score += 1

    if humidity > 85: score += 1

    if score >= 7:
        return 'Critical'
    elif score >= 5:
        return 'Warning'
    elif score >= 3:
        return 'Watch'
    return 'Safe'


def get_weather_for_city(city_name='Chennai'):
    """
    Fetch weather data from OpenWeather API if API key is provided,
    otherwise provide dynamic, realistic simulation.
    """
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    city_info = CITY_COORDINATES.get(city_name, CITY_COORDINATES['Chennai'])

    if api_key:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                temp = data['main']['temp']
                humidity = data['main']['humidity']
                pressure = data['main']['pressure']
                wind_speed = round(data['wind']['speed'] * 3.6, 1) # m/s to km/h
                rainfall = data.get('rain', {}).get('1h', 0.0)
                condition = data['weather'][0]['description'].title()
                risk = calculate_risk_level(rainfall, wind_speed, humidity)
                return {
                    'location': city_name,
                    'temperature': temp,
                    'rainfall': rainfall,
                    'wind_speed': wind_speed,
                    'humidity': humidity,
                    'pressure': pressure,
                    'condition': condition,
                    'risk_level': risk
                }
        except Exception:
            pass # Fall back to simulated weather

    # Dynamic simulation based on realistic climatology
    base_t = city_info['base_temp']
    base_h = city_info['base_humidity']
    
    # Introduce small variations
    temp = round(base_t + random.uniform(-2.5, 2.5), 1)
    humidity = round(min(98.0, max(40.0, base_h + random.uniform(-8.0, 10.0))), 1)
    wind_speed = round(random.uniform(15.0, 55.0), 1)
    
    # Probabilistic rainfall simulation
    if city_name in ['Chennai', 'Visakhapatnam', 'Kolkata', 'Kochi', 'Mumbai']:
        rainfall = round(random.choice([12.5, 45.0, 95.0, 125.0, 5.0, 0.0]), 1)
    else:
        rainfall = round(random.choice([0.0, 2.0, 18.0, 35.0]), 1)

    if rainfall > 80:
        condition = "Heavy Torrential Rain & Gusts"
    elif rainfall > 30:
        condition = "Moderate Rainfall & Storm Clouds"
    elif rainfall > 5:
        condition = "Scattered Rain Showers"
    elif wind_speed > 40:
        condition = "High Wind Advisory"
    else:
        condition = "Partly Cloudy"

    risk = calculate_risk_level(rainfall, wind_speed, humidity)

    return {
        'location': city_name,
        'temperature': temp,
        'rainfall': rainfall,
        'wind_speed': wind_speed,
        'humidity': humidity,
        'pressure': 1008.0 + round(random.uniform(-10.0, 6.0), 1),
        'condition': condition,
        'risk_level': risk
    }


def get_forecasts_for_cities(city_names=None):
    """Return the next 24 hours of precipitation and wind forecasts by city."""
    city_names = city_names or list(CITY_COORDINATES)
    city_names = [name for name in city_names if name in CITY_COORDINATES]
    if not city_names:
        return []

    coordinates = [CITY_COORDINATES[name] for name in city_names]
    params = {
        'latitude': ','.join(f"{city['lat']:.4f}" for city in coordinates),
        'longitude': ','.join(f"{city['lon']:.4f}" for city in coordinates),
        'hourly': 'precipitation,precipitation_probability,wind_speed_10m,wind_gusts_10m',
        'forecast_days': 2,
        'timezone': 'UTC',
        'wind_speed_unit': 'kmh'
    }

    try:
        response = requests.get('https://api.open-meteo.com/v1/forecast', params=params, timeout=8)
        response.raise_for_status()
        payload = response.json()
        forecasts = payload if isinstance(payload, list) else [payload]
        now = datetime.now(timezone.utc)
        end = now + timedelta(hours=24)
        results = []

        for city_name, forecast in zip(city_names, forecasts):
            hourly = forecast.get('hourly', {})
            times = hourly.get('time', [])
            indices = []
            for index, timestamp in enumerate(times):
                forecast_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if forecast_time.tzinfo is None:
                    forecast_time = forecast_time.replace(tzinfo=timezone.utc)
                if now <= forecast_time <= end:
                    indices.append(index)

            if not indices:
                continue

            def peak(field):
                values = hourly.get(field, [])
                return max((values[index] for index in indices if index < len(values) and values[index] is not None), default=0)

            results.append({
                'location': city_name,
                'rainfall_mm': peak('precipitation'),
                'precipitation_probability': peak('precipitation_probability'),
                'wind_speed_kmh': max(peak('wind_speed_10m'), peak('wind_gusts_10m'))
            })

        return results
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return []
