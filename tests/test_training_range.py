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
    # 800 MW en pointe : jamais vu à l'entraînement
    msgs = check_training_range(25, 80, 10, 800, is_peak_hour=1)
    assert len(msgs) == 1 and 'pointe' in msgs[0]
    msgs = check_training_range(25, 80, 10, 1200, is_peak_hour=0)
    assert len(msgs) == 1 and 'hors heure de pointe' in msgs[0]


# ---------------------------------------------------------------------------
# Consommation par défaut cohérente avec l'heure
# ---------------------------------------------------------------------------

from src.config import CONSO_DEFAULT_BY_PEAK
from streamlit_app.utils_simple import default_consommation, sync_conso_default


@pytest.mark.parametrize('heure', range(24))
def test_conso_par_defaut_coherente_avec_l_heure(heure):
    conso = default_consommation(heure)
    peak = 1 if 18 <= heure <= 22 else 0
    assert conso == (1100.0 if peak else 600.0)
    # Le défaut ne déclenche jamais l'avertissement « hors plage d'entraînement »
    assert check_training_range(25, 80, 10, conso, is_peak_hour=peak) == []


def test_defauts_dans_les_plages_du_csv():
    for peak, conso in CONSO_DEFAULT_BY_PEAK.items():
        lo, hi = CONSO_RANGE_BY_PEAK[peak]
        assert lo <= conso <= hi


def test_sync_premier_affichage():
    state = {'s_hour': 19}
    sync_conso_default(state)
    assert state['s_conso'] == 1100.0
    state = {'s_hour': 15}
    sync_conso_default(state)
    assert state['s_conso'] == 600.0


def test_sync_conserve_le_choix_utilisateur_dans_la_meme_periode():
    state = {'s_hour': 15}
    sync_conso_default(state)
    state['s_conso'] = 750.0          # l'utilisateur modifie la consommation
    state['s_hour'] = 10              # reste hors pointe
    sync_conso_default(state)
    assert state['s_conso'] == 750.0


def test_sync_bascule_pointe_hors_pointe():
    state = {'s_hour': 15}
    sync_conso_default(state)
    state['s_conso'] = 750.0
    state['s_hour'] = 20              # passe en pointe
    sync_conso_default(state)
    assert state['s_conso'] == 1100.0
    state['s_conso'] = 1250.0
    state['s_hour'] = 23              # repasse hors pointe
    sync_conso_default(state)
    assert state['s_conso'] == 600.0
