"""Gestion Base de DonnÃ©es via API REST Supabase"""
import requests
import pandas as pd
from datetime import datetime

from src.config import SUPABASE_CONFIG

BASE_URL = SUPABASE_CONFIG['url']
API_KEY = SUPABASE_CONFIG['key']

HEADERS = {
    'apikey': API_KEY,
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

def test_connection():
    """Teste la connexion Ã  l'API Supabase."""
    try:
        response = requests.get(f"{BASE_URL}/rest/v1/", headers=HEADERS, timeout=10)
        if response.status_code in [200, 404]:
            print("âœ… Connexion Supabase API rÃ©ussie")
            return True
        else:
            print(f"âŒ Erreur API : {response.status_code}")
            return False
    except Exception as e:
        print(f"âŒ Erreur de connexion : {e}")
        return False

def get_create_tables_sql():
    """Retourne le SQL pour crÃ©er les tables."""
    return """
CREATE TABLE IF NOT EXISTS enregistrements (
    id BIGSERIAL PRIMARY KEY,
    date_heure TIMESTAMPTZ NOT NULL,
    quartier VARCHAR(50) NOT NULL,
    temp_celsius FLOAT NOT NULL,
    humidite_percent INTEGER NOT NULL,
    vitesse_vent FLOAT NOT NULL,
    conso_megawatt INTEGER NOT NULL,
    heure INTEGER NOT NULL,
    jour_semaine INTEGER NOT NULL,
    mois INTEGER NOT NULL,
    saison INTEGER NOT NULL,
    is_peak_hour INTEGER NOT NULL,
    coupure INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    date_heure TIMESTAMPTZ NOT NULL,
    quartier VARCHAR(50) NOT NULL,
    temp_celsius FLOAT NOT NULL,
    humidite_percent INTEGER NOT NULL,
    vitesse_vent FLOAT NOT NULL,
    conso_megawatt INTEGER NOT NULL,
    proba_lgbm FLOAT NOT NULL,
    proba_lstm FLOAT NOT NULL,
    proba_moyenne FLOAT NOT NULL,
    prediction INTEGER NOT NULL,
    modele_utilise VARCHAR(50),
    seuil_decision FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_enregistrements_date ON enregistrements(date_heure DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_quartier ON predictions(quartier);
"""

def insert_data_bulk(df, table_name='enregistrements'):
    """InsÃ¨re un DataFrame en bulk via l'API REST."""
    print(f"\nðŸ“Š Insertion de {len(df):,} lignes dans '{table_name}'...")
    
    try:
        data = df.to_dict('records')
        
        for record in data:
            if 'date_heure' in record and isinstance(record['date_heure'], pd.Timestamp):
                record['date_heure'] = record['date_heure'].isoformat()
        
        batch_size = 100
        total_batches = (len(data) + batch_size - 1) // batch_size
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            response = requests.post(
                f"{BASE_URL}/rest/v1/{table_name}",
                headers=HEADERS,
                json=batch,
                timeout=30
            )
            
            if response.status_code not in [200, 201]:
                print(f"âŒ Erreur batch {i//batch_size + 1}")
                return False
            
            print(f"  Batch {(i//batch_size)+1}/{total_batches} : {len(batch)} lignes")
        
        print(f"âœ… {len(df):,} lignes insÃ©rÃ©es !")
        return True
        
    except Exception as e:
        print(f"âŒ Erreur : {e}")
        return False

def save_prediction_to_db(quartier, temp, humidite, vent, conso, proba_lgbm, 
                          proba_lstm, proba_moyenne, prediction, 
                          modele_utilise="LightGBM+LSTM", seuil_decision=50.0):
    """Sauvegarde une prÃ©diction."""
    try:
        data = {
            'quartier': quartier,
            'temp_celsius': float(temp),
            'humidite_percent': int(humidite),
            'vitesse_vent': float(vent),
            'conso_megawatt': int(conso),
            'proba_lgbm': float(proba_lgbm),
            'proba_lstm': float(proba_lstm),
            'proba_moyenne': float(proba_moyenne),
            'prediction': int(prediction),
            'modele_utilise': modele_utilise,
            'seuil_decision': float(seuil_decision),
            'date_heure': datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{BASE_URL}/rest/v1/predictions",
            headers=HEADERS,
            json=data,
            timeout=10
        )
        return response.status_code in [200, 201]
    except:
        return False

def get_predictions_history(limit=100):
    """RÃ©cupÃ¨re l'historique des prÃ©dictions."""
    try:
        response = requests.get(
            f"{BASE_URL}/rest/v1/predictions",
            headers=HEADERS,
            params={'order': 'date_heure.desc', 'limit': limit},
            timeout=10
        )
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def get_statistics_by_quartier(quartier_filter=None):
    """
    RÃ©cupÃ¨re les statistiques par quartier depuis les ENREGISTREMENTS SYNTHÃ‰TIQUES.
    
    Args:
        quartier_filter: Si spÃ©cifiÃ©, filtre pour un quartier particulier
    
    Returns:
        DataFrame avec les stats par quartier
    """
    try:
        # RÃ©cupÃ©rer TOUS les enregistrements (avec pagination)
        all_data = []
        offset = 0
        limit = 1000
        
        while True:
            params = {
                'select': 'quartier,coupure,temp_celsius,conso_megawatt',
                'order': 'id',
                'limit': limit,
                'offset': offset
            }
            
            # Filtrer par quartier si spÃ©cifiÃ©
            if quartier_filter:
                params['quartier'] = f'eq.{quartier_filter}'
            
            response = requests.get(
                f"{BASE_URL}/rest/v1/enregistrements",
                headers=HEADERS,
                params=params,
                timeout=15
            )
            
            if response.status_code != 200:
                break
            
            data = response.json()
            
            if not data:
                break
            
            all_data.extend(data)
            
            if len(data) < limit:
                break
            
            offset += limit
        
        if not all_data:
            return pd.DataFrame()
        
        # CrÃ©er DataFrame
        df = pd.DataFrame(all_data)
        
        # Calculer les statistiques par quartier
        stats = df.groupby('quartier').agg({
            'coupure': ['count', 'sum', 'mean'],
            'temp_celsius': 'mean',
            'conso_megawatt': 'mean'
        }).reset_index()
        
        stats.columns = ['quartier', 'total_enregistrements', 'total_coupures', 
                        'taux_coupure', 'temp_moyenne', 'conso_moyenne']
        
        # Calculer le taux en pourcentage
        stats['risque_moyen'] = stats['taux_coupure']  # DÃ©jÃ  entre 0 et 1
        
        # Trier par taux de coupure dÃ©croissant
        stats = stats.sort_values('risque_moyen', ascending=False)
        
        return stats
        
    except Exception as e:
        print(f"âŒ Erreur get_statistics_by_quartier: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def get_table_count(table_name):
    """Compte les lignes dans une table."""
    try:
        response = requests.get(
            f"{BASE_URL}/rest/v1/{table_name}",
            headers={**HEADERS, 'Prefer': 'count=exact'},
            params={'select': 'id', 'limit': 1},
            timeout=10
        )
        if response.status_code == 200:
            count = response.headers.get('Content-Range', '0').split('/')[-1]
            return int(count) if count != '*' else 0
        return 0
    except:
        return 0

def print_database_summary():
    """Affiche un rÃ©sumÃ© de la base de donnÃ©es."""
    print("\n" + "=" * 70)
    print(" ðŸ“Š RÃ‰SUMÃ‰ DE LA BASE DE DONNÃ‰ES SUPABASE")
    print("=" * 70)
    
    count_enr = get_table_count('enregistrements')
    count_pred = get_table_count('predictions')
    
    print(f"ðŸ“‹ Enregistrements : {count_enr:,} lignes")
    print(f"ðŸ”® PrÃ©dictions : {count_pred:,} lignes")
    print("=" * 70)