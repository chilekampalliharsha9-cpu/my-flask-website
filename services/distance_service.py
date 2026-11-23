import math
from models.models import Shelter, Hospital, PoliceStation, FireStation

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth (in kilometers).
    """
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
    
    R = 6371.0 # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def find_nearest_shelters(user_lat, user_lon, limit=5):
    """
    Find nearest safe shelters with available capacity.
    """
    shelters = Shelter.query.all()
    results = []
    for s in shelters:
        if s.latitude is not None and s.longitude is not None:
            dist = haversine(user_lat, user_lon, s.latitude, s.longitude)
            data = s.to_dict()
            data['distance_km'] = dist
            results.append(data)
    
    results.sort(key=lambda x: x['distance_km'])
    return results[:limit]


def find_nearest_hospitals(user_lat, user_lon, limit=5):
    """
    Find nearest hospitals with distance.
    """
    hospitals = Hospital.query.all()
    results = []
    for h in hospitals:
        if h.latitude is not None and h.longitude is not None:
            dist = haversine(user_lat, user_lon, h.latitude, h.longitude)
            data = h.to_dict()
            data['distance_km'] = dist
            results.append(data)
    
    results.sort(key=lambda x: x['distance_km'])
    return results[:limit]


def find_all_nearest_emergency(user_lat, user_lon):
    """
    Find nearest shelter, hospital, police station, and fire station for quick SOS overview.
    """
    nearest_shelter = find_nearest_shelters(user_lat, user_lon, limit=1)
    nearest_hospital = find_nearest_hospitals(user_lat, user_lon, limit=1)
    
    police_stations = PoliceStation.query.all()
    p_results = []
    for p in police_stations:
        if p.latitude and p.longitude:
            dist = haversine(user_lat, user_lon, p.latitude, p.longitude)
            d = p.to_dict()
            d['distance_km'] = dist
            p_results.append(d)
    p_results.sort(key=lambda x: x['distance_km'])
    
    fire_stations = FireStation.query.all()
    f_results = []
    for f in fire_stations:
        if f.latitude and f.longitude:
            dist = haversine(user_lat, user_lon, f.latitude, f.longitude)
            d = f.to_dict()
            d['distance_km'] = dist
            f_results.append(d)
    f_results.sort(key=lambda x: x['distance_km'])

    return {
        'nearest_shelter': nearest_shelter[0] if nearest_shelter else None,
        'nearest_hospital': nearest_hospital[0] if nearest_hospital else None,
        'nearest_police': p_results[0] if p_results else None,
        'nearest_fire': f_results[0] if f_results else None
    }
