import json, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import LabelEncoder
import joblib
import os

base = r"C:\Users\abhishek\Downloads\ai-based soc\backend\ml_models"
os.makedirs(base, exist_ok=True)

# Generate synthetic training data based on legitimate cybersecurity dataset features
np.random.seed(42)
n_samples = 5000

# Features: source_port, dest_port, bytes_sent, bytes_received, failed_logins, request_rate, proto, severity_num
X = np.random.randint(0, 65535, (n_samples, 2))
X = np.column_stack([
    np.random.randint(1024, 65535, n_samples),  # source_port
    np.random.choice([22, 80, 443, 3389, 53, 8080, 445], n_samples),  # dest_port
    np.random.randint(0, 5000, n_samples),  # bytes_sent
    np.random.randint(0, 5000, n_samples),  # bytes_received
    np.random.randint(0, 30, n_samples),  # failed_logins
    np.random.randint(1, 200, n_samples),  # request_rate
    np.random.choice([0, 1, 6], n_samples),  # proto (0=tcp, 1=udp, 6=icmp)
    np.random.randint(1, 5, n_samples),  # severity_num
])

# Attack types to predict
attack_map = {0: "Brute Force SSH", 1: "SQL Injection", 2: "Port Scan",
              3: "DDoS HTTP Flood", 4: "XSS Attempt", 5: "RCE Probe"}
y = np.random.choice(range(6), n_samples)

# Train RandomForest
rf = RandomForestClassifier(n_estimators=100, max_depth=16, random_state=42)
rf.fit(X, y)

# Train IsolationForest for anomaly detection
iso = IsolationForest(contamination=0.1, random_state=42)
iso.fit(X)

# Label encoders
le_attack = LabelEncoder()
le_attack.fit(["Brute Force SSH", "SQL Injection", "Port Scan", "DDoS HTTP Flood", "XSS Attempt", "RCE Probe"])
le_proto = LabelEncoder()
le_proto.fit(["tcp", "udp", "icmp"])

# Feature names
feature_cols = ["source_port", "dest_port", "bytes_sent", "bytes_received", "failed_logins", "request_rate", "proto", "severity_num"]

# Model metadata
meta = {
    "feature_cols": feature_cols,
    "attack_classes": list(le_attack.classes_),
    "proto_classes": list(le_proto.classes_),
    "n_features": len(feature_cols),
    "training_samples": n_samples,
    "train_date": pd.Timestamp.now().isoformat()
}

# Save models
joblib.dump(rf, os.path.join(base, "random_forest.pkl"))
joblib.dump(iso, os.path.join(base, "isolation_forest.pkl"))
joblib.dump(le_attack, os.path.join(base, "label_encoder_attack.pkl"))
joblib.dump(le_proto, os.path.join(base, "label_encoder_proto.pkl"))
with open(os.path.join(base, "model_metadata.json"), "w") as f:
    json.dump(meta, f, indent=2)

print("Models trained and saved successfully!")
print("Feature cols:", feature_cols)