# database.py
import os
import mysql.connector
import pandas as pd
import dotenv 
dotenv.load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "weather_db")
    )

# écriture
def save_to_db(data):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
INSERT INTO weather (city, temperature, humidity, wind_speed)
VALUES (%s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
temperature = VALUES(temperature),
humidity = VALUES(humidity),
wind_speed = VALUES(wind_speed)
"""
    cursor.execute(sql, (data["city"], data["temperature"], data["humidity"], data["wind_speed"]))
    conn.commit()
    cursor.close()
    conn.close()

# lecture
def get_all_data():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM weather ORDER BY created_at DESC", conn)
    conn.close()
    return df