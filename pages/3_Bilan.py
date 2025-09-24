#Avec et sans kmeans 
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
import folium
import folium.plugins as plugins
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex, ListedColormap
from db_connection import get_connection
from utils.osrm_client import osrm_client
from utils.multi_criteria import multi_criteria_optimizer
from utils.territory_boundaries import territory_manager
from utils.performance import load_managers_optimized, load_stores_optimized, performance_optimizer

# Configuration initiale de la page
#st.set_page_config(page_title="Analyse Sectorielle", layout="wide")

st.markdown("<div class='title'><b>Tableau de Bord - Analyse et Bilan de la Performance</b></div>", unsafe_allow_html=True)
st.logo("LOGO.png", icon_image="Logom.png")


# def load_managers_from_db():
#     conn = get_connection()
#     if conn:
#         df = pd.read_sql("SELECT * FROM rh", conn)
#         conn.close()
#         return df
#     return pd.DataFrame()
def load_managers_from_db():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rh")
            columns = [col[0] for col in cursor.description]
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)
            cursor.close()
            conn.close()
            return df
        except Exception as e:
            print(f"Erreur lors du chargement de la table RH : {e}")
            conn.close()
    return pd.DataFrame()


# def load_stores_from_db():
#     conn = get_connection()
#     if conn:
#         df = pd.read_sql("SELECT * FROM pdv", conn)
#         conn.close()
#         return df
#     return pd.DataFrame()

def load_stores_from_db():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pdv")
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        cursor.close()
        conn.close()
        return df
    return pd.DataFrame()

managers_original = load_managers_from_db()
stores_original = load_stores_from_db()

# 👇 Ajoute ici :
if 'managers_optimized' in st.session_state:
    managers = st.session_state.managers_optimized.copy()
else:
    managers = managers_original.copy()

stores = stores_original.copy()
# 👇 Fonction d’anonymisation
def anonymiser_noms(df):
    df = df.copy()
    df['Nom'] = 'Nom_' + df.index.astype(str)
    df['Prenom'] = 'Prenom_' + df.index.astype(str)
    return df

# 👇 Appliquer l’anonymisation après avoir défini `managers`
managers = anonymiser_noms(managers)
managers_original = anonymiser_noms(managers_original)
if 'managers_optimized' in st.session_state:
    st.session_state.managers_optimized = anonymiser_noms(st.session_state.managers_optimized)
print(stores_original)
# Harmonisation des noms de colonnes (standardisation)
stores_original.columns = [col.strip().replace(" ", "_").replace("é", "e").replace("è", "e") for col in stores_original.columns]
managers_original.columns = [col.strip().replace(" ", "_").replace("é", "e").replace("è", "e") for col in managers_original.columns]

# # 🔍 DEBUG : Affichage des données brutes
# st.subheader("📦 Données brutes PDV")
# st.dataframe(stores_original)

# st.subheader("👤 Données brutes RH")
# st.dataframe(managers_original)

# # Optionnel : afficher les colonnes pour debug
# st.write("🧮 Colonnes PDV :", stores_original.columns.tolist())
# st.write("🧮 Colonnes RH :", managers_original.columns.tolist())

# Harmonisation des noms de colonnes (standardisation)
stores_original.columns = [col.strip().replace(" ", "_").replace("é", "e").replace("è", "e") for col in stores_original.columns]
managers_original.columns = [col.strip().replace(" ", "_").replace("é", "e").replace("è", "e") for col in managers_original.columns]

if managers_original.empty or stores_original.empty:
    st.warning("⚠️ Aucune donnée n'a été trouvée dans la base de données.")
    st.stop()

# Versions de travail (modifiables uniquement pour l'optimisation)
managers = managers_original.copy()
stores = stores_original.copy()

# Sauvegarde des données originales pour éviter qu'elles ne soient écrasées
if 'managers_original' not in st.session_state:
    st.session_state.managers_original = managers.copy()

if 'stores_original' not in st.session_state:
    st.session_state.stores_original = stores.copy()

def blend_cmap(cmap1, cmap2, n_colors):
    colors1 = plt.get_cmap(cmap1)(np.linspace(0, 1, n_colors // 2))
    colors2 = plt.get_cmap(cmap2)(np.linspace(0, 1, n_colors // 2))
    colors = np.vstack((colors1, colors2))
    return ListedColormap(colors)

def format_charge(value):
    if pd.notnull(value):
        try:
            value = float(value)
            formatted_value = f"{value:.2f}%"
            # Remove the trailing ".0" if the formatted value ends with ".0%"
            if formatted_value.endswith('.0%'):
                formatted_value = formatted_value.replace('.0%', '%')
            return formatted_value
        except ValueError:
            return str(value)
    return "None"


# Fonction de style pour colorer la colonne 'Charge'
def color_charge(val):
    if val is None or val == "None":
        color = 'white'
    else:
        try:
            val = str(val).rstrip('%')  # Convertir en chaîne si ce n'est pas déjà le cas
            val = float(val)  # Convertir en float pour la comparaison
            if val > 100:
                color = 'rgba(255, 0, 0, 0.3)'  # Rouge avec une opacité de 30%
            else:
                color = 'rgba(0, 255, 0, 0.3)'  # Vert avec une opacité de 30%
        except ValueError:
            color = 'white'
    return f'background-color: {color}'

# Load data from Excel files
#managers = pd.read_excel("CS Data.xlsx")
#stores = pd.read_excel("Datakiss Template 2024 REVILLARS.xlsx")

# # Print the columns to check for the 'Code_secteur'
# print("Columns in managers:", managers.columns)
# print("Columns in stores:", stores.columns)

# st.subheader("Colonnes du fichier PDV")
# st.write(stores.columns.tolist())
# st.write("Aperçu des données :")
# st.dataframe(stores.head())

# Convert latitude and longitude from string to numeric (float)
stores['lat'] = pd.to_numeric(stores['lat'], errors='coerce')
stores['long'] = pd.to_numeric(stores['long'], errors='coerce')
managers['Latitude'] = pd.to_numeric(managers['Latitude'], errors='coerce')
managers['Longitude'] = pd.to_numeric(managers['Longitude'], errors='coerce')

# Drop rows with NaN values
stores.dropna(subset=['lat', 'long'], inplace=True)
managers.dropna(subset=['Latitude', 'Longitude'], inplace=True)

# # Fonction pour formater les nombres en millions
# def format_millions(number):
#     if number >= 1e6:
#         return f"{number / 1e6:.3f} M €"
#     return f"{number}€"

def format_millions(number):
    try:
        number = float(number)  # Convertit Decimal -> float si besoin
    except:
        return "Erreur"
    return f"{number / 1e6:.3f} M €"


# Calculer le nombre de visites nécessaires par secteur
visits_per_sector = stores.groupby('Code_secteur')['Frequence'].sum().reset_index(name='Visites nécessaires')
total_visits = visits_per_sector['Visites nécessaires'].sum()

# Calculer le nombre de commerciaux par secteur
commercials_per_sector = managers.groupby('Code_secteur').size().reset_index(name='Nombre de commerciaux')
total_commercials = commercials_per_sector['Nombre de commerciaux'].sum()

# Calculer le nombre de magasins par secteur
stores_per_sector = stores.groupby('Code_secteur').size().reset_index(name='Nombre de magasins')
total_stores = stores_per_sector['Nombre de magasins'].sum()

# Calculer le CA potentiel par secteur
ca_potentiel_per_sector = stores.groupby('Code_secteur')['Potentiel'].sum().reset_index(name='CA Potentiel')
# total_ca_potentiel = ca_potentiel_per_sector['CA Potentiel'].sum()
total_ca_potentiel = float(ca_potentiel_per_sector['CA Potentiel'].sum())

# Calcul du temps passé clientèle par secteur
# DEBUG : Afficher les colonnes du DataFrame stores
# st.write("Colonnes disponibles :", stores.columns.tolist())
# temps_clientele_per_sector = stores.groupby('Code_secteur').apply(lambda x: (x['Temps'] * x['Frequence']).sum()).reset_index(name='Temps passé clientèle')
# TEST DEPLOIEMENT 
temps_clientele_per_sector = stores.copy()
temps_clientele_per_sector['Poids'] = temps_clientele_per_sector['Temps'] * temps_clientele_per_sector['Frequence']
temps_clientele_per_sector = temps_clientele_per_sector.groupby('Code_secteur')['Poids'].sum().reset_index(name='Temps passé clientèle')
###############
# st.write("Colonnes managers :", managers.columns.tolist())

# Calcul du temps terrain effectif par secteur pour chaque manager
temps_terrain_effectif_per_manager = (managers['Nb_jour_terrain_par_an'] * managers['Nb_heure_par_jour'] * 60).reset_index(name='Temps terrain effectif')

# Jointure des données calculées pour le calcul de la charge
charge_per_sector = pd.merge(temps_clientele_per_sector, managers[['Code_secteur', 'Nb_jour_terrain_par_an', 'Nb_heure_par_jour']], on='Code_secteur', how='left')
charge_per_sector['Temps terrain effectif'] = charge_per_sector['Nb_jour_terrain_par_an'] * charge_per_sector['Nb_heure_par_jour'] * 60

# Ajout du temps passé sur la route
temps_route = 25000

# Calcul de la charge pour chaque secteur
charge_per_sector['Charge'] = ((charge_per_sector['Temps passé clientèle'] + temps_route)/ charge_per_sector['Temps terrain effectif'])* 100

# Streamlit UI
# Préparation de l'interface utilisateur
# Réduction de l'espacement vertical entre les éléments
st.markdown("""
    <style>
        div[data-testid="column"] > div {
            margin-bottom: 0rem !important;
        }
    </style>
""", unsafe_allow_html=True)
# Liste des secteurs disponibles
sector_options = sorted(managers['Code_secteur'].unique().tolist())

# Initialiser les secteurs sélectionnés dans le session_state
if 'selected_sector' not in st.session_state:
    st.session_state.selected_sector = sector_options
    
# ✅ Ajoute ton titre avant les boutons
st.markdown("### Filtrer un ou plusieurs secteurs")
# ✅ Bouton pour tout sélectionner
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("✅ Tout sélectionner"):
        st.session_state.selected_sector = sector_options
with col2:
    if st.button("❌ Tout désélectionner"):
        st.session_state.selected_sector = []

# Affichage du filtre multiselect avec scroll
selected_sector = st.multiselect(
    "<div style='display:none'>hidden</div>",
    options=sector_options,
    default=st.session_state.selected_sector,
    key="selected_sector",
    help="Utilise les boutons pour tout cocher/décocher",
    label_visibility="collapsed"

)

# Calcul du nombre de visites nécessaires pour le secteur sélectionné
if selected_sector:
    visits_needed = visits_per_sector[visits_per_sector['Code_secteur'].isin(selected_sector)]['Visites nécessaires'].sum()
    commercials_needed = commercials_per_sector[commercials_per_sector['Code_secteur'].isin(selected_sector)]['Nombre de commerciaux'].sum()
    stores_needed = stores_per_sector[stores_per_sector['Code_secteur'].isin(selected_sector)]['Nombre de magasins'].sum()
    
    if ca_potentiel_per_sector['Code_secteur'].isin(selected_sector).any():
        ca_potentiel_needed = ca_potentiel_per_sector[ca_potentiel_per_sector['Code_secteur'].isin(selected_sector)]['CA Potentiel'].sum()
        ca_potentiel_display = format_millions(ca_potentiel_needed)
    else:
        ca_potentiel_display = "<span style='color:red;font-size: 14px;'>Aucun magasin affecté !</span>"

    if charge_per_sector['Code_secteur'].isin(selected_sector).any():
        temp_client = charge_per_sector[charge_per_sector['Code_secteur'].isin(selected_sector)]['Temps passé clientèle'].sum()
        temp_terrain = charge_per_sector[charge_per_sector['Code_secteur'].isin(selected_sector)]['Temps terrain effectif'].sum()
        charge_needed = (temp_client + temps_route) / temp_terrain * 100 if temp_terrain > 0 else 0
    else:
        charge_needed = "<span style='color:red;font-size: 14px;'>Aucun magasin affecté !</span>"
else:
    visits_needed = total_visits
    commercials_needed = total_commercials
    stores_needed = total_stores
    ca_potentiel_display = format_millions(total_ca_potentiel)
    temps_total_effectif = charge_per_sector['Nb_jour_terrain_par_an'].sum()

    if temps_total_effectif > 0:
        charge_needed = (charge_per_sector['Temps passé clientèle'].sum() + temps_route) / temps_total_effectif * 100
    else:
        st.warning("Aucun jour terrain effectif trouvé. Impossible de calculer la charge nécessaire.")
        charge_needed = 0




# Formater la charge en pourcentage
if isinstance(charge_needed, (int, float)):
    charge_display = f"{charge_needed:.2f}%"
else:
    charge_display = charge_needed


# Colonnes pour métriques et carte
left_column, right_column = st.columns(2)

# Injecter le CSS pour les cards
st.markdown("""
    <style>
    .card-container {
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
    }
    .title {
        font-family: 'Arial', sans-serif;
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 20px;
        color: #333;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        flex: 1;
    }
    .metric {
        font-size: 2rem;
        font-weight: bold;
    }
    .delta {
        font-size: 1.2rem;
        margin-top: 5px;
    }
    .capacite-label {
        font-size: 1.2rem;
        margin-top: 5px;
        color: black; /* Texte en noir */
        font-weight: normal;
    }
    .capacite-value {
        font-size: 1.2rem;
        color: green; /* % en vert */
        font-weight: normal;
    }
    .label {
        font-size: 1rem;
        color: #555;
    }
    .positive {
        color: green;
    }
    .negative {
        color: red;
    }
    </style>
""", unsafe_allow_html=True)

# Calcul de la capacité utilisée
capacity_label = "Capacité utilisée :"
capacity_value = f"{charge_needed:.0f}%"  # % en vert

with left_column:
    st.subheader("Indicateurs Clés (Avant Optimisation)")

    if selected_sector != 'Tous':
        filtered_stores = stores_original[stores_original['Code_secteur'].isin(selected_sector)]
        filtered_managers = managers_original[managers_original['Code_secteur'].isin(selected_sector)]
    else:
        filtered_stores = stores_original
        filtered_managers = managers_original

    visits_needed = filtered_stores['Frequence'].sum()
    stores_needed = filtered_stores.shape[0]
    ca_potentiel_needed = filtered_stores['Potentiel'].sum()
    commercials_needed = filtered_managers.shape[0]

    temp_client = (filtered_stores['Temps'] * filtered_stores['Frequence']).sum()
    temp_terrain = (filtered_managers['Nb_jour_terrain_par_an'] * filtered_managers['Nb_heure_par_jour'] * 60).sum()
    charge_needed = ((temp_client + 25000) / temp_terrain) * 100 if temp_terrain > 0 else 0

    capacity_label = "Capacité utilisée :"
    capacity_value = f"{charge_needed:.0f}%"
    charge_display = f"{charge_needed:.2f}%"
    ca_potentiel_display = format_millions(ca_potentiel_needed)

    row1, row2, row3 = st.columns(3)
    with row1:
        st.markdown(f"""
            <div class="card">
                <div class="metric">{charge_display}</div>
                <div class="label">Charge</div>
                <div class="delta">
                    <span class="capacite-label">{capacity_label}</span>
                    <span class="capacite-value">{capacity_value}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.markdown(f"""
            <div class="card">
                <div class="metric">0 € / 0 € </div>
                <div class="label">Coût moyen par ressource</div>
                <div class="delta negative">0%</div>
            </div>
        """, unsafe_allow_html=True)
    with row2:
        st.markdown(f"""
            <div class="card">
                <div class="metric">{int(visits_needed)} </div>
                <div class="label">Total des visites</div>
                <div class="delta positive">100%</div>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.markdown(f"""
            <div class="card">
                <div class="metric">{commercials_needed} </div>
                <div class="label">Commerciaux</div>
                <div class="delta positive">100%</div>
            </div>
        """, unsafe_allow_html=True)
    with row3:
        st.markdown(f"""
            <div class="card">
                <div class="metric">{stores_needed} </div>
                <div class="label">PDV DN</div>
                <div class="delta positive">100%</div>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.markdown(f"""
            <div class="card">
                <div class="metric">{ca_potentiel_display} </div>
                <div class="label">CA Potentiel DV</div>
                <div class="delta positive">100%</div>
            </div>
        """, unsafe_allow_html=True)

        
    # Calculez les visites par secteur en utilisant une agrégation sur 'stores'
    # Jointure et calcul des visites par secteur
    visits_per_sector = stores.groupby('Code_secteur').size().reset_index(name='PDV affectés')
    managers = pd.merge(managers, visits_per_sector, on='Code_secteur', how='left')
    managers['PDV affectés'].fillna(0, inplace=True)  # Remplacez les NaN par 0 si aucun PDV n'est visité

        # Calculate necessary visits per sector and merge with managers
    visits_per_sector = stores.groupby('Code_secteur')['Frequence'].sum().reset_index(name='Visites nécessaires')
    managers = pd.merge(managers, visits_per_sector, on='Code_secteur', how='left')
    managers['Visites nécessaires'].fillna(0, inplace=True)

    # Jointure avec charge_per_sector pour ajouter la charge par secteur
    managers = pd.merge(managers, charge_per_sector[['Code_secteur', 'Charge']], on='Code_secteur', how='left')
    
    # Section des données détaillées
    # Liste des colonnes à afficher
    columns_to_display = ['Code_secteur', 'Nom', 'Prenom', 'Adresse', 'PDV affectés', 'Visites nécessaires', 'Charge']
    
    # Formater les colonnes 'PDV affectés' et 'Visites nécessaires' pour afficher sans chiffres après la virgule
    # Convertir les colonnes 'PDV affectés' et 'Visites nécessaires' en entiers
    managers['PDV affectés'] = managers['PDV affectés'].astype(int)
    managers['Visites nécessaires'] = managers['Visites nécessaires'].astype(int)

    if 'Charge' in managers.columns:
        managers['Charge'] = managers['Charge'].apply(lambda x: format_charge(x))
    if selected_sector != 'Tous':
        
        filtered_managers = managers[managers['Code_secteur'].isin(selected_sector)]
        filtered_stores = stores[stores['Code_secteur'].isin(selected_sector)]
    else:
        filtered_managers = managers
        filtered_stores = stores

    # Sélectionner les colonnes à afficher
    filtered_managers_to_display = filtered_managers[columns_to_display]

    # Appliquer le style à la colonne 'Charge' après avoir sélectionné les colonnes
    styled_filtered_managers = filtered_managers_to_display.style.applymap(color_charge, subset=['Charge'])

    num_clusters = len(managers)
    if len(stores) < num_clusters:
        st.write(f"Not enough stores to match the number of managers. Only {len(stores)} stores available for {num_clusters} managers.")
        num_clusters = len(stores)

    if num_clusters > 0:
        # Assume 'Code_secteur' is a shared column between the managers and stores that identifies the sector
        # Create a dictionary to map manager's location based on 'Code_secteur'
        manager_locations = {row['Code_secteur']: (row['Latitude'], row['Longitude']) for _, row in managers.iterrows()}

        # Use a unique color for each sector for visualization
        unique_sectors = pd.concat([stores['Code_secteur'], managers['Code_secteur']]).unique()
        custom_cmap = blend_cmap('tab20', 'Set3', len(unique_sectors))
        color_palette = custom_cmap(np.linspace(0, 1, len(unique_sectors)))
        sector_to_color = {sector: to_hex(color) for sector, color in zip(unique_sectors, color_palette)}

        # Default color for sectors without managers
        default_color = "#808080"  # Gray

        # Map visualization with Monaco support
        map = folium.Map(location=[46.2276, 2.2137], zoom_start=7, tiles=None)
        plugins.Fullscreen(position='topright', force_separate_button=True).add_to(map)
        folium.TileLayer(
            'CartoDB positron',
            name='Fond de carte CartoDB',
            attr='© OpenStreetMap contributors & © CartoDB'
        ).add_to(map)

        folium.TileLayer(
            'OpenStreetMap',
            name='Fond de carte OpenStreetMap',
            attr='© OpenStreetMap contributors'
        ).add_to(map)

        if not filtered_managers.empty:
            territories = territory_manager.create_voronoi_territories(filtered_managers)
            resolved_territories = territory_manager.resolve_overlaps(territories, filtered_stores)
            map = territory_manager.add_territories_to_map(map, resolved_territories, sector_to_color)
        
        # Ajouter le contrôle de couche
        folium.LayerControl().add_to(map)            
        
        for _, store in filtered_stores.iterrows():
            sector = store['Code_secteur']
            sector_color = sector_to_color.get(sector, default_color)
            folium.CircleMarker(
                location=[store['lat'], store['long']],
                radius=5,
                color=sector_color,
                fill=True,
                fill_color=sector_color,
                popup=f"Store ID: {store['Code_mag']} - Sector: {sector}"
            ).add_to(map)

            # Draw line to manager if manager exists for this sector
            manager_loc = manager_locations.get(sector)
            if manager_loc:
                folium.PolyLine(
                    locations=[[manager_loc[0], manager_loc[1]], [store['lat'], store['long']]],
                    color=sector_color,
                    opacity=0.5,
                    weight=2
                ).add_to(map)

        for _, manager in filtered_managers.iterrows():
            manager_color = sector_to_color.get(manager['Code_secteur'], default_color)
            folium.Marker(
                [manager['Latitude'], manager['Longitude']],
                icon=folium.Icon(icon="info-sign", color="red"),
                popup=f"Manager ID: {manager['Code_secteur']}",
                tooltip=folium.Tooltip(text=f"Sector {manager['Code_secteur']}", permanent=True)
            ).add_to(map)

        
    st.write("")
    st.write("")
    st.subheader("Carte Sans Optimisation 🗺️")
    # Display the map in Streamlit
    # # # Toujours initialiser la carte, même si elle est vide
    # map = folium.Map(location=[46.603354, 1.888334], zoom_start=6)

    # Ton code d'ajout de markers ou de calques vient ici
    # (ajoute les markers uniquement si selected_sector ou les données sont valides)

    # Puis tu ajoutes la carte à la figure quoi qu'il arrive
    st_data = folium.Figure(width=700, height=500).add_child(map)
    st.components.v1.html(st_data.render(), width=650, height=700)

with right_column:


    def calculate_new_charge(stores, managers):
        stores = stores.copy()

        # Forcer la conversion en float si jamais l'import a mis du texte
        stores['Temps'] = pd.to_numeric(stores['Temps'], errors='coerce')
        stores['Frequence'] = pd.to_numeric(stores['Frequence'], errors='coerce')

        # Calcul du poids
        stores['Poids'] = stores['Temps'] * stores['Frequence']

        # Agrégation par secteur
        temps_clientele_per_sector_new = stores.groupby('Code_secteur')['Poids'].sum().reset_index(name='New_Temps passé clientèle')
        # temps_clientele_per_sector_new = stores.groupby('Code_secteur').apply(lambda x: (x['Temps'] * x['Frequence']).sum()).reset_index(name='New_Temps passé clientèle')

        charge_per_sector_new = pd.merge(temps_clientele_per_sector_new, managers[['Code_secteur', 'Nb_jour_terrain_par_an', 'Nb_heure_par_jour']], on='Code_secteur', how='left')
        charge_per_sector_new['Temps terrain effectif'] = charge_per_sector_new['Nb_jour_terrain_par_an'] * charge_per_sector_new['Nb_heure_par_jour'] * 60

        # Calculate dynamic travel times using OSRM
        def calculate_sector_travel_time(sector_code):
            sector_stores = stores[stores['Code_secteur'] == sector_code]
            sector_manager = managers[managers['Code_secteur'] == sector_code]
            
            if sector_stores.empty or sector_manager.empty:
                return 25000  # fallback to old fixed value
            
            manager_coords = (sector_manager.iloc[0]['Longitude'], sector_manager.iloc[0]['Latitude'])
            total_travel_time = 0
            
            for _, store in sector_stores.iterrows():
                store_coords = (store['long'], store['lat'])
                travel_time = osrm_client.get_travel_time_minutes(manager_coords, store_coords)
                total_travel_time += travel_time * store.get('Frequence', 1)
            
            return total_travel_time * 60  # convert to seconds
        
        charge_per_sector_new['temps_route'] = charge_per_sector_new['Code_secteur'].apply(calculate_sector_travel_time)

        charge_per_sector_new['New_Charge'] = ((charge_per_sector_new['New_Temps passé clientèle'] + charge_per_sector_new['temps_route']) / charge_per_sector_new['Temps terrain effectif']) * 100
        return charge_per_sector_new[['Code_secteur', 'New_Charge']]    
    # Nouveau calcul des visites après optimisation
    optimized_visits_per_sector = stores.groupby('Code_secteur')['Frequence'].sum().reset_index(name='New_Visites nécessaires')
    st.session_state.managers_optimized = pd.merge(managers, optimized_visits_per_sector, on='Code_secteur', how='left', suffixes=('', '_new'))
    st.session_state.managers_optimized['New_Visites nécessaires'].fillna(0, inplace=True)

    optimized_ca_potentiel_per_sector = stores.groupby('Code_secteur')['Potentiel'].sum().reset_index(name='New_CA Potentiel')
    st.session_state.managers_optimized = pd.merge(st.session_state.managers_optimized, optimized_ca_potentiel_per_sector, on='Code_secteur', how='left', suffixes=('', '_new'))
    st.session_state.managers_optimized['New_CA Potentiel'].fillna(0, inplace=True)

    optimized_stores_per_sector = stores.groupby('Code_secteur').size().reset_index(name='New_PDV affectés')
    st.session_state.managers_optimized = pd.merge(st.session_state.managers_optimized, optimized_stores_per_sector, on='Code_secteur', how='left', suffixes=('', '_new'))
    st.session_state.managers_optimized['New_PDV affectés'].fillna(0, inplace=True)
    # Calculer la nouvelle charge après optimisation
    new_charge_per_sector = calculate_new_charge(stores, managers)

    # Ajouter 'New_Charge' au DataFrame optimisé
    st.session_state.managers_optimized = pd.merge(st.session_state.managers_optimized, new_charge_per_sector, on='Code_secteur', how='left', suffixes=('', '_new'))
    st.session_state.managers_optimized['New_Charge'].fillna(0, inplace=True)

    # Appliquer le formatage de la nouvelle colonne 'New_Charge'
    st.session_state.managers_optimized['New_Charge'] = st.session_state.managers_optimized['New_Charge'].apply(lambda x: format_charge(x))

    if selected_sector != 'Tous':
        filtered_optimized_managers = st.session_state.managers_optimized[st.session_state.managers_optimized['Code_secteur'].isin(selected_sector)]
        new_visits_needed = filtered_optimized_managers['New_Visites nécessaires'].sum()
        new_ca_potentiel_display = format_millions(filtered_optimized_managers['New_CA Potentiel'].sum())
        new_stores_needed = filtered_optimized_managers['New_PDV affectés'].sum()
        new_charge_needed = filtered_optimized_managers['New_Charge'].apply(lambda x: float(x.rstrip('%')) if pd.notnull(x) else 0).mean()
    else:
        new_visits_needed = st.session_state.managers_optimized['New_Visites nécessaires'].sum()
        new_ca_potentiel_display = format_millions(st.session_state.managers_optimized['New_CA Potentiel'].sum())
        new_stores_needed = st.session_state.managers_optimized['New_PDV affectés'].sum()
        new_charge_needed = st.session_state.managers_optimized['New_Charge'].apply(lambda x: float(x.rstrip('%')) if pd.notnull(x) else 0).mean()

    # Formater la nouvelle charge en pourcentage
    if isinstance(new_charge_needed, (int, float)):
        new_charge_display = f"{new_charge_needed:.2f}%"
    else:
        new_charge_display = new_charge_needed
            
    # Calcul de la capacité utilisée
    capacity_label = "Capacité utilisée :"
    capacity_value = f"{new_charge_needed:.0f}%"  # % en vert

    st.subheader("Indicateurs Clés (Mis à Jour)")

    optimized = st.session_state.managers_optimized

    if selected_sector != 'Tous':
        filtered_optimized = optimized[optimized['Code_secteur'].isin(selected_sector)]
    else:
        filtered_optimized = optimized

    new_visits_needed = int(filtered_optimized['New_Visites nécessaires'].sum())
    new_ca_potentiel = filtered_optimized['New_CA Potentiel'].sum()
    new_stores_needed = int(filtered_optimized['New_PDV affectés'].sum())
    commercials_needed = int(filtered_optimized.shape[0])
    new_charge_needed = filtered_optimized['New_Charge'].apply(lambda x: float(str(x).replace('%', '')) if pd.notnull(x) else 0).mean()

    new_charge_display = f"{new_charge_needed:.2f}%"
    new_capacity_value = f"{new_charge_needed:.0f}%"
    new_ca_display = format_millions(new_ca_potentiel)

    row1, row2, row3 = st.columns(3)
    with row1:
        st.markdown(f"""
            <div class="card">
                <div class="metric">{new_charge_display}</div>
                <div class="label">Charge</div>
                <div class="delta">
                    <span class="capacite-label">Capacité utilisée :</span>
                    <span class="capacite-value">{new_capacity_value}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.markdown(f"""
            <div class="card">
                <div class="metric">0 € / 0 € </div>
                <div class="label">Coût moyen par ressource</div>
                <div class="delta negative">0%</div>
            </div>
        """, unsafe_allow_html=True)
    with row2:
        st.markdown(f"""
            <div class="card">
                <div class="metric">{new_visits_needed} </div>
                <div class="label">Total des visites</div>
                <div class="delta positive">100%</div>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.markdown(f"""
            <div class="card">
                <div class="metric">{commercials_needed} </div>
                <div class="label">Commerciaux</div>
                <div class="delta positive">100%</div>
            </div>
        """, unsafe_allow_html=True)
    with row3:
        st.markdown(f"""
            <div class="card">
                <div class="metric">{new_stores_needed} </div>
                <div class="label">PDV DN</div>
                <div class="delta positive">100%</div>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.markdown(f"""
            <div class="card">
                <div class="metric">{new_ca_display} </div>
                <div class="label">CA Potentiel DV</div>
                <div class="delta positive">100%</div>
            </div>
        """, unsafe_allow_html=True)

    if 'show_warning' in st.session_state and st.session_state.show_warning:
        st.warning("Veuillez d'abord calculer les données avant de réaffecter.")

    else:
                # Target number of stores per manager (assuming roughly equal distribution is desired)
        num_clusters = max(1, num_clusters)  # assure-toi qu'on divise jamais par zéro
        target_per_manager = stores.shape[0] // num_clusters

        if managers.empty:
            st.error("Aucun manager n'est disponible. Impossible d'attribuer les secteurs.")

        def find_nearest_manager(cluster_centroid, managers):
            best_manager = None
            best_score = -1
            
            for _, manager in managers.iterrows():
                # Calculate OSRM-based travel time
                manager_coords = (manager['Longitude'], manager['Latitude'])
                store_coords = (cluster_centroid[1], cluster_centroid[0])  # lon, lat for OSRM
                
                travel_time = osrm_client.get_travel_time_minutes(manager_coords, store_coords)
                
                score = max(0, 1 - (travel_time / 180))  # normalize by 3 hours max
                
                if score > best_score:
                    best_score = score
                    best_manager = manager
            
            if best_manager is not None:
                return pd.Series([best_manager['Code_secteur'], best_manager['Latitude'], best_manager['Longitude']],
                                index=['Code_secteur', 'Manager Latitude', 'Manager Longitude'])
            else:
                distances = cdist([cluster_centroid], managers[['Latitude', 'Longitude']])
                nearest_manager_idx = distances.argmin()
                manager = managers.iloc[nearest_manager_idx]
                return pd.Series([manager['Code_secteur'], manager['Latitude'], manager['Longitude']],
                                index=['Code_secteur', 'Manager Latitude', 'Manager Longitude'])

        # Vérification avant le .apply()
        if stores.empty:
            st.error("Le fichier des points de vente est vide.")
        elif 'lat' not in stores.columns or 'long' not in stores.columns:
            st.error("Les colonnes 'lat' et 'long' sont manquantes dans les données.")
        elif stores[['lat', 'long']].isnull().any().any():
            st.error("Certaines coordonnées géographiques (lat/long) sont manquantes dans vos points de vente.")
        elif managers.empty:
            st.error("Le fichier des managers est vide.")
        else:
            stores[['Code_secteur', 'Manager Latitude', 'Manager Longitude']] = stores.apply(
                lambda x: find_nearest_manager((x['lat'], x['long']), managers), axis=1, result_type='expand'
            )


        unique_sectors = stores['Code_secteur'].unique()
        custom_cmap = blend_cmap('Paired', 'tab20b', len(unique_sectors))
        color_palette = custom_cmap(np.linspace(0, 1, len(unique_sectors)))
        sector_to_color = {sector: to_hex(color) for sector, color in zip(unique_sectors, color_palette)}

        map = folium.Map(location=[46.2276, 2.2137], zoom_start=7, tiles=None)
        plugins.Fullscreen(position='topright', force_separate_button=True).add_to(map)
        folium.TileLayer(
            'CartoDB positron',
            name='Fond de carte CartoDB',
            attr='© OpenStreetMap contributors & © CartoDB'
        ).add_to(map)
        folium.TileLayer(
            'OpenStreetMap',
            name='Fond de carte OpenStreetMap',
            attr='© OpenStreetMap contributors'
        ).add_to(map)

        # Ajouter le contrôle de couche
        folium.LayerControl().add_to(map)

        # Filtrage des magasins par secteur sélectionné
        if selected_sector != 'Tous':
            filtered_stores = stores[stores['Code_secteur'].isin(selected_sector)]
        else:
            filtered_stores = stores      

        for _, row in filtered_stores.iterrows():
            sector_color = sector_to_color[row['Code_secteur']]
            folium.CircleMarker(
                location=[row['lat'], row['long']],
                radius=5,
                color=sector_color,
                fill=True,
                fill_color=sector_color,
                popup=f"Store ID: {row['Code_mag']} - Sector: {row['Code_secteur']}"
            ).add_to(map)
            folium.PolyLine(
                locations=[[row['Manager Latitude'], row['Manager Longitude']], [row['lat'], row['long']]],
                color=sector_color,
                opacity=0.3,
                weight=2
            ).add_to(map)
        
        # Filtrage des managers par secteur sélectionné
        if selected_sector != 'Tous':
            filtered_managers = managers[managers['Code_secteur'].isin(selected_sector)]
        else:
            filtered_managers = managers
        
        for _, manager in filtered_managers.iterrows():
            manager_color = sector_to_color.get(manager['Code_secteur'], "#808080")  # Use gray color if sector not found
            folium.Marker(
                [manager['Latitude'], manager['Longitude']],
                icon=folium.Icon(icon="info-sign", color="red"),
                popup=f"Manager ID: {manager['Code_secteur']}",
                tooltip=folium.Tooltip(text=f"Sector {manager['Code_secteur']}", permanent=True)
            ).add_to(map)
            # Display the map in Streamlit
        
        st.write("") 
        st.write("")
        st.subheader("Carte Avec Optimisation 🗺️")
        st_data = folium.Figure(width=700, height=500).add_child(map)
        st.components.v1.html(st_data.render(), width=650, height=700)

st.subheader("Données détaillées générales")

# ✅ 1. Colonnes à afficher
columns_to_display = ['Code_secteur', 'PDV affectés', 'Visites nécessaires', 'Charge']
optimized_columns_to_display = ['Code_secteur', 'Nom', 'Prenom', 'Adresse', 'PDV affectés', 'Visites nécessaires', 'Charge']

managers_clean = st.session_state.managers_original.copy()

# Ajouter les colonnes nécessaires
stores_per_sector = stores.groupby('Code_secteur').size().reset_index(name='PDV affectés')
managers_clean = pd.merge(managers_clean, stores_per_sector, on='Code_secteur', how='left')

visites_par_secteur = stores.groupby('Code_secteur')['Frequence'].sum().reset_index(name='Visites nécessaires')
managers_clean = pd.merge(managers_clean, visites_par_secteur, on='Code_secteur', how='left')

managers_clean['PDV affectés'].fillna(0, inplace=True)
managers_clean['Visites nécessaires'].fillna(0, inplace=True)
managers_clean['PDV affectés'] = managers_clean['PDV affectés'].astype(int)
managers_clean['Visites nécessaires'] = managers_clean['Visites nécessaires'].astype(int)

# Calcul de la charge
# temps_clientele_per_sector = stores.groupby('Code_secteur').apply(lambda x: (x['Temps'] * x['Frequence']).sum()).reset_index(name='Temps passé clientèle')
if 'Temps' in stores.columns and 'Frequence' in stores.columns:
    stores['Poids'] = pd.to_numeric(stores['Temps'], errors='coerce') * pd.to_numeric(stores['Frequence'], errors='coerce')
    temps_clientele_per_sector = stores.groupby('Code_secteur')['Poids'].sum().reset_index(name='Temps passé clientèle')
else:
    temps_clientele_per_sector = pd.DataFrame(columns=['Code_secteur', 'Temps passé clientèle'])

# charge_calc = pd.merge(temps_clientele_per_sector, managers_clean[['Code_secteur', 'Nb_jour_terrain_par_an', 'Nb_heure_par_jour']], on='Code_secteur', how='left')
cols_needed = ['Code_secteur', 'Nb_jour_terrain_par_an', 'Nb_heure_par_jour']
missing_cols = [col for col in cols_needed if col not in managers_clean.columns]

if missing_cols:
    st.error(f"Colonnes manquantes dans managers_clean : {missing_cols}")
    charge_calc = pd.DataFrame()  # ou None selon ton app
else:
    charge_calc = pd.merge(
        temps_clientele_per_sector,
        managers_clean[cols_needed],
        on='Code_secteur',
        how='left'
    )

charge_calc['Temps terrain effectif'] = charge_calc['Nb_jour_terrain_par_an'] * charge_calc['Nb_heure_par_jour'] * 60

# Calculate dynamic travel times for each sector
def calculate_sector_travel_time_optimized(sector_code):
    cache_key = f"travel_time_{sector_code}"
    cached_result = performance_optimizer.get_cached_data(cache_key)
    if cached_result is not None:
        return cached_result
    
    sector_stores = stores[stores['Code_secteur'] == sector_code]
    sector_manager = managers_clean[managers_clean['Code_secteur'] == sector_code]
    
    if sector_stores.empty or sector_manager.empty:
        result = 25000  # fallback
    else:
        manager_coords = (sector_manager.iloc[0]['Longitude'], sector_manager.iloc[0]['Latitude'])
        total_travel_time = 0
        
        for _, store in sector_stores.iterrows():
            store_coords = (store['long'], store['lat'])
            travel_time = osrm_client.get_travel_time_minutes(manager_coords, store_coords)
            total_travel_time += travel_time * store.get('Frequence', 1)
        
        result = total_travel_time * 60  # convert to seconds
    
    performance_optimizer.set_cached_data(cache_key, result)
    return result

charge_calc['temps_route_dynamique'] = charge_calc['Code_secteur'].apply(calculate_sector_travel_time_optimized)
charge_calc['Charge'] = ((charge_calc['Temps passé clientèle'] + charge_calc['temps_route_dynamique']) / charge_calc['Temps terrain effectif']) * 100
managers_clean = pd.merge(managers_clean, charge_calc[['Code_secteur', 'Charge']], on='Code_secteur', how='left')
managers_clean['Charge'] = managers_clean['Charge'].apply(format_charge)


managers_display = managers_clean[columns_to_display]

# ✅ 3. Préparer les données optimisées
optimized_display = st.session_state.managers_optimized.copy()


optimized_display = optimized_display[optimized_columns_to_display]
#optimized_display['Charge'] = optimized_display['Charge'].apply(format_charge)
optimized_display['Charge'] = optimized_display['Charge'].apply(format_charge)
# Supprimer les décimales
optimized_display['PDV affectés'] = optimized_display['PDV affectés'].astype(int)
optimized_display['Visites nécessaires'] = optimized_display['Visites nécessaires'].astype(int)

# Formater la charge
optimized_display['Charge'] = optimized_display['Charge'].apply(format_charge)
# ✅ 4. Affichage côte à côte
col_before, col_after = st.columns(2)

# ✅ Appliquer le filtre sélectionné
filtered_managers_display = managers_display[managers_display['Code_secteur'].isin(st.session_state.selected_sector)]
filtered_optimized_display = optimized_display[optimized_display['Code_secteur'].isin(st.session_state.selected_sector)]

with col_before:
    st.markdown("### Avant Optimisation")
    styled_after = filtered_optimized_display.style.applymap(color_charge, subset=['Charge'])
    st.dataframe(styled_after, use_container_width=True)

with col_after:
    st.markdown("### Après Optimisation")
    styled_before = filtered_managers_display.style.applymap(color_charge, subset=['Charge'])
    st.dataframe(styled_before, use_container_width=True)

st.caption("ℹ️ Les noms des commerciaux ont été anonymisés pour garantir la confidentialité.")

# # Fonction pour afficher toutes les variables de session state
# def display_session_states():
#     st.write("### Tous les états de session:")
#     for key, value in st.session_state.items():
#         st.write(f"{key}: {value}")

# # Afficher les états de session
# display_session_states()
