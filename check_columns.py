import pandas as pd
import pymysql
from sqlalchemy import create_engine

# Connect to your database
db_connection_str = 'mysql+pymysql://root:@localhost/milk_sensor_data'
engine = create_engine(db_connection_str)

# Load the table
df = pd.read_sql('SELECT * FROM milk_test', con=engine)

# Print all column names
print(df.columns)
