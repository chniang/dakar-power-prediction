# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dakar Power Prediction is a Streamlit web app that predicts electricity outage risk (0–100%) for 8 Dakar neighborhoods using a hybrid ML ensemble (LightGBM + LSTM). Models are pre-trained on 70,000 synthetic records and stored as binary artifacts in `models/`.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app (default port 8501)
streamlit run streamlit_app/app.py

# Retrain models from the local CSV (takes 10–15 min due to LSTM)
python scripts/2_train_models.py

# Generate fresh synthetic data (outputs to data/raw/raw_data.csv)
python src/data_generator.py
```

### Docker

```bash
docker build -t dakar-power .
docker run -p 8501:8501 dakar-power
```

The Dockerfile installs `libgomp1` (required by LightGBM on Linux) before installing Python deps.

## Architecture

```
streamlit_app/app.py        # Entry point; sidebar controls, 4 tabs (Prédiction, Carte, Stats, Historique)
streamlit_app/utils_simple.py  # All ML inference, chart creation, and model loading (@st.cache_resource)
src/config.py               # Central config: quartier names, GPS coords, risk adjustments, model feature list
src/data_generator.py       # Synthetic data generation with per-quartier risk profiles
scripts/2_train_models.py   # Train LightGBM + LSTM, saves to models/
models/                     # lgbm_model.pkl, lstm_model.keras, scaler.pkl (tracked via Git LFS)
data/synthetic/synthetic_data_v2.csv  # Training dataset (Git LFS)
```

### Prediction Pipeline

1. User sets weather/consumption inputs in sidebar → clicks "Lancer la Prédiction"
2. `create_time_features()` extracts hour, weekday, month, season, is_peak_hour from `datetime.now()`
3. `make_prediction_single()` builds a 9-feature vector, scales it with the stored `scaler.pkl`, runs LightGBM and LSTM independently, averages their outputs, then multiplies by a per-quartier `QUARTIER_ADJUSTMENT` factor (defined in `src/config.py`)
4. Risk is clamped to 0–100%; classified as FAIBLE (<40%), MOYEN (40–69%), ÉLEVÉ (≥70%)

### Model Feature Order (must match scaler fit order)

```python
['temp_celsius', 'humidite_percent', 'vitesse_vent', 'conso_megawatt',
 'heure', 'jour_semaine', 'mois', 'saison', 'is_peak_hour']
```

This order is defined in `src/config.py:MODEL_CONFIG['features']` and must stay consistent across `scripts/2_train_models.py` and `streamlit_app/utils_simple.py`.

### LSTM Input Shape

The LSTM expects shape `(1, 1, 9)` — single sample, single timestep, 9 features. This is a deliberate simplification; the model captures feature interactions rather than true time series.

## Key Constraints

- Models must be loaded from the project root (paths like `'models/lgbm_model.pkl'`). Always run the app from the repo root.
- LSTM is loaded with `compile=False` then recompiled manually to avoid Keras serialization compatibility issues.
- The app degrades gracefully: if LSTM fails to load, LightGBM prediction is used for both model slots.
- `saison` uses the 3-season Dakar encoding (0 = sèche fraîche Nov-Fév, 1 = sèche chaude Mar-Mai, 2 = pluies Jun-Oct) in both `data_generator.py` and `utils_simple.py`. Both must stay in sync.
- `is_peak_hour` = 1 for hours 7–9 and 18–21 (matching `data_generator.is_peak_hour()`). Both files must stay in sync.
