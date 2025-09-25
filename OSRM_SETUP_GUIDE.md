# Guide d'Installation et Configuration OSRM pour l'Application de Sectorisation

## Vue d'ensemble

Ce guide explique comment configurer et exécuter l'application Streamlit de sectorisation territoriale avec l'intégration OSRM (Open Source Routing Machine) pour des calculs de temps de trajet réalistes.

## Prérequis

- Docker et Docker Compose installés
- Python 3.12+ avec les dépendances du projet
- Accès à une base de données MySQL
- Au moins 4GB d'espace disque libre pour les données OSM

## Architecture du Système

L'application utilise :
- **Streamlit** : Interface utilisateur web
- **OSRM Backend** : Service de routage en conteneur Docker
- **MySQL** : Base de données pour les managers et points de vente
- **Données OSM** : Cartes routières pour les calculs de trajet

## Installation et Configuration

### 1. Configuration de la Base de Données

Créez le fichier `.streamlit/secrets.toml` avec vos credentials MySQL :

```toml
[connections.mysql]
host = "51.158.59.186"
port = 17126
database = "advent-plus"
username = "adv"
password = "4EBr_eUR_HnRZ0"
```

### 2. Installation des Dépendances Python

```bash
pip install -r requirements.txt
```

### 3. Configuration OSRM avec Docker

#### Option A : Utilisation de Docker Compose (Recommandée)

Le projet inclut un `docker-compose.yml` configuré :

```bash
# Télécharger les données OSM (Île-de-France pour les tests)
wget https://download.geofabrik.de/europe/france/ile-de-france-latest.osm.pbf
mkdir -p osrm-data
mv ile-de-france-latest.osm.pbf osrm-data/france-latest.osm.pbf

# Préprocessing des données OSRM
docker run -t -v $(pwd)/osrm-data:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/france-latest.osm.pbf
docker run -t -v $(pwd)/osrm-data:/data osrm/osrm-backend osrm-partition /data/france-latest.osrm
docker run -t -v $(pwd)/osrm-data:/data osrm/osrm-backend osrm-customize /data/france-latest.osrm

# Démarrer les services
docker-compose up -d
```

#### Option B : Configuration Manuelle

```bash
# Créer le conteneur OSRM
docker run -d --name osrm-backend-new \
  -p 5000:5000 \
  -v $(pwd)/osrm-data:/data \
  osrm/osrm-backend osrm-routed --algorithm mld /data/france-latest.osrm
```

### 4. Initialisation de la Base de Données

```bash
# Créer les tables et importer les données
python setup_database.py

# Vérifier la connexion
python test_db_connection.py
```

### 5. Démarrage de l'Application

```bash
streamlit run home.py --server.port 8501
```

L'application sera accessible sur `http://localhost:8501`

## Vérification de l'Installation

### Test de l'API OSRM

```bash
# Vérifier que le service OSRM répond
curl "http://localhost:5000/route/v1/driving/2.3522,48.8566;2.3387,48.8606?overview=false"
```

Réponse attendue : JSON avec les informations de route et temps de trajet.

### Test de l'Application

1. **Page Bilan** (`/Bilan`) :
   - Vérifiez que les temps de trajet ne sont plus fixes (25000ms)
   - Les calculs de charge utilisent des temps réalistes
   - Les cartes s'affichent correctement avec les territoires

2. **Page RH** (`/RH`) :
   - L'assignation des managers utilise OSRM
   - Les temps de trajet varient selon les routes réelles
   - La géolocalisation fonctionne (y compris Monaco)

3. **Page Front de vente** (`/Front de vente`) :
   - La réallocation des magasins utilise des temps réalistes
   - L'impact des changements est calculé avec OSRM

## Fonctionnalités OSRM Intégrées

### 1. Calculs de Temps de Trajet Dynamiques

Remplace les temps fixes par des appels API OSRM :

```python
# Avant (temps fixe)
temps_route = 25000  # 25 secondes fixes

# Après (temps dynamique)
travel_time = osrm_client.get_travel_time_minutes(manager_coords, store_coords)
```

### 2. Assignation Optimisée des Managers

Utilise les temps de trajet réels au lieu de la distance euclidienne :

```python
def find_nearest_manager(cluster_centroid, managers):
    best_manager = None
    best_score = -1
    
    for _, manager in managers.iterrows():
        travel_time = osrm_client.get_travel_time_minutes(manager_coords, store_coords)
        score = max(0, 1 - (travel_time / 180))  # Normalisation sur 3h max
        
        if score > best_score:
            best_score = score
            best_manager = manager
```

### 3. Calculs de Charge Réalistes

Les calculs de charge intègrent les temps de trajet OSRM :

```python
def calculate_sector_travel_time(sector_code):
    total_travel_time = 0
    for _, store in sector_stores.iterrows():
        travel_time = osrm_client.get_travel_time_minutes(manager_coords, store_coords)
        total_travel_time += travel_time * store.get('Frequence', 1)
    return total_travel_time * 60  # Conversion en secondes
```

## Intégration Monaco

L'application traite Monaco comme partie du département 06 (Alpes-Maritimes) :

- **Codes postaux Monaco** : 98000-98999 → Département 06
- **Géocodage spécialisé** : Support des adresses monégasques
- **Routage OSRM** : Calculs de trajet incluant Monaco

## Gestion des Erreurs et Fallback

L'application gère gracieusement les pannes OSRM :

```python
def get_travel_time_minutes(self, origin, destination):
    try:
        # Appel API OSRM
        response = requests.get(url, timeout=10)
        return travel_time_minutes
    except:
        # Fallback vers temps fixe
        return 25  # 25 minutes par défaut
```

## Performance et Optimisation

### Cache OSRM

Le système met en cache les requêtes fréquentes :

```python
@lru_cache(maxsize=1000)
def get_travel_time_minutes(self, origin_tuple, destination_tuple):
    # Calcul avec cache automatique
```

### Données OSM Optimisées

- **Île-de-France** : ~50MB, couvre Paris et région
- **France complète** : ~2.9GB, pour couverture nationale
- **Préprocessing** : Optimise les requêtes de routage

## Dépannage

### Problèmes Courants

1. **OSRM ne démarre pas** :
   ```bash
   docker logs osrm-backend
   # Vérifier les données OSM et le préprocessing
   ```

2. **Erreurs de connexion MySQL** :
   ```bash
   python test_db_connection.py
   # Vérifier les credentials dans secrets.toml
   ```

3. **Données OSM corrompues** :
   ```bash
   # Re-télécharger les données
   rm -rf osrm-data/
   wget https://download.geofabrik.de/europe/france/ile-de-france-latest.osm.pbf
   # Refaire le préprocessing
   ```

### Logs et Monitoring

```bash
# Logs OSRM
docker logs -f osrm-backend

# Logs Streamlit
streamlit run home.py --logger.level debug

# Test API OSRM
curl -v "http://localhost:5000/health"
```

## Mise en Production

### Variables d'Environnement

```bash
export OSRM_URL="http://osrm-backend:5000"
export MYSQL_HOST="your-production-host"
export MYSQL_PASSWORD="your-secure-password"
```

### Docker Compose Production

```yaml
version: '3.8'
services:
  osrm-backend:
    image: osrm/osrm-backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  streamlit-app:
    build: .
    depends_on:
      - osrm-backend
    environment:
      - OSRM_URL=http://osrm-backend:5000
```

## Support et Maintenance

### Mise à Jour des Données OSM

```bash
# Télécharger nouvelles données
wget https://download.geofabrik.de/europe/france/ile-de-france-latest.osm.pbf

# Arrêter OSRM
docker stop osrm-backend

# Refaire le préprocessing
docker run -t -v $(pwd)/osrm-data:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/france-latest.osm.pbf
docker run -t -v $(pwd)/osrm-data:/data osrm/osrm-backend osrm-partition /data/france-latest.osrm
docker run -t -v $(pwd)/osrm-data:/data osrm/osrm-backend osrm-customize /data/france-latest.osrm

# Redémarrer
docker start osrm-backend
```

### Monitoring des Performances

- **Temps de réponse OSRM** : < 100ms pour requêtes locales
- **Cache hit ratio** : > 80% pour optimisation
- **Utilisation mémoire** : ~2GB pour données Île-de-France

## Conclusion

Cette configuration fournit une solution complète de sectorisation avec routage réaliste. L'intégration OSRM améliore significativement la précision des calculs de charge et l'optimisation territoriale par rapport aux calculs de distance euclidienne.

Pour toute question ou problème, consultez les logs Docker et Streamlit, ou contactez l'équipe de développement.
