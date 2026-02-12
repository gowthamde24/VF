# import joblib
# import os
# import numpy as np
# from sklearn.ensemble import IsolationForest

# class AnomalyDetector:
#     def __init__(self):
#         # Initialize model with 5% contamination (expected anomaly rate)
#         self.model = IsolationForest(contamination=0.05)
#         self.trained = False
#         print(" -> ML Engine Initialized.")

#     def train(self, data):
#         # Data format: [[temp, humidity, ph], [temp, humidity, ph]...]
#         if len(data) > 50:
#             print(" -> Training ML Model on new data...")
#             self.model.fit(data)
#             self.trained = True
#             print(" -> ML Model Trained Successfully.")
#         else:
#             print(" -> Not enough data to train yet (Need 50+ samples).")

#     def predict(self, sample):
#         # Sample format: [temp, humidity, ph]
#         if not self.trained:
#             return 1 # Return 1 (Normal) if not trained yet
        
#         # Returns -1 for Anomaly, 1 for Normal
#         try:
#             # Reshape sample if it's a 1D array/list to match expected 2D input
#             if isinstance(sample, (list, tuple, np.ndarray)):
#                 sample_reshaped = np.array(sample).reshape(1, -1)
#                 return self.model.predict(sample_reshaped)[0]
#             else:
#                 return 1 # Invalid input format, assume normal
#         except Exception as e:
#             print(f"Prediction error: {e}")
#             return 1



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
        # Simple algorithmic health score
        health = 100
        alerts = []

        if current_data['ph'] > 8.0:
            health -= 20
            alerts.append("Critical High pH")
        elif current_data['ph'] < 4.5:
            health -= 20
            alerts.append("Critical Low pH")

        if current_data['temp'] > 30.0:
            health -= 15
            alerts.append("High Temp Stress")

        status = "OPTIMAL" if health > 85 else "CORRECTING"
        if not alerts: alerts.append("All Systems Nominal")

        return {
            "health_score": health,
            "status": status,
            "prediction": alerts[0],
            "timestamp": time.time()
        }