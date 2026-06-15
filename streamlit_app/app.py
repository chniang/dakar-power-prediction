import logging
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from streamlit_app.utils_simple import (
    load_models_cached,
    create_time_features,
    make_prediction_single,
    create_gauge_chart,
    create_map,
    create_bar_chart_quartiers,
    create_temporal_chart,
    create_risk_trend_chart,
)
from src.config import QUARTIERS_DAKAR, QUARTIER_ADJUSTMENT, classify_risk
from src.weather_api import get_current_weather_dakar, get_weather_forecast_7days

st.set_page_config(page_title="Dakar Power", page_icon="⚡", layout="wide")

# Clear old session state
if 'initialized' not in st.session_state:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state['initialized'] = True

models = load_models_cached()

_QUARTIER_RENAME = {
    'Sicap-Liberte':    'Sicap-Liberté',
    'Mermoz-Sacre-Coeur': 'Mermoz-Sacré-Cœur',
}

@st.cache_data
def load_csv():
    try:
        df = pd.read_csv("data/synthetic/synthetic_data_v2.csv")
        df['quartier'] = df['quartier'].replace(_QUARTIER_RENAME)
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        return None

df_hist = load_csv()

st.sidebar.title("🌡️ Paramètres")

if st.sidebar.button("🌤️ Météo actuelle Dakar", use_container_width=True):
    weather = get_current_weather_dakar()
    if weather:
        st.session_state['s_temp']  = float(np.clip(weather['temperature'], 15.0, 45.0))
        st.session_state['s_hum']   = float(np.clip(weather['humidity'],    30.0, 100.0))
        st.session_state['s_wind']  = float(np.clip(weather['wind_speed'],  0.0,  50.0))
        st.session_state['wx_time'] = weather['timestamp']
    else:
        st.sidebar.error("❌ API météo indisponible")

if 'wx_time' in st.session_state:
    st.sidebar.caption(f"⏱️ Données météo en temps réel — {st.session_state['wx_time']}")

temperature  = st.sidebar.slider("Température (°C)",   15.0,  45.0,  25.0,  0.5,  key='s_temp')
humidite     = st.sidebar.slider("Humidité (%)",        30.0, 100.0,  65.0,  1.0,  key='s_hum')
vitesse_vent = st.sidebar.slider("Vent (km/h)",          0.0,  50.0,  15.0,  1.0,  key='s_wind')
consommation = st.sidebar.slider("Consommation (MW)",  400.0, 1500.0, 800.0, 10.0)
quartier = st.sidebar.selectbox("Quartier", QUARTIERS_DAKAR, index=0)

if st.sidebar.button("🔮 Lancer la Prédiction", type="primary", use_container_width=True):
    st.session_state['run'] = True
    st.session_state['params'] = {
        'quartier': quartier, 'temperature': temperature, 'humidite': humidite,
        'vitesse_vent': vitesse_vent, 'consommation': consommation, 'timestamp': datetime.now()
    }

st.sidebar.markdown("---")
st.sidebar.header("ℹ️ À propos")
st.sidebar.info("""
**Dakar Power Prediction**

Application de prédiction des coupures d'électricité à Dakar.

**Modèles :**
- 🌳 LightGBM
- 🧠 LSTM

**Données :**
- 70,001 enregistrements
- 8 quartiers
""")
st.sidebar.markdown("---")
st.sidebar.caption("⚡ Version 1.0")

st.title("⚡ Dakar Power Prediction")

col1, col2, col3 = st.columns(3)
with col1:
    st.success("✅ LightGBM" if models['lgb'] else "❌ LightGBM")
with col2:
    st.success("✅ LSTM" if models['lstm'] else "⚠️ LSTM")
with col3:
    st.success(f"✅ CSV ({len(df_hist):,} lignes)" if df_hist is not None else "❌ CSV")

tab1, tab2, tab3, tab4 = st.tabs(["🎯 Prédiction", "🗺️ Carte", "📊 Statistiques", "📈 Historique"])

with tab1:
    st.header("🎯 Prédiction Immédiate")
    if st.session_state.get('run', False):
        params = st.session_state['params']
        time_features = create_time_features(params['timestamp'])
        result = make_prediction_single(models, params['quartier'], params['temperature'], params['humidite'], params['vitesse_vent'], params['consommation'], time_features)
        
        if result:
            pred_lgb, pred_lstm, risque = result
            niveau = classify_risk(risque)
            
            if 'predictions_history' not in st.session_state:
                st.session_state['predictions_history'] = []
            st.session_state['predictions_history'].append({'Date': params['timestamp'], 'Quartier': params['quartier'], 'Température': params['temperature'], 'Humidité': params['humidite'], 'Vent': params['vitesse_vent'], 'Consommation': params['consommation'], 'LightGBM': pred_lgb, 'LSTM': pred_lstm, 'Risque': risque, 'Niveau': niveau})
            
            st.subheader(f"📍 {params['quartier']}")
            fig = create_gauge_chart(risque, params['quartier'])
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🌳 LightGBM", f"{pred_lgb:.1f}%")
            with col2:
                st.metric("🧠 LSTM", f"{pred_lstm:.1f}%")
            with col3:
                st.metric("⚠️ NIVEAU", niveau)
            
            if risque < 40:
                st.success(f"✅ Risque {niveau} ({risque:.0f}%)")
            elif risque < 70:
                st.warning(f"⚠️ Risque {niveau} ({risque:.0f}%)")
            else:
                st.error(f"🚨 Risque {niveau} ({risque:.0f}%)")
            
            if st.session_state.get('predictions_history'):
                df_export = pd.DataFrame(st.session_state['predictions_history'])
                csv = df_export.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Télécharger CSV", csv, f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")
        st.session_state['run'] = False
    else:
        st.info("👈 Configurez et cliquez sur 'Lancer la Prédiction'")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🌡️ Température", f"{temperature}°C")
            st.metric("💧 Humidité", f"{humidite}%")
        with col2:
            st.metric("💨 Vent", f"{vitesse_vent} km/h")
            st.metric("⚡ Consommation", f"{consommation} MW")

with tab2:
    st.header("🗺️ Carte Interactive")
    if st.button("🔄 Calculer pour tous les quartiers"):
        time_features = create_time_features(datetime.now())
        lgb_model = models['lgb']
        lstm_model = models['lstm']
        scaler = models['scaler']

        results = []
        if lgb_model is None or scaler is None:
            st.error("Modèles non chargés — impossible de calculer la carte.")
        else:
            # Matrice 8×9 : une ligne par quartier, mêmes features météo pour tous
            feature_row = [
                temperature, humidite, vitesse_vent, consommation,
                time_features['hour'], time_features['day_of_week'],
                time_features['month'], time_features['saison'],
                time_features['is_peak_hour'],
            ]
            X = np.tile(feature_row, (len(QUARTIERS_DAKAR), 1))   # (8, 9)
            X_scaled = scaler.transform(X)                         # une seule passe

            preds_lgb = lgb_model.predict(X_scaled) * 100         # (8,) en un appel

            if lstm_model is not None:
                X_lstm = X_scaled.reshape(len(QUARTIERS_DAKAR), 1, -1)  # (8, 1, 9)
                preds_lstm = lstm_model.predict(X_lstm, verbose=0).flatten() * 100
            else:
                preds_lstm = preds_lgb.copy()

            risque_base = (preds_lgb + preds_lstm) / 2

            results = [
                {
                    'Quartier': q,
                    'Risque': float(np.clip(risque_base[i] * QUARTIER_ADJUSTMENT.get(q, 1.0), 0, 100)),
                }
                for i, q in enumerate(QUARTIERS_DAKAR)
            ]
        if results:
            fig = create_map(results)
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
            df_res = pd.DataFrame(results).sort_values('Risque', ascending=False)
            df_res['Niveau'] = df_res['Risque'].apply(classify_risk)
            df_res['Risque'] = df_res['Risque'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(df_res, use_container_width=True, hide_index=True)

with tab3:
    st.header("📊 Statistiques CSV")
    if df_hist is not None:
        # Métriques globales SENELEC
        m1, m2, m3, m4 = st.columns(4)
        q_max = df_hist.groupby('quartier')['coupure'].mean().idxmax()
        with m1:
            st.metric("🔴 Total Coupures", f"{int(df_hist['coupure'].sum()):,}")
        with m2:
            st.metric("⚠️ Plus à risque", q_max)
        with m3:
            st.metric("📊 Taux moyen", f"{df_hist['coupure'].mean()*100:.1f}%")
        with m4:
            st.metric("🌡️ Temp. moyenne", f"{df_hist['temp_celsius'].mean():.1f}°C")

        st.markdown("---")

        quartier_filter = st.selectbox("Quartier", ["Tous"] + QUARTIERS_DAKAR, index=0, key='stats_q')
        df_f = df_hist if quartier_filter == "Tous" else df_hist[df_hist['quartier'] == quartier_filter]
        stats = df_f.groupby('quartier').agg({'coupure': ['sum', 'count'], 'temp_celsius': 'mean', 'conso_megawatt': 'mean'}).reset_index()
        stats.columns = ['quartier', 'coupures', 'total', 'temp_moy', 'conso_moy']
        stats['taux_coupure'] = stats['coupures'] / stats['total']
        fig = create_bar_chart_quartiers(stats)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(stats, use_container_width=True, hide_index=True)
        st.info(f"📊 {len(df_f):,} enregistrements")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("⏰ Risque par Heure")
            by_hour = df_hist.groupby('heure')['coupure'].mean() * 100
            fig_h = go.Figure()
            fig_h.add_trace(go.Scatter(
                x=list(range(24)),
                y=by_hour.reindex(range(24), fill_value=0).values,
                mode='lines+markers', fill='tozeroy',
                line=dict(color='#e74c3c', width=2), marker=dict(size=5),
            ))
            fig_h.update_layout(
                xaxis_title="Heure", yaxis_title="Taux (%)",
                xaxis=dict(tickmode='linear', tick0=0, dtick=3),
                height=350, margin=dict(t=10),
            )
            st.plotly_chart(fig_h, use_container_width=True)
            st.caption("⚡ Le pic 18-22h correspond aux heures de pointe du réseau SENELEC (données historiques)")
        with col2:
            st.subheader("📅 Risque par Mois")
            by_month = df_hist.groupby('mois')['coupure'].mean() * 100
            month_labels = ['Jan','Fév','Mar','Avr','Mai','Juin','Juil','Aoû','Sep','Oct','Nov','Déc']
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(
                x=month_labels,
                y=by_month.reindex(range(1, 13), fill_value=0).values,
                marker_color='#f39c12', opacity=0.85,
            ))
            fig_m.update_layout(xaxis_title="Mois", yaxis_title="Taux (%)", height=350, margin=dict(t=10))
            st.plotly_chart(fig_m, use_container_width=True)
            st.caption("ℹ️ Dataset synthétique 2023-2024 : les pics de Déc/Fév reflètent la distribution des données d'entraînement, pas nécessairement la saisonnalité réelle.")

with tab4:
    st.header("📈 Historique")
    if df_hist is not None:
        quartier_hist = st.selectbox("Quartier", ["Tous"] + QUARTIERS_DAKAR, index=0, key='hist_q')
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📉 Évolution Temporelle")
            fig_temp = create_temporal_chart(df_hist, quartier_hist)
            if fig_temp:
                st.plotly_chart(fig_temp, use_container_width=True)
        with col2:
            st.subheader("📊 Tendance des Risques")
            fig_risk = create_risk_trend_chart(df_hist, quartier_hist)
            if fig_risk:
                st.plotly_chart(fig_risk, use_container_width=True)

        st.markdown("---")
        st.subheader("🌤️ Prévisions Météo 7 Jours")
        forecast = get_weather_forecast_7days()
        if forecast:
            df_fc = pd.DataFrame(forecast)
            fig_fc = go.Figure()
            fig_fc.add_trace(go.Bar(
                x=df_fc['date'], y=df_fc['precipitation'],
                name='Précipitations (mm)', marker_color='#3498db', opacity=0.6,
            ))
            fig_fc.add_trace(go.Scatter(
                x=df_fc['date'], y=df_fc['temp_max'],
                mode='lines+markers', name='Temp max (°C)',
                line=dict(color='#e74c3c', width=2), yaxis='y2',
            ))
            fig_fc.add_trace(go.Scatter(
                x=df_fc['date'], y=df_fc['temp_min'],
                mode='lines+markers', name='Temp min (°C)',
                line=dict(color='#2ecc71', width=2, dash='dot'), yaxis='y2',
            ))
            fig_fc.update_layout(
                title="Prévisions Météo Dakar — 7 prochains jours",
                xaxis_title="Date",
                yaxis=dict(title="Précipitations (mm)"),
                yaxis2=dict(title="Température (°C)", overlaying='y', side='right'),
                hovermode='x unified',
                height=400,
            )
            st.plotly_chart(fig_fc, use_container_width=True)
        else:
            st.info("🌐 Prévisions indisponibles (API météo)")



