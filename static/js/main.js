/**
 * SMART DISASTER MANAGEMENT SYSTEM - CORE INTERACTIVE ENGINE 2.0
 * Features: Dark/Light Mode, SOS Web Audio Siren, Geolocation Radar, Real-Time Dispatch Tracker
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeSwitcher();
  initSOSHandler();
  initNotificationPolling();
  initChecklistManager();
  initCounters();
  initLanguageSelector();
});

/* ==================== 1. THEME SWITCHER (DARK / LIGHT) ==================== */
function initThemeSwitcher() {
  const toggleBtn = document.getElementById('themeToggleBtn');
  const themeIcon = document.getElementById('themeIcon');
  if (!toggleBtn) return;

  // Retrieve saved theme or prefer dark by default for high-tech look
  const savedTheme = localStorage.getItem('disaster_theme') || 'light';
  applyTheme(savedTheme);

  toggleBtn.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
  });

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('disaster_theme', theme);
    if (themeIcon) {
      if (theme === 'dark') {
        themeIcon.className = 'bi bi-sun-fill text-warning';
      } else {
        themeIcon.className = 'bi bi-moon-stars-fill text-white';
      }
    }
  }
}

/* ==================== 2. AUDIO SYNTHESIZER (EMERGENCY CHIME) ==================== */
function playEmergencyChime() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
    
    // Play dual high-low emergency alert frequencies
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(880, ctx.currentTime); // A5
    osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.3); // A4
    
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.6);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.start();
    osc.stop(ctx.currentTime + 0.6);
  } catch (e) {
    console.warn("Web Audio API not allowed or supported:", e);
  }
}

/* ==================== 3. SOS EMERGENCY TRIGGER WORKFLOW ==================== */
function initSOSHandler() {
  const sosButtons = document.querySelectorAll('.sos-emergency-btn');
  sosButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      triggerSOSWorkflow();
    });
  });
}

function triggerSOSWorkflow() {
  playEmergencyChime();

  // Create & show emergency interactive modal
  let modalElem = document.getElementById('sosActiveModal');
  if (!modalElem) {
    modalElem = document.createElement('div');
    modalElem.id = 'sosActiveModal';
    modalElem.className = 'modal fade';
    modalElem.setAttribute('tabindex', '-1');
    modalElem.setAttribute('data-bs-backdrop', 'static');
    modalElem.innerHTML = `
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content rounded-4 border-0 shadow-lg overflow-hidden">
          <div class="modal-header bg-danger text-white p-4">
            <div class="d-flex align-items-center gap-3">
              <div class="bg-white text-danger rounded-circle p-2 fs-3 d-flex align-items-center justify-content-center" style="width:50px;height:50px;">
                <i class="bi bi-broadcast-pin animate-pulse"></i>
              </div>
              <div>
                <h4 class="modal-title fw-bold mb-0">🚨 EMERGENCY SOS BROADCAST ACTIVE</h4>
                <p class="small mb-0 opacity-90">Live GPS Location Telemetry & Nearest Safe Facility Router</p>
              </div>
            </div>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body p-4 p-md-5">
            <!-- 4-step dispatch progress -->
            <div class="mb-4">
              <div class="d-flex justify-content-between text-muted small fw-bold mb-2">
                <span id="sosStep1" class="text-danger"><i class="bi bi-geo-alt-fill"></i> 1. GPS Fix</span>
                <span id="sosStep2" class="text-muted"><i class="bi bi-shield-shaded"></i> 2. Operations Alert</span>
                <span id="sosStep3" class="text-muted"><i class="bi bi-people-fill"></i> 3. Contacts Notified</span>
                <span id="sosStep4" class="text-muted"><i class="bi bi-compass"></i> 4. Safe Shelter</span>
              </div>
              <div class="progress" style="height: 8px;">
                <div id="sosProgressBar" class="progress-bar bg-danger progress-bar-striped progress-bar-animated" style="width: 25%;"></div>
              </div>
            </div>

            <div id="sosStatusMessage" class="alert alert-warning d-flex align-items-center gap-3 mb-4 rounded-3">
              <div class="spinner-border spinner-border-sm text-danger" role="status"></div>
              <div>Acquiring real-time browser GPS coordinates...</div>
            </div>

            <div id="sosResultDetails" class="d-none">
              <div class="row g-3 mb-4">
                <div class="col-md-6">
                  <div class="card p-3 border-success bg-success bg-opacity-10 rounded-3">
                    <h6 class="fw-bold text-success mb-1"><i class="bi bi-shield-check me-1"></i> Nearest Safe Shelter</h6>
                    <h5 class="fw-bold text-dark mb-1" id="sosShelterName">Loading...</h5>
                    <p class="small text-muted mb-2" id="sosShelterAddress">-</p>
                    <div class="d-flex justify-content-between align-items-center">
                      <span class="badge bg-success" id="sosShelterDist">0 km away</span>
                      <a href="#" id="sosShelterNavBtn" target="_blank" class="btn btn-sm btn-success rounded-pill px-3">
                        <i class="bi bi-navigation-fill me-1"></i> Navigate
                      </a>
                    </div>
                  </div>
                </div>

                <div class="col-md-6">
                  <div class="card p-3 border-primary bg-primary bg-opacity-10 rounded-3">
                    <h6 class="fw-bold text-primary mb-1"><i class="bi bi-hospital me-1"></i> Nearest Trauma Center</h6>
                    <h5 class="fw-bold text-dark mb-1" id="sosHospitalName">Loading...</h5>
                    <p class="small text-muted mb-2" id="sosHospitalAddress">-</p>
                    <div class="d-flex justify-content-between align-items-center">
                      <span class="badge bg-primary" id="sosHospitalDist">0 km away</span>
                      <a href="#" id="sosHospitalCallBtn" class="btn btn-sm btn-primary rounded-pill px-3">
                        <i class="bi bi-telephone-fill me-1"></i> Call Hospital
                      </a>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Quick WhatsApp / SMS Share Actions -->
              <div class="p-3 bg-light rounded-3 text-center mb-3">
                <div class="small fw-bold text-dark mb-2">Share Live Location with Family / Police:</div>
                <div class="d-flex gap-2 justify-content-center flex-wrap">
                  <a href="#" id="sosShareWhatsapp" target="_blank" class="btn btn-success btn-sm rounded-pill px-3">
                    <i class="bi bi-whatsapp me-1"></i> Share on WhatsApp
                  </a>
                  <a href="tel:112" class="btn btn-danger btn-sm rounded-pill px-3">
                    <i class="bi bi-telephone-fill me-1"></i> Call 112 National Helpline
                  </a>
                  <a href="tel:108" class="btn btn-info btn-sm rounded-pill px-3 text-dark">
                    <i class="bi bi-ambulance me-1"></i> Call 108 Ambulance
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer bg-light">
            <button type="button" class="btn btn-secondary rounded-pill px-4" data-bs-dismiss="modal">Close</button>
            <a href="/emergency" class="btn btn-danger rounded-pill px-4 fw-bold">Open Emergency Center</a>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modalElem);
  }

  const bsModal = new bootstrap.Modal(modalElem);
  bsModal.show();

  // Reset steps UI
  const pBar = document.getElementById('sosProgressBar');
  const statusMsg = document.getElementById('sosStatusMessage');
  const resultDiv = document.getElementById('sosResultDetails');
  resultDiv.classList.add('d-none');
  pBar.style.width = '25%';

  // Step 1: Detect Geolocation
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        document.getElementById('sosStep1').className = 'text-success fw-bold';
        pBar.style.width = '50%';
        statusMsg.innerHTML = `<i class="bi bi-check-circle-fill text-success"></i> GPS Fix Acquired: <strong>[${lat.toFixed(4)}, ${lon.toFixed(4)}]</strong>. Transmitting to Command Center...`;

        sendSOSRequest(lat, lon, pBar, statusMsg, resultDiv);
      },
      (err) => {
        // Fallback to default city center
        const defaultLat = 13.0827;
        const defaultLon = 80.2707;
        statusMsg.innerHTML = `<i class="bi bi-exclamation-circle text-warning"></i> GPS permission denied. Using estimated location: <strong>[${defaultLat}, ${defaultLon}]</strong>.`;
        sendSOSRequest(defaultLat, defaultLon, pBar, statusMsg, resultDiv);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  } else {
    sendSOSRequest(13.0827, 80.2707, pBar, statusMsg, resultDiv);
  }
}

function sendSOSRequest(lat, lon, pBar, statusMsg, resultDiv) {
  fetch('/api/sos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      latitude: lat,
      longitude: lon,
      emergency_type: 'Immediate SOS Rescue'
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      pBar.style.width = '100%';
      document.getElementById('sosStep2').className = 'text-success fw-bold';
      document.getElementById('sosStep3').className = 'text-success fw-bold';
      document.getElementById('sosStep4').className = 'text-success fw-bold';

      statusMsg.className = 'alert alert-success d-flex align-items-center gap-2 rounded-3';
      statusMsg.innerHTML = `<i class="bi bi-shield-check text-success fs-5"></i> <strong>SOS Request #${data.sos_id} Dispatched!</strong> Nearest response facilities computed.`;

      // Fill shelter & hospital cards
      const fac = data.emergency_facilities;
      if (fac.nearest_shelter) {
        document.getElementById('sosShelterName').textContent = fac.nearest_shelter.name;
        document.getElementById('sosShelterAddress').textContent = fac.nearest_shelter.address;
        document.getElementById('sosShelterDist').textContent = `${fac.nearest_shelter.distance_km} km away`;
        document.getElementById('sosShelterNavBtn').href = `https://www.google.com/maps/dir/?api=1&destination=${fac.nearest_shelter.latitude},${fac.nearest_shelter.longitude}`;
      }
      if (fac.nearest_hospital) {
        document.getElementById('sosHospitalName').textContent = fac.nearest_hospital.name;
        document.getElementById('sosHospitalAddress').textContent = fac.nearest_hospital.address;
        document.getElementById('sosHospitalDist').textContent = `${fac.nearest_hospital.distance_km} km away`;
        document.getElementById('sosHospitalCallBtn').href = `tel:${fac.nearest_hospital.contact_number}`;
      }

      // WhatsApp Share Link
      const waText = encodeURIComponent(`🚨 EMERGENCY SOS! I need immediate rescue assistance. My GPS Location: https://maps.google.com/?q=${lat},${lon}`);
      document.getElementById('sosShareWhatsapp').href = `https://api.whatsapp.com/send?text=${waText}`;

      resultDiv.classList.remove('d-none');
    }
  })
  .catch(err => {
    statusMsg.className = 'alert alert-danger';
    statusMsg.textContent = 'Failed to transmit SOS to server. Please call emergency services at 112 directly.';
  });
}

/* ==================== 4. NOTIFICATION POLLING ==================== */
function initNotificationPolling() {
  const notifBadge = document.getElementById('notifBadge');
  const notifDropdownList = document.getElementById('notifDropdownList');
  if (!notifBadge || !notifDropdownList) return;

  function fetchNotifications() {
    fetch('/api/notifications')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && data.notifications.length > 0) {
          notifBadge.textContent = data.notifications.length;
          notifBadge.classList.remove('d-none');

          let html = `
            <li class="dropdown-header fw-bold text-dark d-flex justify-content-between align-items-center">
              <span><i class="bi bi-broadcast text-danger me-1"></i> Live Alerts (${data.notifications.length})</span>
              <span class="badge bg-danger rounded-pill">Active</span>
            </li>
          `;

          data.notifications.slice(0, 6).forEach(n => {
            html += `
              <li>
                <div class="dropdown-item py-2 border-bottom">
                  <div class="d-flex justify-content-between align-items-start mb-1">
                    <strong class="text-danger small">${n.title}</strong>
                    <span class="badge bg-secondary" style="font-size:0.65rem;">${n.severity || 'Advisory'}</span>
                  </div>
                  <p class="text-muted small mb-0">${n.message}</p>
                </div>
              </li>
            `;
          });

          html += `<li><a class="dropdown-item text-center small text-primary fw-bold py-2" href="/alerts">View All Alerts →</a></li>`;
          notifDropdownList.innerHTML = html;
        }
      })
      .catch(e => console.log('Notification fetch silent error'));
  }

  fetchNotifications();
  setInterval(fetchNotifications, 25000);
}

/* ==================== 5. EMERGENCY CHECKLIST MANAGER ==================== */
function initChecklistManager() {
  const checklistItems = document.querySelectorAll('.checklist-item');
  if (!checklistItems.length) return;

  const storageKey = 'disaster_checklist_state';
  let savedState = JSON.parse(localStorage.getItem(storageKey) || '{}');

  checklistItems.forEach((item, idx) => {
    const checkbox = item.querySelector('input[type="checkbox"]');
    if (savedState[idx]) {
      item.classList.add('checked');
      if (checkbox) checkbox.checked = true;
    }

    item.addEventListener('click', (e) => {
      if (e.target !== checkbox) {
        if (checkbox) checkbox.checked = !checkbox.checked;
      }
      item.classList.toggle('checked', checkbox?.checked);
      savedState[idx] = checkbox?.checked;
      localStorage.setItem(storageKey, JSON.stringify(savedState));
      updateChecklistProgress();
    });
  });

  updateChecklistProgress();

  function updateChecklistProgress() {
    const total = checklistItems.length;
    const checked = Object.values(savedState).filter(Boolean).length;
    const percent = total > 0 ? Math.round((checked / total) * 100) : 0;

    const bar = document.getElementById('checklistProgressBar');
    const label = document.getElementById('checklistProgressLabel');
    if (bar) bar.style.width = `${percent}%`;
    if (label) label.textContent = `${percent}% Ready (${checked}/${total} items completed)`;
  }
}

/* ==================== 6. ANIMATED COUNTERS ==================== */
function initCounters() {
  const counters = document.querySelectorAll('.counter-animate');
  counters.forEach(c => {
    const target = +c.getAttribute('data-target') || 0;
    let current = 0;
    const increment = Math.max(1, Math.ceil(target / 40));
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        c.textContent = target;
        clearInterval(timer);
      } else {
        c.textContent = current;
      }
    }, 25);
  });
}

/* ==================== 7. LANGUAGE SELECTOR ==================== */
function initLanguageSelector() {
  const langItems = document.querySelectorAll('.lang-select-item');
  langItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const lang = item.getAttribute('data-lang');
      if (typeof window.applyLanguage === 'function') {
        window.applyLanguage(lang);
      }
    });
  });
}
