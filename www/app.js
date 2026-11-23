let map, userMarker, routeLayer;
let userLat, userLon;
let userState = null;
const statusEl = document.getElementById('status') || {};
const hazardEl = document.getElementById('hazard') || {};
const placesEl = document.getElementById('places') || {};

function setPrecautionsHtml(html){
  const el = document.getElementById('precautions'); if(el) el.innerHTML = html;
}

function initMap() {
  map = L.map('map').setView([0,0], 2);

  const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  });

  const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: '© ESRI, Maxar, Earthstar Geographics, and the GIS User Community'
  });

  const baseLayers = {
    'Street': streetLayer,
    'Satellite': satelliteLayer
  };

  streetLayer.addTo(map);
  L.control.layers(baseLayers, null, { position: 'topright' }).addTo(map);
}

function setStatus(text){
  const el = document.getElementById('status'); if(el) el.innerText = text;
}

function setHazard(text, cls){
  const el = document.getElementById('hazard'); if(el){ el.innerText = text; el.className = cls||''; }
}

function onLocation(lat, lon){
  userLat = lat; userLon = lon;
  setStatus(`Location: ${lat.toFixed(5)}, ${lon.toFixed(5)}`);
  map.setView([lat,lon], 13);
  if(userMarker) map.removeLayer(userMarker);
  userMarker = L.marker([lat,lon]).addTo(map).bindPopup('You are here').openPopup();
  reverseGeocodeState(lat, lon).then(state=>{
    userState = state;
    return findHazards(lat, lon);
  }).then(hazardType=>{
    showPrecautions(userState, hazardType);
  }).catch(err=>{
    console.warn(err);
    // still try to show general precautions
    findHazards(lat, lon).then(h=>showPrecautions(null,h));
  });
  findSafePlaces(lat, lon);
}

function findHazards(lat, lon){
  setHazard('Checking weather...', '');
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&hourly=precipitation&timezone=auto`;
  return fetchWithCache(url, `hazard_${lat.toFixed(3)}_${lon.toFixed(3)}`).then(data=>{
    const cw = data.current_weather;
    let msg = 'No immediate alerts detected.';
    let cls = '';
    let hazardType = 'none';
    if(cw){
      const temp = cw.temperature;
      msg = `Current temp ${temp}°C, wind ${cw.windspeed} m/s.`;
      // detect very high winds (storm)
      if(cw.windspeed && cw.windspeed >= 20){
        msg = `High winds detected (${cw.windspeed} m/s) — storm conditions possible.`;
        cls = 'danger';
        hazardType = 'storm';
      }
    }
    // check next 6 hours precipitation
    if(data.hourly && data.hourly.precipitation){
      const nowIndex = 0;
      const next6 = data.hourly.precipitation.slice(nowIndex, nowIndex+6);
      const maxPrecip = Math.max(...next6);
      if(maxPrecip >= 5){
        msg = 'Heavy rain expected soon — possible flood/drainage risk.';
        cls = 'danger';
        hazardType = 'flood';
      } else if(maxPrecip >= 1){
        msg = 'Rain expected; take caution.';
        cls = 'warning';
        hazardType = 'heavy_rain';
      }
    }
    setHazard(msg, cls);
    // show alert banner / notification for non-none hazards
    if(hazardType !== 'none') triggerAlert(hazardType, msg);
    return hazardType;
  }).catch(err=>{
    setHazard('Weather check failed', '');
    console.warn(err);
    return 'none';
  });
}

function findSafePlaces(lat, lon){
  setStatus('Searching for nearby shelters and hospitals...');
  const radius = 5000; // meters
  const query = `[
out:json][timeout:25];(
  node["emergency"="shelter"](around:${radius},${lat},${lon});
  node["amenity"="shelter"](around:${radius},${lat},${lon});
  node["amenity"="hospital"](around:${radius},${lat},${lon});
  node["amenity"="police"](around:${radius},${lat},${lon});
  node["amenity"="fire_station"](around:${radius},${lat},${lon});
  node["amenity"="school"](around:${radius},${lat},${lon});
);
out center 20;`;
    // extended POIs: food, bus stops, airports
    const query2 = `[
  out:json][timeout:25];(
    node["amenity"="restaurant"](around:${radius},${lat},${lon});
    node["amenity"="cafe"](around:${radius},${lat},${lon});
    node["amenity"="fast_food"](around:${radius},${lat},${lon});
    node["highway"="bus_stop"](around:${radius},${lat},${lon});
    node["amenity"="bus_station"](around:${radius},${lat},${lon});
    node["public_transport"="stop_position"](around:${radius},${lat},${lon});
    node["aeroway"="aerodrome"](around:${radius},${lat},${lon});
    node["aeroway"="airport"](around:${radius},${lat},${lon});
  );
  out center 50;`;
    // fetch main safety POIs first, then extended POIs and merge results
    Promise.all([
    fetchWithCache('https://overpass-api.de/api/interpreter', `places_main_${lat.toFixed(3)}_${lon.toFixed(3)}`, {method:'POST', body:query, headers:{'Content-Type':'text/plain'}}),
    fetchWithCache('https://overpass-api.de/api/interpreter', `places_ext_${lat.toFixed(3)}_${lon.toFixed(3)}`, {method:'POST', body:query2, headers:{'Content-Type':'text/plain'}})
  ]).then(results=>{
    const dataMain = results[0] || {elements:[]};
    const dataExt = results[1] || {elements:[]};
      // merge elements, avoid duplicates by id
      const mapById = new Map();
      (dataMain.elements || []).forEach(e=>mapById.set(e.id, e));
      (dataExt.elements || []).forEach(e=>{ if(!mapById.has(e.id)) mapById.set(e.id,e); });
      const data = { elements: Array.from(mapById.values()) };
      if(!data.elements || data.elements.length===0){
        placesEl.innerHTML = '<li>No safe places found within 5km.</li>';
        document.getElementById('routeBtn').disabled = true;
        setStatus('No nearby safe places found');
        return;
      }
      // compute distance and sort
      const places = data.elements.map(el=>{
        const plat = el.lat||el.center&&el.center.lat;
        const plon = el.lon||el.center&&el.center.lon;
        const type = el.tags && (el.tags.amenity || el.tags.aeroway || el.tags.highway || el.tags.public_transport || el.tags.emergency) || 'place';
        const name = el.tags && (el.tags.name) ? `${el.tags.name} (${type})` : `${type}`;
        const dist = haversine(userLat,userLon,plat,plon);
        const cat = normalizeType(type);
        return {id:el.id,lat:plat,lon:plon,name,dist,raw:el,type,cat};
      }).filter(p=>p.lat&&p.lon).sort((a,b)=>a.dist-b.dist);

      placesEl.innerHTML = '';
      // remove old place markers (support arrays of markers or wrapper objects)
      if(window._placeMarkers) window._placeMarkers.forEach(m=>{
        try{
          if(m && m.marker) map.removeLayer(m.marker);
          else map.removeLayer(m);
        }catch(e){}
      });
      window._placeMarkers = [];

      places.forEach((p,i)=>{
            const li = document.createElement('li'); li.className='place-item';
            li.innerHTML = `<strong>${p.name}</strong><br>${p.dist.toFixed(0)} m <small>${p.cat}</small> <span class="route-link" data-i="${i}">[Route]</span>`;
            placesEl.appendChild(li);
            // create colored circle marker per type
            const color = colorForType(p.type);
            const marker = L.circleMarker([p.lat,p.lon], {radius:8, color:color, fillColor:color, fillOpacity:0.9}).bindPopup(`${p.name} — ${p.dist.toFixed(0)} m`);
            marker.addTo(map);
            // store object with type for filtering
            window._placeMarkers.push({marker, type:p.cat});
        li.querySelector('.route-link').addEventListener('click', ()=>{
          routeTo(p.lat,p.lon);
        });
      });

      // enable route to nearest
      if(places.length>0){
        const nearest = places[0];
        document.getElementById('routeBtn').disabled = false;
        document.getElementById('routeBtn').onclick = ()=>routeTo(nearest.lat,nearest.lon);
        setStatus(`Found ${places.length} nearby safe places. Nearest: ${nearest.name} (${nearest.dist.toFixed(0)} m)`);
      }
    }).catch(err=>{
      console.warn(err);
      setStatus('Place search failed');
    });
}

function normalizeType(type){
  if(!type) return 'place';
  type = type.toLowerCase();
  if(type.includes('hospital')) return 'hospital';
  if(type.includes('police')) return 'police';
  if(type.includes('shelter')) return 'shelter';
  if(type.includes('fire')) return 'fire_station';
  if(type.includes('school')) return 'school';
  if(type.includes('restaurant')||type.includes('cafe')||type.includes('fast_food')) return 'food';
  if(type.includes('bus')||type.includes('stop')||type.includes('station')) return 'bus';
  if(type.includes('airport')||type.includes('aerodrome')) return 'airport';
  return 'place';
}

function colorForType(type){
  const t = normalizeType(type);
  switch(t){
    case 'hospital': return '#d11';
    case 'police': return '#1166cc';
    case 'shelter': return '#1a9a2a';
    case 'fire_station': return '#ff8000';
    case 'school': return '#7b1fa2';
    case 'food': return '#8b5a2b';
    case 'bus': return '#009688';
    case 'airport': return '#000000';
    default: return '#666666';
  }
}

function applyFilters(){
  const checks = Array.from(document.querySelectorAll('#legend input[type=checkbox]')).filter(i=>i.checked).map(i=>i.getAttribute('data-cat'));
  if(!window._placeMarkers) return;
  window._placeMarkers.forEach(obj=>{
    const cat = obj.type;
    if(checks.includes(cat) || checks.includes('place')){
      if(!map.hasLayer(obj.marker)) map.addLayer(obj.marker);
    } else {
      if(map.hasLayer(obj.marker)) map.removeLayer(obj.marker);
    }
  });
}

function routeTo(destLat, destLon){
  setStatus('Requesting route...');
  const url = `https://router.project-osrm.org/route/v1/driving/${userLon},${userLat};${destLon},${destLat}?overview=full&geometries=geojson`;
  fetchWithCache(url, `route_${userLat.toFixed(3)}_${userLon.toFixed(3)}_${destLat.toFixed(3)}_${destLon.toFixed(3)}`, {method:'GET'}).then(data=>{
    if(!data.routes || data.routes.length===0) { setStatus('No route found'); return; }
    const coords = data.routes[0].geometry.coordinates.map(c=>[c[1],c[0]]);
    if(routeLayer) map.removeLayer(routeLayer);
    routeLayer = L.polyline(coords, {color:'blue',weight:4}).addTo(map);
    map.fitBounds(routeLayer.getBounds(),{padding:[50,50]});
    setStatus('Route shown on map');
  }).catch(err=>{ console.warn(err); setStatus('Routing failed'); });
}

function sendSOS(){
  const text = `SOS! I need help. My location: https://www.openstreetmap.org/?mlat=${userLat}&mlon=${userLon} (approx)`;
  if(navigator.share){
    navigator.share({title:'SOS',text,})
      .then(()=>setStatus('Shared SOS'))
      .catch(()=>setStatus('Share cancelled'));
  } else {
    // fallback: open SMS link (mobile browsers only)
    const body = encodeURIComponent(text);
    window.location.href = `sms:?&body=${body}`;
  }
}

function reverseGeocodeState(lat, lon){
  const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=5&addressdetails=1`;
  return fetchWithCache(url, `revgeo_${lat.toFixed(3)}_${lon.toFixed(3)}`, {headers:{'Accept':'application/json','User-Agent':'disaster-prototype/1.0'}}).then(j=>{
    if(!j) return null;
    const addr = j.address || {};
    return addr.state || addr.county || addr.region || addr.state_district || null;
  }).catch(err=>{ console.warn('reverse geocode failed', err); return null; });
}

function showPrecautions(state, hazardType){
  if(!window._precautions){
    fetch('precautions.json').then(r=>r.json()).then(j=>{ window._precautions=j; showPrecautions(state,hazardType); }).catch(()=>{
      setPrecautionsHtml('<em>Precaution data unavailable.</em>');
    });
    return;
  }
  const data = window._precautions;
  const key = state && data[state] ? state : 'default';
  const entry = data[key] || data['default'];
  let html = `<strong>State:</strong> ${state || 'Unknown'}<br>`;
  html += `<strong>Hazard:</strong> ${hazardType || 'none'}<br><ul>`;
  if(hazardType === 'flood') html += `<li>${entry.flood}</li>`;
  else if(hazardType === 'heavy_rain') html += `<li>${entry.heavy_rain}</li>`;
  else if(hazardType === 'storm') html += `<li>${entry.storm || entry.general}</li>`;
  else html += `<li>${entry.general}</li>`;
  html += `</ul>`;
  html += `<p><strong>Emergency:</strong> Call 112</p>`;
  setPrecautionsHtml(html);
}

// Utility: fetch with localStorage fallback cache
function fetchWithCache(url, cacheKey, options){
  // if options provided and method is POST, Overpass expects body; use fetch then cache response JSON
  return fetch(url, options).then(r=>r.clone().json()).then(json=>{
    try{ localStorage.setItem(cacheKey, JSON.stringify(json)); }catch(e){}
    return json;
  }).catch(err=>{
    // attempt to load from localStorage
    try{ const s = localStorage.getItem(cacheKey); if(s) return JSON.parse(s); }catch(e){}
    // attempt caches.match for SW-cached responses
    if('caches' in window){
      return caches.match(url).then(resp=>resp?resp.json():null).catch(()=>null);
    }
    return null;
  });
}

function triggerAlert(hazardType, message){
  const banner = document.getElementById('alertBanner');
  if(!banner) return;
  banner.innerText = message;
  banner.className = 'alert-banner ' + (hazardType === 'flood' || hazardType === 'storm' ? 'alert-danger' : 'alert-warning');
  // try browser notification
  if(window.Notification){
    if(Notification.permission === 'granted'){
      new Notification('Alert: '+hazardType, {body: message});
    } else if(Notification.permission !== 'denied'){
      Notification.requestPermission().then(p=>{ if(p==='granted') new Notification('Alert: '+hazardType, {body: message}); });
    }
  }
  // clear banner after 60s
  setTimeout(()=>{ if(banner) { banner.innerText=''; banner.className=''; } },60000);
}

function haversine(lat1,lon1,lat2,lon2){
  function toRad(x){return x*Math.PI/180}
  const R=6371000;
  const dLat=toRad(lat2-lat1); const dLon=toRad(lon2-lon1);
  const a=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(toRad(lat1))*Math.cos(toRad(lat2))*Math.sin(dLon/2)*Math.sin(dLon/2);
  const c=2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
  return R*c;
}

const ADMIN_SESSION_KEY = 'evac_active_sessions';
const ADMIN_VISIT_KEY = 'evac_visit_count';
const ADMIN_SESSION_TTL = 120000; // 2 minutes
const sessionId = `${Date.now()}_${Math.random().toString(36).slice(2,10)}`;
let adminBroadcast = null;

function getAdminSessions(){
  try{ return JSON.parse(localStorage.getItem(ADMIN_SESSION_KEY) || '{}'); }catch(e){ return {}; }
}

function saveAdminSessions(sessions){
  try{ localStorage.setItem(ADMIN_SESSION_KEY, JSON.stringify(sessions)); }catch(e){}
}

function refreshAdminDashboard(){
  const sessions = getAdminSessions();
  const cutoff = Date.now() - ADMIN_SESSION_TTL;
  Object.keys(sessions).forEach(id => { if(sessions[id] < cutoff) delete sessions[id]; });
  sessions[sessionId] = Date.now();
  saveAdminSessions(sessions);
  if(adminBroadcast) adminBroadcast.postMessage('heartbeat');
  updateAdminCounts(sessions);
}

function updateAdminCounts(sessions){
  const activeCount = Object.keys(sessions).length;
  const visitCount = parseInt(localStorage.getItem(ADMIN_VISIT_KEY) || '0', 10);
  const countEl = document.getElementById('activeUsersCount');
  const visitEl = document.getElementById('visitCount');
  const timeEl = document.getElementById('adminRefreshTime');
  if(countEl) countEl.innerText = activeCount;
  if(visitEl) visitEl.innerText = visitCount;
  if(timeEl) timeEl.innerText = new Date().toLocaleTimeString();
}

function incrementVisitCount(){
  try{
    const current = parseInt(localStorage.getItem(ADMIN_VISIT_KEY) || '0', 10) + 1;
    localStorage.setItem(ADMIN_VISIT_KEY, current);
  }catch(e){}
}

function loadUpdateHistory(){
  const updateList = document.getElementById('updateList');
  if(!updateList) return;
  fetch('updates.json').then(r => r.json()).then(data => {
    if(!data || !Array.isArray(data.notes)){
      updateList.innerHTML = '<p>No update history available.</p>';
      return;
    }
    updateList.innerHTML = '';
    data.notes.forEach(note => {
      const item = document.createElement('div');
      item.className = 'update-item';
      const title = document.createElement('h4');
      title.innerText = `${note.version} — ${note.date}`;
      const desc = document.createElement('p');
      desc.innerText = note.summary || '';
      const list = document.createElement('ul');
      note.changes.forEach(change => {
        const li = document.createElement('li');
        li.innerText = change;
        list.appendChild(li);
      });
      item.appendChild(title);
      if(note.summary) item.appendChild(desc);
      item.appendChild(list);
      updateList.appendChild(item);
    });
  }).catch(() => {
    updateList.innerHTML = '<p>Unable to load update history.</p>';
  });
}

function toggleAdminPanel(){
  const panel = document.getElementById('adminDashboard');
  if(!panel) return;
  panel.classList.toggle('hidden');
  if(!panel.classList.contains('hidden')){
    refreshAdminDashboard();
    loadUpdateHistory();
  }
}

function initAdminDashboard(){
  const adminBtn = document.getElementById('adminBtn');
  if(adminBtn) adminBtn.addEventListener('click', toggleAdminPanel);
  const refreshBtn = document.getElementById('adminRefreshBtn');
  if(refreshBtn) refreshBtn.addEventListener('click', refreshAdminDashboard);

  incrementVisitCount();
  refreshAdminDashboard();
  setInterval(refreshAdminDashboard, 30000);

  if('BroadcastChannel' in window){
    adminBroadcast = new BroadcastChannel('evac-admin-dashboard');
    adminBroadcast.onmessage = message => {
      if(message.data === 'heartbeat') updateAdminCounts(getAdminSessions());
    };
  }

  window.addEventListener('beforeunload', () => {
    const sessions = getAdminSessions();
    delete sessions[sessionId];
    saveAdminSessions(sessions);
    if(adminBroadcast) adminBroadcast.close();
  });
}

function start(){
  initMap();
  initAdminDashboard();
  document.getElementById('locateBtn').addEventListener('click', ()=>{
    setStatus('Locating...');
    if(!navigator.geolocation) { setStatus('Geolocation not supported'); return; }
    navigator.geolocation.getCurrentPosition(pos=>{
      onLocation(pos.coords.latitude,pos.coords.longitude);
    }, err=>{ setStatus('Location failed: '+err.message); });
  });
  // manual test location inputs
  const setBtn = document.getElementById('setTestBtn');
  if(setBtn){
    setBtn.addEventListener('click', ()=>{
      const lat = parseFloat(document.getElementById('testLat').value);
      const lon = parseFloat(document.getElementById('testLon').value);
      if(Number.isFinite(lat) && Number.isFinite(lon)){
        onLocation(lat, lon);
      } else {
        setStatus('Invalid test coordinates');
      }
    });
  }
  // legend filters
  const legendInputs = document.querySelectorAll('#legend input[type=checkbox]');
  legendInputs.forEach(inp=>inp.addEventListener('change', applyFilters));
  document.getElementById('sosBtn').addEventListener('click', ()=>{
    if(!userLat) { setStatus('No location yet'); return; }
    sendSOS();
  });
}

document.addEventListener('DOMContentLoaded', start);
