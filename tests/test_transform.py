import pytest

from models import WeatherReading
from transform import transform_weather_data


class TestTransformNoneInput:
    def test_returns_none_when_input_is_none(self):
        assert transform_weather_data(None) is None


class TestTransformValidInput:
    @pytest.fixture
    def raw_weatherapi_payload(self):
        return {
            "location": {
                "name": "Tunis",
                "region": "Tunis",
                "country": "Tunisia",
            },
            "current": {
                "temp_c": 31.5,
                "temp_f": 88.7,
                "humidity": 45,
                "wind_kph": 14.4,
                "wind_mph": 8.9,
            },
        }

    def test_extracts_correct_fields(self, raw_weatherapi_payload):
        result = transform_weather_data(raw_weatherapi_payload)

        # result is now a WeatherReading object, not a dict:
        # compare via .model_dump() to get a plain dict back.
        assert isinstance(result, WeatherReading)
        assert result.model_dump() == {
            "city": "Tunis",
            "temperature": 31.5,
            "humidity": 45,
            "wind_speed": 14.4,
        }

    def test_ignores_extra_fields_from_api(self, raw_weatherapi_payload):
        result = transform_weather_data(raw_weatherapi_payload)
       
        assert set(result.model_dump().keys()) == {
            "city", "temperature", "humidity", "wind_speed"
        }

    def test_handles_zero_values(self):
        raw_data = {
            "location": {"name": "Moscow"},
            "current": {"temp_c": -5.0, "humidity": 0, "wind_kph": 0},
        }
        result = transform_weather_data(raw_data)
        assert result.humidity == 0
        assert result.wind_speed == 0

    def test_handles_negative_temperature(self):
        raw_data = {
            "location": {"name": "Moscow"},
            "current": {"temp_c": -12.3, "humidity": 80, "wind_kph": 5.0},
        }
        result = transform_weather_data(raw_data)
        assert result.temperature == -12.3


class TestTransformMalformedInput:
   

    def test_returns_none_when_location_missing(self):
        raw_data = {"current": {"temp_c": 20, "humidity": 50, "wind_kph": 10}}
        assert transform_weather_data(raw_data) is None

    def test_returns_none_when_current_missing(self):
        raw_data = {"location": {"name": "Paris"}}
        assert transform_weather_data(raw_data) is None

    def test_returns_none_when_current_field_missing(self):
        raw_data = {
            "location": {"name": "Paris"},
            "current": {"temp_c": 20, "humidity": 50},
        }
        assert transform_weather_data(raw_data) is None

    def test_returns_none_on_empty_dict(self):
        assert transform_weather_data({}) is None

    def test_returns_none_when_humidity_out_of_range(self):
       
        raw_data = {
            "location": {"name": "Paris"},
            "current": {"temp_c": 20, "humidity": 150, "wind_kph": 10},
        }
        assert transform_weather_data(raw_data) is None

    def test_returns_none_when_temperature_is_not_a_number(self):
        
        raw_data = {
            "location": {"name": "Paris"},
            "current": {"temp_c": "not-a-number", "humidity": 50, "wind_kph": 10},
        }
        assert transform_weather_data(raw_data) is None