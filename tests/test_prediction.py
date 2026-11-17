"""
Pipeline de prédiction avec des modèles factices : vérifie que le risque affiché
est la vraie probabilité (pas de rééchelonnement ×2) et que le coefficient de
quartier est appliqué AVANT le plafonnement à 100 %.
"""
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock

import numpy as np
import pytest

sys.modules['streamlit'] = MagicMock()
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import QUARTIER_ADJUSTMENT, QUARTIERS_DAKAR
from streamlit_app.utils_simple import (
    make_prediction_single, compute_map_risks, create_time_features,
)


class _Identity:
    def transform(self, X):
        return np.asarray(X, dtype=float)


class _ConstLGB:
    def __init__(self, p):
        self.p = p

    def predict(self, X):
        return np.full(len(X), self.p)


class _ConstLSTM:
    def __init__(self, p):
        self.p = p

    def predict(self, X, verbose=0):
        return np.full((len(X), 1), self.p)


def _models(p_lgb, p_lstm=None):
    return {
        'lgb': _ConstLGB(p_lgb),
        'lstm': _ConstLSTM(p_lstm) if p_lstm is not None else None,
        'scaler': _Identity(),
    }


TF = create_time_features(datetime(2024, 1, 15, 19, 0))


def _predict(models, quartier):
    return make_prediction_single(models, quartier, 25, 80, 10, 1000, TF)


def test_probabilite_brute_sans_rescaling():
    pred_lgb, pred_lstm, risque = _predict(_models(0.20, 0.30), 'Yoff')
    assert pred_lgb == pytest.approx(20.0)
    assert pred_lstm == pytest.approx(30.0)
    assert risque == pytest.approx(25.0)  # moyenne, coefficient Yoff = 1,00, pas de ×2


def test_pas_de_plancher_artificiel():
    _, _, risque = _predict(_models(0.001, 0.001), 'Dakar-Plateau')
    assert risque == pytest.approx(0.1 * QUARTIER_ADJUSTMENT['Dakar-Plateau'])


def test_coefficient_applique_avant_plafonnement():
    # 0,90 × 0,85 = 76,5 % pour Dakar-Plateau ; 0,90 × 1,20 = 108 % → plafonné à 100 % pour Pikine
    _, _, plateau = _predict(_models(0.90, 0.90), 'Dakar-Plateau')
    _, _, pikine = _predict(_models(0.90, 0.90), 'Pikine')
    assert plateau == pytest.approx(76.5)
    assert pikine == pytest.approx(100.0)


def test_lstm_absent_utilise_lightgbm():
    pred_lgb, pred_lstm, risque = _predict(_models(0.40), 'Yoff')
    assert pred_lgb == pred_lstm == pytest.approx(40.0)
    assert risque == pytest.approx(40.0)


def test_carte_coherente_avec_prediction_unique():
    models = _models(0.20, 0.30)
    carte = {r['Quartier']: r['Risque'] for r in compute_map_risks(models, 25, 80, 10, 1000, TF)}
    assert set(carte) == set(QUARTIERS_DAKAR)
    for q in QUARTIERS_DAKAR:
        assert carte[q] == pytest.approx(_predict(models, q)[2])


# ---------------------------------------------------------------------------
# Affichage « < 1 % »
# ---------------------------------------------------------------------------

from src.config import classify_risk
from streamlit_app.utils_simple import format_risk, create_gauge_chart, create_map


@pytest.mark.parametrize('valeur,texte', [
    (0.0, "< 1 %"), (0.1, "< 1 %"), (0.99, "< 1 %"), (1.0, "1.0%"), (42.06, "42.1%"),
])
def test_format_risk(valeur, texte):
    assert format_risk(valeur) == texte


def test_affichage_ne_change_ni_valeur_ni_niveau():
    _, _, risque = _predict(_models(0.001, 0.001), 'Yoff')
    assert risque == pytest.approx(0.1)          # valeur calculée inchangée
    assert classify_risk(risque) == "FAIBLE"
    fig = create_gauge_chart(risque, 'Yoff')
    assert fig.data[0].value == pytest.approx(0.1)  # la jauge garde la vraie valeur
    assert "< 1 %" in [a.text for a in fig.layout.annotations]


def test_carte_affiche_moins_de_1_pourcent():
    fig = create_map([{'Quartier': 'Yoff', 'Risque': 0.3}, {'Quartier': 'Pikine', 'Risque': 42.0}])
    textes = [row[0] for row in fig.data[0].customdata]
    assert textes == ["< 1 %", "42.0%"]
