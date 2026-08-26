
import pytest

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

        assert result == {
            "city": "Tunis",
            "temperature": 31.5,
            "humidity": 45,
            "wind_speed": 14.4,
        }

    def test_ignores_extra_fields_from_api(self, raw_weatherapi_payload):
        result = transform_weather_data(raw_weatherapi_payload)
        assert set(result.keys()) == {"city", "temperature", "humidity", "wind_speed"}

    def test_handles_zero_values(self):
        raw_data = {
            "location": {"name": "Moscou"},
            "current": {"temp_c": -5.0, "humidity": 0, "wind_kph": 0},
        }
        result = transform_weather_data(raw_data)
        assert result["humidity"] == 0
        assert result["wind_speed"] == 0

    def test_handles_negative_temperature(self):
        raw_data = {
            "location": {"name": "Moscou"},
            "current": {"temp_c": -12.3, "humidity": 80, "wind_kph": 5.0},
        }
        result = transform_weather_data(raw_data)
        assert result["temperature"] == -12.3


class TestTransformMalformedInput:
   

    def test_raises_keyerror_when_location_missing(self):
        raw_data = {"current": {"temp_c": 20, "humidity": 50, "wind_kph": 10}}
        with pytest.raises(KeyError):
            transform_weather_data(raw_data)

    def test_raises_keyerror_when_current_missing(self):
        raw_data = {"location": {"name": "Paris"}}
        with pytest.raises(KeyError):
            transform_weather_data(raw_data)

    def test_raises_keyerror_when_current_field_missing(self):
        raw_data = {
            "location": {"name": "Paris"},
            "current": {"temp_c": 20, "humidity": 50},  
        }
        with pytest.raises(KeyError):
            transform_weather_data(raw_data)

    def test_raises_typeerror_on_empty_dict(self):
        with pytest.raises(KeyError):
            transform_weather_data({})