from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models.models import RiskPrediction
from ml.predictor import predict_disaster_risk

ai_bp = Blueprint('ai', __name__, template_folder='../templates')

@ai_bp.route('/ai-risk')
@ai_bp.route('/predict')
def ai_risk():
    recent_predictions = RiskPrediction.query.order_by(RiskPrediction.created_at.desc()).limit(5).all()
    return render_template('ai_predict.html', recent_predictions=recent_predictions)


@ai_bp.route('/api/predict-risk', methods=['POST'])
def predict_risk_api():
    """
    REST API endpoint for real-time ML disaster risk inference.
    """
    data = request.get_json(silent=True) or request.form.to_dict()
    
    try:
        rainfall = float(data.get('rainfall', 30.0))
        temperature = float(data.get('temperature', 30.0))
        wind_speed = float(data.get('wind_speed', 20.0))
        humidity = float(data.get('humidity', 70.0))
        water_level = float(data.get('water_level', 2.5))
        soil_moisture = float(data.get('soil_moisture', 50.0))
        elevation = float(data.get('elevation', 15.0))
        historical_events = float(data.get('historical_events', 1.0))
        location = data.get('location', 'Selected Station')
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid numerical inputs provided.'}), 400

    input_payload = {
        'rainfall': rainfall,
        'temperature': temperature,
        'wind_speed': wind_speed,
        'humidity': humidity,
        'water_level': water_level,
        'soil_moisture': soil_moisture,
        'elevation': elevation,
        'historical_events': historical_events
    }

    result = predict_disaster_risk(input_payload)
    
    # Save inference history to database
    record = RiskPrediction(
        location=location,
        rainfall=rainfall,
        temperature=temperature,
        wind_speed=wind_speed,
        humidity=humidity,
        water_level=water_level,
        soil_moisture=soil_moisture,
        elevation=elevation,
        flood_risk=result['flood_risk'],
        cyclone_risk=result['cyclone_risk'],
        landslide_risk=result['landslide_risk'],
        general_risk=result['general_risk'],
        confidence_score=result['confidence_score'],
        advisory=result['advisory']
    )
    db.session.add(record)
    db.session.commit()

    response = {
        'status': 'success',
        'prediction_id': record.id,
        'location': location,
        'risk_result': result
    }
    return jsonify(response)
