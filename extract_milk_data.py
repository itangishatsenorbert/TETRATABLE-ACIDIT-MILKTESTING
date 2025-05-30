import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

# Database connection parameters (replace these with your actual credentials)
host = 'localhost'  
database = 'milk_sensor_data'  
user = 'root'  
password = ''  

# Create connection using SQLAlchemy (can be used for MySQL, PostgreSQL, etc.)
engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{database}')

# SQL query to fetch required data (adjust the table name and columns as per your schema)
query = """
    SELECT titrable_acidity, temperature, pH, conductivity, status, created_at
    FROM milk_test  -- Replace with your actual table name
    WHERE conductivity IS NOT NULL  -- Ensure you're fetching rows with valid conductivity
"""

# Fetch the data into a pandas DataFrame
df = pd.read_sql(query, engine)

# Format the 'created_at' column to a proper datetime format
df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')

# Save the data to a CSV file
df.to_csv('milk_data.csv', index=False)

# Confirm success
print(f"Data successfully fetched and saved to 'milk_data.csv'")
