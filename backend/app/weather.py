import os
import random

import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_DESCRIPTIONS = {
    0: "ясно",
    1: "преимущественно ясно",
    2: "переменная облачность",
    3: "пасмурно",
    45: "туман",
    48: "изморозь",
    51: "слабая морось",
    53: "морось",
    55: "сильная морось",
    56: "ледяная морось",
    57: "сильная ледяная морось",
    61: "небольшой дождь",
    63: "дождь",
    65: "сильный дождь",
    66: "ледяной дождь",
    67: "сильный ледяной дождь",
    71: "небольшой снег",
    73: "снег",
    75: "сильный снег",
    77: "снежная крупа",
    80: "небольшой ливень",
    81: "ливень",
    82: "сильный ливень",
    85: "снегопад",
    86: "сильный снегопад",
    95: "гроза",
    96: "гроза с градом",
    99: "сильная гроза с градом",
}

GUESS_RESPONSES = [
    "Похоже, сегодня солнечно.",
    "Судя по всему, облачно.",
    "Кажется, собирается дождь.",
    "Вероятно, прохладно и ветрено.",
    "Похоже на снег.",
    "Возможно, туман.",
    "Скорее всего, тепло и ясно.",
]


def enabled():
    value = os.environ.get("WEATHER_ENABLED", "true").strip().lower()
    return value not in ("0", "false", "no", "off")


def _timeout():
    try:
        return float(os.environ.get("WEATHER_TIMEOUT", "5"))
    except ValueError:
        return 5.0


def _http_get_json(url, params):
    with httpx.Client(timeout=_timeout()) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def _guess():
    return random.choice(GUESS_RESPONSES) + " ⚠ Это догадка: актуальные данные получить не удалось."


def _format(name, current):
    temperature = current.get("temperature_2m")
    feels_like = current.get("apparent_temperature")
    wind = current.get("wind_speed_10m")
    code = current.get("weather_code")

    if isinstance(temperature, (int, float)):
        temperature_text = f"{temperature:+.0f} °C"
    else:
        temperature_text = "температура неизвестна"

    feels_text = ""
    if isinstance(feels_like, (int, float)):
        feels_text = f" (ощущается {feels_like:+.0f})"

    wind_text = ""
    if isinstance(wind, (int, float)):
        wind_text = f", ветер {wind:.0f} м/с"

    description = WMO_DESCRIPTIONS.get(code, "без осадков")
    return f"Погода в {name}: {temperature_text}{feels_text}, {description}{wind_text}."


def describe(city):
    city = (city or "").strip()
    if not city:
        return "Уточните, пожалуйста, город.", True

    if not enabled():
        return _guess(), False

    try:
        geo = _http_get_json(
            GEOCODE_URL,
            {"name": city, "count": 1, "language": "ru", "format": "json"},
        )
        results = geo.get("results") or []
        if not results:
            return f"Не нашёл город «{city}». Уточните название, пожалуйста.", True

        place = results[0]
        forecast = _http_get_json(
            FORECAST_URL,
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
        )
        return _format(place.get("name", city), forecast.get("current", {})), False
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        return _guess(), False


def resolve(city):
    reply, retry = describe(city)
    if retry:
        return {"reply": reply, "retry": True, "step": "city"}
    return {"reply": reply}
