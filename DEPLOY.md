# Procédure de déploiement

Ce projet a deux remotes :
- `origin` → GitHub (`https://github.com/chniang/dakar-power-prediction.git`)
- `hf` → Hugging Face Space (`https://huggingface.co/spaces/TIJAANI/dakar-power-prediction`)

## Workflow standard

```bash
# 1. Pousser sur GitHub (toujours en premier)
git push origin main

# 2. Synchroniser le HF Space
git push hf main
```

Le push sur `hf` déclenche un rebuild automatique du Space (Docker). Compter ~2-3 minutes avant que l'app soit de nouveau disponible.

## Variables d'environnement (HF Space)

Les secrets ne sont pas dans le code — les configurer dans :
**HF Space → Settings → Variables and secrets**

| Variable | Description |
|---|---|
| `SUPABASE_URL` | URL du projet Supabase |
| `SUPABASE_KEY` | Clé anon Supabase |

## Modèles et données (Git LFS)

Les fichiers `models/` et `data/` sont versionnés via Git LFS.
Vérifier avant de pusher que les fichiers LFS sont bien trackés :

```bash
git lfs status
```

## Vérification post-déploiement

1. Ouvrir le Space : https://huggingface.co/spaces/TIJAANI/dakar-power-prediction
2. Vérifier les 3 indicateurs en haut de l'app : LightGBM ✅, LSTM ✅/⚠️, CSV ✅
3. Tester une prédiction sur un quartier
