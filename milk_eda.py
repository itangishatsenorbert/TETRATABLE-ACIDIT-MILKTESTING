import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Load the dataset
df = pd.read_csv('milk_data.csv')

# Remove any unnamed columns (e.g., 'Unnamed: 6')
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

# Basic Information
print(f"Data shape: {df.shape}")
print(f"Data types:\n{df.dtypes}")
print(f"Null values:\n{df.isnull().sum()}")

# Standardize 'status' column to uppercase and convert to string
df['status'] = df['status'].astype(str).str.upper()

# Handle missing or inconsistent labels
valid_labels = ['BAD', 'SPOILED', 'ACCEPTABLE']
df = df[df['status'].isin(valid_labels)]  # Keep only valid labels
df['status'] = df['status'].fillna(df['status'].mode()[0])  # Just in case

# Recheck the shape of the data after cleaning
print(f"Data shape after cleaning: {df.shape}")

# Summary statistics
print(f"Summary statistics:\n{df.describe()}")

# Visualizations
df.hist(bins=20, figsize=(12, 8))
plt.suptitle('Histograms of Numerical Features')
plt.show()

plt.figure(figsize=(12, 8))
sns.boxplot(data=df[['titrable_acidity', 'temperature', 'pH', 'conductivity']])
plt.title('Boxplots of Features')
plt.show()

corr = df[['titrable_acidity', 'temperature', 'pH', 'conductivity']].corr()
plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
plt.title('Correlation Matrix')
plt.show()

plt.figure(figsize=(8, 6))
sns.scatterplot(data=df, x='temperature', y='conductivity', hue='status', palette='coolwarm')
plt.title('Temperature vs Conductivity')
plt.show()

plt.figure(figsize=(8, 6))
sns.scatterplot(data=df, x='titrable_acidity', y='conductivity', hue='status', palette='coolwarm')
plt.title('Titrable Acidity vs Conductivity')
plt.show()

# Fixed the hue warning for countplot
plt.figure(figsize=(8, 6))
sns.countplot(x='status', data=df, hue='status', palette='Set2')
plt.title('Distribution of Status')
plt.show()

sns.pairplot(df[['titrable_acidity', 'temperature', 'pH', 'conductivity', 'status']], hue='status', palette='coolwarm')
plt.suptitle('Pairplot of Features')
plt.show()

# --------------------------------------------------------------------------------------
# Add 'acidity_status' column
# --------------------------------------------------------------------------------------
def classify_acidity(row):
    if row['titrable_acidity'] >= 0.15 and row['pH'] <= 6.5 and row['conductivity'] >= 1.1:
        return 'High Acidity'
    elif row['titrable_acidity'] <= 0.13 and row['pH'] >= 6.6 and row['conductivity'] <= 1.0:
        return 'Low Acidity'
    else:
        return 'Normal Acidity'

df['acidity_status'] = df.apply(classify_acidity, axis=1)

plt.figure(figsize=(8, 6))
sns.countplot(x='acidity_status', data=df, palette='Set3')
plt.title('Distribution of Acidity Status')
plt.show()

# Save cleaned data
df.to_csv('cleaned_milk_data.csv', index=False)
print("Cleaned data saved to 'cleaned_milk_data.csv'")

# --------------------------------------------------------------------------------------
# Train RandomForest Model
# --------------------------------------------------------------------------------------

# Prepare features and target
X = df[['titrable_acidity', 'temperature', 'pH', 'conductivity']]
y = df['status'].map({'BAD': 0, 'SPOILED': 1, 'ACCEPTABLE': 2})  # Map after cleaning

# Final check for NaN in y
if y.isnull().sum() > 0:
    print("Warning: Some values in target are still NaN. Dropping them.")
    df = df[~y.isnull()]
    X = df[['titrable_acidity', 'temperature', 'pH', 'conductivity']]
    y = df['status'].map({'BAD': 0, 'SPOILED': 1, 'ACCEPTABLE': 2})

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predict and evaluate
y_pred = model.predict(X_test)
print(f"Accuracy Score: {accuracy_score(y_test, y_pred)}")
print("Classification Report:")
print(classification_report(y_test, y_pred))

# Save the model
joblib.dump(model, 'milk_quality_model.pkl')
print("Model saved as 'milk_quality_model.pkl'")
