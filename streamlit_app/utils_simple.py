"""
Fonctions utilitaires - THÈME PAR DÉFAUT STREAMLIT/PLOTLY
"""
import streamlit as st
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import plotly.graph_objects as go
from tensorflow import keras
from src.config import QUARTIERS_DAKAR, COORDONNEES_QUARTIERS, QUARTIER_ADJUSTMENT

@st.cache_resource
def load_models_cached():
    models = {'lgb': None, 'lstm': None, 'scaler': None}
    try:
        with open('models/lgbm_model.pkl', 'rb') as f:
            models['lgb'] = pickle.load(f)
    except Exception as e:
        st.warning(f"⚠️ LightGBM: {e}")
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

def create_time_features(date_time):
    month = date_time.month
    if month in [12, 1, 2]:
        saison = 1
    elif month in [3, 4, 5]:
        saison = 2
    elif month in [6, 7, 8]:
        saison = 3
    else:
        saison = 4
    is_peak_hour = 1 if 18 <= date_time.hour <= 22 else 0
    return {'hour': date_time.hour, 'day_of_week': date_time.weekday(), 'month': date_time.month, 'saison': saison, 'is_peak_hour': is_peak_hour}

def make_prediction_single(models, quartier, temp, humidite, vent, conso, time_features):
    lgb_model = models['lgb']
    lstm_model = models['lstm']
    scaler = models['scaler']
    if lgb_model is None or scaler is None:
        return None
    try:
        features = [temp, humidite, vent, conso, time_features['hour'], time_features['day_of_week'], time_features['month'], time_features['saison'], time_features['is_peak_hour']]
        features_array = np.array([features])
        features_scaled = scaler.transform(features_array)
        try:
            pred_lgb = float(lgb_model.predict(features_scaled)[0]) * 100
        except:
            try:
                pred_lgb = lgb_model.predict_proba(features_scaled)[0][1] * 100
            except:
                pred_lgb = 50.0
        if lstm_model is not None:
            try:
                features_lstm = features_scaled.reshape(1, 1, -1)
                pred_lstm = float(lstm_model.predict(features_lstm, verbose=0)[0][0]) * 100
            except:
                pred_lstm = pred_lgb
        else:
            pred_lstm = pred_lgb
        risque_base = (pred_lgb + pred_lstm) / 2
        adjustment = QUARTIER_ADJUSTMENT.get(quartier, 1.0)
        risque_ajuste = risque_base * adjustment
        pred_lgb = np.clip(pred_lgb, 0, 100)
        pred_lstm = np.clip(pred_lstm, 0, 100)
        risque_ajuste = np.clip(risque_ajuste, 0, 100)
        return pred_lgb, pred_lstm, risque_ajuste
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return None

def get_risk_color(risque_pct):
    if risque_pct < 40:
        return "#28a745"
    elif risque_pct < 70:
        return "#ffc107"
    else:
        return "#dc3545"

def create_gauge_chart(risque, quartier):
    color = get_risk_color(risque)
    niveau = "FAIBLE" if risque < 40 else ("MOYEN" if risque < 70 else "ÉLEVÉ")
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risque,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"{quartier}", 'font': {'size': 20}},
        number={'suffix': "%", 'font': {'size': 50}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 2},
            'bar': {'color': color, 'thickness': 0.75},
            'steps': [
                {'range': [0, 40], 'color': '#d4edda'},
                {'range': [40, 70], 'color': '#fff3cd'},
                {'range': [70, 100], 'color': '#f8d7da'}
            ]
        }
    ))
    fig.add_annotation(
        text=f"<b>{niveau}</b>",
        x=0.5, y=0.2,
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
            niveau = "FAIBLE" if r < 40 else ("MOYEN" if r < 70 else "ÉLEVÉ")
            df_map.append({
                'Quartier': quartier, 'Latitude': coords['lat'], 'Longitude': coords['lon'],
                'Risque': r, 'Niveau': niveau
            })
    df_map = pd.DataFrame(df_map)
    df_map['Couleur'] = df_map['Risque'].apply(get_risk_color)
    df_map['Taille'] = 10 + (df_map['Risque'] / 100) * 40
    
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=df_map['Latitude'], lon=df_map['Longitude'], mode='markers',
        marker=dict(size=df_map['Taille'], color=df_map['Couleur'], opacity=0.8),
        text=df_map['Quartier'],
        customdata=df_map[['Risque', 'Niveau']],
        hovertemplate='<b>%{text}</b><br>Risque: %{customdata[0]:.1f}%<br>Niveau: %{customdata[1]}<extra></extra>'
    ))
    fig.update_layout(
        mapbox=dict(style="open-street-map", center=dict(lat=14.7167, lon=-17.4677), zoom=10),
        title="Carte des Risques",
        height=600,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    return fig

def create_bar_chart_quartiers(df_stats):
    if df_stats is None or len(df_stats) == 0:
        return None
    df_sorted = df_stats.sort_values('taux_coupure', ascending=False)
    risques_pct = (df_sorted['taux_coupure'] * 100).tolist()
    colors = [get_risk_color(r) for r in risques_pct]
    niveaux = ["FAIBLE" if r < 40 else ("MOYEN" if r < 70 else "ÉLEVÉ") for r in risques_pct]
    
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
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        if quartier_filter != "Tous" and 'quartier' in df.columns:
            df = df[df['quartier'] == quartier_filter]
        df_sample = df.sample(min(1000, len(df))).sort_values(date_col)
        
        fig = go.Figure()
        if 'conso_megawatt' in df_sample.columns:
            fig.add_trace(go.Scatter(
                x=df_sample[date_col], y=df_sample['conso_megawatt'],
                mode='lines', name='Consommation', line=dict(color='#00bcd4', width=1.5),
                fill='tozeroy', hovertemplate='<b>Conso</b><br>%{y:.0f} MW<extra></extra>'
            ))
        if 'temp_celsius' in df_sample.columns:
            fig.add_trace(go.Scatter(
                x=df_sample[date_col], y=df_sample['temp_celsius'],
                mode='lines', name='Température', line=dict(color='#ff5722', width=1.5, dash='dot'),
                yaxis='y2', hovertemplate='<b>Temp</b><br>%{y:.1f}°C<extra></extra>'
            ))
        title = f"Évolution - {quartier_filter}" if quartier_filter != "Tous" else "Évolution Historique"
        fig.update_layout(
            title=title, xaxis_title="Date",
            yaxis=dict(title="Consommation (MW)"),
            yaxis2=dict(title="Température (°C)", overlaying='y', side='right'),
            hovermode='x unified', height=500
        )
        return fig
    except:
        return None

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
        df_daily['niveau'] = df_daily['taux'].apply(lambda t: "FAIBLE" if t < 40 else ("MOYEN" if t < 70 else "ÉLEVÉ"))
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
        fig.add_hline(y=40, line_dash="dash", line_color="#ffc107", annotation_text="Seuil MOYEN")
        fig.add_hline(y=70, line_dash="dash", line_color="#dc3545", annotation_text="Seuil ÉLEVÉ")
        title = f"Tendance - {quartier_filter}" if quartier_filter != "Tous" else "Tendance"
        fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Taux (%)", height=500)
        return fig
    except:
        return None

