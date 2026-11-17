# Fiche de données — `data/synthetic/synthetic_data_v2.csv`

> ⚠️ **Données synthétiques : démonstration technique, pas des mesures du réseau SENELEC.**
> Aucune ligne de ce fichier ne provient d'une mesure réelle de coupure, de consommation ou de météo.

## 1. Provenance : le générateur d'origine est introuvable

**Le script qui a produit ce CSV n'existe pas dans le dépôt, ni dans son historique git.**

- Le fichier a été ajouté dès le premier commit (`5cda98e`, 13/01/2026), sans le script qui l'a généré.
- `scripts/2_train_models.py` renvoie vers `scripts/generate_new_data.py`, qui n'a jamais été commité.
- `src/data_generator.py` **n'a pas produit ce fichier**. Il génère un jeu de données différent sur tous les points structurants :

| | `synthetic_data_v2.csv` (entraînement) | `src/data_generator.py` |
|---|---|---|
| Lignes | 70 000 | 6 × 8 761 = 52 566 |
| Quartiers | 8 (dont Pikine et Fann), noms sans accents | 6 (sans Pikine ni Fann) |
| Colonne date | `date`, toujours à 00:00:00 ; l'heure est dans `heure` | `date_heure`, pas horaire réel |
| Période | 01/01/2023 → 30/06/2024 | 2024 |
| `saison` | binaire : 1 = juin-août, 0 = reste | 3 valeurs : 0 nov-fév, 1 mars-mai, 2 juin-oct |
| `is_peak_hour` | 1 de 18h à 22h | 1 de 7h à 9h et de 18h à 21h |
| `conso_megawatt` | décimal | entier |
| Effet de la température sur les coupures | **négatif** | positif |
| Fichier écrit | — | `data/raw/raw_data.csv` (jamais utilisé) |

Conséquence : on ne peut ni reproduire ce CSV, ni connaître avec certitude les règles qui ont servi à le générer. Ce qui suit est **observé** dans le fichier, pas documenté par son auteur.

## 2. Ce que contient le fichier

- **70 000 lignes, 12 colonnes**, aucune valeur manquante, aucun doublon.
- Colonnes : `date, quartier, temp_celsius, humidite_percent, vitesse_vent, conso_megawatt, heure, jour_semaine, mois, saison, is_peak_hour, coupure`.
- **547 dates** distinctes (01/01/2023 → 30/06/2024), environ 128 lignes par date. `jour_semaine` et `mois` sont cohérents avec `date`. L'heure est tirée indépendamment de la date : **ce n'est pas une série temporelle**.
- Comme 2024 s'arrête en juin, les mois de juillet à décembre ont environ 2 fois moins de lignes (~3 900) que janvier à juin (~7 800).
- **Cible** `coupure` : 9 836 coupures, soit **14,05 %**.

### Plages des variables

| Variable | Min | Max |
|---|---|---|
| `temp_celsius` | 16,06 | 37,78 |
| `humidite_percent` | 50 | 95 |
| `vitesse_vent` | 2,0 | 20,0 |
| `conso_megawatt` | 400,0 | 1 399,9 |

Ces plages sont reprises dans `TRAINING_RANGES` (`src/config.py`). L'app avertit quand une entrée en sort.

### Taux de coupure par quartier

| Quartier (nom dans le CSV) | Lignes | Coupures | Taux |
|---|---|---|---|
| Pikine | 8 813 | 1 486 | 16,9 % |
| Guediawaye | 8 637 | 1 396 | 16,2 % |
| Sicap-Liberte | 8 793 | 1 302 | 14,8 % |
| Parcelles Assainies | 8 716 | 1 280 | 14,7 % |
| Yoff | 8 807 | 1 187 | 13,5 % |
| Fann | 8 855 | 1 145 | 12,9 % |
| Mermoz-Sacre-Coeur | 8 632 | 1 033 | 12,0 % |
| Dakar-Plateau | 8 747 | 1 007 | 11,5 % |

Les quartiers ont des **features identiques en moyenne** (≈ 25,5 °C, ≈ 740 MW, ≈ 83 % d'humidité) : seul le taux de coupure les distingue. Le quartier n'est pas une feature du modèle ; les coefficients `QUARTIER_ADJUSTMENT` reproduisent ces écarts (voir `PERFORMANCE.md`).

## 3. Règles observées

- **Heure de pointe 18h-22h** : taux de coupure de **43,6 %**, contre **6,3 %** hors pointe. Aucun pic le matin (7-9h ≈ 6-7 %).
- **La consommation est un doublon de l'heure de pointe** : toutes les lignes en pointe ont une consommation entre 900 et 1 400 MW, toutes les lignes hors pointe entre 400 et 900 MW. Aucun recouvrement.
- **Température : effet inverse** de l'intuition (et de `data_generator.py`). Taux de coupure par quintile de température, du plus froid au plus chaud : 24,0 % → 17,1 % → 12,1 % → 8,3 % → 8,7 %.
- **Humidité : effet positif**. Par quintile, du plus sec au plus humide : 8,5 % → 7,6 % → 8,9 % → 17,8 % → 27,7 %.
- **Vent : aucun effet** (≈ 14 % dans tous les quintiles). **Jour de la semaine : aucun effet**.
- **Saison** : 14,8 % hors juin-août, 11,5 % en juin-août. Décembre (18,1 %) et février (18,3 %) sont les mois les plus touchés.
- Corrélations avec la cible : `is_peak_hour` 0,44 ; `conso_megawatt` 0,40 ; `heure` 0,26 ; `humidite_percent` 0,18 ; `temp_celsius` −0,15 ; `vent` et `jour_semaine` ≈ 0.

## 4. Limites

1. **Aucune donnée réelle.** Ni les taux, ni les effets, ni les écarts entre quartiers n'ont été calibrés sur des mesures SENELEC ou terrain. Les performances du modèle sur ce fichier ne disent rien de sa performance sur le réseau réel.
2. **Non reproductible.** Le générateur est perdu : impossible de régénérer le fichier, d'en faire varier les paramètres ou de vérifier l'intention de ses règles.
3. **Règles simplistes et en partie contre-intuitives.** La cible dépend surtout de l'heure de pointe ; l'effet de la température est inversé par rapport à l'hypothèse « chaleur → climatisation → surcharge ».
4. **Pas de dimension temporelle.** Heure tirée au hasard, date à minuit, pas de continuité d'une heure à l'autre : le LSTM ne peut rien apprendre de séquentiel (entrée à un seul pas de temps).
5. **Consommation non indépendante.** Saisir une consommation incohérente avec l'heure (ex. 800 MW à 19h) place le modèle hors de tout ce qu'il a vu.
6. **Couverture temporelle déséquilibrée.** Le second semestre est sous-représenté (une seule année contre deux pour le premier semestre).
7. **Quartier non modélisé.** Les quartiers ne diffèrent que par leur taux de coupure ; le coefficient appliqué après prédiction est une approximation multiplicative.

## 5. Pour aller plus loin

Avant tout usage opérationnel, il faut remplacer ce fichier par des données réelles (journaux d'indisponibilité, annonces de délestage, consommation mesurée, météo historique Open-Meteo), réentraîner, et réévaluer avec un découpage train / validation / test **temporel**.
