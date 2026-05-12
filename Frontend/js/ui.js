/**
 * ui.js
 * ─────────────────────────────────────────────
 * Dashboard: Egyptian city graph with IMPROVED
 * visualization — larger nodes, bezier curves,
 * proper normalization, bigger labels, halos.
 */

import * as THREE from 'three';
import { setMode, setEmergencyMode } from './environment.js?v=20260512-api-sync';
import { setRoadState } from './three-scene.js?v=20260512-api-sync';

const REQUEST_TIMEOUT_MS = 10000;
const HEALTH_POLL_INTERVAL_MS = 5000;
const LOCAL_API_CANDIDATES = [
  'http://127.0.0.1:8000/api',
  'http://localhost:8000/api',
];

let cityNodes = [];
let cityEdges = [];

// ── State ─────────────────────────────────────
let mapCanvas, mapCtx;
let mapCanvasCompare, mapCtxCompare;

let currentPath = [];
let currentPathCompare = []; // Used for right-side A* path in comparison mode

let pathAnimProgress = 0;
let pathAnimId = null;
let trafficParticles = [];
let routeFlowParticles = [];
let edgeCurves = new Map(); // Store THREE.CatmullRomCurve3 per edge
let hoveredNode = null;
let currentTimePeriod = 'morning';
let currentTrafficMode = 'normal';
let currentAlgorithm = 'dijkstra';
let comparisonMode = false;
let mstEdges = []; // For Prim mode
let dpNodes = []; // For DP mode
let lastRouteCoordinates = [];
let resolvedApiBase = null;
let graphLoaded = false;
let graphLoadingPromise = null;
let healthPollId = null;
let dashboardEventsBound = false;
let mapLoopStarted = false;
let labelLayoutCache = new Map();

// Padding for graph display
const PAD = 25;
const NODE_LAYOUT_MAP = Object.freeze({
  '7': { x: 0.1, y: 0.47, region: 'west', label: { dx: -18, dy: -36, align: 'right', baseline: 'alphabetic' } },
  '15': { x: 0.11, y: 0.26, region: 'west', label: { dx: -16, dy: -16, align: 'right', baseline: 'middle' } },
  'F7': { x: 0.19, y: 0.15, region: 'west', label: { dx: 0, dy: -34, align: 'center', baseline: 'alphabetic' } },
  '8': { x: 0.2, y: 0.66, region: 'west', label: { dx: -18, dy: 22, align: 'right', baseline: 'top' } },
  '9': { x: 0.34, y: 0.4, region: 'central_west', label: { dx: -18, dy: -26, align: 'right', baseline: 'alphabetic' } },
  '10': { x: 0.33, y: 0.55, region: 'central_west', label: { dx: -18, dy: 22, align: 'right', baseline: 'top' } },
  '6': { x: 0.43, y: 0.31, region: 'central_west', label: { dx: 0, dy: -34, align: 'center', baseline: 'alphabetic' } },
  'F3': { x: 0.31, y: 0.73, region: 'central_west', label: { dx: 0, dy: 26, align: 'center', baseline: 'top' } },
  '3': { x: 0.49, y: 0.48, region: 'center', label: { dx: 0, dy: -38, align: 'center', baseline: 'alphabetic' } },
  'F2': { x: 0.54, y: 0.26, region: 'north', label: { dx: 16, dy: -18, align: 'left', baseline: 'middle' } },
  'F5': { x: 0.46, y: 0.59, region: 'center', label: { dx: 16, dy: 26, align: 'left', baseline: 'top' } },
  'F9': { x: 0.5, y: 0.71, region: 'center', label: { dx: 18, dy: 18, align: 'left', baseline: 'top' } },
  '11': { x: 0.54, y: 0.12, region: 'north', label: { dx: 0, dy: -32, align: 'center', baseline: 'alphabetic' } },
  '2': { x: 0.68, y: 0.44, region: 'east_central', label: { dx: 18, dy: -18, align: 'left', baseline: 'middle' } },
  'F6': { x: 0.62, y: 0.32, region: 'east_central', label: { dx: 18, dy: -14, align: 'left', baseline: 'middle' } },
  'F4': { x: 0.61, y: 0.61, region: 'east_central', label: { dx: 18, dy: 18, align: 'left', baseline: 'top' } },
  '5': { x: 0.78, y: 0.24, region: 'east', label: { dx: 18, dy: -14, align: 'left', baseline: 'middle' } },
  'F1': { x: 0.91, y: 0.14, region: 'east', label: { dx: 0, dy: -30, align: 'center', baseline: 'alphabetic' } },
  '4': { x: 0.83, y: 0.43, region: 'east', label: { dx: 18, dy: -20, align: 'left', baseline: 'middle' } },
  'F8': { x: 0.79, y: 0.59, region: 'east', label: { dx: 0, dy: 26, align: 'center', baseline: 'top' } },
  '14': { x: 0.9, y: 0.34, region: 'east', label: { dx: 18, dy: 18, align: 'left', baseline: 'top' } },
  '13': { x: 0.95, y: 0.7, region: 'east', label: { dx: 0, dy: 26, align: 'center', baseline: 'top' } },
  '1': { x: 0.57, y: 0.83, region: 'south', label: { dx: -18, dy: 24, align: 'right', baseline: 'top' } },
  'F10': { x: 0.64, y: 0.91, region: 'south', label: { dx: 18, dy: 18, align: 'left', baseline: 'top' } },
  '12': { x: 0.61, y: 0.98, region: 'south', label: { dx: -18, dy: -18, align: 'right', baseline: 'middle' } },
});
const LAYOUT_PADDING = Object.freeze({
  single: { x: 78, y: 64 },
  compare: { x: 156, y: 120 },
});
const TYPE_COLORS = Object.freeze({
  district: '#d7deeb',
  facility: '#7ad4ff',
  hub: '#00ff88',
  hospital: '#ff6a6a',
});

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function getNodeById(nodeId) {
  return cityNodes.find((node) => node.id === nodeId);
}

function getEdgeKey(source, target) {
  return [source, target].sort().join('__');
}

function getLayoutPadding(width, height) {
  const base = comparisonMode ? LAYOUT_PADDING.compare : LAYOUT_PADDING.single;
  return {
    x: Math.max(base.x, Math.round(width * (comparisonMode ? 0.09 : 0.06))),
    y: Math.max(base.y, Math.round(height * (comparisonMode ? 0.09 : 0.07))),
  };
}

function getNodeLabelPreference(node) {
  return node.labelPreference || {
    dx: node.x >= 0.72 ? 18 : node.x <= 0.25 ? -18 : 0,
    dy: node.y >= 0.75 ? 22 : -34,
    align: node.x >= 0.72 ? 'left' : node.x <= 0.25 ? 'right' : 'center',
    baseline: node.y >= 0.75 ? 'top' : 'alphabetic',
  };
}

function applyCuratedLayout(node) {
  const preset = NODE_LAYOUT_MAP[node.id];
  if (!preset) {
    return {
      ...node,
      region: node.type || 'district',
      labelPreference: getNodeLabelPreference(node),
    };
  }

  return {
    ...node,
    x: preset.x,
    y: preset.y,
    region: preset.region,
    labelPreference: preset.label,
  };
}

function getStoredApiBase() {
  try {
    return window.localStorage?.getItem('cairogrid.apiBase') || null;
  } catch (error) {
    return null;
  }
}

function storeApiBase(baseUrl) {
  try {
    window.localStorage?.setItem('cairogrid.apiBase', baseUrl);
  } catch (error) {
    // Ignore storage access issues and continue with the in-memory value.
  }
}

function buildApiCandidates() {
  const overrides = [
    window.CAIROGRID_API_BASE,
    getStoredApiBase(),
  ].filter(Boolean);

  const sameOriginCandidate =
    window.location.protocol === 'file:'
      ? null
      : `${window.location.origin.replace(/\/$/, '')}/api`;

  return [...new Set([
    ...overrides,
    sameOriginCandidate,
    ...LOCAL_API_CANDIDATES,
  ].filter(Boolean))];
}

async function fetchWithTimeout(url, options = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timed out while contacting the backend.');
    }
    throw new Error('Unable to reach the backend API.');
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function probeApiBase(baseUrl) {
  const response = await fetchWithTimeout(`${baseUrl}/health`, {
    headers: { Accept: 'application/json' },
  }, 2500);

  if (!response.ok) {
    throw new Error(`Health probe failed (${response.status})`);
  }

  return baseUrl;
}

async function resolveApiBase(forceRefresh = false) {
  if (!forceRefresh && resolvedApiBase) {
    return resolvedApiBase;
  }

  const candidates = buildApiCandidates();
  for (const candidate of candidates) {
    try {
      resolvedApiBase = await probeApiBase(candidate);
      storeApiBase(resolvedApiBase);
      return resolvedApiBase;
    } catch (error) {
      console.debug(`API probe failed for ${candidate}:`, error.message);
    }
  }

  resolvedApiBase = null;
  throw new Error('Backend API is offline. Start it locally on http://127.0.0.1:8000.');
}

async function getApiUrl(path, forceRefresh = false) {
  const baseUrl = await resolveApiBase(forceRefresh);
  return `${baseUrl}${path}`;
}

async function apiRequest(path, options = {}) {
  let response;

  try {
    response = await fetchWithTimeout(await getApiUrl(path), {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options,
    });
  } catch (error) {
    if (error.message.includes('offline') || error.message.includes('timed out')) {
      throw error;
    }

    resolvedApiBase = null;
    response = await fetchWithTimeout(await getApiUrl(path, true), {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options,
    });
  }

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const payload = isJson ? await response.json() : null;

  if (!response.ok) {
    const message = payload?.error?.message || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return payload;
}

async function syncHealthStatus() {
  const statusEl = document.getElementById('system-status');
  try {
    const health = await apiRequest('/health');
    if (statusEl) {
      statusEl.innerHTML = '<span class="badge-dot"></span> ONLINE';
      statusEl.classList.add('online');
      statusEl.classList.remove('offline');
      statusEl.title = `Graph: ${health.nodes_count} nodes / ${health.edges_count} edges`;
    }
    return health;
  } catch (error) {
    resolvedApiBase = null;
    if (statusEl) {
      statusEl.innerHTML = '<span class="badge-dot"></span> OFFLINE';
      statusEl.classList.remove('online');
      statusEl.classList.add('offline');
      statusEl.title = error.message;
    }
    throw error;
  }
}

async function loadGraphData(forceRefresh = false) {
  if (graphLoadingPromise) {
    return graphLoadingPromise;
  }

  if (graphLoaded && !forceRefresh) {
    return { nodes: cityNodes, edges: cityEdges };
  }

  graphLoadingPromise = (async () => {
    const graph = await apiRequest('/graph');
    cityNodes = graph.nodes.map((node) => applyCuratedLayout({
      id: node.id,
      label: node.name,
      type: node.type,
      x: node.x,
      y: node.y,
      metadata: node.metadata || {},
    }));
    cityEdges = graph.edges.map((edge) => ({
      from: edge.source,
      to: edge.target,
      distance: edge.distance,
      capacity: edge.capacity,
      trafficData: edge.traffic || {},
      metadata: edge.metadata || {},
      traffic: 0.3,
    }));
    labelLayoutCache.clear();
    updateEdgeTraffic();
    populateSelectors();
    generateCurves();
    createTrafficParticles();
    graphLoaded = true;
    return graph;
  })();

  try {
    return await graphLoadingPromise;
  } catch (error) {
    graphLoaded = false;
    throw error;
  } finally {
    graphLoadingPromise = null;
  }
}

async function pollHealthAndBootstrap(notifyOnFailure = false) {
  try {
    await syncHealthStatus();
    if (!graphLoaded || cityNodes.length === 0 || cityEdges.length === 0) {
      await loadGraphData();
    }
  } catch (error) {
    if (notifyOnFailure) {
      showNotification(error.message || 'Backend unavailable');
    }
  }
}

function startHealthPolling() {
  if (healthPollId) {
    window.clearInterval(healthPollId);
  }

  pollHealthAndBootstrap(true);
  healthPollId = window.setInterval(() => {
    pollHealthAndBootstrap(false);
  }, HEALTH_POLL_INTERVAL_MS);
}

function stopHealthPolling() {
  if (healthPollId) {
    window.clearInterval(healthPollId);
    healthPollId = null;
  }
}

function handleDashboardResize() {
  labelLayoutCache.clear();
  resizeMap();
  generateCurves();
}

// ── Init Dashboard ────────────────────────────
export function initDashboard() {
  mapCanvas = document.getElementById('map-canvas');
  mapCanvasCompare = document.getElementById('map-canvas-compare');
  
  if (!mapCanvas) return;

  mapCtx = mapCanvas.getContext('2d');
  if (mapCanvasCompare) mapCtxCompare = mapCanvasCompare.getContext('2d');
  
  resizeMap();
  if (!dashboardEventsBound) {
    bindEvents();
    window.addEventListener('resize', handleDashboardResize);
    dashboardEventsBound = true;
  }
  if (!mapLoopStarted) {
    startMapLoop();
    mapLoopStarted = true;
  }

  startHealthPolling();
}

function resizeMap() {
  if (!mapCanvas) return;
  const wrapper = document.getElementById('map-container-wrapper');
  
  // Resize left canvas
  mapCanvas.width = mapCanvas.parentElement.clientWidth;
  mapCanvas.height = mapCanvas.parentElement.clientHeight;
  
  // Resize right canvas if it exists
  if (mapCanvasCompare && mapCanvasCompare.parentElement) {
    mapCanvasCompare.width = mapCanvasCompare.parentElement.clientWidth;
    mapCanvasCompare.height = mapCanvasCompare.parentElement.clientHeight;
  }
}

function nodeX(node, w) {
  const pad = getLayoutPadding(w, 0).x;
  const nx = clamp(typeof node.x === 'number' ? node.x : 0.5, 0, 1);
  return pad + nx * (w - pad * 2);
}

function nodeY(node, h) {
  const pad = getLayoutPadding(0, h).y;
  const ny = clamp(typeof node.y === 'number' ? node.y : 0.5, 0, 1);
  return pad + ny * (h - pad * 2);
}

// ── Curve Generation — same logic for all ──────
function generateCurves() {
  if (!mapCanvas) return;
  edgeCurves.clear();
  labelLayoutCache.clear();

  cityEdges.forEach((edge, index) => {
    const from = cityNodes.find((n) => n.id === edge.from);
    const to = cityNodes.find((n) => n.id === edge.to);
    if (!from || !to) return;

    const x1 = from.x, y1 = from.y;
    const x2 = to.x, y2 = to.y;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 0.001;
    const nx = -dy / len;
    const ny = dx / len;
    const sign = (getEdgeKey(edge.from, edge.to).split('').reduce((sum, char) => sum + char.charCodeAt(0), 0) % 2 === 0) ? 1 : -1;
    const bend = clamp(0.025 + len * 0.12, 0.035, 0.12);

    let c1x;
    let c1y;
    let c2x;
    let c2y;

    if (Math.abs(dx) > 0.34) {
      const routeY = clamp((y1 + y2) / 2 + sign * bend * 0.75, 0.1, 0.92);
      c1x = x1 + dx * 0.28;
      c2x = x1 + dx * 0.72;
      c1y = routeY;
      c2y = routeY;
    } else if (Math.abs(dy) > 0.26) {
      const routeX = clamp((x1 + x2) / 2 + sign * bend * 0.55, 0.08, 0.94);
      c1x = routeX;
      c2x = routeX;
      c1y = y1 + dy * 0.3;
      c2y = y1 + dy * 0.7;
    } else {
      c1x = x1 + dx * 0.3 + nx * bend * sign;
      c1y = y1 + dy * 0.3 + ny * bend * sign;
      c2x = x1 + dx * 0.7 + nx * bend * sign;
      c2y = y1 + dy * 0.7 + ny * bend * sign;
    }

    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(x1, y1, 0),
      new THREE.Vector3(c1x, c1y, 0),
      new THREE.Vector3(c2x, c2y, 0),
      new THREE.Vector3(x2, y2, 0)
    ], false, 'catmullrom', 0.22);

    curve.points100 = curve.getPoints(100);
    edgeCurves.set(`${edge.from}_${edge.to}`, curve);
  });
}

function getCurvePointsAbs(curve, w, h) {
   if (!curve.points100) return [];
   return curve.points100.map(p => ({
       x: nodeX(p, w),
       y: nodeY(p, h)
   }));
}

function getCurvePointAbs(curve, t, w, h) {
   const p = curve.getPoint(t);
   return {
       x: nodeX(p, w),
       y: nodeY(p, h)
   };
}

function populateSelectors() {
  const srcSelect = document.getElementById('source-select');
  const dstSelect = document.getElementById('dest-select');
  const aiSrcSelect = document.getElementById('ai-source-select');
  const aiDstSelect = document.getElementById('ai-dest-select');
  
  if (!srcSelect || !dstSelect || cityNodes.length === 0) return;
  
  srcSelect.innerHTML = '<option value="" disabled selected>Select origin</option>';
  dstSelect.innerHTML = '<option value="" disabled selected>Select destination</option>';
  if (aiSrcSelect) aiSrcSelect.innerHTML = '';
  if (aiDstSelect) aiDstSelect.innerHTML = '';

  cityNodes.forEach((node) => {
    srcSelect.add(new Option(node.label, node.id));
    dstSelect.add(new Option(node.label, node.id));
    if (aiSrcSelect) aiSrcSelect.add(new Option(node.label, node.id));
    if (aiDstSelect) aiDstSelect.add(new Option(node.label, node.id));
  });
  
  srcSelect.value = cityNodes[0]?.id || '';
  dstSelect.value = cityNodes[1]?.id || cityNodes[0]?.id || '';
  if (aiSrcSelect) aiSrcSelect.value = cityNodes[0]?.id || '';
  if (aiDstSelect) aiDstSelect.value = cityNodes[1]?.id || cityNodes[0]?.id || '';
}

function bindEvents() {

  const timeSelect = document.getElementById('time-select');
  if (timeSelect) {
    timeSelect.addEventListener('change', (e) => {
      currentTimePeriod = e.target.value;
      if (e.target.value === 'morning') setMode('morning');
      else if (e.target.value === 'afternoon') setMode('day');
      else if (e.target.value === 'evening') setMode('night');
      else setMode('night');
      updateEdgeTraffic();
      createTrafficParticles();
    });
  }

  const modeSelect = document.getElementById('mode-select');
  if (modeSelect) {
    modeSelect.addEventListener('change', (e) => {
      currentTrafficMode = e.target.value;
      const isEmergency = e.target.value === 'emergency';
      setEmergencyMode(isEmergency);
      if (!isEmergency) updateRoadFromTraffic();
    });
  }
  
  const algoSelect = document.getElementById('algo-select');
  if (algoSelect) {
    algoSelect.addEventListener('change', (e) => {
      currentAlgorithm = e.target.value;
      setComparisonMode(false); // Disable comparison mode if they select a new single algorithm
    });
  }
  
  const compareBtn = document.getElementById('compare-btn');
  if (compareBtn) {
      compareBtn.addEventListener('click', () => {
         if (comparisonMode) {
             setComparisonMode(false);
             calculateRoute(); // Restore normal single graph state
         } else {
             currentAlgorithm = 'dijkstra';
             if (algoSelect) algoSelect.value = 'dijkstra';
             setComparisonMode(true);
             calculateRoute();
         }
      });
  }
  
  const calcBtn = document.getElementById('calc-route-btn');
  if (calcBtn) {
      // Wrap it so it resets comparison mode if they just click the normal calculate
      calcBtn.addEventListener('click', () => {
          setComparisonMode(false);
          calculateRoute();
      });
  }
  
  const mlScrollBtn = document.getElementById('ml-scroll-btn');
  if (mlScrollBtn) {
      mlScrollBtn.addEventListener('click', () => {
          const aiSection = document.getElementById('ai-section');
          if (aiSection) {
              aiSection.style.display = 'block';
              gsap.to(aiSection, { opacity: 1, duration: 0.8, ease: 'power2.out' });
              setTimeout(() => {
                  aiSection.scrollIntoView({ behavior: 'smooth' });
              }, 100);
          }
      });
  }

  const runPredBtn = document.getElementById('run-prediction-btn');
  if (runPredBtn) {
      runPredBtn.addEventListener('click', () => runPrediction());
  }

  document.querySelectorAll('.mode-btn[data-mode]').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.mode-btn[data-mode]').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      setMode(btn.dataset.mode);
    });
  });

  if (mapCanvas) {
    mapCanvas.addEventListener('mousemove', (e) => onMapMouseMove(e, mapCanvas));
    mapCanvas.addEventListener('click', onMapClick);
  }
  
  if (mapCanvasCompare) {
    mapCanvasCompare.addEventListener('mousemove', (e) => onMapMouseMove(e, mapCanvasCompare));
    mapCanvasCompare.addEventListener('click', onMapClick);
  }
  
  const gmapsBtn = document.getElementById('gmaps-btn');
  if (gmapsBtn) {
      gmapsBtn.addEventListener('click', () => {
          if (!lastRouteCoordinates || lastRouteCoordinates.length < 2) {
              showNotification('Compute a route first');
              return;
          }
          const [origin, ...rest] = lastRouteCoordinates;
          const destination = rest[rest.length - 1];
          const waypoints = rest.slice(0, -1);
          const params = new URLSearchParams({
              api: '1',
              travelmode: 'driving',
              origin: `${origin.lat},${origin.lng}`,
              destination: `${destination.lat},${destination.lng}`,
          });
          if (waypoints.length) {
              params.set('waypoints', waypoints.map((point) => `${point.lat},${point.lng}`).join('|'));
          }
          window.open(`https://www.google.com/maps/dir/?${params.toString()}`, '_blank');
      });
  }
}

function getCompareRouteForMaps(compareResult) {
  const preferredOrder = [compareResult.winner, 'astar', 'dijkstra'];
  for (const key of preferredOrder) {
    if (!key || key === 'tie') continue;
    const route = compareResult[key];
    if (route?.path_coordinates?.length > 1) {
      return route.path_coordinates;
    }
  }
  return [];
}

function setComparisonMode(enabled) {
    comparisonMode = enabled;
    const rightPane = document.getElementById('compare-pane');
    const leftTitle = document.getElementById('canvas-title-left');
    const mapWrapper = document.getElementById('map-container-wrapper');
    const dashBody = document.querySelector('.dash-body');
    const outputPanel = document.getElementById('output-panel');
    const compareBtn = document.getElementById('compare-btn');

    if (enabled) {
        if (document.getElementById('comparison-summary-banner')) document.getElementById('comparison-summary-banner').style.display = 'block';
        rightPane.style.display = 'flex';
        leftTitle.style.display = 'block';
        mapWrapper.classList.add('comparison-active');
        if (dashBody) dashBody.style.gridTemplateColumns = '320px 1fr';
        if (outputPanel) outputPanel.style.display = 'none';
        if (compareBtn) {
            compareBtn.innerHTML = '<span style="color: #fff;">❌ Exit Comparison</span>';
            compareBtn.style.background = 'var(--secondary)';
            compareBtn.style.borderColor = 'var(--secondary)';
            compareBtn.style.boxShadow = '0 0 20px rgba(122, 0, 255, 0.4)';
        }
    } else {
        if (document.getElementById('comparison-summary-banner')) document.getElementById('comparison-summary-banner').style.display = 'none';
        rightPane.style.display = 'none';
        leftTitle.style.display = 'none';
        mapWrapper.classList.remove('comparison-active');
        if (dashBody) dashBody.style.gridTemplateColumns = '320px 1fr 320px';
        if (outputPanel) outputPanel.style.display = 'block';
        if (compareBtn) {
            compareBtn.innerHTML = '<span style="color: var(--secondary);">⚔️ Compare Dijkstra vs A*</span>';
            compareBtn.style.background = 'transparent';
            compareBtn.style.borderColor = 'var(--secondary)';
            compareBtn.style.boxShadow = 'none';
        }
    }
    // Small delay ensures layout updates before resizing canvases
    setTimeout(() => {
        resizeMap();
        generateCurves();
    }, 10);
}

function onMapMouseMove(e, canvas) {
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const w = canvas.width, h = canvas.height;

  hoveredNode = null;
  for (const node of cityNodes) {
    const nx = nodeX(node, w);
    const ny = nodeY(node, h);
    if (Math.hypot(mx - nx, my - ny) < 28) {
      hoveredNode = node.id;
      canvas.style.cursor = 'pointer';
      
      // Sync cursor with other canvas
      if (canvas === mapCanvas && mapCanvasCompare) mapCanvasCompare.style.cursor = 'pointer';
      if (canvas === mapCanvasCompare && mapCanvas) mapCanvas.style.cursor = 'pointer';
      break;
    }
  }
  if (!hoveredNode) {
      canvas.style.cursor = 'default';
      if (canvas === mapCanvas && mapCanvasCompare) mapCanvasCompare.style.cursor = 'default';
      if (canvas === mapCanvasCompare && mapCanvas) mapCanvas.style.cursor = 'default';
  }
}

function onMapClick() {
  if (!hoveredNode) return;
  const srcSelect = document.getElementById('source-select');
  const dstSelect = document.getElementById('dest-select');
  if (!srcSelect.value || srcSelect.value === '' || (srcSelect.value && dstSelect.value)) {
    srcSelect.value = hoveredNode;
    dstSelect.value = '';
  } else {
    dstSelect.value = hoveredNode;
  }
}

function updateEdgeTraffic() {
  cityEdges.forEach((edge) => {
    const flow = edge.trafficData?.[currentTimePeriod] ?? 0;
    edge.traffic = edge.capacity > 0 ? Math.min(1.5, flow / edge.capacity) : 0;
  });
}

function updateRoadFromTraffic() {
  if (!cityEdges.length) return;
  const avg = cityEdges.reduce((s, e) => s + (e.traffic || 0.3), 0) / cityEdges.length;
  if (avg > 0.65) setRoadState('heavy');
  else if (avg > 0.4) setRoadState('moderate');
  else setRoadState('optimal');
}

// ── Routing Algorithms ──────────────────────────────────
async function fetchRoute(sourceId, destId, mode) {
  const endpoint = mode === 'emergency' ? '/route/emergency' : '/route/dijkstra';
  return apiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify({
      source: sourceId,
      destination: destId,
      time_period: currentTimePeriod,
      mode,
    }),
  });
}

async function runPrediction() {
  const source = document.getElementById('ai-source-select')?.value;
  const destination = document.getElementById('ai-dest-select')?.value;
  const horizon = Number(document.getElementById('ai-horizon-select')?.value || 30);
  const placeholder = document.getElementById('ai-placeholder');
  const output = document.getElementById('ai-output');

  if (!source || !destination || source === destination) {
    showNotification('Pick different AI origin and destination');
    return;
  }

  try {
    showNotification('Running ML Analysis...');
    const result = await apiRequest('/ml/predict', {
      method: 'POST',
      body: JSON.stringify({
        source,
        destination,
        time_period: currentTimePeriod,
        prediction_horizon: horizon,
      }),
    });

    if (placeholder) placeholder.style.display = 'none';
    if (output) {
      output.style.display = 'block';
      gsap.fromTo(output, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' });
    }

    const congestionEl = document.getElementById('ai-congestion-val');
    const delayEl = document.getElementById('ai-time-val');
    const analysisEl = document.getElementById('ai-analysis-text');
    const recommendationEl = document.getElementById('ai-rec-text');

    if (congestionEl) congestionEl.textContent = result.predicted_congestion;
    if (delayEl) delayEl.textContent = `+${Math.round(result.recommended_delay)} Mins`;
    if (analysisEl) {
      const finalTrend = result.trend_data[result.trend_data.length - 1];
      analysisEl.textContent = `Forecast score ${result.forecast_score} at ${finalTrend?.horizon_minutes || horizon} minutes for the selected corridor.`;
    }
    if (recommendationEl) {
      const altNames = (result.suggested_alternative || []).map((nodeId) => getNodeById(nodeId)?.label || nodeId);
      recommendationEl.textContent = `Suggested alternative: ${altNames.join(' -> ')}.`;
    }
  } catch (error) {
    showNotification(error.message || 'Prediction failed');
  }
}

async function calculateRoute() {
  const source = document.getElementById('source-select')?.value;
  const dest = document.getElementById('dest-select')?.value;
  const mode = document.getElementById('mode-select')?.value || 'normal';

  if (!source || !dest || source === dest) {
    showNotification('Please select different source and destination');
    return;
  }

  mstEdges = [];
  dpNodes = [];
  lastRouteCoordinates = [];

  try {
    await syncHealthStatus();
    currentTrafficMode = mode;

    const gmapsBtn = document.getElementById('gmaps-btn');
    if (gmapsBtn) gmapsBtn.style.display = 'none';

    if (comparisonMode) {
      const compareResult = await apiRequest('/route/compare', {
        method: 'POST',
        body: JSON.stringify({
          source,
          destination: dest,
          time_period: currentTimePeriod,
          mode,
        }),
      });
      currentPath = compareResult.astar.path || [];
      currentPathCompare = compareResult.dijkstra.path || [];
      lastRouteCoordinates = getCompareRouteForMaps(compareResult);
      if (gmapsBtn) gmapsBtn.style.display = lastRouteCoordinates.length > 1 ? 'block' : 'none';
      displayResults(compareResult.dijkstra, mode, compareResult.astar, compareResult.winner);
      animatePath();
      if (mode !== 'emergency') updateRoadFromTraffic();
      return;
    }

    if (currentAlgorithm === 'dijkstra') {
      const result = await fetchRoute(source, dest, mode);
      currentPath = result.path || [];
      currentPathCompare = [];
      lastRouteCoordinates = result.path_coordinates || [];
      if (gmapsBtn) gmapsBtn.style.display = lastRouteCoordinates.length > 1 ? 'block' : 'none';
      displayResults(result, mode);
      animatePath();
    } else if (currentAlgorithm === 'greedy') {
      const [routeResult, greedyResult] = await Promise.all([
        fetchRoute(source, dest, mode),
        apiRequest('/traffic/optimize', {
          method: 'POST',
          body: JSON.stringify({
            time_period: currentTimePeriod,
            source,
            destination: dest,
            mode,
          }),
        }),
      ]);
      currentPath = routeResult.path || [];
      currentPathCompare = [];
      lastRouteCoordinates = routeResult.path_coordinates || [];
      if (gmapsBtn) gmapsBtn.style.display = lastRouteCoordinates.length > 1 ? 'block' : 'none';
      displayResults({
        ...routeResult,
        metadata: {
          ...(routeResult.metadata || {}),
          greedy: greedyResult,
        },
      }, mode);
      showNotification(`Traffic optimization improved throughput by ${greedyResult.improvement_percent.toFixed(1)}%`);
      animatePath();
    } else if (currentAlgorithm === 'prim') {
      const mstResult = await apiRequest('/mst');
      currentPath = [];
      currentPathCompare = [];
      mstEdges = mstResult.edges.map((edge) => ({ from: edge.source, to: edge.target }));
      displayResults({
        path: [],
        distance: mstResult.total_cost,
        travel_time: 0,
        runtime_ms: 0,
        nodes_explored: mstResult.nodes_connected,
        traffic_level: 'low',
        steps: mstResult.critical_facilities.map((name) => ({ target_name: name })),
        metadata: { mst: mstResult },
      }, mode);
      showNotification('Infrastructure expansion plan loaded');
    } else if (currentAlgorithm === 'dp') {
      const transitResult = await apiRequest('/transit/optimize', {
        method: 'POST',
        body: JSON.stringify({
          time_period: currentTimePeriod,
          capacity: 8,
        }),
      });
      currentPath = [];
      currentPathCompare = [];
      dpNodes = Object.keys(transitResult.schedule)
        .flatMap((key) => key.split('-'))
        .filter((nodeId, index, arr) => getNodeById(nodeId) && arr.indexOf(nodeId) === index);
      displayResults({
        path: [],
        distance: 0,
        travel_time: 0,
        runtime_ms: transitResult.optimization_metrics.total_cost || 0,
        nodes_explored: transitResult.optimization_metrics.combined_passengers_covered || 0,
        traffic_level: 'low',
        steps: Object.entries(transitResult.schedule).map(([busId, times]) => ({
          source_name: busId,
          target_name: Array.isArray(times) ? times.join(', ') : String(times),
        })),
        metadata: { transit: transitResult },
      }, mode);
      showNotification('Transit optimization completed');
    }

    if (mode !== 'emergency') updateRoadFromTraffic();
  } catch (error) {
    currentPath = [];
    currentPathCompare = [];
    showNotification(error.message || 'Route request failed');
  }
}

function displayResults(result, mode, compareResult = null, winner = null) {
  const isSpecial = currentAlgorithm === 'prim' || currentAlgorithm === 'dp';
  const totalTime = Number(result.travel_time || 0);
  const distKm = Number(result.distance || 0);
  const trafficLevel = result.traffic_level || 'low';
  const trafficLabels = { low: 'Low Traffic', medium: 'Moderate', high: 'Heavy', severe: 'Severe' };

  const etaEl = document.getElementById('stat-eta');
  const distEl = document.getElementById('stat-distance');
  const stopsEl = document.getElementById('stat-stops');
  const trafficEl = document.getElementById('stat-traffic');
  const runtimeEl = document.getElementById('stat-runtime');
  const exploredEl = document.getElementById('stat-explored');
  const routeStepsEl = document.getElementById('route-steps');

  if (etaEl) animateValue(etaEl, 0, totalTime, 900, ' min');
  if (distEl) animateValue(distEl, 0, distKm, 900, isSpecial ? '' : ' km');
  if (stopsEl) stopsEl.textContent = result.path ? Math.max(0, result.path.length - 2) + ' stops' : '--';

  if (trafficEl) {
    const bar = trafficEl.querySelector('.traffic-bar');
    const label = trafficEl.querySelector('.traffic-label');
    if (bar) {
      bar.className = 'traffic-bar traffic-' + (trafficLevel === 'severe' ? 'high' : trafficLevel);
      bar.style.width = `${Math.min(100, getPathTraffic(result.path || []) * 100)}%`;
    }
    if (label) label.textContent = trafficLabels[trafficLevel] || trafficLevel;
  }
  
  if (runtimeEl) {
      if (compareResult) {
          runtimeEl.innerHTML = `Dijkstra: ${result.runtime_ms}ms<br/><span style="color:var(--success)">A*: ${compareResult.runtime_ms}ms</span>`;
      } else {
          animateValue(runtimeEl, 0, Number(result.runtime_ms || 0), 900, ' ms');
      }
  }
  if (exploredEl) {
      if (compareResult) {
          exploredEl.innerHTML = `Dijkstra: ${result.nodes_explored}<br/><span style="color:var(--success)">A*: ${compareResult.nodes_explored}</span>`;
      } else {
          animateValue(exploredEl, 0, Number(result.nodes_explored || 0), 900, '');
      }
  }

  // Populate comparison specific cards
  if (compareResult) {
      // A* is compareResult, Dijkstra is result
      document.getElementById('comp-astar-time').textContent = compareResult.runtime_ms + ' ms';
      document.getElementById('comp-astar-nodes').textContent = compareResult.nodes_explored;
      document.getElementById('comp-astar-dist').textContent = compareResult.distance + ' km';
      document.getElementById('comp-astar-eta').textContent = compareResult.travel_time + ' min';

      document.getElementById('comp-dij-time').textContent = result.runtime_ms + ' ms';
      document.getElementById('comp-dij-nodes').textContent = result.nodes_explored;
      document.getElementById('comp-dij-dist').textContent = distKm + ' km';
      document.getElementById('comp-dij-eta').textContent = totalTime + ' min';

      document.getElementById('astar-winner').style.display = 'inline-block';
      document.getElementById('dijkstra-winner').style.display = 'none';
  }

  if (routeStepsEl) {
    routeStepsEl.innerHTML = '';
    const steps = result.steps || [];
    steps.forEach((stepData, i) => {
      const step = document.createElement('div');
      step.className = 'route-step';
      let label = stepData.target_name || stepData.source_name || 'Step';
      if (stepData.source_name && stepData.target_name && stepData.source_name !== stepData.target_name) {
        label = `${stepData.source_name} → ${stepData.target_name}`;
      }
      const dotClass = i === 0 ? 'step-dot start' : i === steps.length - 1 ? 'step-dot end' : 'step-dot';
      step.innerHTML = `<span class="${dotClass}"></span><span>${label}</span>`;
      routeStepsEl.appendChild(step);
      gsap.fromTo(step, { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.5, delay: i * 0.12, ease: 'power3.out' });
    });
  }

  const modeBadge = document.getElementById('mode-badge');
  if (modeBadge) {
    let modeText = mode === 'emergency' ? '🚨 EMERGENCY' : '🚗 NORMAL';
    if (currentAlgorithm === 'prim') modeText = '🏗️ MST PLANNING';
    if (currentAlgorithm === 'dp') modeText = '⏱️ TRANSIT OPT';
    if (currentAlgorithm === 'greedy') modeText = '🚦 TRAFFIC OPT';
    
    modeBadge.textContent = modeText;
    modeBadge.style.color = mode === 'emergency' ? 'var(--accent)' : 'var(--primary)';
  }
}

function getPathTraffic(path) {
  let total = 0, count = 0;
  for (let i = 0; i < path.length - 1; i++) {
    const edge = cityEdges.find(e =>
      (e.from === path[i] && e.to === path[i + 1]) || (e.to === path[i] && e.from === path[i + 1])
    );
    if (edge) { total += edge.traffic || 0.3; count++; }
  }
  return count > 0 ? total / count : 0.3;
}

function animateValue(el, start, end, duration, suffix = '') {
  const startTime = performance.now();
  const isFloat = !Number.isInteger(end);
  function step(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = start + (end - start) * eased;
    el.textContent = (isFloat ? current.toFixed(1) : Math.round(current)) + suffix;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function animatePath() {
  pathAnimProgress = 0;
  if (pathAnimId) cancelAnimationFrame(pathAnimId);
  function tick() {
    pathAnimProgress += 0.008;
    if (pathAnimProgress > 1) pathAnimProgress = 1;
    if (pathAnimProgress < 1) pathAnimId = requestAnimationFrame(tick);
  }
  pathAnimId = requestAnimationFrame(tick);

  // Create flowing route particles
  createRouteFlowParticles();
}

function createRouteFlowParticles() {
  routeFlowParticles = [];
  if (currentPath.length < 2) return;
  for (let i = 0; i < 6; i++) {
    routeFlowParticles.push({
      progress: i / 6,
      speed: 0.003 + Math.random() * 0.001,
      size: 3 + Math.random() * 2,
      opacity: 0.6 + Math.random() * 0.4,
    });
  }
}

function createTrafficParticles() {
  trafficParticles = [];
  cityEdges.forEach((edge) => {
    const t = edge.traffic || 0.3;
    const count = Math.floor(t * 3) + 1;
    for (let i = 0; i < count; i++) {
      trafficParticles.push({
        edge,
        progress: Math.random(),
        speed: 0.001 + Math.random() * 0.002,
        reverse: Math.random() > 0.5,
      });
    }
  });
}

function getActiveEdgeKeys() {
  const keys = new Set();
  const paths = [currentPath, currentPathCompare];
  paths.forEach((path) => {
    for (let i = 0; i < path.length - 1; i++) {
      keys.add(getEdgeKey(path[i], path[i + 1]));
    }
  });
  return keys;
}

function drawCityAura(ctx, w, h) {
  const fields = [
    { x: 0.18, y: 0.38, radius: 0.28, color: '0,195,255', alpha: 0.09 },
    { x: 0.48, y: 0.46, radius: 0.25, color: '122,0,255', alpha: 0.07 },
    { x: 0.79, y: 0.36, radius: 0.27, color: '0,195,255', alpha: 0.08 },
    { x: 0.58, y: 0.86, radius: 0.18, color: '255,170,68', alpha: 0.06 },
  ];

  fields.forEach((field) => {
    const gx = field.x * w;
    const gy = field.y * h;
    const gradient = ctx.createRadialGradient(gx, gy, 0, gx, gy, Math.min(w, h) * field.radius);
    gradient.addColorStop(0, `rgba(${field.color}, ${field.alpha})`);
    gradient.addColorStop(0.55, `rgba(${field.color}, ${field.alpha * 0.35})`);
    gradient.addColorStop(1, `rgba(${field.color}, 0)`);
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, w, h);
  });
}

function createLabelPlacement(node, ctx, w, h, fontSize) {
  const pref = getNodeLabelPreference(node);
  const anchorX = nodeX(node, w);
  const anchorY = nodeY(node, h);
  const textX = anchorX + pref.dx;
  const textY = anchorY + pref.dy;
  const width = ctx.measureText(node.label).width;
  const height = fontSize + 8;

  const placement = {
    nodeId: node.id,
    anchorX,
    anchorY,
    textX,
    textY,
    width,
    height,
    align: pref.align,
    baseline: pref.baseline,
    fontSize,
  };
  updateLabelBounds(placement);
  return placement;
}

function updateLabelBounds(placement) {
  let left = placement.textX;
  if (placement.align === 'center') left -= placement.width / 2;
  if (placement.align === 'right') left -= placement.width;

  let top = placement.textY;
  if (placement.baseline === 'alphabetic') top -= placement.height;
  else if (placement.baseline === 'middle') top -= placement.height / 2;

  placement.left = left - 12;
  placement.top = top - 7;
  placement.right = left + placement.width + 12;
  placement.bottom = top + placement.height + 7;
}

function shiftPlacement(placement, dx, dy) {
  placement.textX += dx;
  placement.textY += dy;
  updateLabelBounds(placement);
}

function buildLabelPlacements(ctx, w, h) {
  const cacheKey = `${comparisonMode ? 'compare' : 'single'}:${w}x${h}:${cityNodes.length}`;
  if (labelLayoutCache.has(cacheKey)) {
    return labelLayoutCache.get(cacheKey);
  }

  const fontSize = comparisonMode ? 15 : 13;
  ctx.save();
  ctx.font = `600 ${fontSize}px "Orbitron", monospace`;

  const placements = cityNodes
    .map((node) => createLabelPlacement(node, ctx, w, h, fontSize))
    .sort((a, b) => a.top - b.top);

  const minGap = comparisonMode ? 16 : 12;
  for (let iteration = 0; iteration < 6; iteration++) {
    for (let i = 0; i < placements.length; i++) {
      for (let j = i + 1; j < placements.length; j++) {
        const a = placements[i];
        const b = placements[j];
        const overlapX = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (overlapX > 0 && overlapY > 0) {
          const direction = a.textY <= b.textY ? 1 : -1;
          const push = overlapY / 2 + minGap / 2;
          shiftPlacement(a, 0, -push * direction);
          shiftPlacement(b, 0, push * direction);
        }
      }
    }
  }

  placements.forEach((placement) => {
    const overflowLeft = 18 - placement.left;
    const overflowRight = placement.right - (w - 18);
    const overflowTop = 18 - placement.top;
    const overflowBottom = placement.bottom - (h - 18);
    if (overflowLeft > 0) shiftPlacement(placement, overflowLeft, 0);
    if (overflowRight > 0) shiftPlacement(placement, -overflowRight, 0);
    if (overflowTop > 0) shiftPlacement(placement, 0, overflowTop);
    if (overflowBottom > 0) shiftPlacement(placement, 0, -overflowBottom);
  });

  const placementMap = new Map(placements.map((placement) => [placement.nodeId, placement]));
  ctx.restore();
  labelLayoutCache.set(cacheKey, placementMap);
  return placementMap;
}

// ══════════════════════════════════════════════
// MAP RENDER — IMPROVED
// ══════════════════════════════════════════════
function startMapLoop() {
  function draw() {
    requestAnimationFrame(draw);
    if (!mapCtx || !mapCanvas.width) return;
    
    // Draw Left Canvas (Dijkstra/Normal)
    renderCanvas(mapCanvas, mapCtx, currentPath, true);
    
    // Draw Right Canvas if Comparison Mode
    if (comparisonMode && mapCanvasCompare && mapCanvasCompare.width) {
        renderCanvas(mapCanvasCompare, mapCtxCompare, currentPathCompare, false);
    }
  }
  requestAnimationFrame(draw);
}

function renderCanvas(canvas, ctx, path, isLeft) {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    drawCityAura(ctx, w, h);
    drawGrid(ctx, w, h);
    
    if (currentAlgorithm === 'prim') {
        drawMSTEdges(ctx, w, h);
    } else {
        drawEdges(ctx, w, h);
        drawTrafficParticles(ctx, w, h);
        drawPath(ctx, w, h, path);
        if (isLeft || comparisonMode) drawRouteFlow(ctx, w, h, path);
    }
    
    drawNodes(ctx, w, h, path);
    
    if (currentAlgorithm === 'dp') {
        drawDPNodes(ctx, w, h);
    }
}

function drawGrid(ctx, w, h) {
  ctx.strokeStyle = 'rgba(0, 195, 255, 0.018)';
  ctx.lineWidth = 0.6;
  const spacing = comparisonMode ? 52 : 46;
  for (let x = 0; x < w; x += spacing) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }
  for (let y = 0; y < h; y += spacing) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }
}

// ── EDGES — same smooth curves for background ──
function drawEdges(ctx, w, h) {
  const activeEdgeKeys = getActiveEdgeKeys();
  const hasActiveRoute = activeEdgeKeys.size > 0;

  cityEdges.forEach((edge) => {
    const curve = edgeCurves.get(`${edge.from}_${edge.to}`);
    if (!curve) return;
    
    const points = getCurvePointsAbs(curve, w, h);
    if (!points || points.length === 0) return;

    const t = currentAlgorithm === 'greedy' ? (edge.traffic || 0.3) * 1.5 : (edge.traffic || 0.3); // Exaggerate greedy
    const isRouteEdge = activeEdgeKeys.has(getEdgeKey(edge.from, edge.to));
    const dimMultiplier = hasActiveRoute && !isRouteEdge ? 0.45 : 1;
    const glowBoost = isRouteEdge ? 1.25 : 1;
    let r, g, b;
    if (t < 0.5) {
      r = Math.round(t * 2 * 255);
      g = Math.round(200 + (1 - t * 2) * 55);
      b = Math.round((1 - t * 2) * 136);
    } else {
      r = 255;
      g = Math.round((1 - (t - 0.5) * 2) * 200);
      b = 50;
    }

    // Outer glow
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${(0.04 + t * 0.05) * dimMultiplier * glowBoost})`;
    ctx.lineWidth = (5 + t * 3.5) * (isRouteEdge ? 1.05 : 1);
    ctx.lineCap = 'round';
    ctx.stroke();

    // Main edge
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${(0.14 + t * 0.16) * dimMultiplier * glowBoost})`;
    ctx.lineWidth = (1.2 + t * 1.5) * (isRouteEdge ? 1.2 : 1);
    ctx.lineCap = 'round';
    ctx.stroke();
  });
}

function drawMSTEdges(ctx, w, h) {
    mstEdges.forEach((edge) => {
        const curve = edgeCurves.get(`${edge.from}_${edge.to}`);
        let points = curve ? getCurvePointsAbs(curve, w, h) : null;
        if (!points || points.length === 0) {
            const from = getNodeById(edge.from);
            const to = getNodeById(edge.to);
            if (!from || !to) return;
            points = [
                { x: nodeX(from, w), y: nodeY(from, h) },
                { x: nodeX(to, w), y: nodeY(to, h) }
            ];
        }

        // Draw structural beams
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.strokeStyle = `rgba(255, 170, 0, 0.4)`;
        ctx.lineWidth = 4;
        ctx.lineCap = 'square';
        ctx.setLineDash([10, 5]);
        ctx.stroke();
        ctx.setLineDash([]);
        
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.strokeStyle = `rgba(255, 200, 0, 0.8)`;
        ctx.lineWidth = 1;
        ctx.stroke();
    });
}

// ── PATH — same geometry as background edges ──
function drawPath(ctx, w, h, path) {
  if (path.length < 2) return;

  const isEmergency = currentTrafficMode === 'emergency';
  const pathColor = isEmergency ? '#ff3b3b' : '#00c3ff';
  const glowColor = isEmergency ? 'rgba(255,59,59,' : 'rgba(0,195,255,';

  const totalSegments = path.length - 1;
  const animSeg = pathAnimProgress * totalSegments;

  for (let i = 0; i < totalSegments; i++) {
    if (i > animSeg) break;

    const fromId = path[i];
    const toId = path[i + 1];
    
    let curve = edgeCurves.get(`${fromId}_${toId}`) || edgeCurves.get(`${toId}_${fromId}`);
    if (!curve) continue;

    const isReverse = !edgeCurves.has(`${fromId}_${toId}`);
    const segT = Math.min(1, animSeg - i);
    
    const pointsAbs = getCurvePointsAbs(curve, w, h);
    if (!pointsAbs || pointsAbs.length === 0) continue;

    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    const drawCurvePath = (glow, width) => {
      ctx.beginPath();
      const startP = isReverse ? pointsAbs[pointsAbs.length - 1] : pointsAbs[0];
      ctx.moveTo(startP.x, startP.y);

      if (segT >= 1) {
        if (isReverse) {
          for (let j = pointsAbs.length - 2; j >= 0; j--) ctx.lineTo(pointsAbs[j].x, pointsAbs[j].y);
        } else {
          for (let j = 1; j < pointsAbs.length; j++) ctx.lineTo(pointsAbs[j].x, pointsAbs[j].y);
        }
      } else {
        const endP = getCurvePointAbs(curve, isReverse ? (1 - segT) : segT, w, h);
        const segmentSplit = Math.floor((pointsAbs.length - 1) * segT);
        
        if (isReverse) {
          for (let j = 1; j <= segmentSplit; j++) {
            const idx = pointsAbs.length - 1 - j;
            ctx.lineTo(pointsAbs[idx].x, pointsAbs[idx].y);
          }
        } else {
          for (let j = 1; j <= segmentSplit; j++) ctx.lineTo(pointsAbs[j].x, pointsAbs[j].y);
        }
        ctx.lineTo(endP.x, endP.y);
      }
      ctx.strokeStyle = glow;
      ctx.lineWidth = width;
      ctx.stroke();
    };

    drawCurvePath(glowColor + '0.06)', 22);
    drawCurvePath(glowColor + '0.2)', 8);
    drawCurvePath(pathColor, 3);
  }
}

// ── ROUTE FLOW ──
function drawRouteFlow(ctx, w, h, path) {
  if (path.length < 2 || pathAnimProgress < 1 || routeFlowParticles.length === 0) return;

  const isEmergency = currentTrafficMode === 'emergency';
  const dotColor = isEmergency ? '#ff3b3b' : '#00c3ff';
  const glowColor = isEmergency ? 'rgba(255,59,59,' : 'rgba(0,195,255,';

  const totalSegments = path.length - 1;

  routeFlowParticles.forEach((fp) => {
    // Only update progress on primary canvas call to avoid double speed
    if (ctx === mapCtx) {
       fp.progress += fp.speed;
       if (fp.progress > 1) fp.progress -= 1;
    }

    const pathT = fp.progress * totalSegments;
    const seg = Math.floor(pathT);
    const segT = pathT - seg;

    if (seg >= totalSegments) return;

    const fromId = path[seg];
    const toId = path[seg + 1];

    let curve = edgeCurves.get(`${fromId}_${toId}`) || edgeCurves.get(`${toId}_${fromId}`);
    if (!curve) return;

    const isReverse = !edgeCurves.has(`${fromId}_${toId}`);
    const realSegT = isReverse ? (1 - segT) : segT;
    
    const p = getCurvePointAbs(curve, realSegT, w, h);
    const tangent = curve.getTangent(realSegT);

    const pulse = 1 + Math.sin(performance.now() * 0.01 + fp.progress * 10) * 0.1;

    ctx.save();
    ctx.translate(p.x, p.y);
    
    let angle = Math.atan2(tangent.y, tangent.x);
    if (isReverse) angle += Math.PI; 
    ctx.rotate(angle);
    
    const gradient = ctx.createLinearGradient(-fp.size * 6, 0, 0, 0);
    gradient.addColorStop(0, glowColor + '0)');
    gradient.addColorStop(1, glowColor + (fp.opacity * 0.4 * pulse).toFixed(3) + ')');
    
    ctx.beginPath();
    ctx.fillStyle = gradient;
    ctx.roundRect(-fp.size * 8 * pulse, -fp.size * 0.8, fp.size * 8 * pulse, fp.size * 1.6, fp.size);
    ctx.fill();

    ctx.beginPath();
    ctx.arc(0, 0, fp.size * pulse, 0, Math.PI * 2);
    ctx.fillStyle = dotColor;
    ctx.shadowColor = dotColor;
    ctx.shadowBlur = 15;
    ctx.globalAlpha = fp.opacity;
    ctx.fill();
    
    ctx.restore();
    ctx.shadowBlur = 0;
    ctx.globalAlpha = 1;
  });
}

// ── Traffic Particles ─────────────────────────
function drawTrafficParticles(ctx, w, h) {
  const activeEdgeKeys = getActiveEdgeKeys();
  const hasActiveRoute = activeEdgeKeys.size > 0;

  trafficParticles.forEach((tp) => {
    // only update progress on main draw loop
    if (ctx === mapCtx) {
       tp.progress += tp.speed * (tp.reverse ? -1 : 1);
       if (tp.progress > 1 || tp.progress < 0) {
         tp.reverse = !tp.reverse;
         tp.progress = Math.max(0, Math.min(1, tp.progress));
       }
    }

    const fromId = tp.edge.from;
    const toId = tp.edge.to;
    const curve = edgeCurves.get(`${fromId}_${toId}`);
    if (!curve) return;

    const p = getCurvePointAbs(curve, tp.progress, w, h);

    const t = tp.edge.traffic || 0.3;
    const isRouteEdge = activeEdgeKeys.has(getEdgeKey(tp.edge.from, tp.edge.to));
    const opacityMultiplier = hasActiveRoute && !isRouteEdge ? 0.45 : 1;
    const color = t > 0.65
      ? `rgba(255, 80, 50, ${(0.25 + tp.progress * 0.25) * opacityMultiplier})`
      : t > 0.4
        ? `rgba(255, 200, 50, ${(0.25 + tp.progress * 0.25) * opacityMultiplier})`
        : `rgba(0, 255, 136, ${(0.25 + tp.progress * 0.25) * opacityMultiplier})`;

    ctx.beginPath();
    ctx.arc(p.x, p.y, isRouteEdge ? 2.5 : 2.0, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  });
}

function drawDPNodes(ctx, w, h) {
    dpNodes.forEach((nodeId) => {
        const node = cityNodes.find(n => n.id === nodeId);
        if (!node) return;
        const x = nodeX(node, w);
        const y = nodeY(node, h);
        
        const pulse = 0.5 + Math.sin(performance.now() * 0.005) * 0.5;
        ctx.beginPath();
        ctx.arc(x, y, 30 + pulse * 10, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(122, 0, 255, ${0.2 - pulse * 0.1})`;
        ctx.lineWidth = 2;
        ctx.stroke();
    });
}

// ── NODES — bigger, with halos + labels ───────
function drawNodes(ctx, w, h, path) {
  const labelPlacements = buildLabelPlacements(ctx, w, h);

  cityNodes.forEach((node) => {
    const x = nodeX(node, w);
    const y = nodeY(node, h);
    const isActive = path.includes(node.id) || mstEdges.some(e => e.from===node.id || e.to===node.id);
    const isHovered = hoveredNode === node.id;
    const isStart = path.length > 0 && path[0] === node.id;
    const isEnd = path.length > 0 && path[path.length - 1] === node.id;
    const placement = labelPlacements.get(node.id);
    const nodeColor = isStart
      ? '#00ff88'
      : isEnd
        ? '#ff3b3b'
        : isActive
          ? '#00c3ff'
          : TYPE_COLORS[node.type] || 'rgba(255,255,255,0.85)';

    // Outer halo
    ctx.beginPath();
    ctx.arc(x, y, isHovered ? 28 : 24, 0, Math.PI * 2);
    if (isStart) ctx.fillStyle = 'rgba(0, 255, 136, 0.08)';
    else if (isEnd) ctx.fillStyle = 'rgba(255, 59, 59, 0.08)';
    else if (isActive) ctx.fillStyle = 'rgba(0, 195, 255, 0.08)';
    else if (isHovered) ctx.fillStyle = 'rgba(122, 0, 255, 0.1)';
    else ctx.fillStyle = node.type === 'hospital' ? 'rgba(255, 90, 90, 0.06)' : 'rgba(255, 255, 255, 0.025)';
    ctx.fill();

    // Pulse ring
    if (isActive || isHovered) {
      const pulse = 0.5 + Math.sin(performance.now() * 0.004) * 0.4;
      ctx.beginPath();
      ctx.arc(x, y, 28 + pulse * 6, 0, Math.PI * 2);
      ctx.strokeStyle = isStart ? `rgba(0, 255, 136, ${pulse * 0.2})`
        : isEnd ? `rgba(255, 59, 59, ${pulse * 0.2})`
        : `rgba(0, 195, 255, ${pulse * 0.2})`;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Node dot
    const radius = isHovered ? 11.5 : isActive ? 9.5 : 7.5;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = nodeColor;
    ctx.shadowColor = nodeColor;
    ctx.shadowBlur = isStart || isEnd ? 28 : isActive ? 24 : isHovered ? 18 : 10;
    ctx.fill();
    ctx.shadowBlur = 0;

    ctx.beginPath();
    ctx.arc(x, y, Math.max(2.8, radius * 0.38), 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.globalAlpha = isHovered || isActive ? 0.95 : 0.75;
    ctx.fill();
    ctx.globalAlpha = 1;

    if (!placement) return;

    // Connector line
    const pillAnchorX = placement.align === 'left'
      ? placement.left + 12
      : placement.align === 'right'
        ? placement.right - 12
        : (placement.left + placement.right) / 2;
    const pillAnchorY = placement.textY + (placement.baseline === 'alphabetic' ? -placement.height / 2 + 3 : placement.baseline === 'middle' ? 0 : placement.height / 2 - 3);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo((x + pillAnchorX) / 2, (y + pillAnchorY) / 2);
    ctx.lineTo(pillAnchorX, pillAnchorY);
    ctx.strokeStyle = isActive || isHovered ? 'rgba(0, 195, 255, 0.28)' : 'rgba(255, 255, 255, 0.12)';
    ctx.lineWidth = isActive || isHovered ? 1.4 : 1;
    ctx.stroke();

    // Label capsule
    const labelWidth = placement.right - placement.left;
    const labelHeight = placement.bottom - placement.top;
    ctx.beginPath();
    ctx.roundRect(placement.left, placement.top, labelWidth, labelHeight, 12);
    ctx.fillStyle = isHovered
      ? 'rgba(14, 18, 34, 0.92)'
      : isActive
        ? 'rgba(8, 14, 24, 0.84)'
        : 'rgba(7, 10, 18, 0.76)';
    ctx.fill();
    ctx.strokeStyle = isStart
      ? 'rgba(0,255,136,0.4)'
      : isEnd
        ? 'rgba(255,59,59,0.42)'
        : isActive
          ? 'rgba(0,195,255,0.35)'
          : 'rgba(255,255,255,0.08)';
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.font = `600 ${placement.fontSize}px "Orbitron", monospace`;
    ctx.textAlign = placement.align;
    ctx.textBaseline = placement.baseline;
    ctx.fillStyle = isActive ? '#8fe8ff' : isHovered ? '#ffffff' : 'rgba(224, 230, 240, 0.88)';
    ctx.fillText(node.label, placement.textX, placement.textY);

    if (isHovered) {
      const chipText = node.type.toUpperCase();
      ctx.font = '600 9px "Inter", sans-serif';
      const chipWidth = ctx.measureText(chipText).width + 14;
      const chipX = placement.left + 10;
      const chipY = placement.top - 18;
      ctx.beginPath();
      ctx.roundRect(chipX, chipY, chipWidth, 16, 8);
      ctx.fillStyle = 'rgba(0, 195, 255, 0.12)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(0, 195, 255, 0.28)';
      ctx.stroke();
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#bcefff';
      ctx.fillText(chipText, chipX + 7, chipY + 8);
    }
  });
}

// ── Notification ──────────────────────────────
function showNotification(msg) {
  let notif = document.getElementById('notification');
  if (!notif) {
    notif = document.createElement('div');
    notif.id = 'notification';
    notif.style.cssText = `
      position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%) translateY(20px);
      padding: 14px 28px; border-radius: 12px; background: rgba(255,59,59,0.15);
      border: 1px solid rgba(255,59,59,0.3); color: #ff3b3b;
      font-family: 'Orbitron', monospace; font-size: 0.7rem;
      letter-spacing: 2px; text-transform: uppercase; z-index: 10000;
      backdrop-filter: blur(10px); opacity: 0;
    `;
    document.body.appendChild(notif);
  }
  notif.textContent = msg;
  gsap.fromTo(notif,
    { opacity: 0, y: 20 },
    { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out',
      onComplete: () => gsap.to(notif, { opacity: 0, y: -10, delay: 2.5, duration: 0.4 }) }
  );
}

// ══════════════════════════════════════════════
// DASHBOARD TRANSITIONS
// ══════════════════════════════════════════════
export function transitionToDashboard() {
  const intro = document.querySelector('.intro-sections');
  const dashboard = document.getElementById('dashboard');
  const threeCanvas = document.getElementById('three-canvas');
  if (!dashboard) return;

  const tl = gsap.timeline();
  tl.to(intro, { opacity: 0, y: -50, duration: 0.7, ease: 'power3.in', onComplete: () => intro.classList.add('hidden') });
  tl.to(threeCanvas, { opacity: 0, duration: 0.6, ease: 'power2.out' }, '-=0.4');
  tl.call(() => { dashboard.classList.add('active'); initDashboard(); });
  tl.to(dashboard, { opacity: 1, duration: 0.9, ease: 'power3.out' });
  tl.fromTo('.dash-header', { y: -40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }, '-=0.4');
  tl.fromTo('.dash-panel', { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.7, stagger: 0.15, ease: 'power3.out' }, '-=0.3');
  tl.fromTo('.map-container', { scale: 0.95, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.6, ease: 'power3.out' }, '-=0.5');
  return tl;
}

export function transitionToIntro() {
  const intro = document.querySelector('.intro-sections');
  const dashboard = document.getElementById('dashboard');
  const threeCanvas = document.getElementById('three-canvas');
  const tl = gsap.timeline();

  setEmergencyMode(false);
  stopHealthPolling();
  tl.to(dashboard, { opacity: 0, duration: 0.6, ease: 'power3.in', onComplete: () => dashboard.classList.remove('active') });
  tl.call(() => intro.classList.remove('hidden'));
  tl.to(intro, { opacity: 1, y: 0, duration: 0.7, ease: 'power3.out' });
  tl.to(threeCanvas, { opacity: 1, duration: 0.7, ease: 'power2.out' }, '-=0.5');
  return tl;
}
