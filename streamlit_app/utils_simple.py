"""
Fonctions utilitaires - THÈME PAR DÉFAUT STREAMLIT/PLOTLY
"""
import logging
import warnings
import pickle
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

try:
    from tensorflow import keras
    _KERAS_AVAILABLE = True
except ImportError:
    keras = None
    _KERAS_AVAILABLE = False

warnings.filterwarnings('ignore', category=UserWarning, module='keras')
warnings.filterwarnings('ignore', category=UserWarning, module='lightgbm')

from src.config import (QUARTIERS_DAKAR, COORDONNEES_QUARTIERS, QUARTIER_ADJUSTMENT,
                        classify_risk, RISK_THRESHOLDS, TRAINING_RANGES, CONSO_RANGE_BY_PEAK,
                        CONSO_DEFAULT_BY_PEAK)

logger = logging.getLogger(__name__)

# Encodage des features temporelles du CSV d'entraînement
SAISON_MONTHS = (6, 7, 8)
PEAK_HOUR_START, PEAK_HOUR_END = 18, 22

@st.cache_resource
def load_models_cached():
    models = {'lgb': None, 'lstm': None, 'scaler': None}
    try:
        with open('models/lgbm_model.pkl', 'rb') as f:
            models['lgb'] = pickle.load(f)
    except Exception as e:
        st.warning(f"⚠️ LightGBM: {e}")
    if not _KERAS_AVAILABLE:
        logger.warning("TensorFlow non disponible — LSTM désactivé, LightGBM seul utilisé.")
        models['lstm'] = None
    else:
        try:
            # Charger LSTM avec compile=False pour éviter les erreurs de compatibilité
            models['lstm'] = keras.models.load_model('models/lstm_model.keras', compile=False)
            # Compiler manuellement avec les bons paramètres
            models['lstm'].compile(optimizer='adam', loss='binary_crossentropy')
        except Exception:
            # Si LSTM échoue, utiliser seulement LightGBM (pas d'avertissement affiché)
            models['lstm'] = None
    try:
        with open('models/scaler.pkl', 'rb') as f:
            models['scaler'] = pickle.load(f)
    except Exception as e:
        st.error(f"❌ Scaler: {e}")
    return models

def create_time_features(date_time: datetime, hour_override: int = None) -> dict:
    hour = hour_override if hour_override is not None else date_time.hour
    month = date_time.month
    # Encodages calés sur data/synthetic/synthetic_data_v2.csv, sur lequel les modèles
    # ont été entraînés (et NON sur data_generator.py, qui n'a pas produit ce CSV).
    # Vérifié par tests/test_features.py contre les valeurs réelles du CSV.
    saison = 1 if month in SAISON_MONTHS else 0          # 1 = juin-août, 0 = reste
    is_peak_hour = is_peak(hour)  # 18h-22h
    return {
        'hour': hour,
        'day_of_week': date_time.weekday(),
        'month': month,
        'saison': saison,
        'is_peak_hour': is_peak_hour,
    }

def is_peak(hour: int) -> int:
    return 1 if PEAK_HOUR_START <= hour <= PEAK_HOUR_END else 0


def default_consommation(hour: int) -> float:
    """Consommation par défaut cohérente avec l'heure : ~1 100 MW en pointe (18h-22h), ~600 MW sinon."""
    return CONSO_DEFAULT_BY_PEAK[is_peak(hour)]


def sync_conso_default(state, hour_key='s_hour', conso_key='s_conso'):
    """Remet la consommation à sa valeur par défaut quand l'heure choisie bascule entre
    pointe et hors pointe (ou au premier affichage). Tant que l'heure reste dans la même
    période, la valeur choisie par l'utilisateur est conservée."""
    peak = is_peak(state[hour_key])
    if conso_key not in state or state.get('_conso_peak') != peak:
        state[conso_key] = default_consommation(state[hour_key])
    state['_conso_peak'] = peak


def check_training_range(temperature, humidite, vitesse_vent, consommation, is_peak_hour):
    """Liste des entrées hors de la plage vue à l'entraînement (vide si tout est dans la plage)."""
    labels = {
        'temperature': ('Température', temperature, '°C'),
        'humidite': ('Humidité', humidite, '%'),
        'vitesse_vent': ('Vent', vitesse_vent, 'km/h'),
        'consommation': ('Consommation', consommation, 'MW'),
    }
    warnings_list = []
    for key, (label, value, unit) in labels.items():
        lo, hi = TRAINING_RANGES[key]
        if not lo <= value <= hi:
            warnings_list.append(f"{label} {value:g} {unit} hors plage d'entraînement ({lo:g}-{hi:g} {unit})")
    lo, hi = CONSO_RANGE_BY_PEAK[int(is_peak_hour)]
    in_global = TRAINING_RANGES['consommation'][0] <= consommation <= TRAINING_RANGES['consommation'][1]
    if in_global and not lo <= consommation <= hi:
        moment = "en heure de pointe (18h-22h)" if is_peak_hour else "hors heure de pointe"
        warnings_list.append(
            f"Consommation {consommation:g} MW jamais observée {moment} à l'entraînement ({lo:g}-{hi:g} MW)"
        )
    return warnings_list


def _predict_probas_pct(models, X_scaled):
    """Probabilités brutes (en %) de LightGBM et du LSTM pour chaque ligne de X_scaled.
    Si le LSTM est indisponible, LightGBM est utilisé pour les deux colonnes."""
    preds_lgb = np.asarray(models['lgb'].predict(X_scaled), dtype=float) * 100
    preds_lstm = preds_lgb.copy()
    if models['lstm'] is not None:
        try:
            preds_lstm = models['lstm'].predict(
                X_scaled.reshape(len(X_scaled), 1, -1), verbose=0
            ).flatten().astype(float) * 100
        except Exception as e:
            logger.warning(f"LSTM prediction failed, falling back to LightGBM: {e}")
    return preds_lgb, preds_lstm


def apply_quartier_adjustment(proba_pct, quartier):
    """Applique le coefficient de quartier à la probabilité (en %), PUIS borne à [0, 100]."""
    return float(np.clip(proba_pct * QUARTIER_ADJUSTMENT.get(quartier, 1.0), 0, 100))


def make_prediction_single(models, quartier, temp, humidite, vent, conso, time_features):
    """Retourne (proba LightGBM %, proba LSTM %, risque du quartier %).

    Le risque est la moyenne des deux probabilités brutes (aucun rééchelonnement),
    multipliée par le coefficient du quartier puis bornée à 100 %."""
    if models['lgb'] is None or models['scaler'] is None:
        return None
    try:
        features = [temp, humidite, vent, conso, time_features['hour'], time_features['day_of_week'], time_features['month'], time_features['saison'], time_features['is_peak_hour']]
        features_scaled = models['scaler'].transform(np.array([features]))
        preds_lgb, preds_lstm = _predict_probas_pct(models, features_scaled)
        pred_lgb, pred_lstm = float(preds_lgb[0]), float(preds_lstm[0])
        risque = apply_quartier_adjustment((pred_lgb + pred_lstm) / 2, quartier)
        return pred_lgb, pred_lstm, risque
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        st.error(f"❌ Erreur de prédiction : {e}")
        return None

def compute_map_risks(models, temperature, humidite, vitesse_vent, consommation, time_features):
    if models['lgb'] is None or models['scaler'] is None:
        return None
    feature_row = [
        temperature, humidite, vitesse_vent, consommation,
        time_features['hour'], time_features['day_of_week'],
        time_features['month'], time_features['saison'],
        time_features['is_peak_hour'],
    ]
    X_scaled = models['scaler'].transform(np.array([feature_row]))
    preds_lgb, preds_lstm = _predict_probas_pct(models, X_scaled)
    # Le quartier n'est pas une feature : même probabilité de base pour tous
    risque_base = float((preds_lgb[0] + preds_lstm[0]) / 2)
    return [
        {'Quartier': q, 'Risque': apply_quartier_adjustment(risque_base, q)}
        for q in QUARTIERS_DAKAR
    ]

def format_risk(risque_pct):
    """Texte affiché pour une probabilité en % : « < 1 % » sous 1 %, sinon une décimale.
    Affichage uniquement : la valeur et le niveau de risque ne changent pas."""
    if risque_pct < 1:
        return "< 1 %"
    return f"{risque_pct:.1f}%"


def risk_message(risque_pct):
    """(type de message Streamlit, texte) affiché sous la jauge pour un risque en %."""
    niveau = classify_risk(risque_pct)
    texte = f"Risque {niveau} ({format_risk(risque_pct)})"
    if niveau == "FAIBLE":
        return 'success', f"✅ {texte}"
    if niveau == "MOYEN":
        return 'warning', f"⚠️ {texte}"
    return 'error', f"🚨 {texte}"


# Streamlit sert ses pages avec <html lang="en"> : Chrome propose alors de « traduire »
# l'app (déjà en français) vers le français, ce qui corrompt les libellés
# (ex. « FAIBLE » → « ÉCHEC », « pics » → « photos »). Ce script, exécuté dans le
# document parent, déclare la page en français et non traduisible.
NO_TRANSLATE_JS = """<script>
const d = window.parent.document;
d.documentElement.lang = 'fr';
d.documentElement.setAttribute('translate', 'no');
d.documentElement.classList.add('notranslate');
if (!d.querySelector('meta[name="google"][content="notranslate"]')) {
  const m = d.createElement('meta'); m.name = 'google'; m.content = 'notranslate';
  d.head.appendChild(m);
}
</script>"""


def get_risk_color(risque_pct):
    if risque_pct < RISK_THRESHOLDS['faible']:
        return "#2ecc71"
    elif risque_pct < RISK_THRESHOLDS['eleve']:
        return "#f39c12"
    else:
        return "#e74c3c"

def create_gauge_chart(risque, quartier):
    color = get_risk_color(risque)
    niveau = classify_risk(risque)

    fig = go.Figure(go.Indicator(
        mode="gauge",  # valeur affichée en annotation pour gérer « < 1 % »
        value=risque,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"{quartier}", 'font': {'size': 20}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 2},
            'bar': {'color': color, 'thickness': 0.75},
            'steps': [
                {'range': [0, RISK_THRESHOLDS['faible']], 'color': '#d4edda'},
                {'range': [RISK_THRESHOLDS['faible'], RISK_THRESHOLDS['eleve']], 'color': '#fff3cd'},
                {'range': [RISK_THRESHOLDS['eleve'], 100], 'color': '#f8d7da'}
            ]
        }
    ))
    fig.add_annotation(
        text=format_risk(risque),
        x=0.5, y=0.32,
        showarrow=False,
        font=dict(size=46, color=color)
    )
    fig.add_annotation(
        text=f"<b>{niveau}</b>",
        x=0.5, y=0.08,
        showarrow=False,
        font=dict(size=28, color=color)
    )
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_map(results):
    df_map = []
    for result in results:
        quartier = result['Quartier']
        if quartier in COORDONNEES_QUARTIERS:
            coords = COORDONNEES_QUARTIERS[quartier]
            r = result['Risque']
            niveau = classify_risk(r)
            df_map.append({
                'Quartier': quartier, 'Latitude': coords['lat'], 'Longitude': coords['lon'],
                'Risque': r, 'Risque_txt': format_risk(r), 'Niveau': niveau
            })
    df_map = pd.DataFrame(df_map)
    df_map['Couleur'] = df_map['Risque'].apply(get_risk_color)
    df_map['Taille'] = 20 + (df_map['Risque'] / 100) * 30

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=df_map['Latitude'], lon=df_map['Longitude'], mode='markers',
        marker=dict(size=df_map['Taille'], color=df_map['Couleur'], opacity=0.85),
        text=df_map['Quartier'],
        customdata=df_map[['Risque_txt', 'Niveau']],
        hovertemplate=(
            '<b>%{text}</b><br>'
            'Risque : %{customdata[0]}<br>'
            'Niveau : %{customdata[1]}<extra></extra>'
        ),
    ))
    fig.update_layout(
        mapbox=dict(style="open-street-map", center=dict(lat=14.72, lon=-17.45), zoom=11),
        title="Carte des Risques de Coupure",
        height=600,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig

def create_bar_chart_quartiers(df_stats):
    if df_stats is None or len(df_stats) == 0:
        return None
    df_sorted = df_stats.sort_values('taux_coupure', ascending=False)
    risques_pct = (df_sorted['taux_coupure'] * 100).tolist()
    colors = [get_risk_color(r) for r in risques_pct]
    niveaux = [classify_risk(r) for r in risques_pct]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_sorted['quartier'], y=risques_pct, marker=dict(color=colors),
        text=[f"{r:.1f}%" for r in risques_pct], textposition='outside',
        customdata=list(zip(niveaux, df_sorted['temp_moy'], df_sorted['conso_moy'])),
        hovertemplate='<b>%{x}</b><br>Taux: %{y:.2f}%<br>Niveau: %{customdata[0]}<br>Temp: %{customdata[1]:.1f}°C<br>Conso: %{customdata[2]:.0f} MW<extra></extra>'
    ))
    fig.update_layout(title="Taux de Coupure", xaxis_title="Quartier", yaxis_title="Taux (%)", height=500)
    return fig

def create_temporal_chart(df_hist, quartier_filter):
    if df_hist is None or len(df_hist) == 0:
        return None
    try:
        df = df_hist.copy()
        date_col = None
        for col in ['timestamp', 'date', 'datetime', 'time']:
            if col in df.columns:
                date_col = col
                break
        if date_col is None:
            df['index_date'] = pd.date_range(start='2023-01-01', periods=len(df), freq='H')
            date_col = 'index_date'
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.sort_values(date_col)
        if quartier_filter != "Tous" and 'quartier' in df.columns:
            df = df[df['quartier'] == quartier_filter]
        df_agg = (
            df.set_index(date_col)
            .resample('W')[['conso_megawatt', 'temp_celsius']]
            .mean()
            .reset_index()
        )
        df_agg[['conso_megawatt', 'temp_celsius']] = (
            df_agg[['conso_megawatt', 'temp_celsius']]
            .interpolate(method='linear')
        )
        df_agg = df_agg.dropna()

        fig = go.Figure()
        if 'conso_megawatt' in df_agg.columns:
            fig.add_trace(go.Scatter(
                x=df_agg[date_col], y=df_agg['conso_megawatt'],
                mode='lines', name='Consommation', line=dict(color='#00bcd4', width=1.5),
                fill='tozeroy', hovertemplate='<b>Conso</b><br>%{y:.0f} MW<extra></extra>'
            ))
        if 'temp_celsius' in df_agg.columns:
            fig.add_trace(go.Scatter(
                x=df_agg[date_col], y=df_agg['temp_celsius'],
                mode='lines', name='Température', line=dict(color='#ff5722', width=1.5, dash='dot'),
                yaxis='y2', hovertemplate='<b>Temp</b><br>%{y:.1f}°C<extra></extra>'
            ))
        title = f"Évolution Hebdomadaire — Consommation & Température ({quartier_filter})" if quartier_filter != "Tous" else "Évolution Hebdomadaire — Consommation & Température"
        fig.update_layout(
            title=title, xaxis_title="Semaine",
            yaxis=dict(title="Consommation (MW)"),
            yaxis2=dict(title="Température (°C)", overlaying='y', side='right'),
            hovermode='x unified', height=500
        )
        return fig
    except Exception as e:
        logger.warning(f"create_temporal_chart failed: {e}")
        return None

def create_forecast_chart(forecast):
    """Prévisions météo 7 jours : précipitations (axe gauche), températures (axe droit).
    Légende horizontale sous le graphique pour ne pas chevaucher l'axe de droite."""
    df_fc = pd.DataFrame(forecast)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_fc['date'], y=df_fc['precipitation'],
        name='Précipitations (mm)', marker_color='#3498db', opacity=0.6,
    ))
    fig.add_trace(go.Scatter(
        x=df_fc['date'], y=df_fc['temp_max'],
        mode='lines+markers', name='Temp max (°C)',
        line=dict(color='#e74c3c', width=2), yaxis='y2',
    ))
    fig.add_trace(go.Scatter(
        x=df_fc['date'], y=df_fc['temp_min'],
        mode='lines+markers', name='Temp min (°C)',
        line=dict(color='#2ecc71', width=2, dash='dot'), yaxis='y2',
    ))
    fig.update_layout(
        title="Prévisions Météo Dakar — 7 prochains jours",
        xaxis_title="Date",
        yaxis=dict(title="Précipitations (mm)", range=[0, 20]),
        yaxis2=dict(title="Température (°C)", overlaying='y', side='right', range=[20, 45]),
        legend=dict(orientation='h', yanchor='top', y=-0.25, xanchor='center', x=0.5),
        margin=dict(b=110),
        hovermode='x unified',
        height=450,
    )
    return fig


def create_risk_trend_chart(df_hist, quartier_filter):
    if df_hist is None or len(df_hist) == 0 or 'coupure' not in df_hist.columns:
        return None
    try:
        df = df_hist.copy()
        date_col = None
        for col in ['timestamp', 'date', 'datetime', 'time']:
            if col in df.columns:
                date_col = col
                break
        if date_col is None:
            df['index_date'] = pd.date_range(start='2023-01-01', periods=len(df), freq='H')
            date_col = 'index_date'
        df[date_col] = pd.to_datetime(df[date_col])
        if quartier_filter != "Tous" and 'quartier' in df.columns:
            df = df[df['quartier'] == quartier_filter]
        df = df.sort_values(date_col)
        df_daily = df.groupby(df[date_col].dt.date).agg({'coupure': ['sum', 'count']}).reset_index()
        df_daily.columns = ['date', 'coupures', 'total']
        df_daily['taux'] = (df_daily['coupures'] / df_daily['total'] * 100)
        df_daily['niveau'] = df_daily['taux'].apply(classify_risk)
        df_daily['couleur'] = df_daily['taux'].apply(get_risk_color)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_daily['date'], y=df_daily['taux'],
            mode='lines+markers', name='Taux', line=dict(width=2, color='#28a745'),
            marker=dict(size=6, color=df_daily['couleur']),
            fill='tozeroy',
            customdata=df_daily[['niveau', 'coupures']],
            hovertemplate='<b>%{x}</b><br>Taux: %{y:.1f}%<br>Niveau: %{customdata[0]}<extra></extra>'
        ))
        fig.add_hline(y=RISK_THRESHOLDS['faible'], line_dash="dash", line_color="#ffc107", annotation_text="Seuil MOYEN")
        fig.add_hline(y=RISK_THRESHOLDS['eleve'], line_dash="dash", line_color="#dc3545", annotation_text="Seuil ÉLEVÉ")
        title = f"Tendance - {quartier_filter}" if quartier_filter != "Tous" else "Tendance"
        fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Taux (%)", height=500)
        return fig
    except Exception as e:
        logger.warning(f"create_risk_trend_chart failed: {e}")
        return None

