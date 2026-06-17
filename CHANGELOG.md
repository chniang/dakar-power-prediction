# Changelog

Tous les changements notables de ce projet seront documentés dans ce fichier.

## [1.1.0] - 2026-06-17

### Corrigé
- Alignement de l'encodage `saison` (0/1/2 — 3 saisons Dakar) entre `data_generator.py` et `utils_simple.py`
- Alignement de `is_peak_hour` : ajout du pic matin 7-9h manquant en inférence
- Restauration de `tensorflow-cpu` dans `requirements-hf.txt` (LSTM désactivé sur HF Spaces)
- Plancher de risque 5% appliqué uniformément (carte + prédiction)
- Correction des valeurs `QUARTIER_ADJUSTMENT` dans `PERFORMANCE.md`

### Supprimé
- Intégration Supabase retirée (`src/database.py`, `scripts/3_load_to_supabase.py`, `SUPABASE_CONFIG`)

### Refactorisé
- `compute_map_risks()` extraite du code inline de tab2
- Seuils de risque, plancher et ranges sliders centralisés dans `src/config.py`

## [1.0.0] - 2025-12-26

### Ajouté
- Application Streamlit complète
- Modèles LightGBM et LSTM
- Prédiction en temps réel
- Carte interactive des risques
- Analyse statistique par quartier
- Historique et tendances
- Export CSV des prédictions
- Documentation complète
- Tests et validation

### Fonctionnalités
- Prédiction pour 8 quartiers de Dakar (6 entraînés + Pikine/Fann par ajustement géographique)
- Dataset de 70 000 enregistrements synthétiques
- Interface utilisateur intuitive
- Visualisations interactives Plotly

## [0.1.0] - 2024-12-01

### Ajouté
- Structure initiale du projet
- Génération de données synthétiques
- Entraînement des modèles de base
