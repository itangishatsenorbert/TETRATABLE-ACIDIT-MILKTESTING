# milk_analysis.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

# --------- STEP 1: LOAD AND EXPLORE DATA ---------
df = pd.read_csv('milk_data.csv')
print("\nFirst 5 rows of dataset:\n", df.head())
print("\nDataset Info:\n")
print(df.info())
print("\nDataset Statistics:\n")
print(df.describe())

# --------- STEP 2: PREPROCESSING ---------
label_encoder = LabelEncoder()
df['status_encoded'] = label_encoder.fit_transform(df['status'])

features = ['titrable_acidity', 'temperature', 'pH']
X = df[features]
y = df['status_encoded']

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

print("\nPreprocessing finished! Dataset is ready for modeling.")

# --------- STEP 3: TRAIN MULTIPLE MODELS ---------
# Random Forest Classifier
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# Logistic Regression
logreg_model = LogisticRegression(random_state=42)
logreg_model.fit(X_train, y_train)

# --------- STEP 4: EVALUATE MODELS ---------
# Predictions from both models
rf_preds = rf_model.predict(X_test)
logreg_preds = logreg_model.predict(X_test)

# Accuracy Score
print("\nRandom Forest Classifier Accuracy: ", accuracy_score(y_test, rf_preds))
print("Logistic Regression Accuracy: ", accuracy_score(y_test, logreg_preds))

# Classification Report for detailed performance
print("\nRandom Forest Classification Report:\n", classification_report(y_test, rf_preds))
print("\nLogistic Regression Classification Report:\n", classification_report(y_test, logreg_preds))

# --------- STEP 5: SAVE THE BEST MODEL ---------
# Save the Random Forest model as the best performing one
import joblib
joblib.dump(rf_model, 'milk_quality_model.pkl')

print("\nModel saved successfully as 'milk_quality_model.pkl'!")
