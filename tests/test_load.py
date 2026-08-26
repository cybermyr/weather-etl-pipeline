
import pandas as pd
import pytest
import mysql.connector
from unittest.mock import patch, MagicMock

import db


VALID_DATA = {
    "city": "Tunis",
    "temperature": 30.0,
    "humidity": 40,
    "wind_speed": 10.0,
}


class TestConnectionConfig:
    def test_uses_defaults_when_env_vars_missing(self, monkeypatch):
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.delenv("DB_USER", raising=False)
        monkeypatch.delenv("DB_NAME", raising=False)
        config = db._connection_config()

        assert config["host"] == "localhost"
        assert config["user"] == "root"
        assert config["database"] == "weather_db"

    def test_ssl_not_set_without_ca(self, monkeypatch):
        monkeypatch.setattr(db, "DB_SSL_CA", None)
        config = db._connection_config()
        assert "ssl_ca" not in config

    def test_ssl_enabled_when_ca_provided(self, monkeypatch):
        monkeypatch.setattr(db, "DB_SSL_CA", "/path/to/ca.pem")
        config = db._connection_config()
        assert config["ssl_ca"] == "/path/to/ca.pem"
        assert config["ssl_verify_cert"] is True


class TestGetConnection:
    def test_closes_connection_on_success(self):
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True

        with patch.object(db.mysql.connector, "connect", return_value=mock_conn):
            with db.get_connection() as conn:
                assert conn is mock_conn

        mock_conn.close.assert_called_once()

    def test_closes_connection_even_on_error_inside_block(self):
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True

        with patch.object(db.mysql.connector, "connect", return_value=mock_conn):
            with pytest.raises(ValueError):
                with db.get_connection() as conn:
                    raise ValueError("erreur pendant l'utilisation de la connexion")

        mock_conn.close.assert_called_once()

    def test_raises_and_logs_when_connect_fails(self):
        with patch.object(
            db.mysql.connector,
            "connect",
            side_effect=mysql.connector.Error("connexion refusée"),
        ):
            with pytest.raises(mysql.connector.Error):
                with db.get_connection():
                    pass

    def test_does_not_close_if_never_connected(self):
        """Si connect() lève avant d'assigner conn, close() ne doit pas
        être appelé sur un objet inexistant (pas de crash secondaire)."""
        with patch.object(
            db.mysql.connector,
            "connect",
            side_effect=mysql.connector.Error("boom"),
        ):
            with pytest.raises(mysql.connector.Error):
                with db.get_connection():
                    pass
        # Le test réussit simplement si aucune exception secondaire n'est levée.


class TestSaveToDb:
    def test_returns_false_when_data_is_none(self):
        assert db.save_to_db(None) is False

    def test_returns_true_and_commits_on_success(self):
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(db.mysql.connector, "connect", return_value=mock_conn):
            result = db.save_to_db(VALID_DATA)

        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_execute_called_with_correct_values(self):
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(db.mysql.connector, "connect", return_value=mock_conn):
            db.save_to_db(VALID_DATA)

        _, values = mock_cursor.execute.call_args[0]
        assert values == ("Tunis", 30.0, 40, 10.0)

    def test_returns_false_on_db_error(self):
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = mysql.connector.Error("table inconnue")
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(db.mysql.connector, "connect", return_value=mock_conn):
            result = db.save_to_db(VALID_DATA)

        assert result is False
        mock_conn.commit.assert_not_called()

    def test_returns_false_when_connect_fails(self):
        with patch.object(
            db.mysql.connector,
            "connect",
            side_effect=mysql.connector.Error("connexion refusée"),
        ):
            result = db.save_to_db(VALID_DATA)

        assert result is False


class TestGetAllData:
    def test_returns_dataframe_on_success(self):
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        expected_df = pd.DataFrame(
            [{"city": "Tunis", "temperature": 30.0, "humidity": 40, "wind_speed": 10.0}]
        )

        with patch.object(db.mysql.connector, "connect", return_value=mock_conn):
            with patch.object(db.pd, "read_sql", return_value=expected_df):
                result = db.get_all_data()

        pd.testing.assert_frame_equal(result, expected_df)

    def test_returns_empty_dataframe_on_db_error(self):
        with patch.object(
            db.mysql.connector,
            "connect",
            side_effect=mysql.connector.Error("connexion refusée"),
        ):
            result = db.get_all_data()

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_returns_empty_dataframe_on_pandas_error(self):
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True

        with patch.object(db.mysql.connector, "connect", return_value=mock_conn):
            with patch.object(
                db.pd,
                "read_sql",
                side_effect=pd.errors.DatabaseError("requête invalide"),
            ):
                result = db.get_all_data()

        assert isinstance(result, pd.DataFrame)
        assert result.empty