---
title: Dakar Power Prediction
emoji: ⚡
colorFrom: yellow
colorTo: orange
sdk: docker
pinned: false
license: mit
---

# ⚡ Dakar Power Prediction - Prédiction des Coupures d'Électricité

Application web de prédiction des risques de coupures d'électricité dans **8 quartiers de Dakar** utilisant le **Machine Learning** et le **Deep Learning**.

## 🎯 Objectif

Anticiper les coupures d'électricité pour permettre aux gestionnaires de réseaux et aux citoyens de mieux planifier leurs activités.

## ✨ Fonctionnalités

### 🔮 Prédiction en Temps Réel
- Analyse basée sur conditions météo (température, humidité, vent)
- Calcul du niveau de risque (FAIBLE 0-39%, MOYEN 40-69%, ÉLEVÉ 70-100%)
- Visualisation avec jauge interactive

### 🗺️ Carte Interactive
- Visualisation géographique des 8 quartiers de Dakar
- Prédictions simultanées pour toutes les zones
- Interface Plotly interactive

### 📊 Analytics
- Statistiques par quartier
- Graphiques de taux de coupure
- Analyse comparative des zones

### 📈 Historique et Tendances
- Évolution temporelle de la consommation
- Tendances des risques de coupure
- Filtrage par quartier

### 💾 Export
- Téléchargement des prédictions en CSV
- Historique complet des analyses

## 🤖 Modèles de Machine Learning

### Ensemble de 2 Modèles
- **LightGBM** (Gradient Boosting) : ~88% de précision
- **LSTM** (Deep Learning) : ~90% de précision
- **Combinaison pondérée** : Risque final en pourcentage

### Dataset
- **70,001 enregistrements** de données synthétiques
- **8 quartiers** : Dakar-Plateau, Guédiawaye, Pikine, Parcelles Assainies, Grand-Yoff, Ouakam, Médina, Almadies

## 🛠️ Technologies

- **Backend** : Python, Pandas, NumPy
- **ML/DL** : LightGBM, TensorFlow/Keras, Scikit-learn
- **Frontend** : Streamlit
- **Visualisation** : Plotly
- **Modèles** : 3 fichiers (lgbm_model.pkl, lstm_model.keras, scaler.pkl)

## 👨‍💻 Auteur

**Cheikh Niang** - Data Scientist Junior
- 🌐 Portfolio : [portfolio-cheikh-niang.streamlit.app](https://portfolio-cheikh-niang.streamlit.app)
- 💼 LinkedIn : [linkedin.com/in/cheikh-niang](https://linkedin.com/in/cheikh-niang)
- 📧 Email : cheikhniang159@gmail.com

## 📄 Licence

Projet sous licence MIT.
