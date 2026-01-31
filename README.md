# ⚡ Dakar Power Prediction
### Système de Prédiction des Coupures d'Électricité à Dakar par Machine Learning

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
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

**Zones couvertes :** Dakar-Plateau, Guédiawaye, Pikine, Parcelles Assainies, Grand-Yoff, Ouakam, Médina, Almadies

---

## 🤖 APPROCHE MACHINE LEARNING

### Modèle Hybride Performant

J'ai développé un **système d'ensemble combinant 2 algorithmes** pour maximiser la précision :

1. **LightGBM** (Gradient Boosting)
   - Traitement rapide des features tabulaires
   - Gestion native des variables catégorielles
   - **Précision : ~88%**

2. **LSTM** (Deep Learning - Réseau de Neurones Récurrent)
   - Capture des dépendances temporelles
   - Apprentissage de patterns complexes
   - **Précision : ~90%**

3. **Prédiction finale** : Moyenne pondérée des 2 modèles
   - Risque exprimé en pourcentage (0-100%)
   - Classification : FAIBLE (0-39%), MOYEN (40-69%), ÉLEVÉ (70-100%)

### Dataset

- **70 001 enregistrements** de données synthétiques réalistes
- **Features principales :** Température, Humidité, Vitesse du vent, Consommation électrique, Quartier, Période (jour/nuit)
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

✅ **Précision globale : 88-90%** sur les prédictions de coupure  
✅ **Temps de prédiction : <1 seconde** pour les 8 quartiers  
✅ **Interface responsive** accessible sur desktop et mobile  
✅ **Export CSV** pour intégration dans systèmes de reporting

### Insights Métier Découverts

- **65% des coupures** surviennent en période de forte chaleur (>30°C)
- **Pikine et Guédiawaye** présentent les taux de coupure les plus élevés
- **Corrélation forte** entre pics de consommation (19h-22h) et risques de délestage

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
1. **Onglet Prédiction** : Sélectionner quartier + saisir conditions météo → Obtenir le risque
2. **Onglet Carte** : Visualiser tous les quartiers simultanément
3. **Onglet Analytics** : Analyser statistiques et tendances
4. **Export** : Télécharger les résultats en CSV

---

## 📸 APERÇU

### Interface de Prédiction
![Prédiction](images/prediction.png)

### Carte Interactive des Quartiers
![Carte](images/carte.png)

### Analytics et Tendances
![Analytics](images/analytics.png)

---

## 🔮 AMÉLIORATIONS FUTURES

- [ ] Intégration de données réelles SENELEC (si API disponible)
- [ ] Ajout de notifications push pour alertes en temps réel
- [ ] Extension à d'autres villes du Sénégal (Thiès, Saint-Louis)
- [ ] Module de recommandations personnalisées (ex: meilleur moment pour utiliser électroménagers)
- [ ] Tableau de bord admin pour gestionnaires de réseau

---

## 👨‍💻 AUTEUR

**Cheikh Niang** - Data Scientist Junior  
Passionné par l'application du ML à des problèmes sociétaux réels en Afrique.

📧 cheikhniang159@gmail.com  
💼 [LinkedIn](https://linkedin.com/in/cheikh-niang)  
🌐 [Portfolio](https://portfolio-cheikh-niang.streamlit.app)

---

## 📄 LICENCE

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 🙏 REMERCIEMENTS

- **GoMyCode Dakar** pour la formation Data Science
- Communauté open-source (LightGBM, TensorFlow, Streamlit)
