import pandas as pd
import os

def load_managers_from_csv():
    """Load manager data from CS Data.csv for testing purposes."""
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "CS Data.csv")
    
    try:
        df = pd.read_csv(csv_path, sep=';', encoding='latin-1')
        
        df.columns = df.columns.str.strip()
        
        column_mapping = {
            'Nom': 'Nom',
            'Prenom': 'Prenom', 
            'Code secteur': 'Code_secteur',
            'Adresse': 'Adresse',
            'Code postal': 'Code_postal',
            'Ville': 'Ville',
            'Pays': 'Pays',
            'Nb heure par jour': 'Nb_heure_par_jour',
            'Nb jour terrain par an': 'Nb_jour_terrain_par_an',
            'Latitude': 'Latitude',
            'Longitude': 'Longitude',
            'Type': 'Type'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        df = df.dropna(subset=['Code_secteur'])
        df = df[~df['Code_secteur'].str.contains('VACANT', na=False)]
        
        coordinate_cols = ['Latitude', 'Longitude']
        for col in coordinate_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
        
        numeric_cols = ['Nb_heure_par_jour', 'Nb_jour_terrain_par_an', 'Latitude', 'Longitude']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['Latitude', 'Longitude'])
        
        return df
        
    except Exception as e:
        print(f"Error loading CSV data: {e}")
        return pd.DataFrame()

def load_stores_from_csv():
    """Generate sample store data for testing purposes."""
    managers_df = load_managers_from_csv()
    
    if managers_df.empty:
        return pd.DataFrame()
    
    stores_data = []
    store_id = 1
    
    for _, manager in managers_df.iterrows():
        for i in range(2, 4):
            import random
            lat_offset = random.uniform(-0.01, 0.01)
            lon_offset = random.uniform(-0.01, 0.01)
            
            if pd.isna(manager['Latitude']) or pd.isna(manager['Longitude']):
                continue
                
            store = {
                'id': store_id,
                'Code_secteur': manager['Code_secteur'],
                'lat': manager['Latitude'] + lat_offset,
                'long': manager['Longitude'] + lon_offset,
                'Frequence': random.randint(1, 4),
                'Temps_clientele': random.randint(30, 120),
                'CA_potentiel': random.randint(10000, 50000),
                'Nom_magasin': f"Store_{store_id}",
                'Ville': manager['Ville']
            }
            stores_data.append(store)
            store_id += 1
    
    return pd.DataFrame(stores_data)

def is_csv_mode_available():
    """Check if CSV data is available for testing."""
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "CS Data.csv")
    return os.path.exists(csv_path)
