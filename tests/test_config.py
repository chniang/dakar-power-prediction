import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import classify_risk, QUARTIERS_DAKAR, QUARTIER_ADJUSTMENT, RISK_THRESHOLDS


def test_seuils_valeurs_figees():
    # Seuils fixés sur la distribution réelle du jeu de test (voir src/config.py)
    assert RISK_THRESHOLDS == {'faible': 15, 'eleve': 35}


def test_classify_risk_faible():
    assert classify_risk(0.1) == "FAIBLE"
    assert classify_risk(14.9) == "FAIBLE"


def test_classify_risk_moyen():
    assert classify_risk(15) == "MOYEN"
    assert classify_risk(34.9) == "MOYEN"


def test_classify_risk_eleve():
    assert classify_risk(35) == "ÉLEVÉ"
    assert classify_risk(80) == "ÉLEVÉ"


def test_quartiers_count():
    assert len(QUARTIERS_DAKAR) == 8


def test_adjustment_keys_match_quartiers():
    assert set(QUARTIER_ADJUSTMENT.keys()) == set(QUARTIERS_DAKAR)
