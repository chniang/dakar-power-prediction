# Changelog

Tous les changements notables de ce projet seront documentés dans ce fichier.

## [Non publié]

### Corrigé
- Formulations laissant croire à des données réelles (app, README, PERFORMANCE, CHANGELOG, docstrings) ; bandeau « Données synthétiques » ajouté dans l'app et le README
- Fausse affirmation « Pikine/Fann absents de l'entraînement » : les 8 quartiers sont dans le CSV
- « 6 quartiers entraînés » → 8 ; prérequis Python 3.9+ → 3.10+ (syntaxe `dict | None`)
- PERFORMANCE.md et conclusion du notebook 02 : chiffres inventés (AUC ~0,93, F1 ~0,55, classe ~8 %) et configuration erronée remplacés par les métriques mesurées, avec la référence « jamais de coupure » et le biais lié à l'usage du test pour l'arrêt anticipé
- Port unifié sur 7860 (Dockerfile, .streamlit/config.toml, CLAUDE.md) ; `.env.example` débarrassé des variables Supabase ; accent cassé du Dockerfile
- **Inférence réalignée sur le CSV d'entraînement** : `saison` binaire (juin-août) et `is_peak_hour` 18h-22h. La « correction » 1.1.0 ci-dessous avait aligné l'app sur `data_generator.py` sans réentraîner, ce qui faussait les prédictions (ex. 22h ≈ 0 % au lieu d'environ 43 %). Tests réécrits pour comparer l'encodage aux valeurs du CSV
- **Risque affiché = vraie probabilité** : suppression du « ×2 » et du plancher de 5 % ; coefficient de quartier appliqué avant le plafonnement ; seuils redéfinis à 15 % / 35 % sur la distribution du jeu de test (au lieu de 40 % / 70 %) ; un échec de LightGBM n'affiche plus un 50 % fictif

### Ajouté
- Avertissement « hors plage d'entraînement » (barre latérale, prédiction, carte) quand une entrée sort des plages du CSV, y compris une consommation incohérente avec l'heure de pointe (ex. 800 MW à 19h, valeur par défaut) ; les sliders ne sont pas bloqués

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
- Prédiction instantanée à partir des curseurs (modèles entraînés sur données synthétiques)
- Carte interactive des risques
- Analyse statistique par quartier (dataset synthétique)
- Tendances du dataset synthétique
- Export CSV des prédictions
- Documentation complète
- Tests et validation

### Fonctionnalités
- Prédiction pour 8 quartiers de Dakar (tous présents dans le dataset ; quartier appliqué par coefficient, pas comme feature)
- Dataset de 70 000 enregistrements synthétiques
- Interface utilisateur intuitive
- Visualisations interactives Plotly

## [0.1.0] - 2024-12-01

### Ajouté
- Structure initiale du projet
- Génération de données synthétiques
- Entraînement des modèles de base
