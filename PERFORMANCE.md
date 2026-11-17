# Rapport de Performance - Dakar Power Prediction

> ⚠️ **Données synthétiques : démonstration technique, pas des mesures du réseau SENELEC.** Toutes les métriques ci-dessous sont mesurées sur des données générées artificiellement.

**Dernière mesure des métriques** : 2026-11-17 (modèles de `models/` rechargés et évalués sur le jeu de test)

## 📊 Modèles Déployés

### LightGBM (Gradient Boosting)
- **Fichier** : `models/lgbm_model.pkl` (`lgb.Booster`, entraîné par `scripts/2_train_models.py`)
- **Statut** : ✅ Entraîné et évalué sur données synthétiques

**Configuration réelle** (`lgb.train`) :
- `objective='binary'`, `num_leaves=31`, `learning_rate=0.05`
- `feature_fraction=0.9`, `bagging_fraction=0.8`, `bagging_freq=5`
- 100 itérations maximum, arrêt anticipé (patience 10) → **90 arbres** retenus

### LSTM (Deep Learning)
- **Fichier** : `models/lstm_model.keras`
- **Statut** : ✅ Entraîné et évalué sur données synthétiques

**Architecture réelle** :
- LSTM(64, `return_sequences=True`) → Dropout(0.2) → LSTM(32) → Dropout(0.2) → Dense(16, ReLU) → Dense(1, sigmoid)
- Adam, `binary_crossentropy`, 50 epochs maximum, `batch_size=32`, arrêt anticipé (patience 5, meilleurs poids restaurés)
- Entrée de forme `(1, 1, 9)` : un seul pas de temps, donc pas de modélisation temporelle réelle

### Modèle Ensemble
- **Méthode** : Moyenne simple des probabilités LightGBM et LSTM
- **Ajustement** : Coefficient par quartier appliqué après prédiction (le quartier n'est pas une feature)
- **Normalisation** : StandardScaler ajusté sur la partie entraînement uniquement

## 📁 Dataset

- **Fichier** : `data/synthetic/synthetic_data_v2.csv` — 70 000 lignes, 8 quartiers, dates 01/2023 → 06/2024
- **Split** : 80 % train (56 000) / 20 % test (14 000), stratifié, `random_state=42`
- **Taux de coupure** : 14,05 %
- Détails et limites : voir [`docs/DATA.md`](docs/DATA.md)

### Features (ordre du scaler)
1. `temp_celsius`, `humidite_percent`, `vitesse_vent`, `conso_megawatt`
2. `heure`, `jour_semaine`, `mois`
3. `saison` — binaire : 1 = juin à août, 0 = reste de l'année
4. `is_peak_hour` — 1 de 18h à 22h inclus, 0 sinon

L'application encode ces deux features exactement comme le CSV (vérifié par `tests/test_features.py`). Entre le 17/06/2026 et cette correction, l'app utilisait un autre encodage (3 saisons, pointe 7-9h + 18-21h) : l'AUC mesurée avec cet encodage tombait à 0,834, et à 22h l'app affichait un risque quasi nul alors que le taux de coupure du dataset est de 43 %.

### Variable cible
- **Coupure** : binaire (0 = pas de coupure, 1 = coupure)

## 📐 Métriques mesurées (jeu de test, 14 000 lignes, 1 967 coupures)

| Modèle | AUC-ROC | PR-AUC | Seuil | Précision | Rappel | F1 | Matrice [[VN, FP], [FN, VP]] |
|---|---|---|---|---|---|---|---|
| LightGBM | 0,873 | 0,503 | 0,50 | 0,604 | 0,303 | 0,404 | [[11643, 390], [1371, 596]] |
| LightGBM | | | 0,25 | 0,454 | 0,597 | 0,516 | [[10618, 1415], [792, 1175]] |
| LSTM | 0,874 | 0,513 | 0,50 | 0,627 | 0,239 | 0,346 | [[11753, 280], [1497, 470]] |
| LSTM | | | 0,25 | 0,456 | 0,601 | 0,519 | [[10623, 1410], [785, 1182]] |
| Ensemble (moyenne) | 0,874 | 0,510 | 0,25 | 0,456 | 0,601 | 0,519 | [[10624, 1409], [785, 1182]] |
| **Référence « jamais de coupure »** | 0,500 | — | — | — | 0 | 0 | [[12033, 0], [1967, 0]] |
| Référence régression logistique | 0,842 | | | | | | |

**Exactitude (accuracy)** : LightGBM 87,4 % au seuil 0,5, contre **85,95 %** pour la référence « jamais de coupure ». Le gain d'exactitude est donc de 1,5 point seulement ; l'AUC et le rappel sont des indicateurs plus parlants.

### Ce que le modèle apprend
- Importance (gain LightGBM) : `is_peak_hour` 51 %, `humidite_percent` 24 %, `conso_megawatt` 12 %, `temp_celsius` 8 %, le reste < 3 %.
- Taux de coupure : 43,6 % en heure de pointe contre 6,3 % hors pointe. À l'intérieur des heures de pointe, l'AUC tombe à 0,68.
- Le LSTM n'apporte pas de gain mesurable par rapport à LightGBM.

### ⚠️ Biais optimiste connu
Le jeu de test **n'est pas strictement indépendant** : il a servi
- à l'arrêt anticipé de LightGBM (`valid_sets=[test_data]`),
- à l'arrêt anticipé du LSTM (`validation_data=test`, meilleurs poids restaurés),
- au choix du seuil 0,25.

Les chiffres ci-dessus surestiment donc légèrement la performance attendue sur des données nouvelles. Correction prévue : découpage train / validation / test.

## 🎯 Niveaux de Risque

Le risque affiché est la **probabilité brute** de l'ensemble (moyenne LightGBM/LSTM), multipliée par le coefficient du quartier, puis bornée à 100 %. Aucun rééchelonnement ni plancher. Cette probabilité est bien calibrée sur le test : moyenne prédite 14,1 %, taux réel 14,05 %, écart ≤ 1,6 point par décile.

Seuils fixés sur la distribution du jeu de test (14 000 lignes, coefficient de quartier appliqué) :

| Niveau | Plage | Part des cas | Taux de coupure réel | Part des coupures captées |
|--------|-------|---|---|---|
| **FAIBLE** | < 15 % | 61,4 % | 2,5 % | 10,9 % |
| **MOYEN** | 15-35 % | 24,9 % | 22,0 % | 38,8 % |
| **ÉLEVÉ** | ≥ 35 % | 13,7 % | 51,5 % | 50,2 % |

FAIBLE correspond à un risque inférieur au taux moyen (14 %) ; ÉLEVÉ à une coupure plus probable qu'improbable. Probabilité maximale observée : 0,72 avant coefficient, 0,84 après. Ces seuils ont été choisis sur le jeu de test, déjà utilisé pour l'arrêt anticipé : même réserve d'optimisme que pour les métriques.

*Historique : jusqu'à cette correction, l'app multipliait la probabilité par 2 (« seuil 0,25 → 50 % »), plafonnait avant d'appliquer le coefficient, imposait un plancher de 5 % et classait à 40 / 70 %.*

## 📊 Ajustements par Quartier

Coefficients appliqués après prédiction, cohérents avec le ratio (taux du quartier / taux moyen 14,05 %) dans le CSV :

| Quartier | Coefficient | Taux dans le CSV | Ratio mesuré |
|---|---|---|---|
| Pikine | 1,20 | 16,9 % | 1,20 |
| Guédiawaye | 1,15 | 16,2 % | 1,15 |
| Parcelles Assainies | 1,10 | 14,7 % | 1,05 |
| Sicap-Liberté | 1,05 | 14,8 % | 1,05 |
| Yoff | 1,00 | 13,5 % | 0,96 |
| Fann | 0,95 | 12,9 % | 0,92 |
| Mermoz-Sacré-Cœur | 0,90 | 12,0 % | 0,85 |
| Dakar-Plateau | 0,85 | 11,5 % | 0,82 |

## 📈 Vérifications fonctionnelles de l'application

- ✅ Chargement des modèles dans l'application Streamlit
- ✅ Prédictions instantanées (à partir des curseurs) pour un quartier et pour la carte
- ✅ Visualisations (jauge, carte, graphiques) et export CSV
- ✅ Exploration du dataset synthétique

## ✅ Conclusion

Démonstrateur technique fonctionnel (pipeline, application, carte). Sur données synthétiques, le modèle atteint une AUC de 0,87, mais son apport par rapport à une règle « heure de pointe » est limité, et **aucune performance sur le réseau réel n'a été mesurée**. Un réentraînement sur données réelles est indispensable avant tout usage opérationnel.
