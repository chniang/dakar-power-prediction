import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import classify_risk, QUARTIERS_DAKAR, QUARTIER_ADJUSTMENT


def test_classify_risk_faible():
    assert classify_risk(25) == "FAIBLE"


def test_classify_risk_moyen():
    assert classify_risk(55) == "MOYEN"


def test_classify_risk_eleve():
    assert classify_risk(80) == "ÉLEVÉ"


def test_quartiers_count():
    assert len(QUARTIERS_DAKAR) == 8


def test_adjustment_keys_match_quartiers():
    assert set(QUARTIER_ADJUSTMENT.keys()) == set(QUARTIERS_DAKAR)
