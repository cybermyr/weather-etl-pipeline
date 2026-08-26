def transform_weather_data(raw_data):
    if raw_data is None:
        return None

    cleaned_data = {
        "city": raw_data["location"]["name"],
        "temperature": raw_data["current"]["temp_c"],
        "humidity": raw_data["current"]["humidity"],
        "wind_speed": raw_data["current"]["wind_kph"]
    }
    return cleaned_data