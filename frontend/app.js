/**
 * METHANOS — City Gas Distribution Network Priority & Prevention Dashboard
 * Frontend Engine
 * Phase 1: App Shell, GIS Map, Segment Detail Inspector
 * Phase 2: Configurable Weight Sliders, Monsoon Weather Modifier & Live Recalculation
 * Phase 3: 48-Hour Pre-Excavation Early Warning, Monitor Dispatch & Safety Blueprint
 */

// Configuration & Default Weights
const CONFIG = {
  API_BASE: 'http://localhost:8000/api',
  FALLBACK_JSON: 'segments.json',
  FALLBACK_DIG_NOTICES_JSON: 'dig_notices.json',
  DEFAULT_CENTER: [28.65, 77.20],
  DEFAULT_ZOOM: 11,
  TIER_COLORS: {
    CRITICAL: '#ef4444',
    HIGH: '#f97316',
    MEDIUM: '#eab308',
    LOW: '#10b981'
  },
  DEFAULT_WEIGHTS: {
    previous_incidents: 25.0,
    pe_vulnerability: 20.0,
    days_since_survey: 20.0,
    third_party_activity: 15.0,
    rodent_history: 10.0,
    public_consequence: 10.0
  },
  FACTOR_BASELINES: {
    previous_incidents: 25.0,
    pe_vulnerability: 20.0,
    days_since_survey: 20.0,
    third_party_activity: 15.0,
    rodent_history: 10.0,
    public_consequence: 10.0
  }
};

const state = {
  segments: [],
  selectedSegmentId: null,
  activeTierFilter: 'ALL',
  searchQuery: '',
  isOnlineApi: false,
  map: null,
  mapLayers: {
    polylines: {},
    markers: {}
  },
  // Phase 2 State
  weights: { ...CONFIG.DEFAULT_WEIGHTS },
  monsoonMode: false,
  normalizeTo100: false,
  activeInspectorTab: 'panelSegmentDetail',
  recalcDebounceTimer: null,
  // Phase 3 State
  digNotices: [],
  selectedNoticeId: null,
  // Phase 4 State
  confidenceBenchmarks: null,
  activeQCKey: 'high',
  // Phase 5 State
  demoStepIndex: 0,
  isDemoGuideActive: false
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initClock();
  initMap();
  setupEventListeners();
  setupPhase2CalibratorListeners();
  setupPhase3DigPreventionListeners();
  setupPhase4ConfidenceListeners();
  setupPhase5RouteAndDemoListeners();
  loadSegmentData();
  loadConfidenceData();
});

/**
 * Real-time clock update
 */
function initClock() {
  const timeEl = document.getElementById('realTimeClock');
  function updateTime() {
    const now = new Date();
    if (timeEl) {
      timeEl.textContent = now.toTimeString().split(' ')[0] + ' UTC';
    }
  }
  updateTime();
  setInterval(updateTime, 1000);
}

/**
 * Initialize Leaflet Map with Dark CartoDB Tiles
 */
function initMap() {
  const mapContainer = document.getElementById('leafletMap');
  if (!mapContainer) return;

  state.map = L.map('leafletMap', {
    zoomControl: true,
    attributionControl: false
  }).setView(CONFIG.DEFAULT_CENTER, CONFIG.DEFAULT_ZOOM);

  // CartoDB Dark Matter tile layer
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    subdomains: 'abcd'
  }).addTo(state.map);

  // Attribution
  L.control.attribution({ position: 'bottomright', prefix: false })
    .addAttribution('&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap | METHANOS GIS')
    .addTo(state.map);
}

/**
 * Setup UI Event Listeners (Phase 1)
 */
function setupEventListeners() {
  // Sync / Refresh button
  const btnRefresh = document.getElementById('btnRefreshData');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => {
      showToast('Refreshing live network & dig alert data...', 'info');
      loadSegmentData();
    });
  }

  // Tier Filter Tabs
  const filterTabs = document.querySelectorAll('.filter-tab');
  filterTabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      filterTabs.forEach(t => t.classList.remove('active'));
      e.target.classList.add('active');
      state.activeTierFilter = e.target.dataset.tier;
      renderSegmentList();
    });
  });

  // Search Input
  const searchInput = document.getElementById('segmentSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value.toLowerCase().trim();
      renderSegmentList();
    });
  }

  // Focus Benchmark P-104 Button
  const btnFocusP104 = document.getElementById('btnFocusBenchmark');
  if (btnFocusP104) {
    btnFocusP104.addEventListener('click', () => {
      selectSegment('P-104', true);
    });
  }

  const btnSelectP104Default = document.getElementById('btnSelectP104Default');
  if (btnSelectP104Default) {
    btnSelectP104Default.addEventListener('click', () => {
      selectSegment('P-104', true);
    });
  }

  // Fit All Map View
  const btnResetMap = document.getElementById('btnResetMapView');
  if (btnResetMap) {
    btnResetMap.addEventListener('click', () => {
      fitMapToAllSegments();
    });
  }

  // Log Repair Action Button
  const btnSimulateRepair = document.getElementById('btnSimulateRepair');
  if (btnSimulateRepair) {
    btnSimulateRepair.addEventListener('click', () => {
      if (state.selectedSegmentId) {
        handleRepairAction(state.selectedSegmentId);
      }
    });
  }

  // Dispatch Survey Action Button
  const btnDispatch = document.getElementById('btnDispatchTeamSurvey');
  if (btnDispatch) {
    btnDispatch.addEventListener('click', () => {
      if (state.selectedSegmentId) {
        showToast(`Priority survey dispatched to Team Alpha for segment ${state.selectedSegmentId}`, 'success');
      }
    });
  }
}

/**
 * Setup Phase 2 Weight Calibrator Listeners
 */
function setupPhase2CalibratorListeners() {
  // Inspector Tab Switching
  const tabs = document.querySelectorAll('.inspector-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      const targetPanel = tab.dataset.target;
      switchInspectorTab(targetPanel);
    });
  });

  // Header Calibrator Button Toggle
  const btnToggleCalibrator = document.getElementById('btnToggleCalibrator');
  if (btnToggleCalibrator) {
    btnToggleCalibrator.addEventListener('click', () => {
      if (state.activeInspectorTab === 'panelWeightSliders') {
        switchInspectorTab('panelSegmentDetail');
      } else {
        switchInspectorTab('panelWeightSliders');
      }
    });
  }

  // Sliders Map definition
  const sliderMappings = [
    { id: 'sliderPreviousIncidents', key: 'previous_incidents', valBadge: 'valPreviousIncidents' },
    { id: 'sliderPeVulnerability', key: 'pe_vulnerability', valBadge: 'valPeVulnerability' },
    { id: 'sliderDaysSinceSurvey', key: 'days_since_survey', valBadge: 'valDaysSinceSurvey' },
    { id: 'sliderThirdPartyActivity', key: 'third_party_activity', valBadge: 'valThirdPartyActivity' },
    { id: 'sliderRodentHistory', key: 'rodent_history', valBadge: 'valRodentHistory' },
    { id: 'sliderPublicConsequence', key: 'public_consequence', valBadge: 'valPublicConsequence' }
  ];

  sliderMappings.forEach(({ id, key, valBadge }) => {
    const sliderEl = document.getElementById(id);
    const badgeEl = document.getElementById(valBadge);

    if (sliderEl) {
      sliderEl.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        state.weights[key] = val;
        if (badgeEl) badgeEl.textContent = `${val} pts`;

        updateWeightSumCard();
        debouncedRecalculate();
      });
    }
  });

  // Monsoon Mode Toggle
  const toggleMonsoon = document.getElementById('toggleMonsoonMode');
  const monsoonCard = document.getElementById('monsoonCard');
  const monsoonTag = document.getElementById('monsoonTag');
  const kpiMonsoon = document.getElementById('kpiMonsoonStatus');

  if (toggleMonsoon) {
    toggleMonsoon.addEventListener('change', (e) => {
      state.monsoonMode = e.target.checked;
      if (monsoonCard) monsoonCard.classList.toggle('active', state.monsoonMode);
      if (monsoonTag) monsoonTag.textContent = state.monsoonMode ? 'ACTIVE (1.25x)' : 'INACTIVE';
      if (kpiMonsoon) {
        kpiMonsoon.textContent = state.monsoonMode ? 'ACTIVE' : 'OFF';
        kpiMonsoon.style.color = state.monsoonMode ? '#38bdf8' : 'var(--text-secondary)';
        kpiMonsoon.style.background = state.monsoonMode ? 'rgba(56, 189, 248, 0.2)' : 'rgba(148, 163, 184, 0.15)';
      }
      showToast(state.monsoonMode ? 'Monsoon Mode Active: 1.25x multiplier applied to PE vulnerability' : 'Monsoon Mode Deactivated', 'info');
      debouncedRecalculate(0); // instant
    });
  }

  // Normalization Checkbox
  const chkNormalize = document.getElementById('chkNormalizeTo100');
  if (chkNormalize) {
    chkNormalize.addEventListener('change', (e) => {
      state.normalizeTo100 = e.target.checked;
      debouncedRecalculate(0);
    });
  }

  // Preset Buttons
  const presetButtons = document.querySelectorAll('.btn-preset[data-preset]');
  presetButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      presetButtons.forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      applyPresetWeights(e.target.dataset.preset);
    });
  });

  // Reset Weights Button
  const btnReset = document.getElementById('btnResetWeights');
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      presetButtons.forEach(b => b.classList.remove('active'));
      const defaultBtn = document.getElementById('btnPresetDefault');
      if (defaultBtn) defaultBtn.classList.add('active');
      applyPresetWeights('default');
      showToast('Weights reset to PNGRB standard defaults (100 pts)', 'info');
    });
  }
}

/**
 * Setup Phase 3 48-Hour Dig Prevention Listeners
 */
function setupPhase3DigPreventionListeners() {
  // Header 48h Dig Alerts KPI Pill -> Switch to Dig Panel
  const statDigAlerts = document.getElementById('statDigAlerts');
  if (statDigAlerts) {
    statDigAlerts.style.cursor = 'pointer';
    statDigAlerts.addEventListener('click', () => {
      switchInspectorTab('panelDigNotices');
    });
  }

  // Banner Actions
  const btnBannerViewDig = document.getElementById('btnBannerViewDig');
  if (btnBannerViewDig) {
    btnBannerViewDig.addEventListener('click', () => {
      switchInspectorTab('panelDigNotices');
    });
  }

  const btnBannerDismiss = document.getElementById('btnBannerDismiss');
  if (btnBannerDismiss) {
    btnBannerDismiss.addEventListener('click', () => {
      const banner = document.getElementById('mapAlertBanner');
      if (banner) banner.style.display = 'none';
    });
  }

  // Blueprint Modal Controls
  const btnCloseModal = document.getElementById('btnCloseBlueprintModal');
  const modalBackdrop = document.getElementById('modalSafetyBlueprint');
  if (btnCloseModal) {
    btnCloseModal.addEventListener('click', closeSafetyBlueprintModal);
  }
  if (modalBackdrop) {
    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) closeSafetyBlueprintModal();
    });
  }

  const btnCopyLink = document.getElementById('btnCopyBlueprintLink');
  if (btnCopyLink) {
    btnCopyLink.addEventListener('click', () => {
      const hash = document.getElementById('bpClearanceHash').textContent;
      navigator.clipboard.writeText(`https://methanos.grid/safety-blueprint/${hash}`).then(() => {
        showToast('Safety route map blueprint link copied to clipboard!', 'success');
      }).catch(() => {
        showToast('Blueprint link copied.', 'success');
      });
    });
  }

  const btnDownloadBp = document.getElementById('btnDownloadBlueprint');
  if (btnDownloadBp) {
    btnDownloadBp.addEventListener('click', () => {
      showToast('Digital Pipeline Clearance issued to contractor! Confirmation logged.', 'success');
      closeSafetyBlueprintModal();
    });
  }
}

/**
 * Switch between Inspector Panels (Phase 1, 2, 3, 4)
 */
function switchInspectorTab(targetPanelId) {
  state.activeInspectorTab = targetPanelId;
  const panelDetail = document.getElementById('panelSegmentDetail');
  const panelSliders = document.getElementById('panelWeightSliders');
  const panelDig = document.getElementById('panelDigNotices');
  const panelQC = document.getElementById('panelConfidenceQC');
  const tabDetail = document.getElementById('tabSegmentInspector');
  const tabSliders = document.getElementById('tabWeightCalibrator');
  const tabDig = document.getElementById('tabDigNotices');
  const tabQC = document.getElementById('tabConfidenceQC');
  const btnHeader = document.getElementById('btnToggleCalibrator');

  // Hide all panels
  if (panelDetail) panelDetail.style.display = 'none';
  if (panelSliders) panelSliders.style.display = 'none';
  if (panelDig) panelDig.style.display = 'none';
  if (panelQC) panelQC.style.display = 'none';

  // Deactivate all tabs
  if (tabDetail) tabDetail.classList.remove('active');
  if (tabSliders) tabSliders.classList.remove('active');
  if (tabDig) tabDig.classList.remove('active');
  if (tabQC) tabQC.classList.remove('active');
  if (btnHeader) btnHeader.classList.remove('active');

  // Activate selected panel
  if (targetPanelId === 'panelWeightSliders') {
    if (panelSliders) panelSliders.style.display = 'flex';
    if (tabSliders) tabSliders.classList.add('active');
    if (btnHeader) btnHeader.classList.add('active');
  } else if (targetPanelId === 'panelDigNotices') {
    if (panelDig) panelDig.style.display = 'flex';
    if (tabDig) tabDig.classList.add('active');
  } else if (targetPanelId === 'panelConfidenceQC') {
    if (panelQC) panelQC.style.display = 'flex';
    if (tabQC) tabQC.classList.add('active');
  } else {
    if (panelDetail) panelDetail.style.display = 'block';
    if (tabDetail) tabDetail.classList.add('active');
  }
}

/**
 * Apply Preset Calibration Weights
 */
function applyPresetWeights(presetKey) {
  let presetWeights = {};

  if (presetKey === 'excavation') {
    presetWeights = {
      previous_incidents: 10,
      pe_vulnerability: 10,
      days_since_survey: 10,
      third_party_activity: 45,
      rodent_history: 10,
      public_consequence: 15
    };
    showToast('Applied "Excavation Threat Bias" preset (Dig Activity weight = 45)', 'info');
  } else if (presetKey === 'rodent') {
    presetWeights = {
      previous_incidents: 15,
      pe_vulnerability: 30,
      days_since_survey: 15,
      third_party_activity: 10,
      rodent_history: 20,
      public_consequence: 10
    };
    showToast('Applied "Rodent & PE Aging Bias" preset (PE + Rodent weight = 50)', 'info');
  } else {
    // Default PNGRB baseline
    presetWeights = { ...CONFIG.DEFAULT_WEIGHTS };
  }

  // Update State and Slider DOM
  state.weights = { ...presetWeights };

  const mappings = {
    previous_incidents: { input: 'sliderPreviousIncidents', badge: 'valPreviousIncidents' },
    pe_vulnerability: { input: 'sliderPeVulnerability', badge: 'valPeVulnerability' },
    days_since_survey: { input: 'sliderDaysSinceSurvey', badge: 'valDaysSinceSurvey' },
    third_party_activity: { input: 'sliderThirdPartyActivity', badge: 'valThirdPartyActivity' },
    rodent_history: { input: 'sliderRodentHistory', badge: 'valRodentHistory' },
    public_consequence: { input: 'sliderPublicConsequence', badge: 'valPublicConsequence' }
  };

  Object.entries(mappings).forEach(([key, { input, badge }]) => {
    const val = state.weights[key];
    const inputEl = document.getElementById(input);
    const badgeEl = document.getElementById(badge);
    if (inputEl) inputEl.value = val;
    if (badgeEl) badgeEl.textContent = `${val} pts`;
  });

  updateWeightSumCard();
  debouncedRecalculate(0);
}

/**
 * Update Total Weights Progress Card
 */
function updateWeightSumCard() {
  const sum = Object.values(state.weights).reduce((acc, v) => acc + (parseFloat(v) || 0), 0);
  const sumEl = document.getElementById('currentWeightSum');
  const barEl = document.getElementById('weightSumBarFill');
  const badgeEl = document.getElementById('sliderWeightsSumBadge');

  if (sumEl) sumEl.innerHTML = `${Math.round(sum)} <span class="sum-max">/ 100 pts</span>`;
  if (badgeEl) badgeEl.textContent = `${Math.round(sum)} pts`;

  if (barEl) {
    const pct = Math.min(100, Math.round((sum / 100) * 100));
    barEl.style.width = `${pct}%`;
    if (Math.round(sum) !== 100 && !state.normalizeTo100) {
      barEl.classList.add('sum-warning');
    } else {
      barEl.classList.remove('sum-warning');
    }
  }
}

/**
 * Debounced live network recalculation
 */
function debouncedRecalculate(delay = 120) {
  clearTimeout(state.recalcDebounceTimer);
  state.recalcDebounceTimer = setTimeout(() => {
    recalculateNetwork();
  }, delay);
}

/**
 * Recalculate Network Priority Scores (API with Local Mathematical Fallback)
 */
async function recalculateNetwork() {
  const payload = {
    weights: state.weights,
    normalize_to_100: state.normalizeTo100,
    monsoon_mode: state.monsoonMode
  };

  if (state.isOnlineApi) {
    try {
      const res = await fetch(`${CONFIG.API_BASE}/recalculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      state.segments = data.segments || [];
      onScoresUpdated();
      return;
    } catch (err) {
      console.warn('API recalculate failed, executing local scoring engine:', err);
    }
  }

  // Local Offline Mathematical Scoring Fallback (matches scoring.py exactly)
  state.segments = state.segments.map(seg => {
    const scored = calculatePriorityLocal(seg, state.weights, state.normalizeTo100, state.monsoonMode);
    return { ...seg, ...scored };
  });

  // Sort by score descending
  state.segments.sort((a, b) => b.score - a.score);
  onScoresUpdated();
}

/**
 * Callback after scores have been recalculated
 */
function onScoresUpdated() {
  updateHeaderKPIs();
  renderSegmentList();
  renderMapPipelines();

  // If a segment is currently selected, refresh its details immediately
  if (state.selectedSegmentId) {
    const seg = state.segments.find(s => s.segment_id === state.selectedSegmentId);
    if (seg) populateDetailInspector(seg);
  }
  checkSegmentExcavationAlert();
}

/**
 * Local mathematical implementation of PNGRB 6-factor formula
 * Fully mirrors priority_engine/scoring.py
 */
function calculatePriorityLocal(seg, weights, normalize, monsoon) {
  const prevIncidents = parseInt(seg.previous_incidents || 0);
  const material = (seg.material || 'pe_distribution').toLowerCase();
  const daysSince = parseInt(seg.days_since_survey || 0);
  const targetCycle = parseInt(seg.target_survey_cycle || 12);
  const thirdParty = (seg.third_party_activity || 'none').toLowerCase();
  const rodent = parseInt(seg.rodent_incidents || 0);
  const area = (seg.area_type || 'residential').toLowerCase();

  // 1. Incidents (Max 25)
  let rawIncidents = 0;
  if (prevIncidents === 1) rawIncidents = 10;
  else if (prevIncidents === 2) rawIncidents = 18;
  else if (prevIncidents >= 3) rawIncidents = 25;

  // 2. PE Vulnerability (Max 20)
  let rawPe = 10;
  if (material.includes('steel')) rawPe = 5;
  else if (material.includes('service') || material.includes('hotspot')) rawPe = 20;
  else if (material.includes('pe') || material.includes('dist')) rawPe = 15;

  if (monsoon && (material.includes('pe') || material.includes('service') || material.includes('dist'))) {
    rawPe = Math.min(20, rawPe * 1.25);
  }

  // 3. Days Since Survey (Max 20)
  const rawDays = Math.min(20, Math.max(0, (20.0 * daysSince) / (targetCycle || 12)));

  // 4. Third-Party Dig Activity (Max 15)
  let rawDig = 0;
  if (thirdParty.includes('hazard') || thirdParty.includes('direct')) rawDig = 15;
  else if (thirdParty.includes('active') || thirdParty.includes('supervis')) rawDig = 10;
  else if (thirdParty.includes('notice') || thirdParty.includes('48h')) rawDig = 5;

  // 5. Rodent History (Max 10)
  let rawRodent = 0;
  if (rodent === 1) rawRodent = 3;
  else if (rodent >= 2 && rodent <= 3) rawRodent = 6;
  else if (rodent >= 4) rawRodent = 10;

  // 6. Public Consequence (Max 10)
  let rawPublic = 5;
  if (area.includes('sensitive') || area.includes('school') || area.includes('hospital') || area.includes('market')) rawPublic = 10;
  else if (area.includes('dense')) rawPublic = 7;
  else if (area.includes('residential')) rawPublic = 5;
  else if (area.includes('low')) rawPublic = 2;

  // Scale by weights
  const factorBreakdown = {
    previous_incidents: Math.round(((rawIncidents / 25.0) * (weights.previous_incidents || 25)) * 10) / 10,
    pe_vulnerability: Math.round(((rawPe / 20.0) * (weights.pe_vulnerability || 20)) * 10) / 10,
    days_since_survey: Math.round(((rawDays / 20.0) * (weights.days_since_survey || 20)) * 10) / 10,
    third_party_activity: Math.round(((rawDig / 15.0) * (weights.third_party_activity || 15)) * 10) / 10,
    rodent_history: Math.round(((rawRodent / 10.0) * (weights.rodent_history || 10)) * 10) / 10,
    public_consequence: Math.round(((rawPublic / 10.0) * (weights.public_consequence || 10)) * 10) / 10,
  };

  let totalScore = Object.values(factorBreakdown).reduce((a, b) => a + b, 0);
  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);

  if (normalize && totalWeight > 0 && totalWeight !== 100) {
    totalScore = (totalScore / totalWeight) * 100.0;
  }

  let finalScore = Math.max(0, Math.min(100, Math.round(totalScore)));

  // Emergency incident override
  if (seg.emergency_incident_active) {
    finalScore = 100;
  }

  let tier = 'LOW';
  if (finalScore >= 85) tier = 'CRITICAL';
  else if (finalScore >= 70) tier = 'HIGH';
  else if (finalScore >= 40) tier = 'MEDIUM';

  return {
    score: finalScore,
    tier: tier,
    factors: factorBreakdown
  };
}

/**
 * Load Pipeline Segment Data (API with Fallback to Static JSON)
 */
async function loadSegmentData() {
  const statusChip = document.getElementById('systemStatusChip');
  const statusText = document.getElementById('statusConnectionText');

  try {
    // Try FastAPI Backend first
    const res = await fetch(`${CONFIG.API_BASE}/segments`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.segments = data.segments || [];
    state.isOnlineApi = true;

    if (statusChip && statusText) {
      statusChip.style.background = 'rgba(16, 185, 129, 0.12)';
      statusChip.style.borderColor = 'rgba(16, 185, 129, 0.3)';
      statusText.textContent = 'API CONNECTED';
      statusText.style.color = '#34d399';
    }
  } catch (err) {
    console.warn('FastAPI backend not reachable, switching to static JSON fallback:', err);
    try {
      const fallbackRes = await fetch(CONFIG.FALLBACK_JSON);
      if (!fallbackRes.ok) throw new Error(`Fallback HTTP ${fallbackRes.status}`);
      const fallbackData = await fallbackRes.json();
      state.segments = fallbackData.segments || [];
      state.isOnlineApi = false;

      if (statusChip && statusText) {
        statusChip.style.background = 'rgba(234, 179, 8, 0.12)';
        statusChip.style.borderColor = 'rgba(234, 179, 8, 0.3)';
        statusText.textContent = 'OFFLINE (STATIC JSON)';
        statusText.style.color = '#facc15';
      }
    } catch (fallbackErr) {
      console.error('Failed to load segment data from both sources:', fallbackErr);
      showToast('Error loading pipeline segment data.', 'critical');
      return;
    }
  }

  updateHeaderKPIs();
  updateWeightSumCard();
  renderSegmentList();
  renderMapPipelines();

  // Load Phase 3 Dig Notices
  loadDigNotices();

  // Auto-select P-104 benchmark for immediate demo inspection
  if (state.segments.some(s => s.segment_id === 'P-104')) {
    selectSegment('P-104', false);
  } else if (state.segments.length > 0) {
    selectSegment(state.segments[0].segment_id, false);
  }
}

/**
 * Phase 3: Load Dig Notices & Excavation Tickets
 */
async function loadDigNotices() {
  try {
    const res = await fetch(`${CONFIG.API_BASE}/dig-notices`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.digNotices = data.notices || [];
  } catch (err) {
    console.warn('Dig notices API unreachable, loading fallback JSON:', err);
    try {
      const fb = await fetch(CONFIG.FALLBACK_DIG_NOTICES_JSON);
      if (!fb.ok) throw new Error(`Fallback HTTP ${fb.status}`);
      const fbData = await fb.json();
      state.digNotices = fbData.notices || [];
    } catch (fbErr) {
      console.error('Failed to load dig notices:', fbErr);
    }
  }

  updateDigKPIs();
  renderDigNoticesFeed();
  checkSegmentExcavationAlert();
}

/**
 * Phase 3: Update Dig KPIs in header and tab badges
 */
function updateDigKPIs() {
  const kpiAlerts = document.getElementById('kpiDigAlerts');
  const tabBadge = document.getElementById('tabDigAlertsBadge');
  const kpiTotal = document.getElementById('digKpiTotal');
  const kpiCompliant = document.getElementById('digKpiCompliant');
  const kpiViolation = document.getElementById('digKpiViolation');

  const total = state.digNotices.length;
  const compliant = state.digNotices.filter(n => n.is_compliant_48h).length;
  const violations = state.digNotices.filter(n => !n.is_compliant_48h).length;

  if (kpiAlerts) kpiAlerts.textContent = total;
  if (tabBadge) tabBadge.textContent = total;
  if (kpiTotal) kpiTotal.textContent = total;
  if (kpiCompliant) kpiCompliant.textContent = compliant;
  if (kpiViolation) kpiViolation.textContent = violations;
}

/**
 * Phase 3: Render Dig Tickets in 48-Hour Excavation Feed
 */
function renderDigNoticesFeed() {
  const container = document.getElementById('digTicketsContainer');
  if (!container) return;

  if (state.digNotices.length === 0) {
    container.innerHTML = `
      <div style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 0.8rem;">
        No active excavation notices reported.
      </div>
    `;
    return;
  }

  container.innerHTML = state.digNotices.map(notice => {
    const isViolation = !notice.is_compliant_48h;
    const cardClass = isViolation ? 'ticket-violation' : 'ticket-compliant';
    
    let statusPillClass = 'pill-dispatched';
    if (notice.status === 'SHORT_NOTICE_VIOLATION') statusPillClass = 'pill-violation';
    else if (notice.status === 'ACTIVE_SUPERVISED') statusPillClass = 'pill-active';
    else if (notice.status === 'COMPLETED_ZERO_LEAK') statusPillClass = 'pill-completed';

    const advanceBadgeText = isViolation
      ? `🚨 ${notice.notice_advance_hours.toFixed(1)}h Advance (SHORT-NOTICE VIOLATION)`
      : `✅ ${notice.notice_advance_hours.toFixed(1)}h Advance (COMPLIANT ≥48H)`;

    const depthClashText = notice.depth_clash_hazard
      ? `<span class="val-danger">CLASH HAZARD (${notice.dig_depth_meters}m dig > ${notice.pipeline_depth_meters}m pipe)</span>`
      : `<span class="val-safe">CLEAR DEPTH (${notice.dig_depth_meters}m dig &lt; ${notice.pipeline_depth_meters}m pipe)</span>`;

    const officerText = notice.assigned_monitor
      ? `<span class="officer-name">👤 ${notice.assigned_monitor}</span>`
      : `<span style="color: #f87171;">⚠️ Unassigned</span>`;

    return `
      <div class="dig-ticket-card ${cardClass}" id="cardNotice_${notice.notice_id}">
        <div class="ticket-header-row">
          <div class="ticket-id-wrap">
            <span class="ticket-id">${notice.notice_id}</span>
            <span class="ticket-segment-badge" title="Click to focus pipeline" onclick="selectSegment('${notice.segment_id}', true)">${notice.segment_id}</span>
          </div>
          <span class="ticket-status-pill ${statusPillClass}">${(notice.status || '').replace(/_/g, ' ')}</span>
        </div>

        <div class="ticket-contractor">
          <span>${notice.contractor_name}</span>
        </div>

        <div style="font-size: 0.7rem; font-family: var(--font-mono); color: ${isViolation ? '#f87171' : '#34d399'};">
          ${advanceBadgeText}
        </div>

        <!-- Conflict Analysis Box -->
        <div class="ticket-conflict-box">
          <div class="conflict-row">
            <span class="conflict-label">Depth Conflict:</span>
            <span class="conflict-val">${depthClashText}</span>
          </div>
          <div class="conflict-row">
            <span class="conflict-label">Proximity Buffer:</span>
            <span class="conflict-val">${notice.proximity_buffer_m || 8.5} m from gas line</span>
          </div>
        </div>

        <div class="ticket-officer-row">
          <span>Field Monitor:</span>
          ${officerText}
        </div>

        <!-- Action Center Buttons -->
        <div class="ticket-actions-grid">
          <button class="btn-ticket-act btn-act-dispatch" onclick="handleDispatchMonitorAction('${notice.notice_id}')">
            <span>Dispatch Monitor</span>
          </button>
          <button class="btn-ticket-act btn-act-map" onclick="openSafetyBlueprintModal('${notice.notice_id}')">
            <span>Safety Blueprint</span>
          </button>
          ${notice.status !== 'ACTIVE_SUPERVISED' && notice.status !== 'COMPLETED_ZERO_LEAK' ? `
            <button class="btn-ticket-act btn-act-start" onclick="handleStartDigAction('${notice.notice_id}')">
              <span>Start Supervised Dig</span>
            </button>
          ` : ''}
          ${notice.status === 'ACTIVE_SUPERVISED' ? `
            <button class="btn-ticket-act btn-act-complete" onclick="handleCompleteDigAction('${notice.notice_id}')">
              <span>Complete Dig (Zero-Leak)</span>
            </button>
          ` : ''}
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Phase 3: Check and Display Floating Excavation Alert Banner
 */
function checkSegmentExcavationAlert() {
  const banner = document.getElementById('mapAlertBanner');
  if (!banner) return;

  const currentSegId = state.selectedSegmentId || 'P-104';
  const notice = state.digNotices.find(n => n.segment_id === currentSegId);

  if (notice && notice.status !== 'COMPLETED_ZERO_LEAK') {
    const isViolation = !notice.is_compliant_48h;
    const headline = document.getElementById('alertBannerHeadline');
    const sub = document.getElementById('alertBannerSub');

    if (headline) {
      headline.textContent = isViolation
        ? `🚨 UNAUTHORIZED SHORT-NOTICE EXCAVATION (${notice.notice_id})`
        : `⚠️ 48-HR PRE-EXCAVATION ACTIVE: ${notice.notice_id} on ${notice.segment_id}`;
    }
    if (sub) {
      sub.textContent = `${notice.contractor_name} trenching ${notice.dig_depth_meters}m deep. Depth clash: ${notice.depth_clash_hazard ? 'YES (EXCEEDS BURIAL DEPTH)' : 'NO'}.`;
    }
    banner.style.display = 'flex';
  } else {
    // Check if any short-notice violation exists across the entire network
    const violationNotice = state.digNotices.find(n => !n.is_compliant_48h);
    if (violationNotice) {
      const headline = document.getElementById('alertBannerHeadline');
      const sub = document.getElementById('alertBannerSub');
      if (headline) headline.textContent = `🚨 SHORT-NOTICE EXCAVATION VIOLATION (${violationNotice.notice_id})`;
      if (sub) sub.textContent = `${violationNotice.contractor_name} near ${violationNotice.segment_id} filed with only ${violationNotice.notice_advance_hours}h notice. Stop-work dispatched.`;
      banner.style.display = 'flex';
    } else {
      banner.style.display = 'none';
    }
  }
}

/**
 * Phase 3: Action 1 - Dispatch On-Site Monitor
 */
window.handleDispatchMonitorAction = async function(noticeId) {
  showToast(`Dispatching utility patrol officer to supervise ${noticeId}...`, 'info');

  const officerName = "Patrol Officer R. Sharma";

  if (state.isOnlineApi) {
    try {
      const res = await fetch(`${CONFIG.API_BASE}/dig-notices/${noticeId}/dispatch-monitor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ monitor_name: officerName })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const result = await res.json();
      showToast(`Patrol Officer R. Sharma dispatched to supervise ${noticeId}! Segment status updated.`, 'success');
      loadDigNotices();
      recalculateNetwork();
      return;
    } catch (err) {
      console.warn('API dispatch failed, falling back to local state:', err);
    }
  }

  // Local Offline Fallback
  const notice = state.digNotices.find(n => n.notice_id === noticeId);
  if (notice) {
    notice.status = 'MONITOR_DISPATCHED';
    notice.assigned_monitor = officerName;

    // Update segment in priority engine
    const seg = state.segments.find(s => s.segment_id === notice.segment_id);
    if (seg) {
      seg.third_party_activity = 'planned_48h_notice';
      if (seg.factors) seg.factors.third_party_activity = 5.0;
    }

    showToast(`Patrol Officer R. Sharma dispatched for ${noticeId}!`, 'success');
    updateDigKPIs();
    renderDigNoticesFeed();
    recalculateNetwork();
  }
};

/**
 * Phase 3: Action 2 - Open Safety Blueprint Modal & Issue Clearance
 */
window.openSafetyBlueprintModal = function(noticeId) {
  const notice = state.digNotices.find(n => n.notice_id === noticeId) || state.digNotices[0];
  if (!notice) return;

  const modal = document.getElementById('modalSafetyBlueprint');
  if (!modal) return;

  // Populate Blueprint Data
  document.getElementById('blueprintNoticeId').textContent = notice.notice_id;
  document.getElementById('bpContractorName').textContent = notice.contractor_name;
  document.getElementById('bpSegmentId').textContent = `${notice.segment_id} (${notice.notes || 'CGD Distribution Line'})`;
  document.getElementById('bpProximityBuffer').textContent = `${notice.proximity_buffer_m || 50.0} m Exclusion Buffer`;
  document.getElementById('bpAssignedMonitor').textContent = notice.assigned_monitor || 'Patrol Officer R. Sharma (Dispatched)';

  // Cross section values
  document.getElementById('bpPipeDepthVal').textContent = `${notice.pipeline_depth_meters || 0.8} m`;
  document.getElementById('bpDigDepthVal').textContent = `${notice.dig_depth_meters} m`;

  const clashTag = document.getElementById('bpClashTag');
  if (clashTag) {
    clashTag.textContent = notice.depth_clash_hazard ? 'DEPTH CLASH HAZARD DETECTED' : 'CLEAR DEPTH PROFILE';
    clashTag.style.color = notice.depth_clash_hazard ? '#f87171' : '#34d399';
    clashTag.style.background = notice.depth_clash_hazard ? 'rgba(239, 68, 68, 0.18)' : 'rgba(16, 185, 129, 0.18)';
  }

  // Adjust indicator positions
  const pipePos = Math.min(80, Math.round(((notice.pipeline_depth_meters || 0.8) / 3.0) * 100));
  const digPos = Math.min(90, Math.round((notice.dig_depth_meters / 3.0) * 100));

  const pipeInd = document.getElementById('bpPipeDepthIndicator');
  const digInd = document.getElementById('bpDigDepthIndicator');
  if (pipeInd) pipeInd.style.top = `${pipePos}%`;
  if (digInd) digInd.style.top = `${digPos}%`;

  document.getElementById('bpClearanceHash').textContent = `METHANOS-CLR-${notice.notice_id.replace('DIG-', '')}-DELHI-2026`;
  document.getElementById('bpCertStatus').textContent = notice.is_compliant_48h ? 'MONITORED CLEARANCE ISSUED' : 'EMERGENCY STOP-WORK CLEARANCE';

  modal.style.display = 'flex';

  // Mark as shared on backend
  if (state.isOnlineApi) {
    fetch(`${CONFIG.API_BASE}/dig-notices/${noticeId}/share-map`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contractor_email: 'contractor@infrastructure.in' })
    }).catch(e => console.warn(e));
  } else {
    notice.safety_map_shared = true;
  }
};

function closeSafetyBlueprintModal() {
  const modal = document.getElementById('modalSafetyBlueprint');
  if (modal) modal.style.display = 'none';
}

/**
 * Phase 3: Action 3 - Start Supervised Dig
 */
window.handleStartDigAction = async function(noticeId) {
  showToast(`Transitioning ${noticeId} to ACTIVE_SUPERVISED dig status...`, 'info');

  if (state.isOnlineApi) {
    try {
      await fetch(`${CONFIG.API_BASE}/dig-notices/${noticeId}/start-dig`, { method: 'POST' });
      showToast(`Excavation at ${noticeId} is now under active field supervision!`, 'success');
      loadDigNotices();
      recalculateNetwork();
      return;
    } catch (e) {
      console.warn(e);
    }
  }

  // Offline fallback
  const notice = state.digNotices.find(n => n.notice_id === noticeId);
  if (notice) {
    notice.status = 'ACTIVE_SUPERVISED';
    const seg = state.segments.find(s => s.segment_id === notice.segment_id);
    if (seg) seg.third_party_activity = 'active_supervised';
    renderDigNoticesFeed();
    recalculateNetwork();
  }
};

/**
 * Phase 3: Action 4 - Complete Dig (Zero-Leak)
 */
window.handleCompleteDigAction = async function(noticeId) {
  showToast(`Closing excavation notice ${noticeId} with Zero-Leak clearance...`, 'info');

  if (state.isOnlineApi) {
    try {
      await fetch(`${CONFIG.API_BASE}/dig-notices/${noticeId}/complete`, { method: 'POST' });
      showToast(`Dig completed safely with ZERO methane leaks! Hazard cleared.`, 'success');
      loadDigNotices();
      recalculateNetwork();
      return;
    } catch (e) {
      console.warn(e);
    }
  }

  // Offline fallback
  const notice = state.digNotices.find(n => n.notice_id === noticeId);
  if (notice) {
    notice.status = 'COMPLETED_ZERO_LEAK';
    const seg = state.segments.find(s => s.segment_id === notice.segment_id);
    if (seg) seg.third_party_activity = 'none';
    renderDigNoticesFeed();
    recalculateNetwork();
  }
};

/**
 * Update Header KPI Badges
 */
function updateHeaderKPIs() {
  const totalEl = document.getElementById('kpiTotalSegments');
  const critEl = document.getElementById('kpiCriticalCount');
  const badgeCount = document.getElementById('segmentCountBadge');

  if (totalEl) totalEl.textContent = state.segments.length;
  if (badgeCount) badgeCount.textContent = state.segments.length;

  const criticals = state.segments.filter(s => s.tier === 'CRITICAL').length;
  if (critEl) critEl.textContent = criticals;

  // Update Tab count labels
  const critTab = document.getElementById('filterTabCritical');
  const highTab = document.getElementById('filterTabHigh');
  const medTab = document.getElementById('filterTabMedium');
  const lowTab = document.getElementById('filterTabLow');

  const crits = state.segments.filter(s => s.tier === 'CRITICAL').length;
  const highs = state.segments.filter(s => s.tier === 'HIGH').length;
  const meds = state.segments.filter(s => s.tier === 'MEDIUM').length;
  const lows = state.segments.filter(s => s.tier === 'LOW').length;

  if (critTab) critTab.textContent = `CRITICAL (${crits})`;
  if (highTab) highTab.textContent = `HIGH (${highs})`;
  if (medTab) medTab.textContent = `MED (${meds})`;
  if (lowTab) lowTab.textContent = `LOW (${lows})`;
}

/**
 * Render Left Sidebar Segment Cards
 */
function renderSegmentList() {
  const container = document.getElementById('segmentListContainer');
  if (!container) return;

  const filtered = state.segments.filter(seg => {
    // Tier filter
    if (state.activeTierFilter !== 'ALL' && seg.tier !== state.activeTierFilter) {
      return false;
    }
    // Search query filter
    if (state.searchQuery) {
      const matchId = seg.segment_id.toLowerCase().includes(state.searchQuery);
      const matchName = (seg.name || '').toLowerCase().includes(state.searchQuery);
      const matchMat = (seg.material || '').toLowerCase().includes(state.searchQuery);
      return matchId || matchName || matchMat;
    }
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 0.8rem;">
        No segments match the selected criteria.
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(seg => {
    const isSelected = seg.segment_id === state.selectedSegmentId ? 'selected' : '';
    const tierClass = `tier-${seg.tier.toLowerCase()}`;
    const tierBadgeClass = `tier-badge-${seg.tier.toLowerCase()}`;
    const materialFormatted = formatMaterialName(seg.material);

    return `
      <div class="segment-card-item ${tierClass} ${isSelected}" data-id="${seg.segment_id}">
        <div class="card-item-header">
          <span class="card-item-id">${seg.segment_id}</span>
          <span class="card-item-tier ${tierBadgeClass}">${seg.tier}</span>
        </div>
        <div class="card-item-name" title="${seg.name || seg.segment_id}">${seg.name || 'CGD Distribution Segment'}</div>
        <div class="card-item-meta">
          <span class="card-item-material">${materialFormatted} • ${seg.depth_meters}m</span>
          <span class="card-item-score">${seg.score}<span style="font-size: 0.65rem; color: var(--text-muted);">/100</span></span>
        </div>
      </div>
    `;
  }).join('');

  // Attach card click handlers
  container.querySelectorAll('.segment-card-item').forEach(card => {
    card.addEventListener('click', () => {
      const segId = card.dataset.id;
      selectSegment(segId, true);
    });
  });
}

/**
 * Render Pipeline Polylines and Markers on Leaflet Map
 */
function renderMapPipelines() {
  if (!state.map) return;

  // Clear previous layers
  Object.values(state.mapLayers.polylines).forEach(layer => state.map.removeLayer(layer));
  Object.values(state.mapLayers.markers).forEach(layer => state.map.removeLayer(layer));
  state.mapLayers.polylines = {};
  state.mapLayers.markers = {};

  state.segments.forEach(seg => {
    const color = CONFIG.TIER_COLORS[seg.tier] || '#3b82f6';
    const coords = seg.polyline || (seg.location ? [[seg.location.lat, seg.location.lng]] : []);

    // Draw Pipeline Polyline
    if (coords.length > 1) {
      const isSelected = seg.segment_id === state.selectedSegmentId;
      const polyline = L.polyline(coords, {
        color: color,
        weight: isSelected ? 7 : 4,
        opacity: isSelected ? 1 : 0.85,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(state.map);

      polyline.on('click', () => selectSegment(seg.segment_id, false));
      polyline.bindTooltip(`<strong>${seg.segment_id}</strong> (${seg.tier})<br>Score: ${seg.score}/100`, {
        className: 'pipeline-tooltip',
        direction: 'top'
      });

      state.mapLayers.polylines[seg.segment_id] = polyline;
    }

    // Add Central Pin Marker
    const centerPoint = seg.location ? [seg.location.lat, seg.location.lng] : coords[0];
    if (centerPoint) {
      const pinHtml = `
        <div class="pipeline-pin pin-${seg.tier.toLowerCase()}" title="${seg.segment_id}">
          ${seg.segment_id.replace('P-', '')}
        </div>
      `;
      const customIcon = L.divIcon({
        className: 'custom-pipeline-marker',
        html: pinHtml,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      const marker = L.marker(centerPoint, { icon: customIcon }).addTo(state.map);
      marker.on('click', () => selectSegment(seg.segment_id, true));

      state.mapLayers.markers[seg.segment_id] = marker;
    }
  });
}

/**
 * Fit Map bounds to show all pipeline segments
 */
function fitMapToAllSegments() {
  if (!state.map) return;
  const allCoords = [];
  state.segments.forEach(s => {
    if (s.polyline) {
      s.polyline.forEach(pt => allCoords.push(pt));
    } else if (s.location) {
      allCoords.push([s.location.lat, s.location.lng]);
    }
  });

  if (allCoords.length > 0) {
    state.map.fitBounds(allCoords, { padding: [50, 50] });
  }
}

/**
 * Select and Inspect a Specific Pipeline Segment
 */
function selectSegment(segmentId, panTo = true) {
  state.selectedSegmentId = segmentId;
  const seg = state.segments.find(s => s.segment_id === segmentId);
  if (!seg) return;

  // Highlight active card in sidebar
  document.querySelectorAll('.segment-card-item').forEach(card => {
    if (card.dataset.id === segmentId) {
      card.classList.add('selected');
      card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
      card.classList.remove('selected');
    }
  });

  // Pan and pulse on map
  if (panTo && state.map && seg.location) {
    state.map.flyTo([seg.location.lat, seg.location.lng], 13.5, {
      duration: 0.8
    });
  }

  // Highlight polyline on map
  Object.entries(state.mapLayers.polylines).forEach(([id, layer]) => {
    if (id === segmentId) {
      layer.setStyle({ weight: 7, opacity: 1 });
    } else {
      layer.setStyle({ weight: 4, opacity: 0.6 });
    }
  });

  // Populate Right Detail Inspector
  populateDetailInspector(seg);
  checkSegmentExcavationAlert();
}

/**
 * Populate Inspector Panel with Segment Data and 6-Factor Breakdown
 */
function populateDetailInspector(seg) {
  const emptyState = document.getElementById('inspectorEmptyState');
  const content = document.getElementById('inspectorContent');
  if (emptyState) emptyState.style.display = 'none';
  if (content) content.style.display = 'flex';

  // Basic Header info
  document.getElementById('detailSegmentId').textContent = seg.segment_id;
  document.getElementById('detailName').textContent = seg.name || 'CGD Distribution Segment';
  document.getElementById('detailAreaType').textContent = seg.area_type || 'standard_zone';

  // Tier Badge
  const tierPill = document.getElementById('detailTierPill');
  tierPill.textContent = seg.tier;
  tierPill.className = `tier-pill tier-pill-${seg.tier.toLowerCase()}`;

  // Gauge & Total Score
  document.getElementById('detailScoreNumber').textContent = seg.score;
  const gaugeCircle = document.getElementById('gaugeProgressCircle');
  if (gaugeCircle) {
    // Circumference = 2 * PI * 42 ≈ 263.89
    const maxCircumference = 264;
    const progressOffset = maxCircumference - (seg.score / 100) * maxCircumference;
    gaugeCircle.style.strokeDashoffset = progressOffset;
    gaugeCircle.className = `fg fg-${seg.tier.toLowerCase()}`;
  }

  // GIS Metadata Cards
  document.getElementById('detailDepth').textContent = `${seg.depth_meters} m`;
  const depthTag = document.getElementById('detailDepthTag');
  if (seg.depth_meters < 1.0) {
    depthTag.textContent = 'Shallow Burial Risk (<1.0m)';
    depthTag.className = 'gis-tag tag-shallow';
  } else {
    depthTag.textContent = 'Compliant Burial Depth';
    depthTag.className = 'gis-tag';
  }

  document.getElementById('detailPressure').textContent = `${seg.operating_pressure_bar.toFixed(2)} bar`;
  const pressureTag = document.getElementById('detailPressureTag');
  if (seg.operating_pressure_bar > 10.0) {
    pressureTag.textContent = 'Steel High Pressure Grid';
  } else if (seg.operating_pressure_bar > 1.0) {
    pressureTag.textContent = 'PE Medium Pressure Line';
  } else {
    pressureTag.textContent = 'PE Low Pressure Service Line';
  }

  document.getElementById('detailMaterial').textContent = formatMaterialName(seg.material);
  const materialTag = document.getElementById('detailMaterialTag');
  if (seg.material === 'pe_service_hotspot') {
    materialTag.textContent = 'High Rat & Wear Risk';
    materialTag.className = 'gis-tag tag-vuln';
  } else {
    materialTag.textContent = 'Standard Material Class';
    materialTag.className = 'gis-tag';
  }

  const excVal = (seg.third_party_activity || 'none').replace(/_/g, ' ');
  document.getElementById('detailExcavation').textContent = excVal;
  const excTag = document.getElementById('detailExcavationTag');
  if (seg.third_party_activity === 'direct_excavation_hazard') {
    excTag.textContent = 'Direct Strike Hazard!';
    excTag.className = 'gis-tag tag-alert';
  } else if (seg.third_party_activity === 'planned_48h_notice') {
    excTag.textContent = '48H Notice Active';
    excTag.className = 'gis-tag tag-alert';
  } else if (seg.third_party_activity === 'active_supervised') {
    excTag.textContent = 'Monitor On-Site';
    excTag.className = 'gis-tag';
  } else {
    excTag.textContent = 'Zero Dig Activity';
    excTag.className = 'gis-tag';
  }

  // 6-Factor Breakdown
  const f = seg.factors || {};
  const w = state.weights;
  updateFactorRow('Incidents', f.previous_incidents || 0, w.previous_incidents || 25, `${seg.previous_incidents || 0} historical incident(s)`);
  updateFactorRow('Vuln', f.pe_vulnerability || 0, w.pe_vulnerability || 20, `${formatMaterialName(seg.material)} vulnerability profile`);
  updateFactorRow('Days', f.days_since_survey || 0, w.days_since_survey || 20, `${seg.days_since_survey || 0} days since survey (target ${seg.target_survey_cycle || 12}d)`);
  updateFactorRow('Dig', f.third_party_activity || 0, w.third_party_activity || 15, `Dig status: ${excVal}`);
  updateFactorRow('Rodent', f.rodent_history || 0, w.rodent_history || 10, `${seg.rodent_incidents || 0} past rodent bite incident(s)`);
  updateFactorRow('Public', f.public_consequence || 0, w.public_consequence || 10, `${(seg.area_type || '').replace(/_/g, ' ')} density area`);
}

function updateFactorRow(suffix, pts, maxPts, desc) {
  const ptsEl = document.getElementById(`fPts${suffix}`);
  const barEl = document.getElementById(`fBar${suffix}`);
  const descEl = document.getElementById(`fDesc${suffix}`);

  if (ptsEl) ptsEl.textContent = pts;
  if (barEl) {
    const pct = Math.min(100, Math.round(((parseFloat(pts) || 0) / (parseFloat(maxPts) || 1)) * 100));
    barEl.style.width = `${pct}%`;
  }
  if (descEl) descEl.textContent = desc;
}

/**
 * Handle Closed-Loop Repair Action
 */
async function handleRepairAction(segmentId) {
  showToast(`Submitting repair completion for ${segmentId}...`, 'info');

  if (state.isOnlineApi) {
    try {
      const res = await fetch(`${CONFIG.API_BASE}/segments/${segmentId}/repair`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clear_hazard: true })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const updated = await res.json();
      showToast(`Repair logged for ${segmentId}! Score updated to ${updated.new_score} (${updated.new_tier})`, 'success');
      loadSegmentData();
      return;
    } catch (err) {
      console.warn('API repair call failed, falling back to local state:', err);
    }
  }

  // Local fallback update
  const seg = state.segments.find(s => s.segment_id === segmentId);
  if (seg) {
    seg.previous_incidents = (seg.previous_incidents || 0) + 1;
    seg.days_since_survey = 0;
    seg.third_party_activity = 'none';
    const scored = calculatePriorityLocal(seg, state.weights, state.normalizeTo100, state.monsoonMode);
    Object.assign(seg, scored);

    showToast(`Offline simulation: Repair logged for ${segmentId}! New score: ${seg.score}`, 'success');
    renderSegmentList();
    renderMapPipelines();
    selectSegment(segmentId, false);
  }
}

/**
 * Utility: Format Material Strings
 */
function formatMaterialName(mat) {
  if (!mat) return 'Unknown';
  if (mat === 'pe_service_hotspot') return 'PE Service Hotspot';
  if (mat === 'pe_distribution') return 'PE Distribution';
  if (mat === 'steel_main') return 'Steel Main Grid';
  return mat.replace(/_/g, ' ');
}

/**
 * Toast Notification Utility
 */
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/* ==========================================================================
   PHASE 4: SURVEY CONFIDENCE QC ENGINE & EMERGENCY BREACH ESCALATION
   ========================================================================== */

/**
 * Setup Phase 4 Event Listeners
 */
function setupPhase4ConfidenceListeners() {
  // Tab click for Survey QC
  const tabQC = document.getElementById('tabConfidenceQC');
  if (tabQC) {
    tabQC.addEventListener('click', () => {
      switchInspectorTab('panelConfidenceQC');
    });
  }

  // Example Toggle Buttons (High vs Low)
  const btnHigh = document.getElementById('btnQCHighExample');
  const btnLow = document.getElementById('btnQCLowExample');

  if (btnHigh && btnLow) {
    btnHigh.addEventListener('click', () => {
      btnHigh.classList.add('active');
      btnLow.classList.remove('active');
      state.activeQCKey = 'high';
      renderConfidenceCard('high');
    });

    btnLow.addEventListener('click', () => {
      btnLow.classList.add('active');
      btnHigh.classList.remove('active');
      state.activeQCKey = 'low';
      renderConfidenceCard('low');
    });
  }

  // Emergency Incident Modal Triggers
  const btnOpenModal = document.getElementById('btnOpenEmergencyModal');
  const btnReportDirect = document.getElementById('btnReportIncidentDirect');
  const btnCloseModal = document.getElementById('btnCloseEmergencyModal');
  const btnCancel = document.getElementById('btnCancelEmergency');
  const btnSubmit = document.getElementById('btnSubmitEmergencyIncident');

  if (btnOpenModal) {
    btnOpenModal.addEventListener('click', () => openEmergencyModal());
  }

  if (btnReportDirect) {
    btnReportDirect.addEventListener('click', () => {
      openEmergencyModal(state.selectedSegmentId);
    });
  }

  if (btnCloseModal) {
    btnCloseModal.addEventListener('click', closeEmergencyModal);
  }

  if (btnCancel) {
    btnCancel.addEventListener('click', closeEmergencyModal);
  }

  if (btnSubmit) {
    btnSubmit.addEventListener('click', handleEmergencyIncidentSubmit);
  }
}

/**
 * Load Survey Confidence Benchmark Data
 */
async function loadConfidenceData() {
  // Try Live API first
  try {
    const res = await fetch(`${CONFIG.API_BASE}/confidence/examples`);
    if (res.ok) {
      const data = await res.json();
      state.confidenceBenchmarks = data;
      renderConfidenceCard(state.activeQCKey || 'high');
      return;
    }
  } catch (e) {
    // ignore and fallback
  }

  // Fallback to static surveys.json
  try {
    const res = await fetch('surveys.json');
    if (res.ok) {
      const data = await res.json();
      state.confidenceBenchmarks = data.benchmarks || data;
      renderConfidenceCard(state.activeQCKey || 'high');
      return;
    }
  } catch (err) {
    console.warn('Failed to load surveys.json, using built-in defaults:', err);
  }

  // Hardcoded built-in fallback
  state.confidenceBenchmarks = {
    high_confidence_example: {
      survey_id: "S-2101",
      segment_id: "P-104",
      surveyor_team: "Team Alpha (Mobile Van #1)",
      gps_coverage: true,
      gps_fix_pct: 99.2,
      sensor_health: true,
      sensor_health_status: "calibrated",
      speed_ok: true,
      vehicle_speed_kmh: 16.5,
      weather_ok: true,
      wind_speed_kmh: 6.2,
      route_complete: true,
      route_completeness_pct: 98.5,
      ch4_reading_ppm: 14.6,
      confidence_score: 100,
      decision: "ACCEPT",
      action_recommendation: "DISPATCH_FIELD_VERIFICATION",
      notes: "Strong elevated CH4 localized near valve pit on PE service line hotspot."
    },
    low_confidence_example: {
      survey_id: "S-2201",
      segment_id: "P-118",
      surveyor_team: "Team Beta (Mobile Van #2)",
      gps_coverage: true,
      gps_fix_pct: 96.0,
      sensor_health: true,
      sensor_health_status: "ok",
      speed_ok: false,
      vehicle_speed_kmh: 36.8,
      weather_ok: false,
      wind_speed_kmh: 26.5,
      route_complete: true,
      route_completeness_pct: 94.0,
      ch4_reading_ppm: 8.4,
      confidence_score: 43,
      decision: "RE-SURVEY",
      action_recommendation: "FLAGGED_FOR_RESURVEY",
      notes: "Elevated CH4 flagged but vehicle speed was 36.8 km/h (>25 km/h limit) with 26.5 km/h gusts (>15 km/h limit); plume dispersed. Corrupted sample rejected."
    }
  };
  renderConfidenceCard(state.activeQCKey || 'high');
}

/**
 * Render Confidence QC Card (High vs Low Example)
 */
function renderConfidenceCard(exampleKey) {
  const container = document.getElementById('qcCardContainer');
  if (!container || !state.confidenceBenchmarks) return;

  const b = exampleKey === 'high'
    ? (state.confidenceBenchmarks.high_confidence_example || state.confidenceBenchmarks.high)
    : (state.confidenceBenchmarks.low_confidence_example || state.confidenceBenchmarks.low);

  if (!b) return;

  const isPass = b.decision === 'ACCEPT';
  const cardClass = isPass ? 'card-pass' : 'card-fail';
  const decisionClass = isPass ? 'decision-accept' : 'decision-resurvey';
  const scoreClass = isPass ? 'text-pass' : 'text-fail';
  const decisionIcon = isPass ? '✓' : '⚠️';

  // 5 Quality Control Gate evaluations
  const gates = [
    {
      name: '1. GPS RTK Fix Accuracy',
      val: `${b.gps_fix_pct || 99.0}% lock`,
      ok: b.gps_coverage !== false,
      score: isPass ? 20 : 18,
      note: b.gps_coverage !== false ? 'Sub-meter carrier phase lock verified' : 'GPS lock degraded'
    },
    {
      name: '2. Optical Laser Sensor Health',
      val: (b.sensor_health_status || 'calibrated').toUpperCase(),
      ok: b.sensor_health !== false,
      score: 20,
      note: 'Zero-gas baseline drift < 0.05 ppm, cell temp calibrated'
    },
    {
      name: '3. Vehicle Survey Speed (Max 25 km/h)',
      val: `${b.vehicle_speed_kmh} km/h`,
      ok: b.speed_ok !== false && b.vehicle_speed_kmh <= 25.0,
      score: (b.speed_ok !== false && b.vehicle_speed_kmh <= 25.0) ? 20 : 0,
      note: (b.speed_ok !== false && b.vehicle_speed_kmh <= 25.0)
        ? 'Within optimal sniffing envelope (15-20 km/h)'
        : `VIOLATION: ${b.vehicle_speed_kmh} km/h exceeds 25 km/h PNGRB limit!`
    },
    {
      name: '4. Atmospheric Wind Dispersion (Max 15 km/h)',
      val: `${b.wind_speed_kmh} km/h`,
      ok: b.weather_ok !== false && b.wind_speed_kmh <= 15.0,
      score: (b.weather_ok !== false && b.wind_speed_kmh <= 15.0) ? 20 : 0,
      note: (b.weather_ok !== false && b.wind_speed_kmh <= 15.0)
        ? 'Calm boundary layer; plume concentration preserved'
        : `VIOLATION: ${b.wind_speed_kmh} km/h gusts disperse plume (>15 km/h)!`
    },
    {
      name: '5. Route Spatial Coverage Completeness',
      val: `${b.route_completeness_pct || 98.0}%`,
      ok: b.route_complete !== false,
      score: isPass ? 20 : 18,
      note: 'Pipeline corridor coverage meets 95% minimum requirement'
    }
  ];

  container.innerHTML = `
    <div class="qc-card ${cardClass}">
      <div class="qc-header-row">
        <div class="qc-title-wrap">
          <span class="qc-survey-id">${b.survey_id} &bull; Target: ${b.segment_id}</span>
          <span class="qc-team-sub">${b.surveyor_team || 'Mobile Sniffing Van'}</span>
        </div>
        <div class="qc-decision-pill ${decisionClass}">
          <span>${decisionIcon}</span>
          <span>${b.decision}</span>
        </div>
      </div>

      <!-- Telemetry Banner -->
      <div class="qc-telemetry-banner">
        <div class="qc-score-gauge">
          <span class="qc-score-big ${scoreClass}">${b.confidence_score}</span>
          <span class="qc-score-unit">/ 100 QC SCORE</span>
        </div>
        <div class="qc-telemetry-grid">
          <div class="qc-telem-item">
            <span class="qc-telem-label">CH₄ CONCENTRATION</span>
            <span class="qc-telem-val" style="color: ${b.ch4_reading_ppm > 5 ? '#f87171' : '#34d399'};">
              ${b.ch4_reading_ppm} ppm
            </span>
          </div>
          <div class="qc-telem-item">
            <span class="qc-telem-label">VEHICLE SPEED</span>
            <span class="qc-telem-val" style="color: ${b.vehicle_speed_kmh > 25 ? '#f87171' : '#34d399'};">
              ${b.vehicle_speed_kmh} km/h
            </span>
          </div>
          <div class="qc-telem-item">
            <span class="qc-telem-label">WIND VELOCITY</span>
            <span class="qc-telem-val" style="color: ${b.wind_speed_kmh > 15 ? '#f87171' : '#34d399'};">
              ${b.wind_speed_kmh} km/h
            </span>
          </div>
          <div class="qc-telem-item">
            <span class="qc-telem-label">ROUTE COVERAGE</span>
            <span class="qc-telem-val">${b.route_completeness_pct || 98.5}%</span>
          </div>
        </div>
      </div>

      <!-- 5 Quality Gates -->
      <div class="qc-gates-section">
        <div class="qc-gates-title">
          <span>5-FACTOR SURVEY INTEGRITY GATES</span>
          <span>WEIGHT: 20 PTS EACH</span>
        </div>
        ${gates.map(g => `
          <div class="qc-gate-row">
            <div class="qc-gate-top">
              <span class="qc-gate-name">${g.name}</span>
              <span class="qc-gate-val ${g.ok ? 'val-pass' : 'val-fail'}">
                ${g.ok ? '✓ PASS' : '✗ FAIL'} (${g.score}/20 pts) &bull; ${g.val}
              </span>
            </div>
            <div class="qc-gate-bar-bg">
              <div class="qc-gate-bar-fill ${g.ok ? 'bar-fill-pass' : 'bar-fill-fail'}" style="width: ${(g.score / 20) * 100}%;"></div>
            </div>
            <span class="qc-gate-note ${g.ok ? '' : 'text-danger'}">${g.note}</span>
          </div>
        `).join('')}
      </div>

      <!-- Human-in-the-Loop Action Recommendation -->
      <div class="qc-action-footer">
        <div class="qc-action-recommendation">
          <span class="qc-rec-label">OPERATIONAL DIRECTIVE:</span>
          <span class="qc-rec-tag ${isPass ? 'tag-dispatch-verify' : 'tag-rejected-resurvey'}">
            ${(b.action_recommendation || (isPass ? 'DISPATCH_FIELD_VERIFICATION' : 'FLAGGED_FOR_RESURVEY')).replace(/_/g, ' ')}
          </span>
        </div>
        <p class="qc-notes-text">"${b.notes || (isPass ? 'Survey verified accurate. Leak indication forwarded for pin-point ground verification.' : 'Corrupted sample rejected. Re-survey queued under calm weather window.')}"</p>
        <button class="btn-qc-locate" id="btnQcLocateTarget" data-segment="${b.segment_id}">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
          </svg>
          <span>Locate Target Pipeline (${b.segment_id}) on GIS Map</span>
        </button>
      </div>
    </div>
  `;

  const btnLocate = document.getElementById('btnQcLocateTarget');
  if (btnLocate) {
    btnLocate.addEventListener('click', () => {
      selectSegment(b.segment_id, true);
    });
  }
}

/**
 * Open Emergency Incident Modal
 */
function openEmergencyModal(preselectedSegmentId) {
  const modal = document.getElementById('modalEmergencyIncident');
  const select = document.getElementById('emergencySegmentSelect');
  if (!modal || !select) return;

  // Populate segments dropdown
  select.innerHTML = '';
  state.segments.forEach(seg => {
    const opt = document.createElement('option');
    opt.value = seg.segment_id;
    opt.textContent = `${seg.segment_id} — ${seg.name} (Tier: ${seg.tier}, Score: ${seg.score})`;
    if (preselectedSegmentId && seg.segment_id === preselectedSegmentId) {
      opt.selected = true;
    } else if (!preselectedSegmentId && seg.segment_id === (state.selectedSegmentId || 'P-104')) {
      opt.selected = true;
    }
    select.appendChild(opt);
  });

  modal.style.display = 'flex';
}

/**
 * Close Emergency Incident Modal
 */
function closeEmergencyModal() {
  const modal = document.getElementById('modalEmergencyIncident');
  if (modal) modal.style.display = 'none';
}

/**
 * Handle Emergency Incident Escalation (PRD §8B & §12 Demo Action)
 */
async function handleEmergencyIncidentSubmit() {
  const select = document.getElementById('emergencySegmentSelect');
  const typeSelect = document.getElementById('emergencyTypeSelect');
  const reporterInput = document.getElementById('emergencyReporterInput');

  const segmentId = select ? select.value : (state.selectedSegmentId || 'P-104');
  const incidentType = typeSelect ? typeSelect.value : 'third_party_strike';
  const reporterName = reporterInput ? reporterInput.value : 'Control Room Live Report';

  closeEmergencyModal();
  showToast(`🚨 Triggering Emergency Protocol for ${segmentId}...`, 'error');

  // Attempt Backend Escalation Call
  try {
    await fetch(`${CONFIG.API_BASE}/incidents/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        segment_id: segmentId,
        incident_type: incidentType,
        reporter_name: reporterName,
        notes: `Emergency excavation breach trigger: ${incidentType}`
      })
    });
  } catch (err) {
    console.warn('API incident call failed, applying local escalation fallback:', err);
  }

  // Mutate local state for instant responsive UI
  const segIndex = state.segments.findIndex(s => s.segment_id === segmentId);
  if (segIndex !== -1) {
    const targetSeg = state.segments[segIndex];
    targetSeg.score = 100;
    targetSeg.tier = 'CRITICAL';
    targetSeg.third_party_activity = 'direct_excavation_hazard';
    targetSeg.factors = {
      previous_incidents: state.weights.previous_incidents || 25,
      pe_vulnerability: state.weights.pe_vulnerability || 20,
      days_since_survey: state.weights.days_since_survey || 20,
      third_party_activity: state.weights.third_party_activity || 15,
      rodent_history: state.weights.rodent_history || 10,
      public_consequence: state.weights.public_consequence || 10
    };

    // Move to front of queue (Position #1)
    state.segments.splice(segIndex, 1);
    state.segments.unshift(targetSeg);

    // Re-render UI
    updateHeaderKPIs();
    renderSegmentList();
    renderMapPipelines();
    selectSegment(segmentId, true);

    // Apply pulsing strobe animation to map polyline
    const polyline = state.mapLayers.polylines[segmentId];
    if (polyline && polyline._path) {
      polyline._path.classList.add('polyline-emergency-strobe');
    }

    showToast(`🚨 CRITICAL EMERGENCY OVERRIDE! ${segmentId} escalated to 100/100 (CRITICAL). Isolation Squad Dispatched to Site!`, 'error');
  }
}

/* ==========================================================================
   PHASE 5: 3-COLUMN ROUTE DISPATCH BOARD & 7-STEP HACKATHON DEMO STEPPER
   ========================================================================== */

/**
 * Setup Phase 5 Event Listeners
 */
function setupPhase5RouteAndDemoListeners() {
  // Route Board Modal Buttons
  const btnOpenDispatch = document.getElementById('btnOpenDispatchModal');
  const btnCloseDispatch = document.getElementById('btnCloseDispatchModal');
  const btnExportRoutes = document.getElementById('btnExportRoutesGeoJSON');

  if (btnOpenDispatch) {
    btnOpenDispatch.addEventListener('click', openRouteDispatchModal);
  }

  if (btnCloseDispatch) {
    btnCloseDispatch.addEventListener('click', closeRouteDispatchModal);
  }

  if (btnExportRoutes) {
    btnExportRoutes.addEventListener('click', exportRouteManifestJSON);
  }

  // Demo Guide Floating Bar Buttons
  const btnToggleGuide = document.getElementById('btnToggleDemoGuide');
  const btnCloseGuide = document.getElementById('btnCloseDemoGuide');
  const btnPrev = document.getElementById('btnDemoPrevStep');
  const btnNext = document.getElementById('btnDemoNextStep');
  const btnExecute = document.getElementById('btnDemoExecuteStep');

  if (btnToggleGuide) {
    btnToggleGuide.addEventListener('click', toggleDemoGuide);
  }

  if (btnCloseGuide) {
    btnCloseGuide.addEventListener('click', () => {
      const bar = document.getElementById('floatingDemoBar');
      if (bar) bar.style.display = 'none';
      state.isDemoGuideActive = false;
    });
  }

  if (btnPrev) {
    btnPrev.addEventListener('click', () => {
      if (state.demoStepIndex > 0) {
        state.demoStepIndex--;
        updateDemoBarUI();
      }
    });
  }

  if (btnNext) {
    btnNext.addEventListener('click', () => {
      if (state.demoStepIndex < DEMO_STEPS.length - 1) {
        state.demoStepIndex++;
        updateDemoBarUI();
      }
    });
  }

  if (btnExecute) {
    btnExecute.addEventListener('click', () => {
      executeCurrentDemoStep();
    });
  }
}

/**
 * Open 3-Column Team Route Dispatch Modal (PRD §11 & §12)
 */
function openRouteDispatchModal() {
  const modal = document.getElementById('modalRouteDispatch');
  if (!modal) return;

  renderRouteDispatchBoard();
  modal.style.display = 'flex';
}

/**
 * Close 3-Column Route Dispatch Modal
 */
function closeRouteDispatchModal() {
  const modal = document.getElementById('modalRouteDispatch');
  if (modal) modal.style.display = 'none';
}

/**
 * Render 3-Column Team Route Assignment Board
 * Categorizes segments by team based on priority score & tier
 */
function renderRouteDispatchBoard() {
  // Sort all segments by current score descending
  const sorted = [...state.segments].sort((a, b) => b.score - a.score);

  // Group into Teams A, B, C
  const teamAlpha = sorted.filter(s => s.tier === 'CRITICAL' || s.score >= 85);
  const teamBeta = sorted.filter(s => s.tier === 'HIGH' || (s.score >= 70 && s.score < 85));
  const teamGamma = sorted.filter(s => s.tier === 'MEDIUM' || s.tier === 'LOW' || s.score < 70);

  // Update Counters & Averages
  updateTeamColStats('Alpha', teamAlpha);
  updateTeamColStats('Beta', teamBeta);
  updateTeamColStats('Gamma', teamGamma);

  // Render cards
  renderTeamCardList('Alpha', teamAlpha, 'col-team-alpha');
  renderTeamCardList('Beta', teamBeta, 'col-team-beta');
  renderTeamCardList('Gamma', teamGamma, 'col-team-gamma');
}

function updateTeamColStats(teamName, segments) {
  const countEl = document.getElementById(`team${teamName}Count`);
  const avgEl = document.getElementById(`team${teamName}AvgScore`);

  if (countEl) countEl.textContent = `${segments.length} Segment(s)`;
  if (avgEl) {
    const avg = segments.length > 0
      ? (segments.reduce((acc, s) => acc + s.score, 0) / segments.length).toFixed(1)
      : '0.0';
    avgEl.textContent = avg;
  }
}

function renderTeamCardList(teamName, segments, columnClass) {
  const container = document.getElementById(`team${teamName}CardsList`);
  if (!container) return;

  if (segments.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 24px 12px; color: var(--text-muted); font-size: 0.72rem;">
        No segments currently match this tier.
      </div>
    `;
    return;
  }

  container.innerHTML = segments.map((s, idx) => {
    const tierPillClass = `tier-pill-${s.tier.toLowerCase()}`;
    const excStatus = (s.third_party_activity || 'none').replace(/_/g, ' ');
    const isP104 = s.segment_id === 'P-104';

    return `
      <div class="dispatch-seg-card" style="${isP104 ? 'border-color: #38bdf8; box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);' : ''}">
        <div class="disp-card-top">
          <span class="disp-seg-id">${idx + 1}. ${s.segment_id}</span>
          <span class="tier-pill ${tierPillClass}" style="font-size: 0.62rem; padding: 2px 6px;">
            ${s.tier} (${s.score})
          </span>
        </div>
        <div class="disp-name">${s.name}</div>
        <div class="disp-meta-row">
          <div class="disp-meta-item">Depth: <strong>${s.depth_meters}m</strong></div>
          <div class="disp-meta-item">Pressure: <strong>${s.operating_pressure_bar} bar</strong></div>
          <div class="disp-meta-item">Material: <strong>${formatMaterialName(s.material)}</strong></div>
        </div>
        <div class="disp-meta-row">
          <div class="disp-meta-item">Dig Hazard: <strong style="color: ${s.third_party_activity === 'direct_excavation_hazard' ? '#f87171' : 'var(--text-secondary)'};">${excStatus}</strong></div>
          <div class="disp-meta-item">Days: <strong>${s.days_since_survey}d / ${s.target_survey_cycle}d</strong></div>
        </div>
        <div class="disp-card-actions">
          <button class="btn-disp-action" onclick="closeRouteDispatchModal(); selectSegment('${s.segment_id}', true);">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
            </svg>
            <span>View on Map</span>
          </button>
          <button class="btn-disp-action" onclick="showToast('Dispatching Team ${teamName} to ${s.segment_id}...', 'success')">
            <span>Deploy Team</span>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Export Route Dispatch Manifest as JSON download
 */
function exportRouteManifestJSON() {
  const sorted = [...state.segments].sort((a, b) => b.score - a.score);
  const manifest = {
    generated_at: new Date().toISOString(),
    grid_location: "Delhi CGD Urban Gas Grid",
    dispatch_plan: {
      team_alpha: {
        vehicle: "Mobile Van #1 (CRDS Methane Sniffer)",
        target_tier: "CRITICAL",
        segments: sorted.filter(s => s.tier === 'CRITICAL' || s.score >= 85).map(s => ({
          segment_id: s.segment_id,
          name: s.name,
          priority_score: s.score,
          burial_depth: s.depth_meters,
          operating_pressure_bar: s.operating_pressure_bar
        }))
      },
      team_beta: {
        vehicle: "Mobile Van #2 (TDLAS Laser Sniffer)",
        target_tier: "HIGH",
        segments: sorted.filter(s => s.tier === 'HIGH' || (s.score >= 70 && s.score < 85)).map(s => ({
          segment_id: s.segment_id,
          name: s.name,
          priority_score: s.score,
          burial_depth: s.depth_meters,
          operating_pressure_bar: s.operating_pressure_bar
        }))
      },
      team_gamma: {
        unit: "Foot Patrol Squad & Sniffer K9",
        target_tier: "MEDIUM & LOW",
        segments: sorted.filter(s => s.tier === 'MEDIUM' || s.tier === 'LOW' || s.score < 70).map(s => ({
          segment_id: s.segment_id,
          name: s.name,
          priority_score: s.score,
          burial_depth: s.depth_meters,
          operating_pressure_bar: s.operating_pressure_bar
        }))
      }
    }
  };

  const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `methanos_dispatch_manifest_${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Exported Fleet Dispatch Manifest (JSON)', 'success');
}

/**
 * 7-Step Demo Script Guide (PRD §12 Demo Flow)
 */
const DEMO_STEPS = [
  {
    step: 1,
    title: "1. Geospatial Network & GIS Profile",
    desc: "Display Delhi CGD grid with 12 pipeline segments color-coded by PNGRB tiers (🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low) with GIS burial depth & operating pressure.",
    btnLabel: "Reset Network View",
    action: () => {
      closeRouteDispatchModal();
      closeEmergencyModal();
      if (state.map) state.map.setView(CONFIG.DEFAULT_CENTER, CONFIG.DEFAULT_ZOOM);
      switchInspectorTab('panelSegmentDetail');
      showToast('Step 1: Delhi CGD Network Overview Active', 'info');
    }
  },
  {
    step: 2,
    title: "2. Inspect P-104 Benchmark (85/100)",
    desc: "Click benchmark segment P-104 (Chandni Chowk Market). Review 6-factor score formula (18+20+15+15+10+7 = 85) and shallow burial depth (0.8m).",
    btnLabel: "Focus P-104 Benchmark",
    action: () => {
      closeRouteDispatchModal();
      closeEmergencyModal();
      switchInspectorTab('panelSegmentDetail');
      selectSegment('P-104', true);
      showToast('Step 2: P-104 Benchmark Inspected (Score 85 / CRITICAL)', 'info');
    }
  },
  {
    step: 3,
    title: "3. Live Recomputation with Sliders",
    desc: "Switch to Weight Sliders. Apply 'Excavation Threat Bias' preset or drag Third-Party Activity slider to watch map routes & scores recalculate live.",
    btnLabel: "Apply Excavation Bias",
    action: () => {
      closeRouteDispatchModal();
      closeEmergencyModal();
      switchInspectorTab('panelWeightSliders');
      applyPresetWeights('excavation');
      showToast('Step 3: Excavation Risk Weight set to 45 pts. Live recomputation active!', 'info');
    }
  },
  {
    step: 4,
    title: "4. 48-Hour Dig Early Warning & Blueprint",
    desc: "Open 48-Hour Excavation Notice feed. Notice DIG-801 trench depth (1.5m) clashes with P-104 pipe depth (0.8m). View Digital Safety Blueprint.",
    btnLabel: "Open 48H Dig & Blueprint",
    action: () => {
      closeRouteDispatchModal();
      closeEmergencyModal();
      switchInspectorTab('panelDigNotices');
      openSafetyBlueprintModal('DIG-801');
      showToast('Step 4: 48H Excavation Clash & Safety Clearance Blueprint Opened', 'info');
    }
  },
  {
    step: 5,
    title: "5. Survey Confidence QC Engine",
    desc: "Answers 'Can we trust this survey?'. Flip between High Confidence S-2101 (ACCEPT, 100 pts) and Low Confidence S-2201 (RE-SURVEY, 43 pts with speed/wind violations).",
    btnLabel: "Toggle Survey QC (S-2201)",
    action: () => {
      const bpModal = document.getElementById('modalSafetyBlueprint');
      if (bpModal) bpModal.style.display = 'none';
      closeEmergencyModal();
      closeRouteDispatchModal();
      switchInspectorTab('panelConfidenceQC');
      const btnLow = document.getElementById('btnQCLowExample');
      const btnHigh = document.getElementById('btnQCHighExample');
      if (btnLow && btnHigh) {
        btnLow.classList.add('active');
        btnHigh.classList.remove('active');
        state.activeQCKey = 'low';
        renderConfidenceCard('low');
      }
      showToast('Step 5: Low Confidence Survey S-2201 flagged for RE-SURVEY (Speed & Wind Violations)', 'warning');
    }
  },
  {
    step: 6,
    title: "6. Report Emergency Incident / Puncture Strike",
    desc: "Simulate excavator strike on P-101 (Connaught Place Ring Main): forces priority to 100/100 CRITICAL instantly with flashing strobe on map and #1 queue position.",
    btnLabel: "Trigger Critical Strike on P-101",
    action: () => {
      const bpModal = document.getElementById('modalSafetyBlueprint');
      if (bpModal) bpModal.style.display = 'none';
      closeRouteDispatchModal();
      openEmergencyModal('P-101');
      setTimeout(() => {
        handleEmergencyIncidentSubmit();
      }, 600);
      showToast('Step 6: Emergency Incident Triggered on P-101 -> Escalated to 100/100 (CRITICAL)', 'error');
    }
  },
  {
    step: 7,
    title: "7. Dynamic Route Dispatch (Team Alpha -> P-104)",
    desc: "Conclude presentation on the 3-column Fleet Route Board: proving Team Alpha is dispatched to P-104 and P-101 today based on real-time risk tiers.",
    btnLabel: "Open Route Dispatch Board",
    action: () => {
      openRouteDispatchModal();
      showToast('Step 7: Final Route Dispatch — "Team Alpha should visit P-104 today"', 'success');
    }
  }
];

function toggleDemoGuide() {
  const bar = document.getElementById('floatingDemoBar');
  if (!bar) return;

  if (bar.style.display === 'none' || !bar.style.display) {
    bar.style.display = 'flex';
    state.isDemoGuideActive = true;
    updateDemoBarUI();
  } else {
    bar.style.display = 'none';
    state.isDemoGuideActive = false;
  }
}

function updateDemoBarUI() {
  const cur = DEMO_STEPS[state.demoStepIndex];
  if (!cur) return;

  const badge = document.getElementById('demoStepBadge');
  const title = document.getElementById('demoStepTitle');
  const desc = document.getElementById('demoStepDesc');
  const btnAction = document.getElementById('btnDemoExecuteStep');
  const btnPrev = document.getElementById('btnDemoPrevStep');
  const btnNext = document.getElementById('btnDemoNextStep');

  if (badge) badge.textContent = `STEP ${cur.step} OF 7`;
  if (title) title.textContent = cur.title;
  if (desc) desc.textContent = cur.desc;
  if (btnAction) {
    btnAction.innerHTML = `
      <span>${cur.btnLabel}</span>
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"/>
      </svg>
    `;
  }

  if (btnPrev) btnPrev.disabled = state.demoStepIndex === 0;
  if (btnNext) btnNext.disabled = state.demoStepIndex === DEMO_STEPS.length - 1;
}

function executeCurrentDemoStep() {
  const cur = DEMO_STEPS[state.demoStepIndex];
  if (cur && typeof cur.action === 'function') {
    cur.action();
  }
}

