---
title: Dakar Power Prediction
emoji: ⚡
colorFrom: yellow
colorTo: red
sdk: docker
pinned: false
---
# ⚡ Dakar Power Prediction
### Système de Prédiction des Coupures d'Électricité à Dakar par Machine Learning

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![CI](https://github.com/chniang/dakar-power-prediction/actions/workflows/ci.yml/badge.svg)](https://github.com/chniang/dakar-power-prediction/actions)
[![HF Spaces](https://img.shields.io/badge/🤗%20HF%20Spaces-Live-blue)](https://huggingface.co/spaces/TIJAANI/dakar-power-prediction)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 CONTEXTE & PROBLÉMATIQUE

Les délestages électriques sont un défi majeur à Dakar, impactant quotidiennement les ménages, commerces et services publics. L'absence d'outil prédictif empêche les citoyens et gestionnaires de réseaux d'anticiper ces coupures et d'adapter leurs activités.

**Objectif du projet :** Développer un système de prédiction intelligent capable d'anticiper les risques de coupure d'électricité dans 8 quartiers stratégiques de Dakar, en fonction des conditions météorologiques et de la consommation.

---

## 🎯 SOLUTION DÉVELOPPÉE

Application web interactive permettant de :
- **Prédire en temps réel** le risque de coupure (0-100%) pour chaque quartier
- **Visualiser géographiquement** les zones à risque sur une carte interactive
- **Analyser les tendances** de consommation et de coupures par quartier
- **Exporter les données** pour reporting et analyses complémentaires

**Zones couvertes :** Guédiawaye, Parcelles Assainies, Sicap-Liberté, Yoff, Mermoz-Sacré-Cœur, Dakar-Plateau *(données d'entraînement)*, Pikine et Fann *(estimations par ajustement géographique)*

---

## 🤖 APPROCHE MACHINE LEARNING

### Modèle Hybride Performant

J'ai développé un **système d'ensemble combinant 2 algorithmes** pour maximiser la précision :

1. **LightGBM** (Gradient Boosting)
   - Traitement rapide des features tabulaires
   - Gestion native des variables catégorielles

2. **LSTM** (Deep Learning - Réseau de Neurones Récurrent, 2 couches)
   - Capture des interactions entre features
   - Apprentissage de patterns complexes

3. **Prédiction finale** : Moyenne simple des 2 modèles
   - Risque exprimé en pourcentage (0-100%)
   - Classification : FAIBLE (0-39%), MOYEN (40-69%), ÉLEVÉ (70-100%)

### Dataset

- **70 000 enregistrements** de données synthétiques réalistes (6 quartiers entraînés)
- **Features principales :** Température, Humidité, Vitesse du vent, Consommation électrique, Heure, Jour, Mois, Saison, Heure de pointe
- **Target :** Présence ou absence de coupure (binaire)

---

## 🛠️ STACK TECHNIQUE

**Machine Learning & Data Science**
- `LightGBM` : Gradient Boosting optimisé
- `TensorFlow/Keras` : Deep Learning (LSTM)
- `Scikit-learn` : Preprocessing, métriques
- `Pandas`, `NumPy` : Manipulation de données

**Développement Web**
- `Streamlit` : Interface interactive
- `Plotly` : Visualisations dynamiques (cartes, graphiques)

**Déploiement**
- Modèles pré-entraînés : `lgbm_model.pkl`, `lstm_model.keras`, `scaler.pkl`
- Conteneurisation Docker pour portabilité

---

## 📊 RÉSULTATS CLÉS

✅ **Modèles validés** sur données synthétiques (split 80/20)  
✅ **Temps de prédiction : <1 seconde** pour les 8 quartiers  
✅ **Interface responsive** accessible sur desktop et mobile  
✅ **Export CSV** pour intégration dans systèmes de reporting  
✅ **Prévisions météo 7 jours** via Open-Meteo API intégrée

### Patterns observés dans les données synthétiques

- **Guédiawaye** présente le facteur de risque le plus élevé parmi les quartiers entraînés
- **Corrélation** entre pics de consommation (18-21h, 7-9h) et risques de délestage

---

## 🚀 INSTALLATION & UTILISATION

### Prérequis
```bash
Python 3.9+
pip
```

### Installation
```bash
# Cloner le repo
git clone https://github.com/chniang/dakar-power-prediction.git
cd dakar-power-prediction

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run streamlit_app/app.py
```

### Utilisation
1. **Onglet Prédiction** : Sélectionner quartier + saisir conditions météo → Obtenir le risque (+ bouton Export CSV)
2. **Onglet Carte** : Visualiser tous les quartiers simultanément sur une carte interactive
3. **Onglet Statistiques** : Analyser les taux de coupure historiques par quartier
4. **Onglet Historique** : Explorer les tendances temporelles de consommation et de risque

---

## 📸 APERÇU

### Interface de Prédiction
![Prédiction](images/prediction.png)

### Carte Interactive des Quartiers
![Carte](images/carte.png)

### Statistiques et Tendances
![Statistiques](images/analytics.png)

---

## 🔮 AMÉLIORATIONS FUTURES

- [ ] Intégration données réelles SENELEC pour réentraînement
- [x] ✅ Données météo temps réel via Open-Meteo API (déjà intégré)
- [ ] Ajout de notifications push pour alertes en temps réel
- [ ] Extension à d'autres villes du Sénégal (Thiès, Saint-Louis)
- [ ] Module de recommandations personnalisées (ex: meilleur moment pour utiliser électroménagers)
- [ ] Tableau de bord admin pour gestionnaires de réseau

---

## 👨‍💻 AUTEUR

**Cheikh Niang** - Data Scientist spécialisé IA & Énergie  
Passionné par l'application du ML à des problèmes sociétaux réels en Afrique.

📧 cheikhniang159@gmail.com  
💼 [LinkedIn](https://www.linkedin.com/in/cheikh-niang-5370091b5/)
🌐 [Portfolio](https://portfolio-cheikh-niang.vercel.app/)
---

## 📄 LICENCE

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 🙏 REMERCIEMENTS

- **GoMyCode Dakar** pour la formation Data Science
- Communauté open-source (LightGBM, TensorFlow, Streamlit)
