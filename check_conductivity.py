import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv('milk_data.csv')

# Check if 'conductivity' column exists
if 'conductivity' in df.columns:
    print("The 'conductivity' column is present.")
else:
    print("The 'conductivity' column is missing.")

# Optionally, print the column names to check them
print("Columns in the CSV:", df.columns)
