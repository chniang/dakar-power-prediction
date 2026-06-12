import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from streamlit_app.utils_simple import create_time_features


def test_create_time_features_keys():
    result = create_time_features(datetime(2024, 6, 15, 14, 0))
    assert set(result.keys()) == {'hour', 'day_of_week', 'month', 'saison', 'is_peak_hour'}


def test_saison_juillet():
    result = create_time_features(datetime(2024, 7, 1, 12, 0))
    assert result['saison'] == 1


def test_saison_janvier():
    result = create_time_features(datetime(2024, 1, 1, 12, 0))
    assert result['saison'] == 0


def test_is_peak_hour_20h():
    result = create_time_features(datetime(2024, 6, 15, 20, 0))
    assert result['is_peak_hour'] == 1


def test_is_peak_hour_14h():
    result = create_time_features(datetime(2024, 6, 15, 14, 0))
    assert result['is_peak_hour'] == 0
