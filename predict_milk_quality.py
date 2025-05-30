import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder

# Load the saved model, scaler, and label encoder
model = joblib.load('milk_quality_model.pkl')
scaler = joblib.load('scaler.pkl')
label_encoder = joblib.load('label_encoder.pkl')

# Load new data (replace 'new_data.csv' with the actual path of the new data file)
new_data = pd.read_csv('new_data.csv')

# Check the structure of the new data to ensure it's consistent
print("\nFirst 5 rows of new data:")
print(new_data.head())

# Make sure the new data contains the same features as the training data
required_features = ['titrable_acidity', 'temperature', 'pH', 'conductivity']
for feature in required_features:
    if feature not in new_data.columns:
        print(f"Warning: '{feature}' is missing from the new data.")
        # You can choose how to handle missing features, like setting them to 0 or using mean/median imputation.
        new_data[feature] = 0  # Example: Filling missing features with 0 (You can change this logic)

# Preprocess the new data (Standardizing the numerical columns)
new_data_scaled = scaler.transform(new_data[['titrable_acidity', 'temperature', 'pH', 'conductivity']])

# Make predictions
predictions = model.predict(new_data_scaled)

# Decode the predictions (from numerical values back to the original 'status' labels)
decoded_predictions = label_encoder.inverse_transform(predictions)

# Add the predicted labels to the new data
new_data['predicted_status'] = decoded_predictions

# Show the results with the predictions
print("\nPredictions for new data:")
print(new_data)

# Save the predictions to a new CSV file
new_data.to_csv('predicted_milk_status.csv', index=False)
print("\nPredictions saved to 'predicted_milk_status.csv'!")
