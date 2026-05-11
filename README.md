

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=200&section=header&text=CAIRO%20GRID%20OPTIMIZER&fontSize=40&fontColor=ffffff&animation=fadeIn" />

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white" />
    <img src="https://img.shields.io/badge/Three.js-3D%20Engine-black?style=for-the-badge&logo=three.js&logoColor=white" />
    <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
    <img src="https://img.shields.io/badge/Algorithms-Optimized-orange?style=for-the-badge&logo=gitbook&logoColor=white" />
  </p>

  **** 

  <a href="https://github.com/Basmala-ElKady/CairoGrid-Optimizer">
    <img src="https://readme-typing-svg.demolab.com/?lines=URBAN%20LOGISTICS%20ENGINE;ALGORITHMIC%20ORCHESTRATION;PREDICTIVE%20TRAFFIC%20MODELS;CINEMATIC%20DATA%20VISUALS&font=Fira%20Code&center=true&width=600&height=50&color=36BCF7&vCenter=true&size=26" />
  </a>
</div>

---

## Introduction

**CairoGrid Optimizer** is a high-fidelity urban engineering and transport simulation platform. It addresses the multi-dimensional challenges of Cairo's metropolitan traffic by orchestrating six core computational disciplines into a single, unified engine. From Minimum Spanning Trees to Machine Learning forecasts, it transforms raw data into actionable urban insights.

---

## Algorithmic Core

| Domain | Algorithm | Purpose in Cairo |
| :--- | :--- | :--- |
| **Infrastructure** | `Prim's MST` | Designing the optimal backbone of road networks with minimal cost. |
| **Emergency** | `A* (Heuristic)` | Routing ambulances via the fastest path during peak congestion hours. |
| **Transit** | `Dynamic Programming` | Optimizing bus schedules and resource allocation for maximum coverage. |
| **Congestion** | `Greedy Strategy` | Real-time traffic signal timing based on intersection throughput. |
| **Navigation** | `Dijkstra` | Static shortest-path calculation for standard commuting patterns. |
| **Forecasting** | `Random Forest (ML)` | Predicting traffic flow indices based on historical patterns. |

---

## Key Features

### Intelligent Infrastructure
- **Unified Graph Model:** Merges districts, medical facilities, and road segments into a weighted bidirectional graph.
- **Dynamic Cost Evaluation:** Factors in road length, capacity, and real-time traffic indices.

### Cinematic 3D Dashboard
- **Three.js Visualization:** A futuristic 3D representation of the city's road network.
- **GSAP Animations:** Smooth cinematic transitions and interactive scroll-based storytelling.
- **Real-time Map:** Interactive 2D/3D map with glowing pathfinding effects and traffic flow particles.

### Production-Ready Environment
- **Containerized Architecture:** Fully orchestrated using Docker for seamless deployment across any environment.
- **CI/CD Friendly:** Clean modular architecture for testing and scaling backend services.

---

## Tech Stack

- **Core Logic:** `Python 3.11`, `Scikit-Learn`, `Pandas`, `Joblib`
- **Frontend UI:** `Three.js`, `GSAP`, `CSS Glassmorphism`, `Orbitron Typography`
- **Infrastructure:** `Docker`, `Docker Compose`, `Nginx`

---

## Deployment Guide

### 1. Automated Setup (Recommended)
The fastest way to get the engine running is via Docker Compose:

```powershell
docker-compose up --build
```

### 2. Manual Installation
If you prefer a local environment:

```bash
# Setup Backend
pip install -r requirements.txt
python main.py

# Setup Frontend
# Open Frontend/index.html in a local server
```

---

## Architecture

```text
├── Backend/                 
│   ├── algorithms/          # Pure algorithmic implementations
│   ├── simulation/          # Scenario engines (Emergency, Normal)
│   ├── services/            # API-ready service wrappers
│   └── data/                # Geospatial and traffic datasets
├── Frontend/                
│   ├── js/                  # Scroll systems & Three.js logic
│   └── css/                 # Cinematic UI tokens
└── docker-compose.yml       # Full system orchestration
```

---

<div align="center">
  <img 
    src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=120&section=footer&text=OPTIMIZING%20CAIRO%20ONE%20NODE%20AT%20A%20TIME&fontSize=22&fontColor=ffffff&animation=fadeIn" 
  />

  <p align="center">
    <img src="https://img.shields.io/badge/Smart%20Routing-Dijkstra-success?style=for-the-badge" />
    <img src="https://img.shields.io/badge/Traffic-AI%20Simulation-blue?style=for-the-badge" />
    <img src="https://img.shields.io/badge/DP-Knapsack-orange?style=for-the-badge" />
  </p>

  <p>
    <i>Developed as a Semester 6 Project for Design & Analysis of Algorithms.</i>
  </p>
</div>
