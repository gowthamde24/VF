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