# 🛸 Lightweight ArduPilot SITL Docker Image

[![Docker Build and Publish](https://github.com/CacheFail/ardupilot-sitl-slim/actions/workflows/docker-push.yml/badge.svg)](https://github.com/CacheFail/ardupilot-sitl-slim/actions)

This repository provides a highly optimized **ArduPilot SITL (Copter 4.5.7)** Docker image. Using multi-stage builds and binary stripping, the image size has been reduced to **613MB**, making it ideal for CI/CD pipelines and fast local testing.

## 🚀 Key Features

- **Ultra-Lightweight**: Minimal runtime dependencies (Python 3.11-slim).
- **Console Dashboard**: The included `takeoff.py` script provides a real-time telemetry dashboard.
- **Ready to Fly**: Pre-configured with MAVProxy and essential flight parameters.
- **Fast Startup**: Optimized EKF alignment for immediate testing.

---

## 🛠️ Getting Started

### 1. Spin up the Simulator

Launch the environment using Docker Compose:

```bash
docker-compose up -d
```

### 2. Run the Takeoff Mission

The `takeoff.py` script manages the arming sequence and monitors critical flight data (EKF, GPS, Altitude) in a terminal dashboard.

```bash
# Setup environment
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r scripts/requirements.txt

# Run mission
python scripts/takeoff.py
```

## 📊 Telemetry Dashboard Logic

The control script performs low-level checks before execution:

- **EKF Health**: Monitors `EKF_STATUS_REPORT` (Flags `0x01`, `0x02`, `0x04`) to ensure navigation safety.
- **GPS Integrity**: Validates `GLOBAL_POSITION_INT` scaling (degrees * `1e7`).
- **Heartbeat Sync**: Real-time mode verification (`GUIDED`) and system status.

## ⚙️ Configuration

Override default simulation parameters via environment variables

- `LAT`, `LON`, `ALT`: Initial origin coordinates.
- `SPEEDUP`: Simulation clock multiplier (e.g., `5` for rapid testing).
- `OUT_ADDR`: UDP telemetry target (default: `host.docker.internal:14550`).

> **Note:** This image is intended for console-based automated testing and telemetry prototyping.