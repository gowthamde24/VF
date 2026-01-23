# Intelligent Vertical Farm System (IoT + AI)

**Automated Hydroponic Control System using Raspberry Pi 5**

This project is a fully automated control system for a vertical farm. It manages irrigation, climate control, and water chemistry (pH/EC) using a Raspberry Pi 5, an 8-channel relay module, and a network of sensors. It features a Machine Learning engine for anomaly detection and a live web dashboard.

**Project Status:** Production Ready

---

## Hardware Architecture

### Controller & Logic
* **Main Controller:** Raspberry Pi 5 (running Python 3 logic)
* **Power:** 12V PSU (for actuators) + 5V Buck Converter (for Pi/Sensors)
* **Control Box:** Centralized terminal block wiring (No Breadboards!)

### Sensors (Inputs)
* **BME280 (I2C):** Air Temperature & Humidity
* **ADS1115 (I2C):** 16-bit ADC for Analog Sensors
    * **pH Probe (Analog A0):** Water Acidity
    * **EC Probe (Analog A1):** Nutrient Strength
    * **Water Level Sensor (Analog A2):** Tank Safety Cutoff

### Actuators (Outputs - 8 Channel Relay)

| Relay | GPIO | Device | Function |
| :--- | :--- | :--- | :--- |
| **1** | 5 | Water Pump | Irrigation Cycle (5 min/hr) |
| **2** | 6 | Grow Lights | Day/Night Cycle (06:00-20:00) |
| **3** | 13 | Fan | Cooling (if Temp > 25°C) |
| **4** | 19 | pH Down Pump | Acid Dosing (if pH > 6.5) |
| **5** | 26 | pH Up Pump | Base Dosing (if pH < 5.5) |
| **6-8** | N/A | Expansion | Nutrient Dosing / Spares |

---

## Installation Guide

### Prerequisites
* Raspberry Pi 5 with Raspberry Pi OS (Bookworm)
* Python 3.11+
* I2C Interface Enabled (`sudo raspi-config` -> Interface Options -> I2C)

### 1. Set Up Virtual Environment
Run these commands on your Raspberry Pi terminal:

```bash
# Create project folder
mkdir vertical_farm
cd vertical_farm

# Create virtual environment (with access to system GPIO libs)
python3 -m venv venv --system-site-packages

# Activate it
source venv/bin/activate


### 2. Install Dependencies
[cite_start]Install all required Python libraries for sensors, AI, and GPIO[cite: 34].

```bash
pip install adafruit-circuitpython-bme280 adafruit-circuitpython-ads1x15 adafruit-blinka smbus2 rpi-lgpio scikit-learn pandas numpy joblib


### 3. Deploy Code
Copy the following files into the `vertical_farm` folder:
* [cite_start]`main.py` (Master Logic) [cite: 38]
* [cite_start]`config.py` (Settings & Pins) [cite: 39]
* [cite_start]`ml_engine.py` (AI Anomaly Detector) [cite: 40]
* [cite_start]`diagnostics.py` (Testing Tool) [cite: 41]
* [cite_start]`farm_dashboard.html` (Live Web UI) [cite: 43]