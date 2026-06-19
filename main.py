from extract import get_weather
from transform import transform_weather_data
from db import save_to_db
cities=["Tunis", "Rome", "Paris", "London", "New York", "Tokyo", "Sydney", "Moscow", "Beijing", "Rio de Janeiro"]


def run_pipeline():
    for city in cities:
        data_raw = get_weather(city)

        print("Ville demandée :", city)
        print("Ville API :", data_raw["location"]["name"])

        data_cleaned = transform_weather_data(data_raw)

        print(data_cleaned)

        save_to_db(data_cleaned)


if __name__ == "__main__":
    run_pipeline()