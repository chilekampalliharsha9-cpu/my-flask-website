import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def generate_synthetic_dataset(n_samples=2500, random_state=42):
    np.random.seed(random_state)
    
    # Generate feature distributions
    rainfall = np.random.exponential(scale=45.0, size=n_samples) # mm
    temperature = np.random.normal(loc=30.0, scale=6.0, size=n_samples) # C
    wind_speed = np.random.exponential(scale=25.0, size=n_samples) # km/h
    humidity = np.clip(np.random.normal(loc=70.0, scale=15.0, size=n_samples), 20.0, 100.0) # %
    water_level = np.clip(np.random.normal(loc=3.0, scale=2.5, size=n_samples), 0.5, 15.0) # meters
    soil_moisture = np.clip(np.random.normal(loc=55.0, scale=20.0, size=n_samples), 5.0, 100.0) # %
    elevation = np.clip(np.random.exponential(scale=120.0, size=n_samples), 2.0, 2000.0) # meters
    historical_events = np.random.poisson(lam=1.5, size=n_samples) # count

    # Determine risk labels based on physical domain principles
    labels = []
    for i in range(n_samples):
        score = 0
        r, w, wl, sm, el, hist = rainfall[i], wind_speed[i], water_level[i], soil_moisture[i], elevation[i], historical_events[i]
        
        # Rainfall impact
        if r > 180: score += 4
        elif r > 100: score += 3
        elif r > 50: score += 2
        elif r > 20: score += 1
        
        # Wind speed impact (cyclonic)
        if w > 110: score += 4
        elif w > 75: score += 3
        elif w > 45: score += 2
        elif w > 25: score += 1
        
        # River water level impact
        if wl > 9.0: score += 4
        elif wl > 6.0: score += 3
        elif wl > 4.0: score += 2
        elif wl > 2.5: score += 1
        
        # Soil moisture & low elevation (flooding / landslide)
        if sm > 85 and r > 60: score += 2
        if el < 15 and (r > 60 or w > 60): score += 2
        if hist >= 3: score += 1
        
        if score >= 10:
            labels.append('CRITICAL RISK')
        elif score >= 7:
            labels.append('HIGH RISK')
        elif score >= 4:
            labels.append('MEDIUM RISK')
        else:
            labels.append('LOW RISK')

    df = pd.DataFrame({
        'rainfall': np.round(rainfall, 1),
        'temperature': np.round(temperature, 1),
        'wind_speed': np.round(wind_speed, 1),
        'humidity': np.round(humidity, 1),
        'water_level': np.round(water_level, 2),
        'soil_moisture': np.round(soil_moisture, 1),
        'elevation': np.round(elevation, 1),
        'historical_events': historical_events,
        'risk_label': labels
    })
    return df


def train_and_save_model():
    print("Generating synthetic disaster data based on meteorological models...")
    df = generate_synthetic_dataset()
    
    feature_cols = ['rainfall', 'temperature', 'wind_speed', 'humidity', 'water_level', 'soil_moisture', 'elevation', 'historical_events']
    X = df[feature_cols]
    y = df['risk_label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Training Random Forest & Gradient Boosting Classifier...")
    model = RandomForestClassifier(n_estimators=120, max_depth=12, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model Training Complete! Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    model_payload = {
        'model': model,
        'feature_names': feature_cols,
        'classes': list(model.classes_),
        'feature_importances': dict(zip(feature_cols, [round(float(fi), 4) for fi in model.feature_importances_]))
    }
    
    output_path = BASE_DIR / 'disaster_model.pkl'
    joblib.dump(model_payload, output_path)
    print(f"Model saved successfully to: {output_path}")
    return model_payload

if __name__ == '__main__':
    train_and_save_model()
