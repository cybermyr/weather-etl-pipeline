import logging

from db import save_to_db
from extract import get_weather
from transform import transform_weather_data

CITIES = [
    "Tunis", "Rome", "Paris", "London", "New York",
    "Tokyo", "Sydney", "Moscow", "Beijing", "Rio de Janeiro",
]


def configure_logging():
    """Configure le logging global de l'application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_pipeline():
    """Exécute le pipeline ETL pour toutes les villes.

    Returns:
        tuple[int, int]: (nombre de succès, nombre d'échecs).
    """
    logger = logging.getLogger(__name__)
    logger.info("=== Démarrage du pipeline (%d villes) ===", len(CITIES))

    success_count = 0
    failure_count = 0

    for city in CITIES:
        raw_data = get_weather(city)
        cleaned_data = transform_weather_data(raw_data)

        if save_to_db(cleaned_data):
            success_count += 1
        else:
            failure_count += 1

    logger.info(
        "=== Pipeline terminé : %d succès, %d échec(s) ===",
        success_count,
        failure_count,
    )
    return success_count, failure_count


if __name__ == "__main__":
    configure_logging()
    run_pipeline()