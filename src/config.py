"""
Configuration globale du projet Dakar Power Prediction
VERSION FINALE - 8 quartiers
"""
import os

# ============================================================================
# CHEMINS DES FICHIERS
# ============================================================================

MODELS_DIR = 'models/'
DATA_DIR = 'data/'
SYNTHETIC_DIR = 'data/synthetic/'
# ============================================================================
# QUARTIERS DE DAKAR (8 quartiers)
# ============================================================================

QUARTIERS_DAKAR = [
    'Guédiawaye',
    'Parcelles Assainies',
    'Pikine',
    'Sicap-Liberté',
    'Yoff',
    'Mermoz-Sacré-Cœur',
    'Dakar-Plateau',
    'Fann'
]

# ============================================================================
# COORDONNÉES GPS DES QUARTIERS
# ============================================================================

COORDONNEES_QUARTIERS = {
    'Guédiawaye': {'lat': 14.7692, 'lon': -17.4008},
    'Parcelles Assainies': {'lat': 14.7586, 'lon': -17.4147},
    'Pikine': {'lat': 14.7564, 'lon': -17.3924},
    'Sicap-Liberté': {'lat': 14.7167, 'lon': -17.4677},
    'Yoff': {'lat': 14.7539, 'lon': -17.4894},
    'Mermoz-Sacré-Cœur': {'lat': 14.7206, 'lon': -17.4706},
    'Dakar-Plateau': {'lat': 14.6928, 'lon': -17.4467},
    'Fann': {'lat': 14.6937, 'lon': -17.4531}
}

# ============================================================================
# AJUSTEMENTS PAR QUARTIER (facteur de risque)
# Le quartier n'est PAS une feature du modèle : ce coefficient est appliqué
# après inférence. Les 8 quartiers sont présents dans synthetic_data_v2.csv ;
# les valeurs suivent le ratio (taux de coupure du quartier / taux moyen 14,05 %).
# ============================================================================

QUARTIER_ADJUSTMENT = {
    'Guédiawaye': 1.15,
    'Parcelles Assainies': 1.10,
    'Pikine': 1.20,
    'Sicap-Liberté': 1.05,
    'Yoff': 1.00,
    'Mermoz-Sacré-Cœur': 0.90,
    'Dakar-Plateau': 0.85,
    'Fann': 0.95
}

# Seuils en % de probabilité (ensemble LightGBM + LSTM × coefficient de quartier).
# Fixés sur la distribution réelle du jeu de test (14 000 lignes) :
#   FAIBLE < 15 % : 61,4 % des cas, taux de coupure réel 2,5 % (sous le taux moyen de 14 %)
#   MOYEN 15-35 % : 24,9 % des cas, taux de coupure réel 22,0 %
#   ÉLEVÉ ≥ 35 %  : 13,7 % des cas, taux de coupure réel 51,5 % (coupure plus probable qu'improbable)
# Le jeu de test ayant déjà servi à l'arrêt anticipé, ces chiffres sont légèrement optimistes.
RISK_THRESHOLDS = {'faible': 15, 'eleve': 35}

def classify_risk(score: float) -> str:
    if score < RISK_THRESHOLDS['faible']: return "FAIBLE"
    elif score < RISK_THRESHOLDS['eleve']: return "MOYEN"
    return "ÉLEVÉ"

SLIDER_CONFIG = {
    'temperature':  {'min': 15.0,  'max':   45.0, 'default': 25.0,  'step':  0.5},
    'humidite':     {'min': 30.0,  'max':  100.0, 'default': 65.0,  'step':  1.0},
    'vitesse_vent': {'min':  0.0,  'max':   50.0, 'default': 15.0,  'step':  1.0},
    'consommation': {'min': 400.0, 'max': 1500.0, 'default': 800.0, 'step': 10.0},
}

# ============================================================================
# CONFIGURATION MODÈLES ML
# ============================================================================

MODEL_CONFIG = {
    'features': [
        'temp_celsius',
        'humidite_percent',
        'vitesse_vent',
        'conso_megawatt',
        'heure',
        'jour_semaine',
        'mois',
        'saison',
        'is_peak_hour'
    ],
    'target': 'coupure',
    'test_size': 0.2,
    'random_state': 42
}

