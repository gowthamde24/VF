# Grow Smart OS 🌱

**An Autonomous, IoT-Based Cyber-Physical System for Hydroponic Vertical Farming**

Grow Smart OS is a fully autonomous, four-layer Cyber-Physical System (CPS) engineered specifically for the resilient hydroponic cultivation of polycultures. Designed to overcome the vulnerabilities of "Thin Edge" cloud-dependent systems, it operates on a "Thick Edge" computing paradigm, ensuring 100% offline autonomy and absolute hardware protection.

##  Key Features

* **Thick Edge Autonomy:** All decision-making, data logging, and UI hosting are performed locally on the edge device, eliminating cloud latency and network dependency.
* **Deterministic Rule-Based Engine:** Utilizes rigid hysteresis deadbands and a proprietary "Pulse-and-Wait" micro-dosing algorithm to perfectly regulate fluid diffusion and prevent chemical oscillation.
* **Asynchronous Multithreading:** Separates the 100Hz real-time hardware polling loop from the local web server, preventing blocking I/O and latency during mechanical actuation.
* **Software-Based Galvanic Isolation:** Implements precise 120-second settling delays (`PH_SETTLING_TIME`) and state-holding to eliminate active galvanic interference ("Motor Drop") and endless dosing loops during the switching of heavy inductive loads.
* **Hardware Fail-Safes:** Features an Active-Low logic topology with opto-isolated relays, ensuring that all 12V pumps fail to a safe "OFF" state upon system reboot or kernel panic.
* **Glassmorphism Dashboard:** A localized, zero-latency Human-Machine Interface (HMI) built with asynchronous JSON serialization and reverse proxy tunneling for secure global overrides.

##  System Architecture

The project is strictly segmented into four isolated tiers to ensure that high-voltage physical actuation does not electrically interfere with low-voltage digital logic:

1. **Layer 1 (Physical):** 50-Liter Nutrient Reservoir and UV-blocking PVC NFT channels.
2. **Layer 2 (Perception & Actuation):** 16-bit ADC (ADS1115), BME280 Climate Sensor, Capacitive Water Level Sensor (XKC-Y25-V), and 12V Peristaltic/Centrifugal pumps.
3. **Layer 3 (Cyber/Logic):** Raspberry Pi 4 Model B running the multithreaded Python control loop.
4. **Layer 4 (Application):** AJAX-driven local web dashboard with real-time JSON state serialization.

##  Hardware Stack

* **Core Processing:** Raspberry Pi 4 Model B (Broadcom BCM2711)
* **Analog-to-Digital Converter:** ADS1115 (16-bit precision for sub-millivolt pH/EC reading)
* **Environmental Sensor:** Bosch BME280 (Temperature, Humidity, VPD calculation)
* **Fluid Level Sensor:** XKC-Y25-V (Non-contact capacitive sensor)
* **Relay Plane:** 8-Channel Opto-Isolated Relay Module (Active-Low)
* **Power Management:** High-Efficiency 12V to 5.1V Buck Converter (92% Efficiency)
* **Protection:** Custom 3D-printed IP54-rated PLA enclosures with TPU vibration-damping mounts

##  Software Stack

* **Backend:** Python 3 (Native `threading` module, `socketserver.TCPServer`)
* **Data Serialization:** File-based JSON state management & CSV persistent logging
* **Frontend UI:** HTML5, CSS3 Grid, JavaScript (AJAX Fetch API), SVG Kinetic Animations
* **Process Manager:** Linux `systemd` daemon for automated crash recovery

##  Installation & Setup

**1. Clone the Repository**

git clone [https://github.com/gowthamde24/VF.git](https://github.com/gowthamde24/VF.git)
cd VF

**2. Set up the Virtual Environment & Dependencies**

python3 -m venv env
source env/bin/activate
pip install RPi.GPIO adafruit-circuitpython-ads1x15 adafruit-circuitpython-bme280

**3. Clone the Repository**

sudo cp growsmart.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable growsmart.service
sudo systemctl start growsmart.service

**4. Launch the Dashboard**

http://<RASPBERRY_PI_IP>:8000/stunning_dashboard.html


## Authors
Gowtham Reddy Sodanapalli - Hardware Architecture & Implementation

Sai Kalyani Yerrasani - Software Integration & Automation Dashboard

Syeda Khadeeja Naqvi - Botanical Growth & Agronomy

Charishma Sai Pinnemaneni - 3D Modelling & Hardware Protection

Developed for the Master’s Degree Program in Information Technology at TH OWL (University of Applied Sciences and Arts)


