"""
Les plages déclarées dans src/config.py doivent correspondre au CSV d'entraînement,
et check_training_range() doit signaler (sans bloquer) les entrées hors plage.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

sys.modules['streamlit'] = MagicMock()
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.config import TRAINING_RANGES, CONSO_RANGE_BY_PEAK, SLIDER_CONFIG
from streamlit_app.utils_simple import check_training_range

CSV_PATH = ROOT / 'data' / 'synthetic' / 'synthetic_data_v2.csv'
CSV_COLS = {
    'temperature': 'temp_celsius',
    'humidite': 'humidite_percent',
    'vitesse_vent': 'vitesse_vent',
    'consommation': 'conso_megawatt',
}


@pytest.fixture(scope='module')
def training_csv():
    head = CSV_PATH.read_bytes()[:200] if CSV_PATH.exists() else b''
    if not head or head.startswith(b'version https://git-lfs'):
        pytest.skip("CSV d'entraînement absent ou pointeur Git LFS non téléchargé (git lfs pull)")
    return pd.read_csv(CSV_PATH, usecols=list(CSV_COLS.values()) + ['is_peak_hour'])


@pytest.mark.parametrize('key', list(CSV_COLS))
def test_plages_couvrent_le_csv_au_plus_juste(training_csv, key):
    lo, hi = TRAINING_RANGES[key]
    col = training_csv[CSV_COLS[key]]
    assert lo <= col.min() and col.max() <= hi
    assert col.min() - lo < 0.5 and hi - col.max() < 0.5  # pas de marge excessive


@pytest.mark.parametrize('peak', [0, 1])
def test_conso_par_heure_de_pointe(training_csv, peak):
    lo, hi = CONSO_RANGE_BY_PEAK[peak]
    conso = training_csv.loc[training_csv['is_peak_hour'] == peak, 'conso_megawatt']
    assert lo <= conso.min() and conso.max() <= hi


def test_sliders_non_bloques():
    # Les sliders restent plus larges que les plages : on avertit, on ne bloque pas
    for key, (lo, hi) in TRAINING_RANGES.items():
        assert SLIDER_CONFIG[key]['min'] <= lo and hi <= SLIDER_CONFIG[key]['max']


def test_valeurs_dans_la_plage_sans_avertissement():
    assert check_training_range(25, 80, 10, 1100, is_peak_hour=1) == []
    assert check_training_range(25, 80, 10, 600, is_peak_hour=0) == []


def test_valeurs_hors_plage_signalees():
    msgs = check_training_range(42, 30, 35, 1450, is_peak_hour=1)
    assert len(msgs) == 4
    assert all("hors plage d'entraînement" in m for m in msgs)


def test_conso_incoherente_avec_l_heure():
    # 800 MW en pointe : valeur par défaut des sliders, jamais vue à l'entraînement
    msgs = check_training_range(25, 80, 10, 800, is_peak_hour=1)
    assert len(msgs) == 1 and 'pointe' in msgs[0]
    msgs = check_training_range(25, 80, 10, 1200, is_peak_hour=0)
    assert len(msgs) == 1 and 'hors heure de pointe' in msgs[0]
