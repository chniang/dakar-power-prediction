"""
Configuration globale du projet Dakar Power Prediction
VERSION FINALE - 8 quartiers
"""

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
    'Pikine',            # ATTENTION : absent des données d'entraînement (data_generator.py)
    'Sicap-Liberté',
    'Yoff',
    'Mermoz-Sacré-Cœur',
    'Dakar-Plateau',
    'Fann'              # ATTENTION : absent des données d'entraînement (data_generator.py)
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
# ============================================================================

QUARTIER_ADJUSTMENT = {
    'Guédiawaye': 1.15,
    'Parcelles Assainies': 1.10,
    'Pikine': 1.20,             # ATTENTION : absent des données d'entraînement
    'Sicap-Liberté': 1.05,
    'Yoff': 1.00,
    'Mermoz-Sacré-Cœur': 0.90,
    'Dakar-Plateau': 0.85,
    'Fann': 0.95                # ATTENTION : absent des données d'entraînement
}

def classify_risk(score: float) -> str:
    if score < 40: return "FAIBLE"
    elif score < 70: return "MOYEN"
    return "ÉLEVÉ"

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

