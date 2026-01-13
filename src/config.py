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
# CONFIGURATION SUPABASE
# ============================================================================

SUPABASE_CONFIG = {
    'url': 'https://krudbbmsixrejemqqphn.supabase.co',
    'key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtydWRiYm1zaXhyZWplbXFxcGhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQxNDc4NzAsImV4cCI6MjA3OTcyMzg3MH0.X4HEFRhR-WOsc0g-d70NAqLOy33qst7Z7z-EUIOnhjQ'
}

# ============================================================================
# QUARTIERS DE DAKAR (8 quartiers)
# ============================================================================

QUARTIERS_DAKAR = [
    'Guediawaye',
    'Parcelles Assainies',
    'Pikine',
    'Sicap-Liberte',
    'Yoff',
    'Mermoz-Sacre-Coeur',
    'Dakar-Plateau',
    'Fann'
]

# ============================================================================
# COORDONNÉES GPS DES QUARTIERS
# ============================================================================

COORDONNEES_QUARTIERS = {
    'Guediawaye': {'lat': 14.7692, 'lon': -17.4008},
    'Parcelles Assainies': {'lat': 14.7586, 'lon': -17.4147},
    'Pikine': {'lat': 14.7564, 'lon': -17.3924},
    'Sicap-Liberte': {'lat': 14.7167, 'lon': -17.4677},
    'Yoff': {'lat': 14.7539, 'lon': -17.4894},
    'Mermoz-Sacre-Coeur': {'lat': 14.7206, 'lon': -17.4706},
    'Dakar-Plateau': {'lat': 14.6928, 'lon': -17.4467},
    'Fann': {'lat': 14.6937, 'lon': -17.4531}
}

# ============================================================================
# AJUSTEMENTS PAR QUARTIER (facteur de risque)
# ============================================================================

QUARTIER_ADJUSTMENT = {
    'Guediawaye': 1.15,
    'Parcelles Assainies': 1.10,
    'Pikine': 1.20,
    'Sicap-Liberte': 1.05,
    'Yoff': 1.00,
    'Mermoz-Sacre-Coeur': 0.90,
    'Dakar-Plateau': 0.85,
    'Fann': 0.95
}

# ============================================================================
# SEUILS DE RISQUE (en pourcentage)
# ============================================================================

SEUILS_RISQUE = {
    'faible': 40,
    'moyen': 40,
    'eleve': 70
}

# ============================================================================
# PLAGES DE TEMPÉRATURE PAR SAISON
# ============================================================================

TEMPERATURE_RANGES = {
    'hiver': (18, 28),
    'printemps': (20, 30),
    'ete': (24, 35),
    'automne': (22, 32)
}

# ============================================================================
# PLAGES DE CONSOMMATION (MW)
# ============================================================================

CONSO_RANGES = {
    'base': (400, 600),
    'normale': (600, 900),
    'pointe': (900, 1400)
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

print("✅ Config chargée : 8 quartiers")