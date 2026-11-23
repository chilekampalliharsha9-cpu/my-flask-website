import os
import secrets
from datetime import datetime, timedelta
from app import create_app
from extensions import db
from models.models import (
    User, Admin, EmergencyContact, DisasterAlert, DisasterReport,
    Shelter, Hospital, PoliceStation, FireStation, Volunteer,
    RescueRequest, Notification, WeatherData, RiskPrediction
)

def seed_database():
    app = create_app()
    with app.app_context():
        print("Initializing database tables...")
        db.create_all()

        # Check if already seeded
        if Admin.query.first():
            print("Database already contains data. Skipping re-seeding.")
            return

        print("Seeding Administrator account...")
        admin = Admin(
            username='admin',
            email='admin@disastermanagement.gov.in',
            role='Chief Disaster Management Director'
        )
        admin_password = os.environ.get('ADMIN_INITIAL_PASSWORD') or secrets.token_urlsafe(24)
        admin.set_password(admin_password)
        db.session.add(admin)

        print("Seeding Citizen demo account...")
        citizen = User(
            username='citizen',
            email='citizen@demo.org',
            full_name='Aarav Sharma',
            phone='+91 98765 43210',
            address='14 Marina Bay Road, Mylapore, Chennai, Tamil Nadu',
            is_volunteer=True,
            volunteer_status='Available'
        )
        citizen.set_password(secrets.token_urlsafe(24))
        db.session.add(citizen)
        db.session.flush()

        # Emergency contacts for citizen
        c1 = EmergencyContact(user_id=citizen.id, name='Priya Sharma (Spouse)', phone='+91 98765 11111', relationship='Spouse')
        c2 = EmergencyContact(user_id=citizen.id, name='Dr. Rajesh Sharma (Father)', phone='+91 98765 22222', relationship='Parent')
        c3 = EmergencyContact(user_id=citizen.id, name='Kiran Reddy (Neighbour)', phone='+91 98765 33333', relationship='Friend/Neighbour')
        db.session.add_all([c1, c2, c3])

        # Volunteer profile for citizen
        vol1 = Volunteer(
            user_id=citizen.id,
            skills='First Aid Certified, Flood Boat Evacuation, Radio Comms',
            location='Chennai Coastal Sector',
            available=True,
            status='Available',
            contact_number='+91 98765 43210'
        )
        db.session.add(vol1)

        # Additional Citizen Volunteers
        c_vol2 = User(username='meera_nurse', email='meera@health.org', full_name='Meera Sundaram', phone='+91 94441 22334', address='T. Nagar, Chennai', is_volunteer=True, volunteer_status='Available')
        c_vol2.set_password(secrets.token_urlsafe(24))
        c_vol3 = User(username='vikram_diver', email='vikram@rescue.org', full_name='Vikramaditya Rao', phone='+91 98840 55667', address='Besant Nagar, Chennai', is_volunteer=True, volunteer_status='Assigned')
        c_vol3.set_password(secrets.token_urlsafe(24))
        db.session.add_all([c_vol2, c_vol3])
        db.session.flush()

        vol2 = Volunteer(user_id=c_vol2.id, skills='Critical Trauma Nursing, Paramedic Care, Triage', location='T. Nagar, Chennai', available=True, status='Available', contact_number='+91 94441 22334')
        vol3 = Volunteer(user_id=c_vol3.id, skills='Deep Water Diving, Structural Search & Rescue', location='Besant Nagar, Chennai', available=False, status='Assigned', contact_number='+91 98840 55667')
        db.session.add_all([vol2, vol3])

        print("Seeding Disaster Alerts...")
        alerts = [
            DisasterAlert(
                disaster_type='Cyclone',
                title='Severe Cyclonic Storm "Michaung" Warning',
                description='Severe cyclonic system approaching North Tamil Nadu and South Andhra Pradesh coast. Heavy to extremely heavy rainfall with gale wind speeds reaching 90-110 kmph anticipated.',
                severity='Critical',
                location='Chennai & Coastal Tamil Nadu',
                latitude=13.0827,
                longitude=80.2707,
                affected_radius_km=35.0,
                status='Active',
                recommended_action='Stay indoors, stock 72h dry food and clean water, evacuate coastal lowlands to designated community shelters.'
            ),
            DisasterAlert(
                disaster_type='Flood',
                title='Adyar & Cooum River Flash Flood Inundation Alert',
                description='Water discharge from Chembarambakkam reservoir increased to 12,000 cusecs due to continuous catchment downpours. Low-lying zones along the riverbanks face rapid water rise.',
                severity='High',
                location='Saidapet, Kotturpuram & Velachery, Chennai',
                latitude=13.0189,
                longitude=80.2223,
                affected_radius_km=12.0,
                status='Active',
                recommended_action='Move to upper floors or nearest relief shelter immediately. Disconnect main power grid switches.'
            ),
            DisasterAlert(
                disaster_type='Storm',
                title='Heavy Coastal Squall & Sea Surge Warning',
                description='Rough sea conditions with wave heights of 3.5 to 4.8 meters expected along the Visakhapatnam and Bay of Bengal coast. Fishermen advised not to venture into deep sea.',
                severity='Moderate',
                location='Visakhapatnam Port & Beach Corridor',
                latitude=17.6868,
                longitude=83.2185,
                affected_radius_km=25.0,
                status='Active',
                recommended_action='Avoid beachfront promenades and secure small marine vessels on elevated ground.'
            ),
            DisasterAlert(
                disaster_type='Landslide',
                title='High Landslide Vulnerability Advisory',
                description='Persistent monsoonal saturation on hillside slopes triggering slope destabilization warnings across the Western Ghats corridor.',
                severity='High',
                location='Munnar & Idukki District, Kerala',
                latitude=10.0889,
                longitude=77.0595,
                affected_radius_km=20.0,
                status='Active',
                recommended_action='Avoid non-essential travel on mountain ghat passes; evacuate homes on steep unreinforced slopes.'
            ),
            DisasterAlert(
                disaster_type='Fire',
                title='Industrial Warehouse Fire Incident Under Control',
                description='Hazardous chemical smoke emissions contained by fire tenders near Manali Industrial Park. Air quality sensors normalizing.',
                severity='Low',
                location='Manali Industrial Zone, Chennai',
                latitude=13.1667,
                longitude=80.2667,
                affected_radius_km=5.0,
                status='Watch',
                recommended_action='Keep windows closed and wear N95 face masks within 2 km perimeter.'
            )
        ]
        db.session.add_all(alerts)

        print("Seeding Safe Shelters...")
        shelters = [
            Shelter(
                name='Chennai Central Multi-Purpose Cyclone Relief Shelter',
                address='Poonamallee High Road, Periamet, Chennai, TN 600003',
                latitude=13.0836,
                longitude=80.2755,
                capacity=500,
                occupancy=140,
                food_available=True,
                water_available=True,
                medical_support=True,
                power_backup=True,
                contact_number='+91 44 2561 9001'
            ),
            Shelter(
                name='Mylapore Community Disaster Relief Center',
                address='Luz Church Road, Mylapore, Chennai, TN 600004',
                latitude=13.0368,
                longitude=80.2676,
                capacity=350,
                occupancy=85,
                food_available=True,
                water_available=True,
                medical_support=True,
                power_backup=True,
                contact_number='+91 44 2498 3310'
            ),
            Shelter(
                name='Anna Nagar West Safe Evacuation Hall',
                address='12th Main Road, Anna Nagar, Chennai, TN 600040',
                latitude=13.0850,
                longitude=80.2100,
                capacity=400,
                occupancy=45,
                food_available=True,
                water_available=True,
                medical_support=True,
                power_backup=True,
                contact_number='+91 44 2621 4455'
            ),
            Shelter(
                name='Velachery High Ground Disaster Camp',
                address='Velachery Main Road, Near Bypass, Chennai, TN 600042',
                latitude=12.9815,
                longitude=80.2180,
                capacity=300,
                occupancy=210,
                food_available=True,
                water_available=True,
                medical_support=True,
                power_backup=True,
                contact_number='+91 44 2244 8890'
            ),
            Shelter(
                name='Visakhapatnam Port Cyclone Evacuation Center',
                address='Beach Road, Maharani Peta, Visakhapatnam, AP 530002',
                latitude=17.7041,
                longitude=83.3012,
                capacity=600,
                occupancy=120,
                food_available=True,
                water_available=True,
                medical_support=True,
                power_backup=True,
                contact_number='+91 891 256 7890'
            ),
            Shelter(
                name='Mumbai Coastal Resilience Relief Center',
                address='Worli Seaface Road, Worli, Mumbai, MH 400030',
                latitude=19.0167,
                longitude=72.8167,
                capacity=450,
                occupancy=60,
                food_available=True,
                water_available=True,
                medical_support=True,
                power_backup=True,
                contact_number='+91 22 2493 0012'
            )
        ]
        db.session.add_all(shelters)

        print("Seeding Hospitals & Emergency Medical Facilities...")
        hospitals = [
            Hospital(
                name='Rajiv Gandhi Government General Hospital',
                address='EVR Periyar Salai, Park Town, Chennai, TN 600003',
                latitude=13.0805,
                longitude=80.2785,
                contact_number='+91 44 2530 5000',
                beds_total=2500,
                beds_available=185,
                ambulance_available=True,
                emergency_department=True
            ),
            Hospital(
                name='Apollo Speciality Emergency Hospital',
                address='21 Greams Lane, Thousand Lights, Chennai, TN 600006',
                latitude=13.0569,
                longitude=80.2527,
                contact_number='+91 44 2829 0200',
                beds_total=600,
                beds_available=42,
                ambulance_available=True,
                emergency_department=True
            ),
            Hospital(
                name='King Institute Trauma & Disaster Center',
                address='Mount Road, Guindy, Chennai, TN 600032',
                latitude=13.0102,
                longitude=80.2158,
                contact_number='+91 44 2250 1520',
                beds_total=400,
                beds_available=78,
                ambulance_available=True,
                emergency_department=True
            ),
            Hospital(
                name='King George Hospital (KGH)',
                address='Maharanipeta, Visakhapatnam, AP 530002',
                latitude=17.7082,
                longitude=83.3060,
                contact_number='+91 891 256 4891',
                beds_total=1200,
                beds_available=95,
                ambulance_available=True,
                emergency_department=True
            ),
            Hospital(
                name='KEM Hospital Disaster Trauma Unit',
                address='Acharya Donde Marg, Parel, Mumbai, MH 400012',
                latitude=19.0028,
                longitude=72.8427,
                contact_number='+91 22 2410 7000',
                beds_total=1800,
                beds_available=110,
                ambulance_available=True,
                emergency_department=True
            )
        ]
        db.session.add_all(hospitals)

        print("Seeding Police & Fire Stations...")
        police_stations = [
            PoliceStation(
                name='Greater Chennai Police Commissionerate & Control Room',
                address='132 EVK Sampath Road, Vepery, Chennai, TN 600007',
                latitude=13.0878,
                longitude=80.2644,
                contact_number='100 / +91 44 2345 2359',
                jurisdiction='Greater Chennai Metro'
            ),
            PoliceStation(
                name='Mylapore Police Station (E-1)',
                address='Kutchery Road, Mylapore, Chennai, TN 600004',
                latitude=13.0335,
                longitude=80.2690,
                contact_number='+91 44 2345 2570',
                jurisdiction='South Chennai District'
            ),
            PoliceStation(
                name='Visakhapatnam Central Police Control',
                address='Suryabagh, Jagadamba Junction, Visakhapatnam, AP 530002',
                latitude=17.7125,
                longitude=83.3000,
                contact_number='100 / +91 891 256 5454',
                jurisdiction='Visakhapatnam City'
            )
        ]
        db.session.add_all(police_stations)

        fire_stations = [
            FireStation(
                name='State Fire & Disaster Rescue Services HQ',
                address='No. 12 Rukmani Lakshmipathi Salai, Egmore, Chennai, TN 600008',
                latitude=13.0732,
                longitude=80.2610,
                contact_number='101 / +91 44 2855 4101',
                fire_trucks=12,
                rescue_boats=8
            ),
            FireStation(
                name='Mylapore Fire & Water Rescue Station',
                address='Dr. Radhakrishnan Salai, Mylapore, Chennai, TN 600004',
                latitude=13.0410,
                longitude=80.2630,
                contact_number='101 / +91 44 2811 0101',
                fire_trucks=4,
                rescue_boats=3
            ),
            FireStation(
                name='Visakhapatnam Port Fire & Emergency Station',
                address='Port Area, Visakhapatnam, AP 530035',
                latitude=17.6950,
                longitude=83.2850,
                contact_number='101 / +91 891 256 0101',
                fire_trucks=6,
                rescue_boats=4
            )
        ]
        db.session.add_all(fire_stations)

        print("Seeding Citizen Disaster Reports & Rescue Requests...")
        rep1 = DisasterReport(
            user_id=citizen.id,
            disaster_type='Flood',
            title='Severe Street Waterlogging & Submerged Transformers',
            description='Water depth exceeds 3.5 feet on South Mada Street. Ground floor apartments flooded, electricity shut down, families moving to terrace.',
            location='South Mada Street, Mylapore, Chennai',
            latitude=13.0338,
            longitude=80.2685,
            status='Verified',
            verified=True,
            created_at=datetime.utcnow() - timedelta(hours=3)
        )
        rep2 = DisasterReport(
            user_id=citizen.id,
            disaster_type='Storm',
            title='Large Banyan Tree Uprooted Blocking Hospital Entrance',
            description='Gale winds caused giant tree collapse directly across the ambulance gate of King Institute road.',
            location='Guindy Main Road, Chennai',
            latitude=13.0115,
            longitude=80.2170,
            status='Verified',
            verified=True,
            created_at=datetime.utcnow() - timedelta(hours=1)
        )
        rep3 = DisasterReport(
            user_id=citizen.id,
            disaster_type='Flood',
            title='Drainage Overflow Near Gandhi Nagar Subway',
            description='Subway water depth rising quickly. Vehicles advised to divert via Kotturpuram bridge.',
            location='Adyar Subway, Chennai',
            latitude=13.0067,
            longitude=80.2542,
            status='Pending Verification',
            verified=False,
            created_at=datetime.utcnow() - timedelta(minutes=25)
        )
        db.session.add_all([rep1, rep2, rep3])

        rescue1 = RescueRequest(
            user_id=citizen.id,
            emergency_type='Flooded Residence - Elderly Couple Stranded',
            description='Water level reached 4 feet. Two elderly citizens need inflatable boat evacuation with prescription insulin.',
            location='Flat 2B, Lake View Road, Velachery, Chennai',
            latitude=12.9830,
            longitude=80.2210,
            people_count=2,
            priority='Critical',
            status='In Progress',
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        rescue2 = RescueRequest(
            user_id=citizen.id,
            emergency_type='Medical Transport - Oxygen Refill Needed',
            description='Respiratory patient stranded due to waterlogged approach road. Oxygen cylinder running low in 3 hours.',
            location='Door 45, TTK Road, Alwarpet, Chennai',
            latitude=13.0390,
            longitude=80.2510,
            people_count=1,
            priority='High',
            status='Assigned',
            created_at=datetime.utcnow() - timedelta(hours=1)
        )
        db.session.add_all([rescue1, rescue2])

        print("Seeding Weather and Risk Prediction logs...")
        w1 = WeatherData(
            location='Chennai',
            temperature=27.4,
            rainfall=115.0,
            wind_speed=78.5,
            humidity=92.0,
            pressure=996.0,
            condition='Cyclonic Torrential Downpours',
            risk_level='Critical'
        )
        w2 = WeatherData(
            location='Visakhapatnam',
            temperature=29.0,
            rainfall=42.0,
            wind_speed=48.0,
            humidity=84.0,
            pressure=1004.0,
            condition='Squally Wind & Rain Showers',
            risk_level='Watch'
        )
        db.session.add_all([w1, w2])

        r1 = RiskPrediction(
            location='Chennai Coastal Sector',
            rainfall=130.0,
            temperature=27.0,
            wind_speed=82.0,
            humidity=94.0,
            water_level=7.8,
            soil_moisture=88.0,
            elevation=8.0,
            flood_risk='CRITICAL',
            cyclone_risk='HIGH',
            landslide_risk='LOW',
            general_risk='CRITICAL RISK',
            confidence_score=0.96,
            advisory='🚨 IMMEDIATE EVACUATION ORDER: Severe multi-hazard conditions detected. Proceed to designated elevated safe shelters immediately.'
        )
        db.session.add(r1)

        # Broadcast notification
        n1 = Notification(
            title='🚨 RED WARNING: Cyclone Michaung Impending Landfall',
            message='All citizens in North Coastal Tamil Nadu advised to evacuate to nearest safe shelters. Emergency helplines active 24/7 on 112.',
            level='danger'
        )
        db.session.add(n1)

        db.session.commit()
        print("Database seeding completed successfully!")
        print("--------------------------------------------------")
        print("Administrator username: admin")
        if os.environ.get('ADMIN_INITIAL_PASSWORD'):
            print("Administrator password was read from ADMIN_INITIAL_PASSWORD.")
        else:
            print(f"Generated initial administrator password: {admin_password}")
        print("Citizen accounts must be created through the registration page.")
        print("--------------------------------------------------")

if __name__ == '__main__':
    seed_database()
