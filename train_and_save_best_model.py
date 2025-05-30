import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load dataset
df = pd.read_csv('cleaned_milk_data.csv')

# Convert 'status' to lowercase
df['status'] = df['status'].str.lower()

# Keep only the rows where status is 'bad', 'spoiled', or 'acceptable'
valid_status = ['bad', 'spoiled', 'acceptable']
df = df[df['status'].isin(valid_status)]

# Drop rows with NaN values (if any)
df = df.dropna()

# Features and Target
X = df[['titrable_acidity', 'temperature', 'pH', 'conductivity']]
y = df['status'].map({'bad': 0, 'spoiled': 1, 'acceptable': 2})

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize models
models = {
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'SVM': SVC(random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(random_state=42)
}

# Train and Evaluate models
accuracies = {}

for name, model in models.items():
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    
    acc = accuracy_score(y_test, predictions)
    accuracies[name] = acc
    
    print(f"\n{name} Accuracy: {acc:.4f}")
    print(f"{name} Classification Report:")
    print(classification_report(y_test, predictions, zero_division=1))  # Added zero_division=1 to suppress warnings

# Select and save the best model
best_model_name = max(accuracies, key=accuracies.get)
best_model = models[best_model_name]
joblib.dump(best_model, 'best_milk_quality_model.pkl')

print(f"\nBest model ({best_model_name}) saved as 'best_milk_quality_model.pkl'")
