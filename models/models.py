from datetime import datetime
from flask_login import UserMixin
from extensions import db, login_manager, bcrypt

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(128), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    address = db.Column(db.String(255))
    is_volunteer = db.Column(db.Boolean, default=False)
    volunteer_status = db.Column(db.String(32), default='Offline') # Available, Assigned, Busy, Offline
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    contacts = db.relationship('EmergencyContact', backref='user', lazy=True, cascade="all, delete-orphan")
    reports = db.relationship('DisasterReport', backref='user', lazy=True)
    sos_requests = db.relationship('SOSRequest', backref='user', lazy=True)
    rescue_requests = db.relationship('RescueRequest', foreign_keys='RescueRequest.user_id', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return False

    def get_id(self):
        return f"user_{self.id}"

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'address': self.address,
            'is_volunteer': self.is_volunteer,
            'volunteer_status': self.volunteer_status
        }


class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(64), default='Disaster Operations Manager')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return True

    def get_id(self):
        return f"admin_{self.id}"


@login_manager.user_loader
def load_user(user_id_str):
    if not user_id_str:
        return None
    if isinstance(user_id_str, str) and user_id_str.startswith('admin_'):
        admin_id = int(user_id_str.split('_')[1])
        return Admin.query.get(admin_id)
    elif isinstance(user_id_str, str) and user_id_str.startswith('user_'):
        user_id = int(user_id_str.split('_')[1])
        return User.query.get(user_id)
    else:
        # Fallback for plain integer IDs
        try:
            uid = int(user_id_str)
            u = User.query.get(uid)
            if u:
                return u
            return Admin.query.get(uid)
        except (ValueError, TypeError):
            return None


class EmergencyContact(db.Model):
    __tablename__ = 'emergency_contacts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(32), nullable=False)
    relationship = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'relationship': self.relationship
        }


class DisasterAlert(db.Model):
    __tablename__ = 'disasters'
    id = db.Column(db.Integer, primary_key=True)
    disaster_type = db.Column(db.String(64), nullable=False) # Flood, Cyclone, Earthquake, Tsunami, Fire, Landslide, Storm, Industrial Accident
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(32), nullable=False) # Low, Moderate, High, Critical
    location = db.Column(db.String(128), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    affected_radius_km = db.Column(db.Float, default=15.0)
    status = db.Column(db.String(64), default='Active') # Active, Watch, Resolved
    recommended_action = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'disaster_type': self.disaster_type,
            'type': self.disaster_type,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'affected_radius_km': self.affected_radius_km or 15.0,
            'status': self.status,
            'recommended_action': self.recommended_action,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


class DisasterReport(db.Model):
    __tablename__ = 'disaster_reports'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    disaster_type = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(128), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    video = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(64), default='Pending Verification') # Pending Verification, Verified, Rejected
    verified = db.Column(db.Boolean, default=False)
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'reporter_name': self.user.full_name or self.user.username if self.user else 'Anonymous Citizen',
            'disaster_type': self.disaster_type,
            'type': self.disaster_type,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'image': self.image,
            'video': self.video,
            'status': self.status,
            'verified': self.verified,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


class Shelter(db.Model):
    __tablename__ = 'shelters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, default=100)
    occupancy = db.Column(db.Integer, default=0)
    food_available = db.Column(db.Boolean, default=True)
    water_available = db.Column(db.Boolean, default=True)
    medical_support = db.Column(db.Boolean, default=True)
    power_backup = db.Column(db.Boolean, default=True)
    contact_number = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def available_capacity(self):
        return max(0, self.capacity - self.occupancy)

    @property
    def occupancy_percentage(self):
        if self.capacity <= 0:
            return 100
        return min(100, int((self.occupancy / self.capacity) * 100))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'capacity': self.capacity,
            'occupancy': self.occupancy,
            'available_capacity': self.available_capacity,
            'occupancy_percentage': self.occupancy_percentage,
            'food_available': self.food_available,
            'water_available': self.water_available,
            'medical_support': self.medical_support,
            'power_backup': self.power_backup,
            'contact_number': self.contact_number
        }


class Hospital(db.Model):
    __tablename__ = 'hospitals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    contact_number = db.Column(db.String(32), nullable=False)
    beds_total = db.Column(db.Integer, default=100)
    beds_available = db.Column(db.Integer, default=25)
    ambulance_available = db.Column(db.Boolean, default=True)
    emergency_department = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'contact_number': self.contact_number,
            'beds_total': self.beds_total,
            'beds_available': self.beds_available,
            'ambulance_available': self.ambulance_available,
            'emergency_department': self.emergency_department
        }


class PoliceStation(db.Model):
    __tablename__ = 'police_stations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    contact_number = db.Column(db.String(32), nullable=False)
    jurisdiction = db.Column(db.String(128), default='Metropolitan Area')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'contact_number': self.contact_number,
            'jurisdiction': self.jurisdiction
        }


class FireStation(db.Model):
    __tablename__ = 'fire_stations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    contact_number = db.Column(db.String(32), nullable=False)
    fire_trucks = db.Column(db.Integer, default=4)
    rescue_boats = db.Column(db.Integer, default=2)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'contact_number': self.contact_number,
            'fire_trucks': self.fire_trucks,
            'rescue_boats': self.rescue_boats
        }


class Volunteer(db.Model):
    __tablename__ = 'volunteers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skills = db.Column(db.String(255), nullable=False) # First Aid, Evacuation, Food Distribution, Boat Rescue, Radio Comms
    location = db.Column(db.String(255), nullable=False)
    available = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(32), default='Available') # Available, Assigned, Busy, Offline
    contact_number = db.Column(db.String(32), nullable=False)
    assigned_request_id = db.Column(db.Integer, db.ForeignKey('rescue_requests.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_rel = db.relationship('User', backref=db.backref('volunteer_profile', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.user_rel.full_name or self.user_rel.username if self.user_rel else 'Volunteer',
            'skills': self.skills,
            'location': self.location,
            'available': self.available,
            'status': self.status,
            'contact_number': self.contact_number,
            'assigned_request_id': self.assigned_request_id
        }


class RescueRequest(db.Model):
    __tablename__ = 'rescue_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    emergency_type = db.Column(db.String(64), nullable=False) # Trapped in Flood, Medical Emergency, Building Collapse, Fire Evacuation
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    people_count = db.Column(db.Integer, default=1)
    priority = db.Column(db.String(32), default='Normal') # Normal, High, Critical
    image = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(64), default='Pending') # Pending, Assigned, In Progress, Resolved
    assigned_volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteers.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assigned_volunteer = db.relationship('Volunteer', foreign_keys=[assigned_volunteer_id], post_update=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'citizen_name': self.user.full_name or self.user.username if self.user else 'Citizen',
            'phone': self.user.phone if self.user else 'N/A',
            'emergency_type': self.emergency_type,
            'description': self.description,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'people_count': self.people_count,
            'priority': self.priority,
            'image': self.image,
            'status': self.status,
            'assigned_volunteer_id': self.assigned_volunteer_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


class SOSRequest(db.Model):
    __tablename__ = 'sos_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    caller_name = db.Column(db.String(128), default='Anonymous Citizen')
    caller_phone = db.Column(db.String(32), default='N/A')
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    emergency_type = db.Column(db.String(64), default='Immediate SOS Rescue')
    status = db.Column(db.String(64), default='Pending') # Pending, Assigned, In Progress, Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'caller_name': self.caller_name,
            'caller_phone': self.caller_phone,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'emergency_type': self.emergency_type,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Null for broadcast
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(32), default='info') # info, warning, danger, success
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'level': self.level,
            'read': self.read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(128), nullable=False)
    temperature = db.Column(db.Float) # Celsius
    rainfall = db.Column(db.Float) # mm
    wind_speed = db.Column(db.Float) # km/h
    humidity = db.Column(db.Float) # %
    pressure = db.Column(db.Float, default=1012.0) # hPa
    condition = db.Column(db.String(128))
    risk_level = db.Column(db.String(32), default='Safe') # Safe, Watch, Warning, Critical
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'location': self.location,
            'temperature': self.temperature,
            'rainfall': self.rainfall,
            'wind_speed': self.wind_speed,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'condition': self.condition,
            'risk_level': self.risk_level,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


class RiskPrediction(db.Model):
    __tablename__ = 'risk_predictions'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(128), nullable=False)
    rainfall = db.Column(db.Float)
    temperature = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    humidity = db.Column(db.Float)
    water_level = db.Column(db.Float) # meters
    soil_moisture = db.Column(db.Float) # %
    elevation = db.Column(db.Float) # meters
    flood_risk = db.Column(db.String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    cyclone_risk = db.Column(db.String(32))
    landslide_risk = db.Column(db.String(32))
    general_risk = db.Column(db.String(32))
    confidence_score = db.Column(db.Float, default=0.92)
    advisory = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'location': self.location,
            'rainfall': self.rainfall,
            'temperature': self.temperature,
            'wind_speed': self.wind_speed,
            'humidity': self.humidity,
            'water_level': self.water_level,
            'soil_moisture': self.soil_moisture,
            'elevation': self.elevation,
            'flood_risk': self.flood_risk,
            'cyclone_risk': self.cyclone_risk,
            'landslide_risk': self.landslide_risk,
            'general_risk': self.general_risk,
            'confidence_score': self.confidence_score,
            'advisory': self.advisory,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }
