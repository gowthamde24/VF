# import time

# class AnomalyDetector:
#     def __init__(self):
#         self.history = []
#         self.threshold = 1.5 # Deviation threshold

#     def analyze(self, current_data):
#         """
#         Analyzes sensor data for anomalies and provides health scores.
#         This fixes the 'AttributeError' from your screenshot.
#         """
#         # Simple algorithmic health score based on deviations from targets
#         health = 100
#         alerts = []

#         # Check pH
#         if current_data['ph'] > 8.0:
#             health -= 20
#             alerts.append("Critical High pH")
#         elif current_data['ph'] < 4.5:
#             health -= 20
#             alerts.append("Critical Low pH")

#         # Check Temperature
#         if current_data['temp'] > 30.0:
#             health -= 15
#             alerts.append("High Temp Stress")
            
#         # Check EC (if available)
#         if 'ec' in current_data and current_data['ec'] < 0.5:
#              health -= 10
#              alerts.append("Low Nutrients")

#         status = "HEALTHY" if health > 85 else "ALERT"
#         if not alerts: alerts.append("All Systems Nominal")

#         return {
#             "health_score": health,
#             "status": status,
#             "prediction": alerts[0],
#             "trend": "Stable", # Placeholder for trend analysis
#             "timestamp": time.time()        }


import time
import os
import pandas as pd
from sklearn.ensemble import IsolationForest
import warnings

# Ignore minor warnings from pandas/sklearn to keep the console clean
warnings.filterwarnings('ignore')

class AnomalyDetector:
    def __init__(self, log_file="system_log.csv"):
        self.log_file = log_file
        self.model = None
        self.is_trained = False
        
        # Try to train the model as soon as the system boots
        self.train_model()

    def train_model(self):
        """Reads historical CSV data and trains the Machine Learning model."""
        if not os.path.exists(self.log_file):
            print("-> [ML Engine] No log file found yet. Waiting for data collection...")
            return

        try:
            # Load the logged data
            df = pd.read_csv(self.log_file)
            
            # Require at least 200 data points (~7 minutes of data) to find patterns
            if len(df) < 200:
                print(f"-> [ML Engine] Collecting data... ({len(df)}/200 rows). Using safety rules only.")
                return

            # Extract just the environmental data for pattern recognition
            features = df[['Temp_C', 'Humidity_%', 'pH', 'EC']].dropna()

            # Initialize Isolation Forest (contamination=0.05 means we assume 5% of historical data might be unusual)
            self.model = IsolationForest(contamination=0.05, random_state=42)
            self.model.fit(features)
            
            self.is_trained = True
            print(f"-> [ML Engine] ONLINE. Isolation Forest trained on {len(features)} data points.")
            
        except Exception as e:
            print(f"! [ML Engine] Training Error: {e}")

    def analyze(self, current_data):
        """Analyzes real-time sensor data using both hard rules and ML patterns."""
        health = 100
        alerts = []
        status = "HEALTHY"

        # --- 1. HARD SAFETY RULES (Immediate Threats) ---
        if current_data['ph'] > 7.5:
            health -= 20
            alerts.append("High pH")
        elif current_data['ph'] < 5.0:
            health -= 20
            alerts.append("Low pH")

        if current_data['temp'] > 28.0:
            health -= 15
            alerts.append("Heat Stress")
            
        if 'ec' in current_data and current_data['ec'] < 0.6:
             health -= 10
             alerts.append("Low Nutrients")

        # --- 2. MACHINE LEARNING ANOMALY DETECTION (Hidden Patterns) ---
        if self.is_trained and self.model:
            try:
                # Format current data for the model
                current_df = pd.DataFrame([{
                    'Temp_C': current_data['temp'],
                    'Humidity_%': current_data['hum'],
                    'pH': current_data['ph'],
                    'EC': current_data['ec']
                }])

                # Predict: 1 means Normal, -1 means Anomaly
                prediction = self.model.predict(current_df)[0]
                
                if prediction == -1:
                    health -= 25
                    alerts.append("ML Alert: Unusual Pattern")
            except Exception:
                pass # Silently fail back to hard rules if prediction errors

        # --- 3. FINALIZE STATUS ---
        if health <= 85:
            status = "ALERT"
        if not alerts: 
            alerts.append("All Systems Nominal")

        # Retrain model automatically if we accumulate a lot of new data (Placeholder logic)
        # In a production environment, you would run self.train_model() on a nightly schedule.

        return {
            "health_score": max(0, health),
            "status": status,
            "prediction": " | ".join(alerts),
            "trend": "Learning" if not self.is_trained else "Monitoring ML",
            "timestamp": time.time()
        }