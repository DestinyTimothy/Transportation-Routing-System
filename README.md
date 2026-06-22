# 🗺️ Transportation Routing Engine

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Framework](https://img.shields.io/badge/flask-v3.0-red?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/mysql-8.0-orange?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Frontend Maps](https://img.shields.io/badge/leaflet.js-1.9.4-green?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com/)


**An intelligent, multi-objective public transit routing application optimized via discrete Particle Swarm Optimization (PSO). Tailored for complex, informal urban transport networks.**

[Explore Features](#-key-features) • [How It Works](#-how-the-optimization-engine-works) • [Installation](#%EF%B8%8F-installation--workspace-setup) • [API Reference](#-api-endpoints)

</div>

---

## 📌 Project Overview

**Transportation Routing System** bridges metaheuristic optimization with everyday commuter usability. Traditional routing systems (like Dijkstra's or A\*) struggle to compute journeys under fluid, conflicting constraints like multi-modal transport switching, sudden fare spikes, and strict commuter budget preferences. 

This system models the urban transit web of Port Harcourt as a discrete network graph. By running a customized **Particle Swarm Optimization (PSO)** algorithm on the server backend, it dynamically computes and ranks transit itineraries based on real-time parameter weighting—balancing **Financial Cost** and **Travel Time** into a singular, minimized fitness evaluation.

---

## ✨ Key Features

* 🛠️ **Multi-Objective Optimization Engine:** Commuters choose their journey profile—**Economic Mode** (minimizes transport fares) or **Express Mode** (minimizes travel duration).
* 🗺️ **Geospatial Polyline Mapping:** Dynamic JSON response mapping natively binds into a Leaflet.js canvas interface, rendering exact visual polyline routes across terminal nodes.
* 🔒 **Secured Administrative Control Panel:** Middleware-protected graph adjustments (`/admin`) let authorized operators introduce new transport legs, update fare patterns, and map additional landmarks without touching code base strings.
* 💾 **User Account & Travel Profiles:** Enforces password cryptography security using `werkzeug.security` to let authenticated commuters save customized itineraries securely.

---
