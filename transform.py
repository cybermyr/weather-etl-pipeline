from pydantic import ValidationError

from models import WeatherReading


def transform_weather_data(raw_data):

    if raw_data is None:
        return None

    location = raw_data.get("location", {})
    current = raw_data.get("current", {})

    try:
        return WeatherReading(
            city=location.get("name"),
            temperature=current.get("temp_c"),
            humidity=current.get("humidity"),
            wind_speed=current.get("wind_kph"),
        )
    except ValidationError as err:
        print(f"Invalid weather data, rejected: {err}")
        return None