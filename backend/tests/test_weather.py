import httpx

from app import storage, weather
from app.engine import build_engine


def _success_transport():
    def fake(url, params):
        if url == weather.GEOCODE_URL:
            return {"results": [{"name": "Москва", "latitude": 55.75, "longitude": 37.62}]}
        return {
            "current": {
                "temperature_2m": 5.2,
                "apparent_temperature": 2.1,
                "weather_code": 3,
                "wind_speed_10m": 3.4,
            }
        }

    return fake


def test_describe_success(monkeypatch):
    monkeypatch.setattr(weather, "_http_get_json", _success_transport())
    reply, retry = weather.describe("Москва")
    assert retry is False
    assert "Москва" in reply
    assert "+5" in reply
    assert "пасмурно" in reply


def test_describe_network_error_returns_guess(monkeypatch):
    def boom(url, params):
        raise httpx.ConnectError("нет сети")

    monkeypatch.setattr(weather, "_http_get_json", boom)
    reply, retry = weather.describe("Москва")
    assert retry is False
    assert "догадка" in reply.lower()


def test_describe_city_not_found_retries(monkeypatch):
    monkeypatch.setattr(weather, "_http_get_json", lambda url, params: {"results": []})
    reply, retry = weather.describe("Абракадабрск")
    assert retry is True
    assert "не нашёл" in reply.lower()


def test_weather_disabled_returns_guess(monkeypatch):
    monkeypatch.setenv("WEATHER_ENABLED", "false")
    reply, retry = weather.describe("Москва")
    assert retry is False
    assert "догадка" in reply.lower()


def test_weather_flow_via_engine(monkeypatch):
    monkeypatch.setattr(weather, "_http_get_json", _success_transport())
    engine = build_engine()
    session_id = "weather-flow"
    storage.reset_session(session_id)

    step = engine.process(session_id, "Какая погода?")
    assert step["state"] == "flow.weather.city"

    result = engine.process(session_id, "Москва")
    assert result["state"] == "idle"
    assert "Москва" in result["reply"]


def test_weather_flow_retries_unknown_city(monkeypatch):
    monkeypatch.setattr(weather, "_http_get_json", lambda url, params: {"results": []})
    engine = build_engine()
    session_id = "weather-retry"
    storage.reset_session(session_id)

    engine.process(session_id, "Какая погода?")
    result = engine.process(session_id, "Абракадабрск")
    assert result["state"] == "flow.weather.city"
    assert "не нашёл" in result["reply"].lower()
