"""
Chargement des données dans Supabase
À exécuter : python scripts/load_to_supabase.py
"""

import pandas as pd
import requests
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import SUPABASE_CONFIG

print("=" * 70)
print("📤 CHARGEMENT SUPABASE")
print("=" * 70)

# Charger les données
csv_path = Path('data/synthetic/synthetic_data_v2.csv')

if not csv_path.exists():
    print(f"\n❌ Fichier non trouvé : {csv_path}")
    print("Exécutez d'abord : python scripts/generate_new_data.py")
    sys.exit(1)

print(f"\n📂 Lecture de {csv_path}...")
df = pd.read_csv(csv_path)
print(f"✅ {len(df)} lignes chargées")

# Statistiques
print("\n📊 Aperçu des données:")
print(f"  Quartiers : {df['quartier'].nunique()}")
for q in sorted(df['quartier'].unique()):
    count = len(df[df['quartier'] == q])
    print(f"    {q:25s}: {count:6d}")

# Connexion Supabase
url = SUPABASE_CONFIG['url']
key = SUPABASE_CONFIG['key']

headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

# Charger par batch de 1000 lignes
batch_size = 1000
total_batches = (len(df) + batch_size - 1) // batch_size

print(f"\n📦 Chargement par batch de {batch_size} lignes...")
print(f"  Total batches : {total_batches}")

success_count = 0
error_count = 0

for i in range(0, len(df), batch_size):
    batch_num = i // batch_size + 1
    batch = df[i:i + batch_size]
    
    # Préparer les données
    records = []
    for _, row in batch.iterrows():
        records.append({
            'date_heure': row['date'],
            'quartier': row['quartier'],
            'temp_celsius': float(row['temp_celsius']),
            'humidite_percent': int(row['humidite_percent']),
            'vitesse_vent': float(row['vitesse_vent']),
            'conso_megawatt': int(row['conso_megawatt']),
            'prediction': int(row['coupure'])
        })
    
    # Envoyer à Supabase
    try:
        response = requests.post(
            f"{url}/rest/v1/enregistrements",
            headers=headers,
            json=records
        )
        
        if response.status_code in [200, 201]:
            success_count += len(records)
            print(f"  ✅ Batch {batch_num}/{total_batches} : {len(records)} lignes")
        else:
            error_count += len(records)
            print(f"  ❌ Batch {batch_num}/{total_batches} : Erreur {response.status_code}")
            if batch_num == 1:  # Afficher détails pour première erreur
                print(f"     {response.text[:200]}")
        
        # Pause pour éviter rate limit
        time.sleep(0.5)
        
    except Exception as e:
        error_count += len(records)
        print(f"  ❌ Batch {batch_num}/{total_batches} : {e}")

print("\n" + "=" * 70)
print("📊 RÉSUMÉ")
print("=" * 70)
print(f"✅ Succès : {success_count} lignes")
print(f"❌ Erreurs : {error_count} lignes")
print(f"📈 Taux réussite : {success_count / len(df) * 100:.1f}%")

if success_count > 0:
    print("\n✅ CHARGEMENT TERMINÉ")
    print("\nVérifiez dans Supabase:")
    print("  → https://krudbbmsixrejemqqphn.supabase.co")
    print("  → Table Editor → enregistrements")
else:
    print("\n❌ ÉCHEC DU CHARGEMENT")
    sys.exit(1)