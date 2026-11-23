/**
 * SMART DISASTER MANAGEMENT SYSTEM - TACTICAL GIS MAP ENGINE 2.0
 * Features: Dark/Light/Satellite Tiles, Sonar GPS Beacon, Danger Perimeters, Dynamic Routing Polyline
 */

let mapInstance = null;
let userMarker = null;
let currentRouteLine = null;
let layerGroups = {
  alerts: L.layerGroup(),
  shelters: L.layerGroup(),
  hospitals: L.layerGroup(),
  police: L.layerGroup(),
  fire: L.layerGroup(),
  reports: L.layerGroup()
};

document.addEventListener('DOMContentLoaded', () => {
  const mapElement = document.getElementById('disasterMap');
  if (!mapElement) return;

  initDisasterMap(mapElement);
});

function initDisasterMap(container) {
  // Center of India / Default coastal coordinates
  const defaultLat = 13.0827;
  const defaultLon = 80.2707;

  // Base Layers
  const darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap, © CartoDB',
    maxZoom: 19
  });

  const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  });

  const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    maxZoom: 19
  });

  // Pick initial layer based on current theme
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  const initialBaseLayer = currentTheme === 'dark' ? darkLayer : streetLayer;

  mapInstance = L.map(container, {
    center: [defaultLat, defaultLon],
    zoom: 12,
    layers: [initialBaseLayer]
  });

  // Layer control for base maps and overlays
  const baseMaps = {
    "🌙 High-Tech Dark": darkLayer,
    "🗺️ Standard Street": streetLayer,
    "🛰️ Satellite Imagery": satelliteLayer
  };

  const overlayMaps = {
    "🚨 Active Disaster Alerts": layerGroups.alerts,
    "🛡️ Safe Shelters": layerGroups.shelters,
    "🏥 Hospitals & Trauma": layerGroups.hospitals,
    "👮 Police Stations": layerGroups.police,
    "🚒 Fire & Rescue": layerGroups.fire,
    "📍 Verified Reports": layerGroups.reports
  };

  L.control.layers(baseMaps, overlayMaps, { position: 'topright' }).addTo(mapInstance);

  // Add all overlay layer groups to the map
  Object.values(layerGroups).forEach(group => group.addTo(mapInstance));

  // Load backend map data
  fetchMapData();

  // Trigger browser GPS location
  locateUserGPS();

  // Setup layer checkboxes if present in DOM
  setupLayerToggles();
}

function fetchMapData() {
  fetch('/api/map-data')
    .then(res => res.json())
    .then(data => {
      if (data.status !== 'success') return;

      renderAlerts(data.alerts);
      renderShelters(data.shelters);
      renderHospitals(data.hospitals);
      renderPolice(data.police);
      renderFireStations(data.fire_stations);
      renderVerifiedReports(data.reports);

      // Populate nearby shelter sidebar if element exists
      populateShelterSidebar(data.shelters);
    })
    .catch(err => console.error("Error loading map data:", err));
}

/* ==================== USER GPS SONAR RADAR ==================== */
function locateUserGPS() {
  if (!navigator.geolocation || !mapInstance) return;

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;

      const sonarIcon = L.divIcon({
        className: 'sonar-marker-container',
        html: `
          <div class="sonar-emitter">
            <div class="sonar-wave"></div>
          </div>
        `,
        iconSize: [22, 22],
        iconAnchor: [11, 11]
      });

      if (userMarker) mapInstance.removeLayer(userMarker);

      userMarker = L.marker([lat, lon], { icon: sonarIcon, zIndexOffset: 1000 })
        .addTo(mapInstance)
        .bindPopup(`
          <div style="font-family: 'Outfit', sans-serif;">
            <strong class="text-primary"><i class="bi bi-geo-alt-fill"></i> Your Current Location</strong><br>
            <small class="text-muted">GPS: [${lat.toFixed(4)}, ${lon.toFixed(4)}]</small>
          </div>
        `);

      mapInstance.setView([lat, lon], 13);
    },
    (err) => console.log("GPS Location unavailable"),
    { timeout: 8000 }
  );
}

/* ==================== RENDERING LAYERS ==================== */
function renderAlerts(alerts) {
  layerGroups.alerts.clearLayers();
  alerts.forEach(a => {
    if (!a.latitude || !a.longitude) return;

    // Severity color
    let color = '#ef4444';
    if (a.severity === 'High') color = '#f97316';
    else if (a.severity === 'Moderate') color = '#eab308';
    else if (a.severity === 'Low') color = '#22c55e';

    // Danger Radius Circle
    const radiusMeters = (a.affected_radius_km || 10) * 1000;
    L.circle([a.latitude, a.longitude], {
      radius: radiusMeters,
      color: color,
      fillColor: color,
      fillOpacity: 0.18,
      weight: 2,
      dashArray: '6, 6'
    }).addTo(layerGroups.alerts);

    // Hazard Marker Icon
    const markerHtml = `
      <div style="background: ${color}; width: 34px; height: 34px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 0 15px ${color}; font-size: 16px;">
        <i class="bi bi-exclamation-triangle-fill"></i>
      </div>
    `;
    const alertIcon = L.divIcon({ className: '', html: markerHtml, iconSize: [34, 34], iconAnchor: [17, 17] });

    L.marker([a.latitude, a.longitude], { icon: alertIcon })
      .addTo(layerGroups.alerts)
      .bindPopup(`
        <div style="min-width: 220px; font-family: 'Plus Jakarta Sans', sans-serif;">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="badge" style="background:${color}; color:white;">${a.severity}</span>
            <span class="badge bg-dark">${a.disaster_type}</span>
          </div>
          <h6 class="fw-bold mb-1" style="font-family:'Outfit',sans-serif;">${a.title}</h6>
          <p class="small text-muted mb-2"><i class="bi bi-geo-alt"></i> ${a.location}</p>
          <p class="small mb-2">${a.description || ''}</p>
          <div class="p-2 bg-light rounded small mb-2 text-danger">
            <strong>Advisory:</strong> ${a.recommended_action || 'Follow civil defense updates.'}
          </div>
          <a href="/alerts" class="btn btn-sm btn-danger w-100 rounded-pill">View Emergency Bulletin</a>
        </div>
      `);
  });
}

function renderShelters(shelters) {
  layerGroups.shelters.clearLayers();
  shelters.forEach(s => {
    if (!s.latitude || !s.longitude) return;

    const markerHtml = `
      <div style="background: #10b981; width: 34px; height: 34px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 0 15px #10b981; font-size: 16px;">
        <i class="bi bi-shield-check"></i>
      </div>
    `;
    const icon = L.divIcon({ className: '', html: markerHtml, iconSize: [34, 34], iconAnchor: [17, 17] });

    const shelterMarker = L.marker([s.latitude, s.longitude], { icon: icon })
      .addTo(layerGroups.shelters)
      .bindPopup(`
        <div style="min-width: 240px; font-family: 'Plus Jakarta Sans', sans-serif;">
          <span class="badge bg-success mb-1">Safe Evacuation Shelter</span>
          <h6 class="fw-bold mb-1" style="font-family:'Outfit',sans-serif;">${s.name}</h6>
          <p class="small text-muted mb-2"><i class="bi bi-geo-alt"></i> ${s.address}</p>
          
          <div class="mb-2">
            <div class="d-flex justify-content-between small mb-1">
              <span>Occupancy</span>
              <strong>${s.occupancy} / ${s.capacity} (${s.available_capacity} spots left)</strong>
            </div>
            <div class="progress" style="height: 6px;">
              <div class="progress-bar ${s.occupancy_percentage > 80 ? 'bg-danger' : 'bg-success'}" style="width: ${s.occupancy_percentage}%;"></div>
            </div>
          </div>

          <div class="d-flex gap-1 flex-wrap mb-3">
            <span class="badge ${s.food_available ? 'bg-success' : 'bg-secondary'}">Food</span>
            <span class="badge ${s.water_available ? 'bg-success' : 'bg-secondary'}">Water</span>
            <span class="badge ${s.medical_support ? 'bg-success' : 'bg-secondary'}">Medical</span>
            <span class="badge ${s.power_backup ? 'bg-success' : 'bg-secondary'}">Power</span>
          </div>

          <div class="d-flex gap-1">
            <button onclick="drawEvacuationRoute(${s.latitude}, ${s.longitude}, '${s.name.replace(/'/g, "\\'")}')" class="btn btn-sm btn-success rounded-pill flex-grow-1">
              <i class="bi bi-compass-fill me-1"></i> Evac Route
            </button>
            <a href="tel:${s.contact_number || '112'}" class="btn btn-sm btn-outline-success rounded-pill px-3">
              <i class="bi bi-telephone-fill"></i>
            </a>
          </div>
        </div>
      `);
  });
}

function renderHospitals(hospitals) {
  layerGroups.hospitals.clearLayers();
  hospitals.forEach(h => {
    if (!h.latitude || !h.longitude) return;

    const markerHtml = `
      <div style="background: #0284c7; width: 32px; height: 32px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 0 12px #0284c7; font-size: 15px;">
        <i class="bi bi-hospital"></i>
      </div>
    `;
    const icon = L.divIcon({ className: '', html: markerHtml, iconSize: [32, 32], iconAnchor: [16, 16] });

    L.marker([h.latitude, h.longitude], { icon: icon })
      .addTo(layerGroups.hospitals)
      .bindPopup(`
        <div style="min-width: 220px; font-family: 'Plus Jakarta Sans', sans-serif;">
          <span class="badge bg-primary mb-1">Trauma & Medical Facility</span>
          <h6 class="fw-bold mb-1" style="font-family:'Outfit',sans-serif;">${h.name}</h6>
          <p class="small text-muted mb-2">${h.address}</p>
          <div class="small mb-2">
            <span class="badge bg-success">${h.beds_available} Available Beds</span>
            <span class="badge ${h.ambulance_available ? 'bg-info text-dark' : 'bg-secondary'}">Ambulance Ready</span>
          </div>
          <a href="tel:${h.contact_number}" class="btn btn-sm btn-primary w-100 rounded-pill">
            <i class="bi bi-telephone-fill me-1"></i> Call ${h.contact_number}
          </a>
        </div>
      `);
  });
}

function renderPolice(police) {
  layerGroups.police.clearLayers();
  police.forEach(p => {
    if (!p.latitude || !p.longitude) return;

    const markerHtml = `
      <div style="background: #3b82f6; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 0 10px #3b82f6; font-size: 14px;">
        <i class="bi bi-shield-shaded"></i>
      </div>
    `;
    const icon = L.divIcon({ className: '', html: markerHtml, iconSize: [30, 30], iconAnchor: [15, 15] });

    L.marker([p.latitude, p.longitude], { icon: icon })
      .addTo(layerGroups.police)
      .bindPopup(`
        <div style="min-width: 200px;">
          <span class="badge bg-primary mb-1">Police Command Post</span>
          <h6 class="fw-bold mb-1">${p.name}</h6>
          <p class="small text-muted mb-2">${p.address}</p>
          <a href="tel:${p.contact_number}" class="btn btn-sm btn-outline-primary w-100 rounded-pill">Call Station</a>
        </div>
      `);
  });
}

function renderFireStations(fire) {
  layerGroups.fire.clearLayers();
  fire.forEach(f => {
    if (!f.latitude || !f.longitude) return;

    const markerHtml = `
      <div style="background: #f97316; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 0 10px #f97316; font-size: 14px;">
        <i class="bi bi-fire"></i>
      </div>
    `;
    const icon = L.divIcon({ className: '', html: markerHtml, iconSize: [30, 30], iconAnchor: [15, 15] });

    L.marker([f.latitude, f.longitude], { icon: icon })
      .addTo(layerGroups.fire)
      .bindPopup(`
        <div style="min-width: 200px;">
          <span class="badge bg-warning text-dark mb-1">Fire & Water Rescue</span>
          <h6 class="fw-bold mb-1">${f.name}</h6>
          <p class="small text-muted mb-2">${f.address}</p>
          <div class="small mb-2">
            <span class="badge bg-primary">${f.rescue_boats} Rescue Boats</span>
            <span class="badge bg-secondary">${f.fire_trucks} Trucks</span>
          </div>
          <a href="tel:${f.contact_number}" class="btn btn-sm btn-outline-warning text-dark w-100 rounded-pill">Call Fire Unit</a>
        </div>
      `);
  });
}

function renderVerifiedReports(reports) {
  layerGroups.reports.clearLayers();
  reports.forEach(r => {
    if (!r.latitude || !r.longitude) return;

    const markerHtml = `
      <div style="background: #dc2626; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 0 12px #dc2626; font-size: 14px;">
        <i class="bi bi-patch-exclamation-fill"></i>
      </div>
    `;
    const icon = L.divIcon({ className: '', html: markerHtml, iconSize: [30, 30], iconAnchor: [15, 15] });

    L.marker([r.latitude, r.longitude], { icon: icon })
      .addTo(layerGroups.reports)
      .bindPopup(`
        <div style="min-width: 220px;">
          <span class="badge bg-danger mb-1">Verified Field Incident</span>
          <h6 class="fw-bold mb-1">${r.title}</h6>
          <p class="small text-muted mb-2">${r.location}</p>
          <p class="small text-secondary mb-2">${r.description || ''}</p>
          ${r.image ? `<img src="/static/uploads/${r.image}" class="img-fluid rounded mb-2" style="max-height:120px;width:100%;object-fit:cover;">` : ''}
        </div>
      `);
  });
}

/* ==================== DYNAMIC EVACUATION ROUTING ==================== */
window.drawEvacuationRoute = function(destLat, destLon, destName) {
  if (!mapInstance) return;

  // If user marker exists, use it; otherwise ask or use center
  const userLat = userMarker ? userMarker.getLatLng().lat : mapInstance.getCenter().lat;
  const userLon = userMarker ? userMarker.getLatLng().lng : mapInstance.getCenter().lng;

  if (currentRouteLine) {
    mapInstance.removeLayer(currentRouteLine);
  }

  // Draw smooth animated evacuation line
  const routePoints = [
    [userLat, userLon],
    [destLat, destLon]
  ];

  currentRouteLine = L.polyline(routePoints, {
    color: '#06b6d4',
    weight: 5,
    opacity: 0.9,
    dashArray: '10, 10',
    lineCap: 'round'
  }).addTo(mapInstance);

  // Fit bounds to show route
  mapInstance.fitBounds(currentRouteLine.getBounds(), { padding: [50, 50] });

  // Open destination popup with navigation trigger
  L.popup()
    .setLatLng([destLat, destLon])
    .setContent(`
      <div class="text-center p-2" style="font-family:'Outfit',sans-serif;">
        <strong class="text-success"><i class="bi bi-shield-check"></i> Route Plotted to ${destName}</strong><br>
        <a href="https://www.google.com/maps/dir/?api=1&destination=${destLat},${destLon}" target="_blank" class="btn btn-sm btn-primary rounded-pill mt-2 px-3">
          <i class="bi bi-google"></i> Open Turn-by-Turn GPS
        </a>
      </div>
    `)
    .openOn(mapInstance);
};

/* ==================== SHELTER SIDEBAR POINTER ==================== */
function populateShelterSidebar(shelters) {
  const container = document.getElementById('mapShelterList');
  if (!container) return;

  if (!shelters || shelters.length === 0) {
    container.innerHTML = '<div class="text-muted small p-3">No shelters loaded.</div>';
    return;
  }

  let html = '';
  shelters.slice(0, 6).forEach(s => {
    html += `
      <div class="p-3 border-bottom shelter-sidebar-card" style="cursor: pointer;" onclick="focusMapOn(${s.latitude}, ${s.longitude})">
        <div class="d-flex justify-content-between align-items-start mb-1">
          <strong class="small text-dark">${s.name}</strong>
          <span class="badge bg-success" style="font-size:0.7rem;">${s.available_capacity} free</span>
        </div>
        <p class="small text-muted mb-2">${s.address}</p>
        <button class="btn btn-xs btn-outline-success rounded-pill px-2 py-0" style="font-size:0.75rem;" onclick="event.stopPropagation(); drawEvacuationRoute(${s.latitude}, ${s.longitude}, '${s.name.replace(/'/g, "\\'")}')">
          <i class="bi bi-compass"></i> Route Here
        </button>
      </div>
    `;
  });

  container.innerHTML = html;
}

window.focusMapOn = function(lat, lon) {
  if (mapInstance && lat && lon) {
    mapInstance.flyTo([lat, lon], 15, { animate: true, duration: 1.2 });
  }
};

function setupLayerToggles() {
  const toggles = {
    'layerAlerts': layerGroups.alerts,
    'layerShelters': layerGroups.shelters,
    'layerHospitals': layerGroups.hospitals,
    'layerPolice': layerGroups.police,
    'layerFire': layerGroups.fire,
    'layerReports': layerGroups.reports
  };

  Object.entries(toggles).forEach(([id, layer]) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', (e) => {
        if (e.target.checked) mapInstance.addLayer(layer);
        else mapInstance.removeLayer(layer);
      });
    }
  });
}
