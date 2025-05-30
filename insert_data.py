from flask import Flask, render_template, jsonify, send_file
import mysql.connector
import serial
import threading
import time
from datetime import datetime
import os
from collections import deque
import logging
import socket 
import pandas as pd
from sqlalchemy import create_engine
import joblib
import pickle
from werkzeug.serving import WSGIRequestHandler

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
CONFIG = {
    'db': {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'milk_sensor_data'
    },
    'serial': {
        'port': 'COM3',
        'baudrate': 9600,
        'timeout': 2
    }
}

# SQLAlchemy Engine
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{CONFIG['db']['user']}:{CONFIG['db']['password']}@{CONFIG['db']['host']}/{CONFIG['db']['database']}"
engine = create_engine(SQLALCHEMY_DATABASE_URI)

# Load model and scaler
model = joblib.load('milk_quality_model.pkl')
scaler = joblib.load('scaler.pkl')

# Data buffers
DATA_BUFFER = {
    'ta': deque(maxlen=20),
    'temp': deque(maxlen=20),
    'ph': deque(maxlen=20),
    'cond': deque(maxlen=20),
    'time': deque(maxlen=20),
    'status': deque(maxlen=20),
    'prediction': deque(maxlen=20),
    'errors': deque(maxlen=5)
}

# Database connection pool
DB_POOL = []
DB_POOL_SIZE = 5

def init_db_pool():
    global DB_POOL
    DB_POOL = []
    for _ in range(DB_POOL_SIZE):
        conn = create_database_connection()
        if conn:
            DB_POOL.append(conn)

def get_db_connection():
    if not DB_POOL:
        init_db_pool()
    return DB_POOL.pop() if DB_POOL else create_database_connection()

def release_db_connection(conn):
    if conn and len(DB_POOL) < DB_POOL_SIZE:
        DB_POOL.append(conn)
    elif conn:
        conn.close()

def create_database_connection():
    for attempt in range(3):
        try:
            conn = mysql.connector.connect(**CONFIG['db'])
            return conn
        except mysql.connector.Error as e:
            logger.error(f"DB connection error (attempt {attempt+1}): {e}")
            time.sleep(2)
    return None

def buffer_sensor_data(data):
    timestamp = datetime.now().strftime("%H:%M:%S")
    for key in ['ta', 'temp', 'ph', 'cond']:
        DATA_BUFFER[key].append(data[key])
    DATA_BUFFER['time'].append(timestamp)
    DATA_BUFFER['status'].append(data['status'])
    logger.info(f"Buffered data: {DATA_BUFFER}")

def insert_sensor_data(data):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Database connection failed.")
            return False

        cursor = conn.cursor()
        logger.info(f"Inserting into milk_test: {data}")

        cursor.execute(""" 
            INSERT INTO milk_test (titrable_acidity, temperature, pH, conductivity, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['ta'],
            data['temp'],
            data['ph'],
            data['cond'],
            data['status'],
            datetime.now()
        ))
        conn.commit()
        logger.info("Data inserted successfully.")

        milk_data = {
            'titrable_acidity': data['ta'],
            'temperature': data['temp'],
            'ph': data['ph'],
            'conductivity': data['cond'],
            'status': data['status'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        milk_data_df = pd.DataFrame([milk_data])
        milk_data_df.to_csv('milk_data.csv', mode='a', header=not os.path.exists('milk_data.csv'), index=False)
        logger.info("Data saved to milk_data.csv.")

        return True
    except mysql.connector.Error as e:
        logger.error(f"MySQL error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db_connection(conn)

def parse_serial_data(line):
    try:
        logger.debug(f"Raw sensor data: {line}")
        if not line.strip():
            logger.error("Received empty line from Arduino.")
            return None
        if "SIMULATION_MODE" in line or "READY" in line:
            logger.warning("Arduino is in simulation/ready mode.")
            return None

        data = {}
        for pair in line.split(','):
            if '=' in pair:
                key, value = pair.split('=', 1)
                try:
                    data[key.strip()] = float(value) if '.' in value else value
                except ValueError:
                    logger.error(f"Invalid value for key '{key}': {value}")
                    return None

        required = ['TA', 'Temp', 'pH', 'Conductivity']
        if all(k in data for k in required):
            parsed_data = {
                'ta': data['TA'],
                'temp': data['Temp'],
                'ph': data['pH'],
                'cond': data['Conductivity'],
                'status': data.get('Status', 'Unknown')
            }
            logger.debug(f"Parsed data: {parsed_data}")
            return parsed_data
        else:
            logger.error("Missing required fields in sensor data.")
            return None
    except Exception as e:
        logger.error(f"Parse error: {e}")
        return None

def serial_reader():
    ser = None
    while True:
        try:
            if ser is None or not ser.is_open:
                logger.info(f"Connecting to serial port {CONFIG['serial']['port']}...")
                ser = serial.Serial(**CONFIG['serial'])
                logger.info("Connected to serial port.")
                ser.flushInput()

            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                logger.debug(f"Received: {line}")
                data = parse_serial_data(line)
                if data:
                    buffer_sensor_data(data)
                    insert_sensor_data(data)
        except serial.SerialException as e:
            logger.error(f"Serial error: {e}")
            if ser:
                ser.close()
            ser = None
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected serial reader error: {e}")
            if ser:
                ser.close()
            ser = None
            time.sleep(5)

@app.route('/')
def dashboard():
    try:
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Dashboard load error: {e}")
        return f"<h1>Error loading dashboard</h1><p>{str(e)}</p>", 500

@app.route('/api/realtime')
def get_realtime_data():
    ta = DATA_BUFFER['ta'][-1] 
    temp = DATA_BUFFER['temp'][-1] 
    ph = DATA_BUFFER['ph'][-1] 
    cond = DATA_BUFFER['cond'][-1] 
    latest_data = [ta, temp, ph, cond]
    
    model= pickle.load(open('./models training/decision_tree_model.pkl', 'rb'))
    try:
        columns = ['titrable_acidity', 'temperature', 'pH', 'conductivity']
        input_df = pd.DataFrame([latest_data], columns=columns)
        prediction = model.predict(input_df)[0]
    except Exception as e:
        print("Prediction error:", e)
        prediction = "Error during prediction", 500

    return jsonify({
        'ta': list(DATA_BUFFER['ta']),
        'temp': list(DATA_BUFFER['temp']),
        'ph': list(DATA_BUFFER['ph']),
        'cond': list(DATA_BUFFER['cond']),
        'time': list(DATA_BUFFER['time']),
        'status': list(DATA_BUFFER['status']),
        'prediction': prediction,
        'errors': list(DATA_BUFFER['errors']),
        'timestamp': datetime.now().isoformat()
    })

# ✅ CSV Download Route
@app.route('/download-csv')
def download_csv():
    try:
        return send_file('milk_data.csv', as_attachment=True)
    except Exception as e:
        logger.error(f"CSV download error: {e}")
        return f"Failed to download CSV: {str(e)}", 500

# Run the app
if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(base_dir, 'templates'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'static'), exist_ok=True)

    init_db_pool()
    threading.Thread(target=serial_reader, daemon=True).start()

    port = 5000
    host = '127.0.0.1'

    class FixedHandler(WSGIRequestHandler):
        def handle(self):
            self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            super().handle()

    app.run(
        host=host,
        port=port,
        debug=True,
        threaded=True,
        use_reloader=False,
        request_handler=FixedHandler
    )