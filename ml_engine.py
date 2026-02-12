import time

class AnomalyDetector:
    def __init__(self):
        self.history = []
        self.threshold = 1.5 # Deviation threshold

    def analyze(self, current_data):
        """
        Analyzes sensor data for anomalies and provides health scores.
        This fixes the 'AttributeError' from your screenshot.
        """
        # Simple algorithmic health score based on deviations from targets
        health = 100
        alerts = []

        # Check pH
        if current_data['ph'] > 8.0:
            health -= 20
            alerts.append("Critical High pH")
        elif current_data['ph'] < 4.5:
            health -= 20
            alerts.append("Critical Low pH")

        # Check Temperature
        if current_data['temp'] > 30.0:
            health -= 15
            alerts.append("High Temp Stress")
            
        # Check EC (if available)
        if 'ec' in current_data and current_data['ec'] < 0.5:
             health -= 10
             alerts.append("Low Nutrients")

        status = "HEALTHY" if health > 85 else "ALERT"
        if not alerts: alerts.append("All Systems Nominal")

        return {
            "health_score": health,
            "status": status,
            "prediction": alerts[0],
            "trend": "Stable", # Placeholder for trend analysis
            "timestamp": time.time()
        }