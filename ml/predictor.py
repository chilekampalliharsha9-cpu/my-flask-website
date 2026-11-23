import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / 'disaster_model.pkl'

_MODEL_CACHE = None

def get_loaded_model():
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    
    if not MODEL_PATH.exists():
        # Automatically train and save if file not found
        from .train_model import train_and_save_model
        _MODEL_CACHE = train_and_save_model()
    else:
        _MODEL_CACHE = joblib.load(MODEL_PATH)
    return _MODEL_CACHE


def evaluate_specific_hazards(rainfall, wind_speed, water_level, soil_moisture, elevation):
    """
    Evaluate specific hazard categories based on multi-variable criteria.
    """
    # Flood Risk
    flood_score = 0
    if rainfall > 150: flood_score += 4
    elif rainfall > 80: flood_score += 3
    elif rainfall > 40: flood_score += 2
    elif rainfall > 15: flood_score += 1
    
    if water_level > 8.0: flood_score += 4
    elif water_level > 5.5: flood_score += 3
    elif water_level > 3.5: flood_score += 2
    elif water_level > 2.0: flood_score += 1

    if soil_moisture > 80: flood_score += 2
    elif soil_moisture > 65: flood_score += 1

    if flood_score >= 8: flood_risk = 'CRITICAL'
    elif flood_score >= 5: flood_risk = 'HIGH'
    elif flood_score >= 3: flood_risk = 'MEDIUM'
    else: flood_risk = 'LOW'

    # Cyclone Risk
    cyclone_score = 0
    if wind_speed > 115: cyclone_score += 5
    elif wind_speed > 80: cyclone_score += 4
    elif wind_speed > 55: cyclone_score += 3
    elif wind_speed > 35: cyclone_score += 1

    if rainfall > 60: cyclone_score += 2

    if cyclone_score >= 6: cyclone_risk = 'CRITICAL'
    elif cyclone_score >= 4: cyclone_risk = 'HIGH'
    elif cyclone_score >= 2: cyclone_risk = 'MEDIUM'
    else: cyclone_risk = 'LOW'

    # Landslide Risk (requires slope/elevation + saturated soil/heavy rain)
    landslide_score = 0
    if elevation > 100:
        if rainfall > 120 and soil_moisture > 75: landslide_score += 4
        elif rainfall > 70 and soil_moisture > 60: landslide_score += 3
        elif rainfall > 40: landslide_score += 2
        elif rainfall > 15: landslide_score += 1
    
    if landslide_score >= 4: landslide_risk = 'CRITICAL'
    elif landslide_score >= 3: landslide_risk = 'HIGH'
    elif landslide_score >= 2: landslide_risk = 'MEDIUM'
    else: landslide_risk = 'LOW'

    return flood_risk, cyclone_risk, landslide_risk


def generate_safety_advisory(general_risk, flood_risk, cyclone_risk, landslide_risk):
    advisories = []
    if general_risk == 'CRITICAL RISK':
        advisories.append("🚨 IMMEDIATE EVACUATION ORDER: Severe multi-hazard conditions detected. Proceed to designated elevated safe shelters immediately.")
    elif general_risk == 'HIGH RISK':
        advisories.append("⚠️ HIGH DANGER: Severe weather impact anticipated. Keep emergency kits ready, avoid low-lying roads, and monitor alert broadcasts.")
    elif general_risk == 'MEDIUM RISK':
        advisories.append("🟡 ELEVATED ADVISORY: Potential localized disruption. Clear drainage, secure outdoor items, and charge emergency communication devices.")
    else:
        advisories.append("🟢 NORMAL BASELINE: Environmental parameters are within standard safety thresholds. No immediate disaster warnings.")

    if flood_risk in ['HIGH', 'CRITICAL']:
        advisories.append("• Water levels approaching warning marks. Disconnect main power switches in flooded premises and do not drive through submerged underpasses.")
    if cyclone_risk in ['HIGH', 'CRITICAL']:
        advisories.append("• Gale-force wind hazard. Stay indoors away from glass windows and avoid taking shelter under unstable trees or tin roofs.")
    if landslide_risk in ['HIGH', 'CRITICAL']:
        advisories.append("• Slopes are critically saturated. Evacuate hillside settlements and avoid mountain roads prone to rockfalls.")

    return "\n".join(advisories)


def predict_disaster_risk(input_data):
    """
    input_data: dict with keys:
    rainfall, temperature, wind_speed, humidity, water_level, soil_moisture, elevation, historical_events
    """
    model_obj = get_loaded_model()
    model = model_obj['model']
    feature_names = model_obj['feature_names']
    
    features = [
        float(input_data.get('rainfall', 25.0)),
        float(input_data.get('temperature', 30.0)),
        float(input_data.get('wind_speed', 20.0)),
        float(input_data.get('humidity', 70.0)),
        float(input_data.get('water_level', 2.5)),
        float(input_data.get('soil_moisture', 50.0)),
        float(input_data.get('elevation', 15.0)),
        float(input_data.get('historical_events', 1.0))
    ]

    df_in = pd.DataFrame([features], columns=feature_names)
    prediction = model.predict(df_in)[0]
    probabilities = model.predict_proba(df_in)[0]
    
    prob_dict = {cls: round(float(p) * 100, 1) for cls, p in zip(model.classes_, probabilities)}
    confidence = max(probabilities)

    # Domain evaluations
    flood_r, cyclone_r, landslide_r = evaluate_specific_hazards(
        features[0], features[2], features[4], features[5], features[6]
    )

    advisory = generate_safety_advisory(prediction, flood_r, cyclone_r, landslide_r)

    return {
        'general_risk': prediction,
        'flood_risk': flood_r,
        'cyclone_risk': cyclone_r,
        'landslide_risk': landslide_r,
        'confidence_score': round(float(confidence), 2),
        'probabilities': prob_dict,
        'advisory': advisory,
        'feature_importances': model_obj.get('feature_importances', {}),
        'input_values': dict(zip(feature_names, features))
    }
