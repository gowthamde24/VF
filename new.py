sudo nano /etc/systemd/system/verticalfarm.service

#--------------------------------------------------------->

[Unit]
Description=Vertical Farm Automation System
After=network.target

[Service]
# The user running the script
User=pi

# The exact path to your project folder
WorkingDirectory=/home/pi/Downloads/VF-main

# The path to your venv Python, followed by the path to main.py
ExecStart=/home/pi/Downloads/VF-main/venv/bin/python3 /home/pi/Downloads/VF-main/main.py

# Automatically restart if the script crashes
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target


#--------------------------------------------------------->


sudo systemctl daemon-reload
sudo systemctl enable verticalfarm.service
sudo systemctl start verticalfarm.service



#--------------------------------------------------------->

nano ~/.config/wayfire.ini

#--------------------------------------------------------->

dashboard = chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:8000/stunning_dashboard.html




#----------------------------------------------------------->

sudo apt update && sudo apt upgrade -y
sudo raspi-config nonint do_i2c 0


# Create the environment (you only do this once)
python3 -m venv env

# Activate the environment (you must do this every time before running your script)
source env/bin/activate

pip3 install RPi.GPIO adafruit-blinka adafruit-circuitpython-ads1x15 adafruit-circuitpython-bme280

