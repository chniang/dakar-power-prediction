"""
Fichier : src/data_generator.py
Générateur de Données Synthétiques avec Hiérarchie de Risque
============================================================

Ce générateur crée des données réalistes avec:
- Pondération par quartier (Guediawaye plus risqué)
- Patterns temporels (heures de pointe, saisons)
- Corrélations réalistes entre features
- Export direct vers Supabase

Auteur : Cheikh Niang
Date : Décembre 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import Dict, List

# Seed pour reproductibilité
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ============================================================================
# CONFIGURATION DES QUARTIERS AVEC PONDÉRATION
# ============================================================================

QUARTIERS_CONFIG = {
    'Guediawaye': {
        'risque_base': 0.134,  # 13.4% (le PLUS risqué)
        'facteur': 1.8,
        'consommation_avg': 850,
        'temperature_bias': 1.5  # Plus chaud
    },
    'Parcelles Assainies': {
        'risque_base': 0.097,  # 9.7%
        'facteur': 1.3,
        'consommation_avg': 750,
        'temperature_bias': 1.0
    },
    'Sicap-Liberté': {
        'risque_base': 0.088,  # 8.8%
        'facteur': 1.2,
        'consommation_avg': 700,
        'temperature_bias': 0.5
    },
    'Yoff': {
        'risque_base': 0.071,  # 7.1%
        'facteur': 1.0,
        'consommation_avg': 650,
        'temperature_bias': 0.0
    },
    'Mermoz-Sacré-Cœur': {
        'risque_base': 0.054,  # 5.4%
        'facteur': 0.8,
        'consommation_avg': 600,
        'temperature_bias': -0.5
    },
    'Dakar-Plateau': {
        'risque_base': 0.040,  # 4.0% (le MOINS risqué)
        'facteur': 0.5,
        'consommation_avg': 550,
        'temperature_bias': -1.0  # Plus frais
    }
}

# ============================================================================
# FONCTIONS DE GÉNÉRATION
# ============================================================================

def generate_date_range(start_date: str, end_date: str, freq: str = '1H') -> pd.DatetimeIndex:
    """
    Génère une plage de dates.
    
    Args:
        start_date: Date de début (format: 'YYYY-MM-DD')
        end_date: Date de fin
        freq: Fréquence ('1H' pour horaire)
    
    Returns:
        DatetimeIndex
    """
    return pd.date_range(start=start_date, end=end_date, freq=freq)


def get_season(month: int) -> int:
    """
    Détermine la saison à Dakar.
    
    Args:
        month: Mois (1-12)
    
    Returns:
        0: Saison sèche fraîche (Nov-Fév)
        1: Saison sèche chaude (Mar-Mai)
        2: Saison des pluies (Juin-Oct)
    """
    if month in [11, 12, 1, 2]:
        return 0  # Saison sèche fraîche
    elif month in [3, 4, 5]:
        return 1  # Saison sèche chaude
    else:
        return 2  # Saison des pluies


def is_peak_hour(hour: int) -> bool:
    """
    Vérifie si c'est une heure de pointe.
    
    Args:
        hour: Heure (0-23)
    
    Returns:
        True si heure de pointe
    """
    return hour in range(7, 10) or hour in range(18, 22)


def generate_temperature(month: int, hour: int, quartier_config: Dict) -> float:
    """
    Génère une température réaliste pour Dakar.
    
    Args:
        month: Mois (1-12)
        hour: Heure (0-23)
        quartier_config: Configuration du quartier
    
    Returns:
        Température en °C
    """
    # Température de base par saison
    season = get_season(month)
    if season == 0:  # Saison fraîche
        base_temp = 24.0
    elif season == 1:  # Saison chaude
        base_temp = 30.0
    else:  # Saison des pluies
        base_temp = 27.0
    
    # Variation diurne (plus chaud l'après-midi)
    hour_effect = 5 * np.sin((hour - 6) * np.pi / 12)
    
    # Biais du quartier
    quartier_bias = quartier_config['temperature_bias']
    
    # Bruit aléatoire
    noise = np.random.normal(0, 2)
    
    temp = base_temp + hour_effect + quartier_bias + noise
    
    # Limiter entre 18°C et 42°C
    return np.clip(temp, 18, 42)


def generate_humidity(temperature: float, season: int) -> int:
    """
    Génère l'humidité en fonction de la température et de la saison.
    
    Args:
        temperature: Température en °C
        season: Saison (0, 1, 2)
    
    Returns:
        Humidité en %
    """
    # Corrélation inverse avec température
    base_humidity = 100 - (temperature - 20) * 1.5
    
    # Ajustement saisonnier
    if season == 2:  # Saison des pluies
        base_humidity += 15
    elif season == 1:  # Saison chaude
        base_humidity -= 10
    
    # Bruit aléatoire
    noise = np.random.normal(0, 8)
    
    humidity = base_humidity + noise
    
    # Limiter entre 30% et 95%
    return int(np.clip(humidity, 30, 95))


def generate_wind_speed(season: int, is_peak: bool) -> float:
    """
    Génère la vitesse du vent.
    
    Args:
        season: Saison (0, 1, 2)
        is_peak: Est-ce une heure de pointe ?
    
    Returns:
        Vitesse du vent en km/h
    """
    # Vent plus fort pendant la saison des pluies
    if season == 2:
        base_wind = 20
    else:
        base_wind = 12
    
    # Vent plus fort le soir
    if is_peak:
        base_wind += 5
    
    # Bruit aléatoire
    noise = np.random.normal(0, 5)
    
    wind = base_wind + noise
    
    # Limiter entre 0 et 50 km/h
    return np.clip(wind, 0, 50)


def generate_consumption(hour: int, is_peak: bool, quartier_config: Dict, temperature: float) -> int:
    """
    Génère la consommation électrique.
    
    Args:
        hour: Heure (0-23)
        is_peak: Heure de pointe ?
        quartier_config: Configuration du quartier
        temperature: Température
    
    Returns:
        Consommation en MW
    """
    base_consumption = quartier_config['consommation_avg']
    
    # Variation horaire
    if is_peak:
        hour_factor = 1.3
    elif 22 <= hour or hour <= 5:  # Nuit
        hour_factor = 0.7
    else:
        hour_factor = 1.0
    
    # Effet de la température (climatisation)
    if temperature > 32:
        temp_factor = 1 + (temperature - 32) * 0.03
    else:
        temp_factor = 1.0
    
    # Bruit aléatoire
    noise = np.random.normal(0, 50)
    
    consumption = base_consumption * hour_factor * temp_factor + noise
    
    # Limiter entre 200 et 1500 MW
    return int(np.clip(consumption, 200, 1500))


def calculate_outage_probability(
    temperature: float,
    humidity: int,
    wind_speed: float,
    consumption: int,
    is_peak: bool,
    quartier_config: Dict,
    season: int
) -> float:
    """
    Calcule la probabilité de coupure basée sur tous les facteurs.
    
    Args:
        temperature: Température
        humidity: Humidité
        wind_speed: Vitesse du vent
        consumption: Consommation
        is_peak: Heure de pointe
        quartier_config: Configuration quartier
        season: Saison
    
    Returns:
        Probabilité de coupure (0-1)
    """
    # Risque de base du quartier
    base_risk = quartier_config['risque_base']
    
    # Facteurs multiplicateurs
    temp_risk = 0 if temperature < 30 else (temperature - 30) * 0.02
    consumption_risk = 0 if consumption < 900 else (consumption - 900) * 0.0001
    peak_risk = 0.03 if is_peak else 0
    season_risk = 0.02 if season == 1 else 0  # Saison chaude
    
    # Probabilité finale
    proba = base_risk + temp_risk + consumption_risk + peak_risk + season_risk
    
    # Limiter entre 0 et 1
    return np.clip(proba, 0, 1)


def generate_dataset(
    start_date: str = '2024-01-01',
    end_date: str = '2024-12-31',
    quartiers: List[str] = None
) -> pd.DataFrame:
    """
    Génère le dataset complet.
    
    Args:
        start_date: Date de début
        end_date: Date de fin
        quartiers: Liste des quartiers (None = tous)
    
    Returns:
        DataFrame avec toutes les données
    """
    if quartiers is None:
        quartiers = list(QUARTIERS_CONFIG.keys())
    
    print("=" * 70)
    print(" 🔄 GÉNÉRATION DES DONNÉES SYNTHÉTIQUES")
    print("=" * 70)
    print(f"📅 Période : {start_date} → {end_date}")
    print(f"🏘️  Quartiers : {len(quartiers)}")
    
    # Générer les dates
    dates = generate_date_range(start_date, end_date, freq='1H')
    print(f"⏰ Timestamps : {len(dates):,}")
    
    data = []
    
    for quartier in quartiers:
        print(f"\n📍 Génération pour {quartier}...")
        config = QUARTIERS_CONFIG[quartier]
        
        for date in dates:
            hour = date.hour
            month = date.month
            day_of_week = date.dayofweek
            season = get_season(month)
            is_peak = is_peak_hour(hour)
            
            # Générer les features
            temp = generate_temperature(month, hour, config)
            humidity = generate_humidity(temp, season)
            wind = generate_wind_speed(season, is_peak)
            consumption = generate_consumption(hour, is_peak, config, temp)
            
            # Calculer probabilité de coupure
            proba = calculate_outage_probability(
                temp, humidity, wind, consumption, is_peak, config, season
            )
            
            # Déterminer s'il y a coupure
            coupure = 1 if np.random.random() < proba else 0
            
            data.append({
                'date_heure': date,
                'quartier': quartier,
                'temp_celsius': round(temp, 2),
                'humidite_percent': humidity,
                'vitesse_vent': round(wind, 2),
                'conso_megawatt': consumption,
                'heure': hour,
                'jour_semaine': day_of_week,
                'mois': month,
                'saison': season,
                'is_peak_hour': int(is_peak),
                'coupure': coupure
            })
    
    df = pd.DataFrame(data)
    
    print("\n" + "=" * 70)
    print(" ✅ GÉNÉRATION TERMINÉE")
    print("=" * 70)
    print(f"📊 Total lignes : {len(df):,}")
    print(f"🔴 Coupures : {df['coupure'].sum():,} ({df['coupure'].mean()*100:.2f}%)")
    print(f"🟢 Pas de coupure : {(~df['coupure'].astype(bool)).sum():,}")
    
    # Taux par quartier
    print("\n📊 Taux de coupure par quartier :")
    for quartier in quartiers:
        taux = df[df['quartier'] == quartier]['coupure'].mean() * 100
        print(f"  {quartier:25s} : {taux:6.2f}%")
    
    return df


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

if __name__ == "__main__":
    # Générer les données
    df = generate_dataset(
        start_date='2024-01-01',
        end_date='2024-12-31'
    )
    
    # Sauvegarder en CSV
    from pathlib import Path
    output_dir = Path('data/raw')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / 'raw_data.csv'
    df.to_csv(output_file, index=False)
    print(f"\n✅ Données sauvegardées : {output_file}")