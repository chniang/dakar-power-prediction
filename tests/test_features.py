"""
Vérifie que l'encodage des features temporelles en inférence
(utils_simple.create_time_features) est identique à celui du CSV
sur lequel les modèles ont été entraînés.
"""
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest

# Mock streamlit avant tout import pour le CI headless
sys.modules['streamlit'] = MagicMock()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from streamlit_app.utils_simple import create_time_features

CSV_PATH = ROOT / 'data' / 'synthetic' / 'synthetic_data_v2.csv'


@pytest.fixture(scope='module')
def training_csv():
    head = CSV_PATH.read_bytes()[:200] if CSV_PATH.exists() else b''
    if not head or head.startswith(b'version https://git-lfs'):
        pytest.skip("CSV d'entraînement absent ou pointeur Git LFS non téléchargé (git lfs pull)")
    return pd.read_csv(CSV_PATH, usecols=['heure', 'mois', 'saison', 'is_peak_hour'])


# ---------------------------------------------------------------------------
# Comparaison directe avec les valeurs réelles du CSV
# ---------------------------------------------------------------------------

def test_saison_identique_au_csv_pour_chaque_mois(training_csv):
    pairs = training_csv[['mois', 'saison']].drop_duplicates()
    assert pairs['mois'].nunique() == 12
    assert not pairs['mois'].duplicated().any(), "Le CSV doit avoir une saison unique par mois"
    for mois, saison_csv in pairs.itertuples(index=False):
        result = create_time_features(datetime(2024, int(mois), 15, 12, 0))
        assert result['saison'] == saison_csv, f"mois={mois}"


def test_is_peak_hour_identique_au_csv_pour_chaque_heure(training_csv):
    pairs = training_csv[['heure', 'is_peak_hour']].drop_duplicates()
    assert pairs['heure'].nunique() == 24
    assert not pairs['heure'].duplicated().any(), "Le CSV doit avoir un is_peak_hour unique par heure"
    for heure, peak_csv in pairs.itertuples(index=False):
        result = create_time_features(datetime(2024, 1, 15, int(heure), 0))
        assert result['is_peak_hour'] == peak_csv, f"heure={heure}"
        result_override = create_time_features(datetime(2024, 1, 15, 0, 0), hour_override=int(heure))
        assert result_override['is_peak_hour'] == peak_csv, f"hour_override={heure}"


def test_valeurs_de_saison_vues_a_l_entrainement(training_csv):
    vues = set(training_csv['saison'].unique())
    for mois in range(1, 13):
        assert create_time_features(datetime(2024, mois, 1))['saison'] in vues


# ---------------------------------------------------------------------------
# Valeurs attendues explicites (tournent même sans le CSV)
# ---------------------------------------------------------------------------

def test_create_time_features_keys():
    result = create_time_features(datetime(2024, 6, 15, 14, 0))
    assert set(result.keys()) == {'hour', 'day_of_week', 'month', 'saison', 'is_peak_hour'}


@pytest.mark.parametrize('mois,attendu', [(1, 0), (5, 0), (6, 1), (7, 1), (8, 1), (9, 0), (12, 0)])
def test_saison_binaire_juin_aout(mois, attendu):
    assert create_time_features(datetime(2024, mois, 1, 12, 0))['saison'] == attendu


@pytest.mark.parametrize('heure,attendu', [(8, 0), (15, 0), (17, 0), (18, 1), (20, 1), (22, 1), (23, 0)])
def test_pointe_18h_22h(heure, attendu):
    assert create_time_features(datetime(2024, 6, 15, heure, 0))['is_peak_hour'] == attendu
