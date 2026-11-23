# Smart Disaster Management and Emergency Response System Using AI, Cloud Computing and Real-Time Location Services

A modern, responsive, full-stack disaster management and civil defense platform designed for real-time alerting, AI-powered multi-hazard risk prediction, GIS live mapping, rapid SOS rescue coordination, and shelter navigation.

---

## 🌟 Key Features

### 1. Citizen Portal
- **Real-Time Disaster Alerts**: Filterable feed of emergency advisories with severity classifications (Critical, High, Moderate, Low).
- **One-Touch Emergency SOS**: Broadcasts GPS coordinates to emergency response dispatchers, computes the nearest shelter and hospital with distances in kilometers, and notifies registered emergency contacts.
- **Interactive Live Map (Leaflet.js & OpenStreetMap)**: Multi-layer GIS map displaying active disaster perimeters, safe relief shelters, hospitals, police stations, fire stations, and verified citizen reports.
- **Crowdsourced Incident Reporting**: Citizens can submit field incident reports with GPS geolocation and photo/video attachments. Reports are verified by operations staff before appearing on the public map.
- **Safe Shelter Finder**: Lists evacuation camps with real-time bed capacity, occupancy progress bars, and amenity badges (Clean water, Food, Medical aid, Power backup), sorted by shortest distance.
- **Emergency Services Directory**: Searchable directory of hospitals, trauma centers, police stations, and fire & rescue fleet stations with 1-click calling.
- **AI Disaster Risk Prediction Lab**: Machine Learning model (Random Forest & Gradient Boosting) forecasting Flood, Cyclone, Landslide, and General Risk levels with confidence scores and safety advisories.
- **Multi-Hazard Preparedness Guides**: Comprehensive Before/During/After emergency guides for Flood, Cyclone, Earthquake, Fire, Tsunami, and Landslide.
- **Interactive Emergency Go-Bag Checklist**: Persistent checklist for a 72-hour family survival kit saved to local storage.
- **Multilingual Support**: Dynamic translation across **English**, **Tamil (தமிழ்)**, **Telugu (తెలుగు)**, and **Hindi (हिन्दी)**.

### 2. Admin Command Center
- **Dedicated Protected Portal**: Accessible via `/admin/login` (hidden from the public user navbar).
- **KPI Overview & Analytics**: Live counters and visual analytics powered by Chart.js (Disaster distribution, rescue operations status, monthly trends).
- **Disaster Alerts CRUD**: Create, edit, publish, and delete official disaster advisories.
- **Incident Verification Queue**: Review submitted photos/videos and verify or reject citizen reports.
- **Shelter & Resource Management**: Update shelter capacities, food/water amenities, and hospital beds.
- **Volunteer & Rescue Dispatch**: Assign civil defense volunteers to active rescue missions and track mission lifecycles (Pending → Assigned → In Progress → Resolved).

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Leaflet.js, OpenStreetMap |
| **Backend** | Python 3 (Flask), Flask-Login, Flask-Bcrypt, Flask-Migrate |
| **Database** | SQLite (Development) / PostgreSQL & MySQL ready (SQLAlchemy ORM) |
| **Machine Learning** | Scikit-Learn, Pandas, NumPy, Joblib (Random Forest Classifier) |
| **Architecture** | Modular Blueprint Design, RESTful API Endpoints, Responsive Glassmorphism UI |

---

## 🚀 Step-by-Step Setup & Running Guide

### 1. Prerequisites Check
Ensure you have Python 3.10+ installed:
```bash
python --version
```

### 2. Open Project in VS Code
Open the project directory in Visual Studio Code or your preferred terminal.

### 3. Create & Activate Virtual Environment (Optional but Recommended)
```bash
# Windows (Command Prompt / PowerShell)
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Train the AI Disaster Prediction Model
Run the ML model training script to generate the trained model:
```bash
python ml/train_model.py
```

### 6. Initialize & Seed Database with Demo Data
Populate realistic disaster alerts, shelters, hospitals, police stations, rescue requests, and sample accounts:
```bash
python seed_data.py
```

### 7. Run the Flask Application
```bash
python app.py
```

Open your browser and navigate to:
👉 **Public Citizen Portal:** `http://localhost:5000`
👉 **Admin Command Center:** `http://localhost:5000/admin/login`

---

## 🔐 Accounts and deployment secrets

- Citizens create an account from `/register` and sign in with their email address.
- The database seeder creates an administrator named `admin`. Set
  `ADMIN_INITIAL_PASSWORD` before the first seed, or copy the generated
  administrator password from the private server console output.
- Set a stable, randomly generated `SECRET_KEY` in the hosting environment.
  The application creates a temporary random key when this variable is absent;
  sessions will not survive an application restart in that mode.
- Never publish `.env` files, the SQLite database, real user records, or
  administrator credentials.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/map-data` | `GET` | Returns active alerts, verified reports, shelters, hospitals, police, and fire stations for Leaflet.js. |
| `/api/sos` | `POST` | Dispatches emergency SOS signal with GPS coordinates, alerts contacts, and finds nearest facilities. |
| `/api/nearest-shelter` | `GET` | Given `lat` and `lon`, returns closest safe shelters sorted by distance in km. |
| `/api/predict-risk` | `POST` | Runs ML inference on rainfall, temperature, wind, water level, soil moisture, and elevation. |
| `/api/weather` | `GET` | Fetches real-time / simulated meteorological parameters and hazard risk index. |
| `/api/notifications` | `GET` | Fetches recent broadcast and user-specific emergency notifications. |
| `/api/stats` | `GET` | Live KPI counts for disasters, shelters, and rescues. |

---

## 📁 Project Folder Structure

```
disaster_management/
│
├── app.py                     # Flask application factory & server entrypoint
├── config.py                  # Environment config, DB URI, upload constraints
├── extensions.py              # SQLAlchemy, LoginManager, Bcrypt, Migrate
├── seed_data.py               # Comprehensive database seeder
├── requirements.txt           # Python dependencies
├── database.db                # SQLite database (auto-generated)
│
├── models/
│   ├── __init__.py
│   └── models.py              # User, Admin, Shelter, Alert, Report, RescueRequest models
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Registration, Login, Profile & Emergency Contacts
│   ├── main.py                # Public Citizen Routes (Home, Alerts, Map, Shelters, Weather)
│   ├── api.py                 # REST API Endpoints
│   ├── ai_routes.py           # AI Risk Prediction Lab
│   └── admin.py               # Admin Command Center operations
│
├── services/
│   ├── __init__.py
│   ├── distance_service.py    # Haversine distance calculator
│   ├── weather_service.py     # Meteorological risk calculator & OpenWeather integration
│   └── notification_service.py# Notification dispatcher
│
├── ml/
│   ├── __init__.py
│   ├── train_model.py         # Model training script
│   ├── predictor.py           # ML inference engine
│   └── disaster_model.pkl     # Serialized Random Forest model
│
├── static/
│   ├── css/
│   │   ├── style.css          # Modern emergency operations styling
│   │   └── admin.css          # Dark-theme command center styling
│   ├── js/
│   │   ├── main.js            # Core interactive logic & SOS workflow
│   │   ├── map.js             # Leaflet live map engine & GPS tracker
│   │   ├── alerts.js          # Client-side alert filter
│   │   ├── translations.js    # Multilingual dictionary (EN, TA, TE, HI)
│   │   └── admin_charts.js    # Chart.js analytics for admin dashboard
│   └── uploads/               # Uploaded incident photos and evidence
│
├── templates/
│   ├── base.html              # Master layout with SOS trigger & language switcher
│   ├── index.html             # Homepage with Hero, Live Stats, Alerts, Categories
│   ├── alerts.html            # Disaster Alerts directory
│   ├── map.html               # Interactive Live Disaster Map
│   ├── report.html            # Citizen Disaster Reporting with map picker
│   ├── emergency.html         # Emergency Help Central & Helplines
│   ├── shelters.html          # Safe Shelter Finder & Distance Sorter
│   ├── services.html          # Emergency Services Directory
│   ├── weather.html           # Weather & Hazard Dashboard
│   ├── ai_predict.html        # Interactive AI Disaster Risk Prediction Lab
│   ├── preparedness.html      # Educational Guides & Interactive Kit Checklist
│   ├── volunteer.html         # Volunteer Registration Form
│   ├── request_rescue.html    # Rescue Assistance Request Form
│   ├── user_reports.html      # My Submitted Reports & Requests
│   ├── profile.html           # Profile & Emergency Contacts CRUD
│   ├── login.html             # Citizen Login
│   ├── register.html          # Citizen Registration
│   └── admin/
│       ├── base_admin.html    # Admin Layout
│       ├── login.html         # Admin Login Portal
│       ├── dashboard.html     # Admin Command Dashboard with Chart.js
│       ├── disasters.html     # Disaster Alerts Management
│       ├── create_alert.html  # Create Alert Form
│       ├── edit_alert.html    # Edit Alert Form
│       ├── reports.html       # Report Verification Queue
│       ├── shelters.html      # Shelter Capacity Manager
│       ├── services.html      # Hospital, Police & Fire Facility Manager
│       ├── volunteers.html    # Volunteer Roster
│       └── rescue_requests.html # Rescue Operations Coordinator
│
└── README.md                  # Complete documentation
```

---

## 🎓 College & Project Demonstration Walkthrough

When presenting this project for B.Tech / Academic / Technical evaluations:
1. **Showcase Real-Time SOS:** Click the **SOS EMERGENCY** button, observe browser geolocation capture, and note the automatic nearest safe shelter calculation and contact alerts.
2. **Demonstrate AI Prediction Lab:** Open `/ai-risk`, adjust sliders (e.g. increase rainfall to 180mm and water level to 8m), and click **Compute AI Inference** to demonstrate the machine learning classification and advisory generation.
3. **Showcase Verification Workflow:** 
   - On the Citizen portal (`/report`), submit a new incident report with a photo.
   - Switch to the Admin portal (`/admin/login`), navigate to **Report Verification**, and click **Verify & Pin to Live Map**.
   - Open `/live-map` on the public portal to see the verified incident marker instantly appear.
4. **Demonstrate Multilingual Support:** Click the language switcher in the navbar to seamlessly toggle between English, Tamil, Telugu, and Hindi.
