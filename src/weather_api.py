"""
Client Open-Meteo pour les données météo de Dakar.
API gratuite, sans clé : https://open-meteo.com/
"""
import logging
from datetime import datetime, timedelta

import requests
import pandas as pd

logger = logging.getLogger(__name__)

_DAKAR_LAT = 14.7167
_DAKAR_LON = -17.4677
_TIMEOUT   = 10


def get_current_weather_dakar() -> dict | None:
    """
    Retourne les conditions météo actuelles à Dakar.
    Clés : temperature (°C), humidity (%), wind_speed (km/h), timestamp (str ISO).
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={_DAKAR_LAT}&longitude={_DAKAR_LON}"
        "&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        "&wind_speed_unit=kmh"
    )
    try:
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        current = resp.json()['current']
        return {
            'temperature': current['temperature_2m'],
            'humidity':    current['relative_humidity_2m'],
            'wind_speed':  current['wind_speed_10m'],
            'timestamp':   current['time'],
        }
    except Exception as e:
        logger.warning(f"get_current_weather_dakar failed: {e}")
        return None


def get_weather_forecast_7days() -> list[dict] | None:
    """
    Retourne les prévisions météo sur 7 jours pour Dakar.
    Chaque entrée : date, temp_max, temp_min, precipitation, wind_max.
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={_DAKAR_LAT}&longitude={_DAKAR_LON}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max"
        "&wind_speed_unit=kmh&timezone=Africa%2FDakar"
    )
    try:
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        daily = resp.json()['daily']
        return [
            {
                'date':          daily['time'][i],
                'temp_max':      daily['temperature_2m_max'][i],
                'temp_min':      daily['temperature_2m_min'][i],
                'precipitation': max(0.0, daily['precipitation_sum'][i] or 0.0),
                'wind_max':      daily['wind_speed_10m_max'][i],
            }
            for i in range(len(daily['time']))
        ]
    except Exception as e:
        logger.warning(f"get_weather_forecast_7days failed: {e}")
        return None


def get_historical_weather_dakar(days: int = 30) -> pd.DataFrame | None:
    """
    Retourne les données météo historiques sur `days` jours pour Dakar.
    Colonnes : date, temp_mean, precipitation, wind_max.
    """
    end_date   = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={_DAKAR_LAT}&longitude={_DAKAR_LON}"
        f"&start_date={start_date}&end_date={end_date}"
        "&daily=temperature_2m_mean,precipitation_sum,wind_speed_10m_max"
        "&wind_speed_unit=kmh&timezone=Africa%2FDakar"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        daily = resp.json()['daily']
        return pd.DataFrame({
            'date':          daily['time'],
            'temp_mean':     daily['temperature_2m_mean'],
            'precipitation': daily['precipitation_sum'],
            'wind_max':      daily['wind_speed_10m_max'],
        })
    except Exception as e:
        logger.warning(f"get_historical_weather_dakar failed: {e}")
        return None
