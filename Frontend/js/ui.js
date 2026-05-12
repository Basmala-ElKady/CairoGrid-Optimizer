/**
 * ui.js
 * ─────────────────────────────────────────────
 * Dashboard: Egyptian city graph with IMPROVED
 * visualization — larger nodes, bezier curves,
 * proper normalization, bigger labels, halos.
 */

import * as THREE from 'three';
import { setMode, setEmergencyMode } from './environment.js';
import { setRoadState } from './three-scene.js';

// ══════════════════════════════════════════════
// EGYPTIAN CITY GRAPH — expanded with new nodes
// ══════════════════════════════════════════════
const cityNodes = [
  { id: 'october',       label: '6th October',       x: 0.05, y: 0.40 },
  { id: 'sheikh_zayed',  label: 'Sheikh Zayed',      x: 0.08, y: 0.25 },
  { id: 'smart_village', label: 'Smart Village',     x: 0.10, y: 0.15 },
  { id: 'mohandessin',   label: 'Mohandessin',       x: 0.35, y: 0.45 },
  { id: 'dokki',         label: 'Dokki',             x: 0.35, y: 0.52 },
  { id: 'giza',          label: 'Giza',              x: 0.32, y: 0.60 },
  { id: 'cairo_univ',    label: 'Cairo University',  x: 0.35, y: 0.57 },
  { id: 'zamalek',       label: 'Zamalek',           x: 0.42, y: 0.48 },
  { id: 'downtown',      label: 'Downtown',          x: 0.48, y: 0.50 },
  { id: 'ramses_station',label: 'Ramses Station',    x: 0.50, y: 0.45 },
  { id: 'egyptian_museum',label:'Egyptian Museum',   x: 0.47, y: 0.52 },
  { id: 'qasr_el_aini',  label: 'Qasr El Aini Hosp', x: 0.45, y: 0.55 },
  { id: 'shubra',        label: 'Shubra',            x: 0.48, y: 0.25 },
  { id: 'heliopolis',    label: 'Heliopolis',        x: 0.65, y: 0.30 },
  { id: 'airport',       label: 'Cairo Int. Airport',x: 0.75, y: 0.20 },
  { id: 'nasr_city',     label: 'Nasr City',         x: 0.65, y: 0.45 },
  { id: 'cairo_stadium', label: 'Cairo Stadium',     x: 0.62, y: 0.40 },
  { id: 'al_azhar',      label: 'Al-Azhar Univ',     x: 0.60, y: 0.48 },
  { id: 'new_cairo',     label: 'New Cairo',         x: 0.85, y: 0.50 },
  { id: 'festival_city', label: 'Cairo Festival City',x: 0.80, y: 0.55 },
  { id: 'al_rehab',      label: 'Al Rehab',          x: 0.88, y: 0.40 },
  { id: 'nac',           label: 'New Admin Capital', x: 0.95, y: 0.60 },
  { id: 'maadi',         label: 'Maadi',             x: 0.55, y: 0.75 },
  { id: 'maadi_military',label: 'Maadi Military Hosp',x:0.57, y: 0.80 },
  { id: 'helwan',        label: 'Helwan',            x: 0.60, y: 0.95 }
];

const cityEdges = [
  // West links
  { from: 'smart_village', to: 'sheikh_zayed',  weight: 5,  morningPeak: 0.4, nightTraffic: 0.1 },
  { from: 'sheikh_zayed',  to: 'october',       weight: 8,  morningPeak: 0.5, nightTraffic: 0.2 },
  { from: 'sheikh_zayed',  to: 'mohandessin',   weight: 12, morningPeak: 0.8, nightTraffic: 0.3 },
  { from: 'october',       to: 'giza',          weight: 15, morningPeak: 0.7, nightTraffic: 0.2 },

  // West/Central
  { from: 'mohandessin',   to: 'dokki',         weight: 3,  morningPeak: 0.8, nightTraffic: 0.4 },
  { from: 'dokki',         to: 'cairo_univ',    weight: 2,  morningPeak: 0.9, nightTraffic: 0.3 },
  { from: 'cairo_univ',    to: 'giza',          weight: 2,  morningPeak: 0.8, nightTraffic: 0.4 },
  { from: 'mohandessin',   to: 'zamalek',       weight: 4,  morningPeak: 0.7, nightTraffic: 0.3 },
  { from: 'dokki',         to: 'qasr_el_aini',  weight: 3,  morningPeak: 0.9, nightTraffic: 0.4 },

  // Zamalek
  { from: 'zamalek',       to: 'downtown',      weight: 3,  morningPeak: 0.8, nightTraffic: 0.5 },

  // Central Hubs
  { from: 'downtown',      to: 'ramses_station',weight: 2,  morningPeak: 0.9, nightTraffic: 0.6 },
  { from: 'downtown',      to: 'egyptian_museum',weight:1,  morningPeak: 0.8, nightTraffic: 0.4 },
  { from: 'egyptian_museum',to: 'qasr_el_aini', weight: 2,  morningPeak: 0.7, nightTraffic: 0.3 },
  { from: 'ramses_station',to: 'shubra',        weight: 4,  morningPeak: 0.8, nightTraffic: 0.5 },

  // East paths
  { from: 'ramses_station',to: 'cairo_stadium', weight: 6,  morningPeak: 0.7, nightTraffic: 0.3 },
  { from: 'downtown',      to: 'al_azhar',      weight: 5,  morningPeak: 0.9, nightTraffic: 0.4 },
  { from: 'cairo_stadium', to: 'heliopolis',    weight: 4,  morningPeak: 0.7, nightTraffic: 0.2 },
  { from: 'cairo_stadium', to: 'nasr_city',     weight: 3,  morningPeak: 0.8, nightTraffic: 0.3 },
  { from: 'al_azhar',      to: 'nasr_city',     weight: 4,  morningPeak: 0.9, nightTraffic: 0.4 },

  // North-East
  { from: 'shubra',        to: 'heliopolis',    weight: 8,  morningPeak: 0.8, nightTraffic: 0.4 },
  { from: 'heliopolis',    to: 'airport',       weight: 5,  morningPeak: 0.6, nightTraffic: 0.2 },
  { from: 'nasr_city',     to: 'airport',       weight: 7,  morningPeak: 0.7, nightTraffic: 0.2 },

  // Deep East
  { from: 'nasr_city',     to: 'new_cairo',     weight: 9,  morningPeak: 0.8, nightTraffic: 0.3 },
  { from: 'airport',       to: 'al_rehab',      weight: 8,  morningPeak: 0.6, nightTraffic: 0.1 },
  { from: 'new_cairo',     to: 'al_rehab',      weight: 4,  morningPeak: 0.5, nightTraffic: 0.2 },
  { from: 'new_cairo',     to: 'festival_city', weight: 3,  morningPeak: 0.6, nightTraffic: 0.3 },
  { from: 'festival_city', to: 'nac',           weight: 12, morningPeak: 0.5, nightTraffic: 0.1 },

  // South links
  { from: 'qasr_el_aini',  to: 'maadi',         weight: 10, morningPeak: 0.7, nightTraffic: 0.2 },
  { from: 'al_azhar',      to: 'maadi',         weight: 12, morningPeak: 0.6, nightTraffic: 0.3 },
  { from: 'festival_city', to: 'maadi',         weight: 14, morningPeak: 0.5, nightTraffic: 0.2 },
  { from: 'maadi',         to: 'maadi_military',weight: 2,  morningPeak: 0.4, nightTraffic: 0.1 },
  { from: 'maadi_military',to: 'helwan',        weight: 12, morningPeak: 0.5, nightTraffic: 0.2 },
  { from: 'giza',          to: 'helwan',        weight: 18, morningPeak: 0.6, nightTraffic: 0.2 }
];

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

// Padding for graph display
const PAD = 25;

// ── Init Dashboard ────────────────────────────
export function initDashboard() {
  mapCanvas = document.getElementById('map-canvas');
  mapCanvasCompare = document.getElementById('map-canvas-compare');
  
  if (!mapCanvas) return;

  mapCtx = mapCanvas.getContext('2d');
  if (mapCanvasCompare) mapCtxCompare = mapCanvasCompare.getContext('2d');
  
  resizeMap();
  populateSelectors();
  bindEvents();
  startMapLoop();
  generateCurves(); // Generate initial curves
  createTrafficParticles();
  updateEdgeTraffic();

  window.addEventListener('resize', () => {
    resizeMap();
    generateCurves(); // Re-generate curves on resize
  });
  
  // Set initial status to Online
  const statusEl = document.getElementById('system-status');
  if (statusEl) {
    statusEl.innerHTML = '<span class="badge-dot"></span> ONLINE';
    statusEl.classList.add('online');
  }
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

// ── Node position helpers (with padding) ──────
function getNonLinearPos(val, spreadMulti) {
   const d = val - 0.5;
   return 0.5 + Math.sign(d) * Math.pow(Math.abs(d), 0.6) * spreadMulti;
}

function nodeX(node, w) {
  const pad = comparisonMode ? 140 : PAD; 
  const spreadMulti = comparisonMode ? 0.82 : 0.76;
  const nx = getNonLinearPos(node.x, spreadMulti);
  return pad + nx * (w - pad * 2);
}

function nodeY(node, h) {
  const pad = comparisonMode ? 120 : PAD;
  const spreadMulti = comparisonMode ? 0.82 : 0.76;
  const ny = getNonLinearPos(node.y, spreadMulti);
  return pad + ny * (h - pad * 2);
}

// ── Curve Generation — same logic for all ──────
function generateCurves() {
  if (!mapCanvas) return;
  // Use a base width/height to compute abstract curves, then scale during draw
  const w = 800, h = 600; 
  edgeCurves.clear();

  cityEdges.forEach((edge, index) => {
    const from = cityNodes.find((n) => n.id === edge.from);
    const to = cityNodes.find((n) => n.id === edge.to);
    if (!from || !to) return;

    // We store abstract coordinates [0..1] points instead of absolute pixel points
    const x1 = from.x, y1 = from.y;
    const x2 = to.x, y2 = to.y;

    // Compute control point (mid-point + offset)
    const mx = (x1 + x2) / 2;
    const my = (y1 + y2) / 2;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.sqrt(dx * dx + dy * dy);
    const offset = len * 0.15;
    const cpx = mx + (-dy / len) * offset;
    const cpy = my + (dx / len) * offset;

    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(x1, y1, 0),
      new THREE.Vector3(cpx, cpy, 0),
      new THREE.Vector3(x2, y2, 0)
    ], false, 'catmullrom', 0.5);

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
  
  if (!srcSelect || !dstSelect) return;
  
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
  
  srcSelect.value = 'sheikh_zayed';
  dstSelect.value = 'new_cairo';
  if (aiSrcSelect) aiSrcSelect.value = 'sheikh_zayed';
  if (aiDstSelect) aiDstSelect.value = 'new_cairo';
}

function bindEvents() {

  const timeSelect = document.getElementById('time-select');
  if (timeSelect) {
    timeSelect.addEventListener('change', (e) => {
      currentTimePeriod = e.target.value;
      if (e.target.value === 'morning') setMode('morning');
      else if (e.target.value === 'afternoon') setMode('day');
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
      runPredBtn.addEventListener('click', () => {
          const placeholder = document.getElementById('ai-placeholder');
          const output = document.getElementById('ai-output');
          
          if (placeholder) placeholder.style.display = 'none';
          if (output) {
              output.style.display = 'none'; // hide first
              showNotification("Running ML Analysis...");
              setTimeout(() => {
                  output.style.display = 'block';
                  gsap.fromTo(output, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' });
              }, 1200);
          }
      });
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
          showNotification("Opening route in Google Maps (Mock)");
          setTimeout(() => {
              window.open("https://maps.google.com/?q=Cairo", "_blank");
          }, 800);
      });
  }
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
    if (currentTimePeriod === 'morning') edge.traffic = edge.morningPeak;
    else if (currentTimePeriod === 'night') edge.traffic = edge.nightTraffic;
    else edge.traffic = (edge.morningPeak + edge.nightTraffic) / 2;
  });
}

function updateRoadFromTraffic() {
  const avg = cityEdges.reduce((s, e) => s + (e.traffic || 0.3), 0) / cityEdges.length;
  if (avg > 0.65) setRoadState('heavy');
  else if (avg > 0.4) setRoadState('moderate');
  else setRoadState('optimal');
}

// ── Routing Algorithms ──────────────────────────────────
function dijkstra(sourceId, destId, mode) {
  return runShortestPath(sourceId, destId, mode, false);
}

function astar(sourceId, destId, mode) {
  // Mock A* as returning the same route but exploring fewer nodes
  const res = runShortestPath(sourceId, destId, mode, true);
  return res;
}

function runShortestPath(sourceId, destId, mode, useAStarMock) {
  const adj = {};
  cityNodes.forEach((n) => (adj[n.id] = []));

  cityEdges.forEach((e) => {
    let w = e.weight;
    if (mode === 'emergency') w *= 0.5;
    else w *= 1 + (e.traffic || 0.3);
    adj[e.from].push({ to: e.to, weight: w });
    adj[e.to].push({ to: e.from, weight: w });
  });

  const dist = {}, prev = {};
  const visited = new Set();
  cityNodes.forEach((n) => { dist[n.id] = Infinity; prev[n.id] = null; });
  dist[sourceId] = 0;
  
  let exploredNodes = 0;

  while (true) {
    let u = null, minD = Infinity;
    for (const nid of Object.keys(dist)) {
      if (!visited.has(nid) && dist[nid] < minD) { minD = dist[nid]; u = nid; }
    }
    if (u === null || u === destId) {
        if (u === destId) exploredNodes++;
        break;
    }
    visited.add(u);
    exploredNodes++;
    
    for (const edge of adj[u]) {
      const alt = dist[u] + edge.weight;
      if (alt < dist[edge.to]) { dist[edge.to] = alt; prev[edge.to] = u; }
    }
  }

  const path = [];
  let curr = destId;
  while (curr) { path.unshift(curr); curr = prev[curr]; }
  if (path[0] !== sourceId) return { path: [], distance: Infinity, explored: exploredNodes, runtime: Math.floor(Math.random()*20)+10 };
  
  if (useAStarMock) {
      exploredNodes = Math.floor(exploredNodes * 0.6); // A* explores fewer nodes
  }
  
  const runtimeMs = useAStarMock ? Math.floor(Math.random()*8)+3 : Math.floor(Math.random()*25)+15;
  return { path, distance: dist[destId], explored: exploredNodes, runtime: runtimeMs };
}

function calculateRoute() {
  const source = document.getElementById('source-select')?.value;
  const dest = document.getElementById('dest-select')?.value;
  const mode = document.getElementById('mode-select')?.value || 'normal';

  if (!source || !dest || source === dest) {
    showNotification('Please select different source and destination');
    return;
  }
  
  // Reset special modes
  mstEdges = [];
  dpNodes = [];

  let resultDijkstra = dijkstra(source, dest, mode);
  let resultAStar = astar(source, dest, mode);
  
  if (resultDijkstra.path.length === 0) { showNotification('No route found'); return; }

  currentTrafficMode = mode;
  
  const gmapsBtn = document.getElementById('gmaps-btn');
  if (gmapsBtn) gmapsBtn.style.display = 'block';

  if (comparisonMode) {
      currentPath = resultAStar.path;
      currentPathCompare = resultDijkstra.path;
      displayResults(resultDijkstra, mode, resultAStar);
  } else {
      if (currentAlgorithm === 'dijkstra') {
          currentPath = resultDijkstra.path;
          displayResults(resultDijkstra, mode);
      } else if (currentAlgorithm === 'greedy') {
          // Mock greedy logic
          currentPath = resultDijkstra.path; // Same path, different visualization
          showNotification('Greedy Traffic Opt. Applied');
          displayResults({...resultDijkstra, runtime: Math.floor(Math.random()*5)+1}, mode);
      } else if (currentAlgorithm === 'prim') {
          currentPath = [];
          mstEdges = buildMockMST();
          showNotification('Prim MST Infrastructure Planning');
          displayResults({path:[], distance: 150, explored: 25, runtime: 35}, mode);
      } else if (currentAlgorithm === 'dp') {
          currentPath = [];
          dpNodes = buildMockDP();
          showNotification('Dynamic Programming Transit Optimization');
          displayResults({path:[], distance: 0, explored: 25, runtime: 120}, mode);
      }
  }
  
  animatePath();
  if (mode !== 'emergency') updateRoadFromTraffic();
}

function buildMockMST() {
    // Return a random subset of edges that look like a tree
    const tree = [];
    const usedNodes = new Set();
    const availableEdges = [...cityEdges].sort(() => Math.random() - 0.5);
    
    for (const e of availableEdges) {
        if (!usedNodes.has(e.from) || !usedNodes.has(e.to)) {
            tree.push(e);
            usedNodes.add(e.from);
            usedNodes.add(e.to);
        }
        if (usedNodes.size === cityNodes.length) break;
    }
    return tree;
}

function buildMockDP() {
    // Return nodes with DP schedule times
    return cityNodes.slice(0, 8).map(n => n.id);
}

function displayResults(result, mode, compareResult = null) {
  const isSpecial = currentAlgorithm === 'prim' || currentAlgorithm === 'dp';
  const totalTime = isSpecial ? 0 : Math.round(result.distance * 2.5);
  const distKm = isSpecial ? 0 : (result.distance * 1.8).toFixed(1);
  const avgTraffic = result.path && result.path.length > 1 ? getPathTraffic(result.path) : 0;
  const trafficLevel = avgTraffic > 0.65 ? 'high' : avgTraffic > 0.4 ? 'medium' : 'low';
  const trafficLabels = { low: 'Low Traffic', medium: 'Moderate', high: 'Heavy' };

  const etaEl = document.getElementById('stat-eta');
  const distEl = document.getElementById('stat-distance');
  const stopsEl = document.getElementById('stat-stops');
  const trafficEl = document.getElementById('stat-traffic');
  const runtimeEl = document.getElementById('stat-runtime');
  const exploredEl = document.getElementById('stat-explored');
  const routeStepsEl = document.getElementById('route-steps');

  if (etaEl) animateValue(etaEl, 0, totalTime, 900, ' min');
  if (distEl) animateValue(distEl, 0, parseFloat(distKm), 900, ' km');
  if (stopsEl) stopsEl.textContent = result.path ? Math.max(0, result.path.length - 2) + ' stops' : '--';

  if (trafficEl) {
    const bar = trafficEl.querySelector('.traffic-bar');
    const label = trafficEl.querySelector('.traffic-label');
    if (bar) bar.className = 'traffic-bar traffic-' + trafficLevel;
    if (label) label.textContent = trafficLabels[trafficLevel];
  }
  
  if (runtimeEl) {
      if (compareResult) {
          runtimeEl.innerHTML = `Dijkstra: ${result.runtime}ms<br/><span style="color:var(--success)">A*: ${compareResult.runtime}ms</span>`;
      } else {
          animateValue(runtimeEl, 0, result.runtime, 900, ' ms');
      }
  }
  if (exploredEl) {
      if (compareResult) {
          exploredEl.innerHTML = `Dijkstra: ${result.explored}<br/><span style="color:var(--success)">A*: ${compareResult.explored}</span>`;
      } else {
          animateValue(exploredEl, 0, result.explored, 900, '');
      }
  }

  // Populate comparison specific cards
  if (compareResult) {
      // A* is compareResult, Dijkstra is result
      document.getElementById('comp-astar-time').textContent = compareResult.runtime + ' ms';
      document.getElementById('comp-astar-nodes').textContent = compareResult.explored;
      document.getElementById('comp-astar-dist').textContent = (compareResult.distance * 1.8).toFixed(1) + ' km';
      document.getElementById('comp-astar-eta').textContent = Math.round(compareResult.distance * 2.5) + ' min';

      document.getElementById('comp-dij-time').textContent = result.runtime + ' ms';
      document.getElementById('comp-dij-nodes').textContent = result.explored;
      document.getElementById('comp-dij-dist').textContent = distKm + ' km';
      document.getElementById('comp-dij-eta').textContent = totalTime + ' min';

      const astarWin = compareResult.runtime < result.runtime;
      document.getElementById('astar-winner').style.display = astarWin ? 'inline-block' : 'none';
      document.getElementById('dijkstra-winner').style.display = astarWin ? 'none' : 'inline-block';
  }

  if (routeStepsEl) {
    routeStepsEl.innerHTML = '';
    if (result.path) {
        result.path.forEach((nodeId, i) => {
          const node = cityNodes.find((n) => n.id === nodeId);
          const step = document.createElement('div');
          step.className = 'route-step';
          let dotClass = 'step-dot';
          if (i === 0) dotClass += ' start';
          else if (i === result.path.length - 1) dotClass += ' end';
          step.innerHTML = `<span class="${dotClass}"></span><span>${node ? node.label : nodeId}</span>`;
          routeStepsEl.appendChild(step);
          gsap.fromTo(step, { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.5, delay: i * 0.12, ease: 'power3.out' });
        });
    }
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
  ctx.strokeStyle = 'rgba(0, 195, 255, 0.02)';
  ctx.lineWidth = 0.5;
  const spacing = 40;
  for (let x = 0; x < w; x += spacing) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }
  for (let y = 0; y < h; y += spacing) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }
}

// ── EDGES — same smooth curves for background ──
function drawEdges(ctx, w, h) {
  cityEdges.forEach((edge) => {
    const curve = edgeCurves.get(`${edge.from}_${edge.to}`);
    if (!curve) return;
    
    const points = getCurvePointsAbs(curve, w, h);
    if (!points || points.length === 0) return;

    const t = currentAlgorithm === 'greedy' ? (edge.traffic || 0.3) * 1.5 : (edge.traffic || 0.3); // Exaggerate greedy
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
    ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${0.06 + t * 0.06})`;
    ctx.lineWidth = 6 + t * 4;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Main edge
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${0.2 + t * 0.25})`;
    ctx.lineWidth = 1.5 + t * 2;
    ctx.lineCap = 'round';
    ctx.stroke();
  });
}

function drawMSTEdges(ctx, w, h) {
    mstEdges.forEach((edge) => {
        const curve = edgeCurves.get(`${edge.from}_${edge.to}`);
        if (!curve) return;
        const points = getCurvePointsAbs(curve, w, h);
        if (!points || points.length === 0) return;

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
    const color = t > 0.65
      ? `rgba(255, 80, 50, ${0.25 + tp.progress * 0.25})`
      : t > 0.4
        ? `rgba(255, 200, 50, ${0.25 + tp.progress * 0.25})`
        : `rgba(0, 255, 136, ${0.25 + tp.progress * 0.25})`;

    ctx.beginPath();
    ctx.arc(p.x, p.y, 2.2, 0, Math.PI * 2);
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
  cityNodes.forEach((node) => {
    const x = nodeX(node, w);
    const y = nodeY(node, h);
    const isActive = path.includes(node.id) || mstEdges.some(e => e.from===node.id || e.to===node.id);
    const isHovered = hoveredNode === node.id;
    const isStart = path.length > 0 && path[0] === node.id;
    const isEnd = path.length > 0 && path[path.length - 1] === node.id;

    // Outer halo
    ctx.beginPath();
    ctx.arc(x, y, 24, 0, Math.PI * 2);
    if (isStart) ctx.fillStyle = 'rgba(0, 255, 136, 0.08)';
    else if (isEnd) ctx.fillStyle = 'rgba(255, 59, 59, 0.08)';
    else if (isActive) ctx.fillStyle = 'rgba(0, 195, 255, 0.08)';
    else if (isHovered) ctx.fillStyle = 'rgba(122, 0, 255, 0.08)';
    else ctx.fillStyle = 'rgba(255, 255, 255, 0.02)';
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
    
    // Tooltip Hover effect
    if (isHovered) {
        ctx.fillStyle = 'rgba(10, 10, 20, 0.8)';
        ctx.strokeStyle = 'var(--primary)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(x - 45, y - 55, 90, 24, 4);
        ctx.fill();
        ctx.stroke();
        
        ctx.font = '500 9px "Inter", sans-serif';
        ctx.fillStyle = '#fff';
        ctx.textAlign = 'center';
        ctx.fillText("DISTRICT", x, y - 39);
    }

    // Node dot
    const radius = isHovered ? 12 : isActive ? 10 : 8;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);

    if (isStart) {
      ctx.fillStyle = '#00ff88';
      ctx.shadowColor = '#00ff88'; ctx.shadowBlur = 26;
    } else if (isEnd) {
      ctx.fillStyle = '#ff3b3b';
      ctx.shadowColor = '#ff3b3b'; ctx.shadowBlur = 26;
    } else if (isActive) {
      ctx.fillStyle = '#00c3ff';
      ctx.shadowColor = '#00c3ff'; ctx.shadowBlur = 22;
    } else {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
      ctx.shadowBlur = 0;
    }
    ctx.fill();
    ctx.shadowBlur = 0;

    // Label
    ctx.font = comparisonMode ? '600 16px "Orbitron", monospace' : '600 14px "Orbitron", monospace';
    ctx.textAlign = 'center';
    ctx.fillStyle = isActive ? '#00c3ff'
      : isHovered ? '#ffffff'
      : 'rgba(224, 230, 240, 0.7)';
    
    // Stagger labels up and down universally to prevent text collisions
    const nodeIndex = cityNodes.findIndex(n => n.id === node.id);
    let yOffset = (nodeIndex % 2 === 0) ? -32 : 32;
    
    if (comparisonMode) {
        yOffset = (nodeIndex % 2 === 0) ? -38 : 38;
    }
    
    if (yOffset > 0) ctx.textBaseline = 'top'; // draw below node
    else ctx.textBaseline = 'alphabetic';
    
    ctx.fillText(node.label, x, y + yOffset);
    ctx.textBaseline = 'alphabetic'; // reset
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
  tl.to(dashboard, { opacity: 0, duration: 0.6, ease: 'power3.in', onComplete: () => dashboard.classList.remove('active') });
  tl.call(() => intro.classList.remove('hidden'));
  tl.to(intro, { opacity: 1, y: 0, duration: 0.7, ease: 'power3.out' });
  tl.to(threeCanvas, { opacity: 1, duration: 0.7, ease: 'power2.out' }, '-=0.5');
  return tl;
}
