import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY")
BASE_URL = "http://api.weatherapi.com/v1/current.json"
REQUEST_TIMEOUT = 10  

def get_weather(city):
  
    if not API_KEY:
        logger.error("API_KEY manquante : vérifie ton fichier .env")
        return None

    params = {"key": API_KEY, "q": city}

    try:
        response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Timeout lors de la requête pour la ville '%s'", city)
        return None
    except requests.exceptions.HTTPError as err:
        logger.error("Erreur HTTP pour '%s' : %s", city, err)
        return None
    except requests.exceptions.RequestException as err:
        logger.error("Erreur réseau pour '%s' : %s", city, err)
        return None

    logger.info("Données météo récupérées avec succès pour '%s'", city)
    return response.json()