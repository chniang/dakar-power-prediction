"""
Entraînement des modèles ML avec les données locales CSV
VERSION CORRIGÉE - Utilise synthetic_data_v2.csv
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb
from tensorflow import keras
from tensorflow.keras import layers
import sys

# Ajouter le dossier parent
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import MODEL_CONFIG

print("=" * 80)
print("🤖 ENTRAÎNEMENT MODÈLES - DONNÉES CSV LOCALES (70,000 lignes)")
print("=" * 80)

# ============================================================================
# ÉTAPE 1 : CHARGER LES DONNÉES DEPUIS LE CSV
# ============================================================================

print("\n📂 ÉTAPE 1 : Chargement des données depuis CSV")
print("-" * 80)

csv_path = Path('data/synthetic/synthetic_data_v2.csv')

if not csv_path.exists():
    print(f"❌ Fichier non trouvé : {csv_path}")
    print("Exécutez d'abord : python scripts/generate_new_data.py")
    sys.exit(1)

df = pd.read_csv(csv_path)
print(f"✅ {len(df)} lignes chargées")

# Vérifier les quartiers
quartiers = sorted(df['quartier'].unique())
print(f"\n📊 Quartiers dans les données ({len(quartiers)}) :")
for q in quartiers:
    count = len(df[df['quartier'] == q])
    pct = count / len(df) * 100
    print(f"  {q:25s}: {count:6d} ({pct:5.2f}%)")

# Vérifier distribution coupures
print(f"\n📊 Distribution coupures :")
for val, count in df['coupure'].value_counts().items():
    pct = count / len(df) * 100
    label = "Non" if val == 0 else "Oui"
    print(f"  {label:5s}: {count:6d} ({pct:5.2f}%)")

# ============================================================================
# ÉTAPE 2 : PRÉPARER LES FEATURES
# ============================================================================

print("\n🔧 ÉTAPE 2 : Préparation des features")
print("-" * 80)

# Features à utiliser
feature_cols = MODEL_CONFIG['features']
target_col = MODEL_CONFIG['target']

print(f"Features utilisées ({len(feature_cols)}) :")
for i, feat in enumerate(feature_cols, 1):
    print(f"  {i}. {feat}")

X = df[feature_cols].values
y = df[target_col].values

print(f"\n✅ Features préparées")
print(f"  X shape : {X.shape}")
print(f"  y shape : {y.shape}")
print(f"  Coupures : {y.sum()} ({y.mean()*100:.2f}%)")

# ============================================================================
# ÉTAPE 3 : SPLIT TRAIN/TEST
# ============================================================================

print("\n🔀 ÉTAPE 3 : Split train/test (80/20)")
print("-" * 80)

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=MODEL_CONFIG['test_size'],
    random_state=MODEL_CONFIG['random_state'],
    stratify=y
)

print(f"✅ Train : {len(X_train):,} samples ({y_train.mean()*100:.2f}% coupures)")
print(f"✅ Test  : {len(X_test):,} samples ({y_test.mean()*100:.2f}% coupures)")

# ============================================================================
# ÉTAPE 4 : NORMALISATION
# ============================================================================

print("\n📐 ÉTAPE 4 : Normalisation des données")
print("-" * 80)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"✅ Scaler entraîné")
print(f"  Moyennes : {scaler.mean_[:4]}")
print(f"  Écarts-types : {scaler.scale_[:4]}")

# ============================================================================
# ÉTAPE 5 : ENTRAÎNEMENT LIGHTGBM
# ============================================================================

print("\n🌳 ÉTAPE 5 : Entraînement LightGBM")
print("-" * 80)

lgb_params = {
    'objective': 'binary',
    'metric': 'binary_logloss',
    'boosting_type': 'gbdt',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': -1,
    'random_state': 42
}

train_data = lgb.Dataset(X_train_scaled, label=y_train)
test_data = lgb.Dataset(X_test_scaled, label=y_test, reference=train_data)

print("🔄 Entraînement en cours...")
lgb_model = lgb.train(
    lgb_params,
    train_data,
    num_boost_round=100,
    valid_sets=[test_data],
    callbacks=[lgb.early_stopping(stopping_rounds=10)]
)

# Évaluation
y_pred_lgb = lgb_model.predict(X_test_scaled)
accuracy_lgb = ((y_pred_lgb > 0.5) == y_test).mean()

print(f"✅ LightGBM entraîné")
print(f"  Précision test : {accuracy_lgb*100:.2f}%")
print(f"  Prédiction moyenne : {y_pred_lgb.mean()*100:.2f}%")

# ============================================================================
# ÉTAPE 6 : ENTRAÎNEMENT LSTM
# ============================================================================

print("\n🧠 ÉTAPE 6 : Entraînement LSTM")
print("-" * 80)

# Reshape pour LSTM (samples, timesteps, features)
X_train_lstm = X_train_scaled.reshape(-1, 1, X_train_scaled.shape[1])
X_test_lstm = X_test_scaled.reshape(-1, 1, X_test_scaled.shape[1])

# Modèle LSTM
lstm_model = keras.Sequential([
    layers.LSTM(64, input_shape=(1, X_train_scaled.shape[1]), return_sequences=True),
    layers.Dropout(0.2),
    layers.LSTM(32),
    layers.Dropout(0.2),
    layers.Dense(16, activation='relu'),
    layers.Dense(1, activation='sigmoid')
])

lstm_model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

print("🔄 Entraînement en cours (peut prendre 10-15 minutes)...")
history = lstm_model.fit(
    X_train_lstm, y_train,
    validation_data=(X_test_lstm, y_test),
    epochs=50,
    batch_size=32,
    verbose=1,
    callbacks=[
        keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)
    ]
)

# Évaluation
y_pred_lstm = lstm_model.predict(X_test_lstm, verbose=0).flatten()
accuracy_lstm = ((y_pred_lstm > 0.5) == y_test).mean()

print(f"\n✅ LSTM entraîné")
print(f"  Précision test : {accuracy_lstm*100:.2f}%")
print(f"  Prédiction moyenne : {y_pred_lstm.mean()*100:.2f}%")

# ============================================================================
# ÉTAPE 7 : SAUVEGARDE DES MODÈLES
# ============================================================================

print("\n💾 ÉTAPE 7 : Sauvegarde des modèles")
print("-" * 80)

models_dir = Path('models')
models_dir.mkdir(parents=True, exist_ok=True)

# Sauvegarder LightGBM
lgb_path = models_dir / 'lgbm_model.pkl'
with open(lgb_path, 'wb') as f:
    pickle.dump(lgb_model, f)
print(f"✅ LightGBM sauvegardé : {lgb_path}")

# Sauvegarder LSTM
lstm_path = models_dir / 'lstm_model.keras'
lstm_model.save(lstm_path)
print(f"✅ LSTM sauvegardé : {lstm_path}")

# Sauvegarder Scaler
scaler_path = models_dir / 'scaler.pkl'
with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)
print(f"✅ Scaler sauvegardé : {scaler_path}")

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================

print("\n" + "=" * 80)
print("📊 RÉSUMÉ FINAL")
print("=" * 80)
print(f"✅ Données : {len(df):,} lignes, {len(quartiers)} quartiers")
print(f"✅ LightGBM : {accuracy_lgb*100:.2f}% précision")
print(f"✅ LSTM : {accuracy_lstm*100:.2f}% précision")
print(f"✅ Modèles sauvegardés dans : {models_dir}/")
print("\n" + "=" * 80)
print("✅ ENTRAÎNEMENT TERMINÉ")
print("=" * 80)
print("\nProchaine étape : streamlit run streamlit_app/app.py")