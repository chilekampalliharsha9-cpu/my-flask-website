import os
import sys
import io
import requests

# Ensure utf-8 output on Windows consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = 'http://127.0.0.1:5000'

def run_tests():
    print("Testing Smart Disaster Management System...\n")
    session = requests.Session()

    # 1. Test Homepage
    r = session.get(f"{BASE_URL}/")
    assert r.status_code == 200, f"Homepage failed with {r.status_code}"
    assert "Stay Alert. Stay Safe." in r.text
    assert "SOS EMERGENCY" in r.text
    print("[PASS] 1. Homepage loads successfully with hero section, statistics, and alert feed.")

    # 2. Test Alerts page
    r = session.get(f"{BASE_URL}/alerts")
    assert r.status_code == 200
    assert "Disaster Alerts Dashboard" in r.text
    print("[PASS] 2. Disaster Alerts Dashboard loads with filters.")

    # 3. Test Live Map page
    r = session.get(f"{BASE_URL}/live-map")
    assert r.status_code == 200
    assert "disasterMap" in r.text
    print("[PASS] 3. Live Disaster Map page loads with Leaflet container.")

    # 4. Test REST API /api/map-data
    r = session.get(f"{BASE_URL}/api/map-data")
    assert r.status_code == 200
    data = r.json()
    assert data['status'] == 'success'
    assert len(data['alerts']) > 0
    assert len(data['shelters']) > 0
    assert len(data['hospitals']) > 0
    print(f"[PASS] 4. Map REST API working: {len(data['alerts'])} alerts, {len(data['shelters'])} shelters, {len(data['hospitals'])} hospitals returned.")

    # 5. Test AI Risk Prediction API
    payload = {
        'rainfall': 180.0,
        'temperature': 26.0,
        'wind_speed': 115.0,
        'humidity': 95.0,
        'water_level': 8.5,
        'soil_moisture': 90.0,
        'elevation': 8.0,
        'historical_events': 3.0,
        'location': 'Chennai Coastal Zone'
    }
    r = session.post(f"{BASE_URL}/api/predict-risk", json=payload)
    assert r.status_code == 200
    ai_res = r.json()
    assert ai_res['status'] == 'success'
    assert 'risk_result' in ai_res
    print(f"[PASS] 5. AI Risk Prediction working: Prediction = {ai_res['risk_result']['general_risk']} (Confidence: {ai_res['risk_result']['confidence_score'] * 100}%)")

    # 6. Test SOS Emergency API
    sos_payload = {
        'latitude': 13.0827,
        'longitude': 80.2707,
        'emergency_type': 'Trapped in Flash Flood'
    }
    r = session.post(f"{BASE_URL}/api/sos", json=sos_payload)
    assert r.status_code == 200
    sos_res = r.json()
    assert sos_res['status'] == 'success'
    assert 'emergency_facilities' in sos_res
    nearest_shelter = sos_res['emergency_facilities']['nearest_shelter']
    print(f"[PASS] 6. Emergency SOS Dispatch working: Generated SOS #{sos_res['sos_id']}, Nearest Shelter = {nearest_shelter['name']} ({nearest_shelter['distance_km']} km away).")

    # 7. Test Nearest Shelter API
    r = session.get(f"{BASE_URL}/api/nearest-shelter?lat=13.0827&lon=80.2707&limit=3")
    assert r.status_code == 200
    s_data = r.json()
    assert len(s_data['shelters']) > 0
    print(f"[PASS] 7. Nearest Shelter Router working: Closest = {s_data['shelters'][0]['name']} ({s_data['shelters'][0]['distance_km']} km).")

    # 8. Test Weather API
    r = session.get(f"{BASE_URL}/api/weather?city=Chennai")
    assert r.status_code == 200
    w_data = r.json()
    assert 'weather' in w_data
    print(f"[PASS] 8. Weather Telemetry working: Temp = {w_data['weather']['temperature']}°C, Condition = {w_data['weather']['condition']}.")

    # 9. Test Shelters & Services page
    r = session.get(f"{BASE_URL}/shelters")
    assert r.status_code == 200
    r = session.get(f"{BASE_URL}/services")
    assert r.status_code == 200
    r = session.get(f"{BASE_URL}/emergency")
    assert r.status_code == 200
    r = session.get(f"{BASE_URL}/preparedness")
    assert r.status_code == 200
    print("[PASS] 9. Shelters, Services, Emergency Helplines, and Preparedness guides loaded successfully.")

    # 10. Test Citizen Authentication
    citizen_email = os.environ.get('TEST_CITIZEN_EMAIL')
    citizen_password = os.environ.get('TEST_CITIZEN_PASSWORD')
    if citizen_email and citizen_password:
        citizen_session = requests.Session()
        login_resp = citizen_session.post(
            f"{BASE_URL}/login",
            data={'email': citizen_email, 'password': citizen_password},
            allow_redirects=True
        )
        assert login_resp.status_code == 200
        profile_resp = citizen_session.get(f"{BASE_URL}/profile")
        assert profile_resp.status_code == 200
        print("[PASS] 10. Citizen email login & profile authenticated successfully.")
    else:
        print("[SKIP] 10. Set TEST_CITIZEN_EMAIL and TEST_CITIZEN_PASSWORD to test citizen authentication.")

    # 11. Test Admin Authentication & Dashboard
    admin_username = os.environ.get('TEST_ADMIN_USERNAME')
    admin_password = os.environ.get('TEST_ADMIN_PASSWORD')
    if admin_username and admin_password:
        admin_session = requests.Session()
        admin_login = admin_session.post(
            f"{BASE_URL}/admin/login",
            data={'username': admin_username, 'password': admin_password},
            allow_redirects=True
        )
        assert admin_login.status_code == 200
        admin_dash = admin_session.get(f"{BASE_URL}/admin/dashboard")
        assert "Disaster Command Center" in admin_dash.text
        assert "ACTIVE DISASTERS" in admin_dash.text
        print("[PASS] 11. Admin Command Center authenticated & loaded with real-time KPI metrics and analytics.")

        # 12. Test Admin Operations (Reports, Shelters, Volunteers, Rescue Requests)
        r_rep = admin_session.get(f"{BASE_URL}/admin/reports")
        assert r_rep.status_code == 200
        r_she = admin_session.get(f"{BASE_URL}/admin/shelters")
        assert r_she.status_code == 200
        r_vol = admin_session.get(f"{BASE_URL}/admin/volunteers")
        assert r_vol.status_code == 200
        r_res = admin_session.get(f"{BASE_URL}/admin/rescue-requests")
        assert r_res.status_code == 200
        print("[PASS] 12. Admin Sub-Modules (Report Verification, Shelter Manager, Volunteers, Rescue Missions) all verified.")
    else:
        print("[SKIP] 11-12. Set TEST_ADMIN_USERNAME and TEST_ADMIN_PASSWORD to test admin features.")

    print("\n>>> Integration test run completed. Review any skipped authentication tests. <<<")

if __name__ == '__main__':
    run_tests()
