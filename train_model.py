# train_model.py

import pandas as pd
import pymysql
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Database connection
db_connection_str = 'mysql+pymysql://root:@localhost/milk_sensor_data'  # Updated database name
engine = create_engine(db_connection_str)

# Load dataset
df = pd.read_sql('SELECT * FROM milk_test', con=engine)

# Optional: drop ID column
if 'id' in df.columns:
    df = df.drop(columns=['id'])

# Feature and target (Update here)
X = df[['titrable_acidity', 'temperature', 'pH', 'conductivity']]  # Use all four features
y = df['status']  # Target

# Encode labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
model = RandomForestClassifier()
model.fit(X_train_scaled, y_train)

# Test model
y_pred = model.predict(X_test_scaled)
print(classification_report(y_test, y_pred))

# Save model, scaler, and label encoder
joblib.dump(model, 'milk_quality_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(label_encoder, 'label_encoder.pkl')  # Save the label encoder

print("✅ Model, Scaler, and Label Encoder saved!")
