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

> ⚠️ **Données synthétiques : démonstration technique, pas des mesures du réseau SENELEC.**
> Les 70 000 enregistrements utilisés pour entraîner et évaluer les modèles sont générés artificiellement. Seule la météo (Open-Meteo) est réelle.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-red.svg)](https://streamlit.io/)
[![CI](https://github.com/chniang/dakar-power-prediction/actions/workflows/ci.yml/badge.svg)](https://github.com/chniang/dakar-power-prediction/actions)
[![HF Spaces](https://img.shields.io/badge/🤗%20HF%20Spaces-Live-blue)](https://huggingface.co/spaces/TIJAANI/dakar-power-prediction)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 CONTEXTE & PROBLÉMATIQUE

Les délestages électriques sont un défi majeur à Dakar, impactant quotidiennement les ménages, commerces et services publics. L'absence d'outil prédictif empêche les citoyens et gestionnaires de réseaux d'anticiper ces coupures et d'adapter leurs activités.

**Objectif du projet :** Démontrer, sur données synthétiques, la chaîne technique d'un système capable d'anticiper les risques de coupure d'électricité dans 8 quartiers stratégiques de Dakar, en fonction des conditions météorologiques et de la consommation.

---

## 🎯 SOLUTION DÉVELOPPÉE

Application web interactive permettant de :
- **Estimer instantanément** un risque de coupure pour chaque quartier, à partir de conditions saisies (modèle entraîné sur données synthétiques)
- **Visualiser géographiquement** les zones à risque sur une carte interactive
- **Explorer le dataset synthétique** (consommation et coupures par quartier)
- **Exporter les données** pour reporting et analyses complémentaires

**Zones couvertes :** Guédiawaye, Parcelles Assainies, Pikine, Sicap-Liberté, Yoff, Mermoz-Sacré-Cœur, Dakar-Plateau, Fann — les 8 quartiers sont présents dans le dataset synthétique. Le quartier n'est pas une variable du modèle : il est appliqué par un coefficient multiplicateur après prédiction.

---

## 🤖 APPROCHE MACHINE LEARNING

### Modèle Hybride Performant

J'ai développé un **système d'ensemble combinant 2 algorithmes** pour maximiser la précision :

1. **LightGBM** (Gradient Boosting)
   - Traitement rapide des features tabulaires

2. **LSTM** (Deep Learning - Réseau de Neurones Récurrent, 2 couches)
   - Capture des interactions entre features
   - Apprentissage de patterns complexes

3. **Prédiction finale** : Moyenne simple des 2 modèles
   - Risque = probabilité moyenne des 2 modèles × coefficient du quartier (en %, sans rééchelonnement)
   - Classification : FAIBLE (< 15 %), MOYEN (15-35 %), ÉLEVÉ (≥ 35 %) — sur le test synthétique, taux réel de coupure 2,5 % / 22 % / 51,5 %

### Dataset

- **70 000 enregistrements** de données synthétiques, générées par des règles simplifiées non validées sur le terrain (8 quartiers) — provenance, règles observées et limites : [docs/DATA.md](docs/DATA.md)
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

✅ **Modèles évalués** sur données synthétiques uniquement (split 80/20) — aucune validation sur données réelles  
📐 **AUC-ROC 0,87** (LightGBM et LSTM) ; exactitude 87,4 % contre 85,95 % pour un modèle qui répond toujours « pas de coupure » — détail dans [PERFORMANCE.md](PERFORMANCE.md)  
✅ **Temps de prédiction : <1 seconde** pour les 8 quartiers  
✅ **Interface responsive** accessible sur desktop et mobile  
✅ **Export CSV** pour intégration dans systèmes de reporting  
✅ **Prévisions météo 7 jours** via Open-Meteo API intégrée

### Patterns observés dans les données synthétiques

- **Pikine** (16,9 %) et **Guédiawaye** (16,2 %) ont les taux de coupure les plus élevés, **Dakar-Plateau** le plus bas (11,5 %)
- Les coupures sont concentrées sur **18h-22h** (≈ 44 % contre ≈ 6 % hors pointe) ; aucun pic le matin dans ce dataset

---

## 🚀 INSTALLATION & UTILISATION

### Prérequis
```bash
Python 3.10+
pip
```

### Installation
```bash
# Cloner le repo
git clone https://github.com/chniang/dakar-power-prediction.git
cd dakar-power-prediction

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application (http://localhost:7860, port fixé dans .streamlit/config.toml)
streamlit run streamlit_app/app.py
```

### Utilisation
1. **Onglet Prédiction** : Sélectionner quartier + saisir conditions météo → Obtenir le risque (+ bouton Export CSV)
2. **Onglet Carte** : Visualiser tous les quartiers simultanément sur une carte interactive
3. **Onglet Statistiques** : Taux de coupure par quartier dans le dataset synthétique
4. **Onglet Tendances** : Évolution de la consommation et des coupures dans le dataset synthétique, plus les prévisions météo réelles à 7 jours

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

- [ ] Réentraînement sur données réelles (ex. journaux d'indisponibilité, annonces de délestage) — prérequis avant tout usage opérationnel
- [x] ✅ Météo actuelle et prévisions via Open-Meteo API (déjà intégré)
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
