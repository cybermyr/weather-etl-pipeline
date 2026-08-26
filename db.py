import os
import logging
from contextlib import contextmanager

import mysql.connector
import pandas as pd
import dotenv

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

# Activé en posant DB_SSL_CA dans le .env (obligatoire sur Azure).
DB_SSL_CA = os.getenv("DB_SSL_CA")


def _connection_config():
    """Construit la configuration de connexion à partir des variables d'env."""
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME", "weather_db"),
    }
    # Azure Database for MySQL impose le SSL.
    if DB_SSL_CA:
        config["ssl_ca"] = DB_SSL_CA
        config["ssl_verify_cert"] = True
    return config


@contextmanager
def get_connection():
    """Fournit une connexion MySQL et garantit sa fermeture.

    Usage:
        with get_connection() as conn:
            ...
    """
    conn = None
    try:
        conn = mysql.connector.connect(**_connection_config())
        yield conn
    except mysql.connector.Error as err:
        logger.error("Erreur de connexion à la base : %s", err)
        raise
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


def save_to_db(data):
    """Insère ou met à jour une ligne météo (upsert).

    Args:
        data (dict | None): données nettoyées issues de transform.

    Returns:
        bool: True si l'écriture a réussi, False sinon.
    """
    if data is None:
        logger.warning("Aucune donnée à sauvegarder (data est None)")
        return False

    sql = """
        INSERT INTO weather (city, temperature, humidity, wind_speed)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            temperature = VALUES(temperature),
            humidity = VALUES(humidity),
            wind_speed = VALUES(wind_speed)
    """
    values = (
        data["city"],
        data["temperature"],
        data["humidity"],
        data["wind_speed"],
    )

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            cursor.close()
    except mysql.connector.Error as err:
        logger.error("Échec de l'écriture pour '%s' : %s", data["city"], err)
        return False

    logger.info("Données enregistrées pour '%s'", data["city"])
    return True


def get_all_data():
    """Lit toutes les données météo, les plus récentes d'abord.

    Returns:
        pd.DataFrame: les données, ou un DataFrame vide en cas d'erreur.
    """
    sql = "SELECT * FROM weather ORDER BY created_at DESC"
    try:
        with get_connection() as conn:
            df = pd.read_sql(sql, conn)
    except (mysql.connector.Error, pd.errors.DatabaseError) as err:
        logger.error("Échec de la lecture des données : %s", err)
        return pd.DataFrame()

    logger.info("%d lignes lues depuis la base", len(df))
    return df