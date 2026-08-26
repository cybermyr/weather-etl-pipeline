
import requests
import pytest
from unittest.mock import patch, MagicMock

import extract


def _fake_response(json_data, status_code=200):
    """Construit un mock de requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{status_code} Error"
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


class TestGetWeatherSuccess:
    def test_returns_json_on_success(self, monkeypatch):
        monkeypatch.setattr(extract, "API_KEY", "fake_key")
        payload = {
            "location": {"name": "Tunis"},
            "current": {"temp_c": 28.0, "humidity": 40, "wind_kph": 12.0},
        }
        with patch.object(extract.requests, "get", return_value=_fake_response(payload)) as mock_get:
            result = extract.get_weather("Tunis")

        assert result == payload
        mock_get.assert_called_once()

    def test_calls_correct_url_and_params(self, monkeypatch):
        monkeypatch.setattr(extract, "API_KEY", "fake_key")
        with patch.object(extract.requests, "get", return_value=_fake_response({})) as mock_get:
            extract.get_weather("Paris")

        args, kwargs = mock_get.call_args
        assert args[0] == extract.BASE_URL
        assert kwargs["params"] == {"key": "fake_key", "q": "Paris"}
        assert kwargs["timeout"] == extract.REQUEST_TIMEOUT


class TestGetWeatherMissingApiKey:
    def test_returns_none_when_api_key_missing(self, monkeypatch):
        monkeypatch.setattr(extract, "API_KEY", None)
        with patch.object(extract.requests, "get") as mock_get:
            result = extract.get_weather("Tunis")

        assert result is None
        mock_get.assert_not_called()

    def test_returns_none_when_api_key_empty_string(self, monkeypatch):
        monkeypatch.setattr(extract, "API_KEY", "")
        result = extract.get_weather("Tunis")
        assert result is None


class TestGetWeatherErrors:
    def test_returns_none_on_timeout(self, monkeypatch):
        monkeypatch.setattr(extract, "API_KEY", "fake_key")
        with patch.object(
            extract.requests, "get", side_effect=requests.exceptions.Timeout
        ):
            result = extract.get_weather("Rome")

        assert result is None

    def test_returns_none_on_http_error(self, monkeypatch):
        monkeypatch.setattr(extract, "API_KEY", "fake_key")
        bad_response = _fake_response({}, status_code=404)
        with patch.object(extract.requests, "get", return_value=bad_response):
            result = extract.get_weather("VilleInconnue")

        assert result is None

    def test_returns_none_on_network_error(self, monkeypatch):
        monkeypatch.setattr(extract, "API_KEY", "fake_key")
        with patch.object(
            extract.requests,
            "get",
            side_effect=requests.exceptions.ConnectionError,
        ):
            result = extract.get_weather("Tokyo")

        assert result is None

    def test_one_city_failure_does_not_raise(self, monkeypatch):
        """get_weather ne doit jamais lever d'exception vers l'appelant."""
        monkeypatch.setattr(extract, "API_KEY", "fake_key")
        with patch.object(
            extract.requests,
            "get",
            side_effect=requests.exceptions.RequestException("boom"),
        ):
            result = extract.get_weather("Moscou")

        assert result is None


class TestGetWeatherLogging:
    def test_logs_error_on_missing_api_key(self, monkeypatch, caplog):
        monkeypatch.setattr(extract, "API_KEY", None)
        with caplog.at_level("ERROR"):
            extract.get_weather("Tunis")
        assert any("API_KEY" in record.message for record in caplog.records)

    def test_logs_info_on_success(self, monkeypatch, caplog):
        monkeypatch.setattr(extract, "API_KEY", "fake_key")
        payload = {"location": {"name": "Sydney"}, "current": {}}
        with patch.object(extract.requests, "get", return_value=_fake_response(payload)):
            with caplog.at_level("INFO"):
                extract.get_weather("Sydney")
        assert any("Sydney" in record.message for record in caplog.records)