# 🌱 Intelligent Vertical Farm System (IoT + AI)

Automated Hydroponic Control System using Raspberry Pi 5

This project is a fully automated control system for a vertical farm. It manages irrigation, climate control, and water chemistry (pH/EC) using a Raspberry Pi 5, an 8-channel relay module, and a network of sensors. It features a Machine Learning engine for anomaly detection and a live web dashboard.

## 🏗️ Hardware Architecture

### Controller & Logic
- Main Controller: Raspberry Pi 5 (running Python 3 logic)
- Power: 12V PSU (for actuators) + 5V Buck Converter (for Pi/Sensors)
- Control Box: Centralized terminal block wiring (No Breadboards!)

### Sensors (Inputs)
- BME280 (I2C): Air Temperature & Humidity
- ADS1115 (I2C): 16-bit ADC for Analog Sensors
- pH Probe (Analog A0): Water Acidity
- EC Probe (Analog A1): Nutrient Strength
- Water Level Sensor (Analog A2): Tank Safety Cutoff

### Actuators (Outputs - 8 Channel Relay)

| Relay | GPIO | Device | Function |
|------:|-----:|--------|----------|
| 1 | 5 | Water Pump | Irrigation Cycle (5 min/hr) |
| 2 | 6 | Grow Lights | Day/Night Cycle (06:00-20:00) |
| 3 | 13 | Fan | Cooling (if Temp > 25°C) |
| 4 | 19 | pH Down Pump | Acid Dosing (if pH > 6.5) |
| 5 | 26 | pH Up Pump | Base Dosing (if pH < 5.5) |
| 6-8 | - | Expansion | Nutrient Dosing / Spares |

## 🚀 Installation Guide

### Prerequisites
- Raspberry Pi 5 with Raspberry Pi OS (Bookworm)
- Python 3.11+
- I2C Interface Enabled (sudo raspi-config -> Interface Options -> I2C)

## 1. Set Up Virtual Environment
Run these commands on your Raspberry Pi terminal:

```bash
### Create project folder
mkdir vertical_farm
cd vertical_farm

### Create virtual environment (with access to system GPIO libs)
python3 -m venv venv --system-site-packages

### Activate it
source venv/bin/activate

## 2. Install Dependencies

Install all required Python libraries for sensors, AI, and GPIO.

```bash
pip install adafruit-circuitpython-bme280 adafruit-circuitpython-ads1x15 adafruit-blinka smbus2 rpi-lgpio scikit-learn pandas numpy joblib


## 3. Deploy Code

Copy the following files into the `vertical_farm` folder:

- `main.py` (Master Logic)
- `config.py` (Settings & Pins)
- `ml_engine.py` (AI Anomaly Detector)
- `diagnostics.py` (Testing Tool)
- `farm_dashboard.html` (Live Web UI)

## 🛠️ Usage

### A. Run Diagnostics (Test Mode)

Before running the main loop, test your wiring manually:

```bash
python3 diagnostics.py


Use the menu to toggle relays 1-8 and read sensor values.

### B. Start the Main System

Run the automated controller:

```bash
python3 main.py

The system will start reading sensors, controlling relays, and printing status logs.

### C. View Live Dashboard

To see the stunning graphical interface on your screen:

1. Keep `main.py` running (it generates `dashboard.json`).
2. Open a new terminal window.
3. Start a local web server:

```bash
python3 -m http.server 8000

Open the browser (Chromium) on the Pi and go to:

```text
http://localhost:8000/stunning_dashboard.html

## 🧠 Machine Learning Engine

The system uses an Isolation Forest algorithm (`ml_engine.py`) to detect anomalies.

- **Training:** It learns "Normal" behavior from your sensor data over time.
- **Inference:** Every cycle, it checks if the current combination of Temperature, Humidity, and pH looks "weird" (e.g., Temp rising but Fan is off).
- **Alert:** If an anomaly is found, it flags an alert on the Dashboard.

## ⚠️ Safety Features

- **Water Level Safety:** If the tank sensor reads EMPTY (< 1.5V), the Main Pump is forced OFF to prevent burning out.
- **Thermal Cutoff:** If Air Temp > 30°C, Grow Lights are forced OFF to cool the system.
- **Dosing Lockout:** After adding pH chemicals, the system waits 15 minutes before dosing again to prevent overdose.

Project Status: Production Ready 🟢
