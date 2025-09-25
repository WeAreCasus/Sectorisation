#!/bin/bash

#

set -e  # Arrêter en cas d'erreur

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OSRM_DATA_DIR="${SCRIPT_DIR}/osrm-data"
SECRETS_FILE="${SCRIPT_DIR}/.streamlit/secrets.toml"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
DOCKER_COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

SKIP_OSRM=false
DEV_MODE=false
PROD_MODE=false
STREAMLIT_PORT=8501
OSRM_PORT=5000


print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "Commande '$1' non trouvée. Veuillez l'installer."
        return 1
    fi
    return 0
}

wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_info "Attente du démarrage de $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_success "$service_name est prêt !"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_error "$service_name n'a pas démarré dans les temps"
    return 1
}


show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --skip-osrm     Ignorer la configuration OSRM"
    echo "  --dev           Mode développement (données CSV)"
    echo "  --prod          Mode production (MySQL requis)"
    echo "  --help          Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0                    # Installation complète"
    echo "  $0 --dev             # Mode développement"
    echo "  $0 --skip-osrm       # Sans OSRM"
    echo "  $0 --prod            # Mode production"
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-osrm)
                SKIP_OSRM=true
                shift
                ;;
            --dev)
                DEV_MODE=true
                shift
                ;;
            --prod)
                PROD_MODE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Option inconnue: $1"
                show_help
                exit 1
                ;;
        esac
    done
}


check_prerequisites() {
    print_header "Vérification des prérequis"
    
    local required_commands=("python3" "pip" "curl" "wget")
    
    if [ "$SKIP_OSRM" = false ]; then
        required_commands+=("docker")
    fi
    
    for cmd in "${required_commands[@]}"; do
        if check_command "$cmd"; then
            print_success "$cmd est installé"
        else
            print_error "Installation de $cmd requise"
            exit 1
        fi
    done
    
    python_version=$(python3 --version | cut -d' ' -f2)
    if [[ $(echo "$python_version 3.8" | tr ' ' '\n' | sort -V | head -n1) == "3.8" ]]; then
        print_success "Python $python_version détecté"
    else
        print_error "Python 3.8+ requis (version actuelle: $python_version)"
        exit 1
    fi
    
    if [ "$SKIP_OSRM" = false ]; then
        if docker --version > /dev/null 2>&1; then
            print_success "Docker est installé"
        else
            print_error "Docker est requis pour OSRM"
            exit 1
        fi
    fi
    
    print_success "Tous les prérequis sont satisfaits"
}


install_python_dependencies() {
    print_header "Installation des dépendances Python"
    
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_error "Fichier requirements.txt non trouvé"
        exit 1
    fi
    
    print_info "Installation des packages Python..."
    pip install -r "$REQUIREMENTS_FILE" --quiet
    
    print_success "Dépendances Python installées"
}


setup_database_config() {
    print_header "Configuration de la base de données"
    
    mkdir -p "$(dirname "$SECRETS_FILE")"
    
    if [ "$DEV_MODE" = true ]; then
        print_info "Mode développement: utilisation des données CSV"
        cat > "$SECRETS_FILE" << EOF
[connections.mysql]
host = "localhost"
port = 3306
database = "test"
username = "test"
password = "test"
EOF
        print_success "Configuration développement créée"
        return 0
    fi
    
    if [ "$PROD_MODE" = true ]; then
        print_info "Mode production: configuration MySQL requise"
        
        if [ ! -f "$SECRETS_FILE" ] || ! grep -q "advent-plus" "$SECRETS_FILE" 2>/dev/null; then
            print_info "Configuration de la base de données MySQL..."
            
            read -p "Host MySQL (défaut: 51.158.59.186): " mysql_host
            mysql_host=${mysql_host:-51.158.59.186}
            
            read -p "Port MySQL (défaut: 17126): " mysql_port
            mysql_port=${mysql_port:-17126}
            
            read -p "Base de données (défaut: advent-plus): " mysql_db
            mysql_db=${mysql_db:-advent-plus}
            
            read -p "Nom d'utilisateur (défaut: adv): " mysql_user
            mysql_user=${mysql_user:-adv}
            
            read -s -p "Mot de passe: " mysql_password
            echo
            
            cat > "$SECRETS_FILE" << EOF
[connections.mysql]
host = "$mysql_host"
port = $mysql_port
database = "$mysql_db"
username = "$mysql_user"
password = "$mysql_password"
EOF
            
            print_success "Configuration MySQL créée"
        else
            print_success "Configuration MySQL existante trouvée"
        fi
        
        print_info "Initialisation de la base de données..."
        if python3 setup_database.py; then
            print_success "Base de données initialisée"
        else
            print_warning "Erreur lors de l'initialisation de la base de données"
            print_info "L'application fonctionnera en mode CSV de secours"
        fi
    else
        cat > "$SECRETS_FILE" << EOF
[connections.mysql]
host = "51.158.59.186"
port = 17126
database = "advent-plus"
username = "adv"
password = "4EBr_eUR_HnRZ0"
EOF
        
        print_info "Initialisation de la base de données..."
        if python3 setup_database.py; then
            print_success "Base de données initialisée avec configuration par défaut"
        else
            print_warning "Erreur lors de l'initialisation - mode CSV de secours activé"
        fi
    fi
}


setup_osrm() {
    if [ "$SKIP_OSRM" = true ]; then
        print_header "Configuration OSRM ignorée"
        print_info "L'application utilisera des temps de trajet fixes (25 secondes)"
        return 0
    fi
    
    print_header "Configuration du backend OSRM"
    
    mkdir -p "$OSRM_DATA_DIR"
    
    local osm_file="$OSRM_DATA_DIR/france-latest.osm.pbf"
    if [ ! -f "$osm_file" ]; then
        print_info "Téléchargement des données OSM (Île-de-France)..."
        wget -q --show-progress -O "$osm_file" \
            "https://download.geofabrik.de/europe/france/ile-de-france-latest.osm.pbf"
        print_success "Données OSM téléchargées"
    else
        print_success "Données OSM existantes trouvées"
    fi
    
    local osrm_file="$OSRM_DATA_DIR/france-latest.osrm"
    if [ ! -f "$osrm_file" ]; then
        print_info "Préprocessing des données OSRM..."
        
        print_info "Étape 1/3: Extraction..."
        docker run --rm -t -v "$OSRM_DATA_DIR:/data" osrm/osrm-backend \
            osrm-extract -p /opt/car.lua /data/france-latest.osm.pbf
        
        print_info "Étape 2/3: Partitioning..."
        docker run --rm -t -v "$OSRM_DATA_DIR:/data" osrm/osrm-backend \
            osrm-partition /data/france-latest.osrm
        
        print_info "Étape 3/3: Customization..."
        docker run --rm -t -v "$OSRM_DATA_DIR:/data" osrm/osrm-backend \
            osrm-customize /data/france-latest.osrm
        
        print_success "Préprocessing OSRM terminé"
    else
        print_success "Données OSRM préprocessées trouvées"
    fi
    
    print_info "Nettoyage des conteneurs OSRM existants..."
    docker stop osrm-backend osrm-backend-new 2>/dev/null || true
    docker rm osrm-backend osrm-backend-new 2>/dev/null || true
    
    print_info "Démarrage du backend OSRM..."
    docker run -d --name osrm-backend-new \
        -p "$OSRM_PORT:5000" \
        -v "$OSRM_DATA_DIR:/data" \
        osrm/osrm-backend osrm-routed --algorithm mld /data/france-latest.osrm
    
    if wait_for_service "http://localhost:$OSRM_PORT/health" "OSRM Backend"; then
        print_success "Backend OSRM opérationnel sur le port $OSRM_PORT"
    else
        print_error "Échec du démarrage du backend OSRM"
        return 1
    fi
    
    print_info "Test de l'API OSRM..."
    local test_url="http://localhost:$OSRM_PORT/route/v1/driving/2.3522,48.8566;2.3387,48.8606?overview=false"
    if curl -s "$test_url" | grep -q "Ok"; then
        print_success "API OSRM fonctionnelle"
    else
        print_warning "API OSRM ne répond pas correctement"
    fi
}


start_application() {
    print_header "Démarrage de l'application Streamlit"
    
    if lsof -Pi :$STREAMLIT_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $STREAMLIT_PORT déjà utilisé"
        print_info "Arrêt du processus existant..."
        pkill -f "streamlit run" || true
        sleep 2
    fi
    
    print_info "Lancement de Streamlit sur le port $STREAMLIT_PORT..."
    
    nohup streamlit run home.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0 > streamlit.log 2>&1 &
    local streamlit_pid=$!
    
    if wait_for_service "http://localhost:$STREAMLIT_PORT" "Application Streamlit"; then
        print_success "Application Streamlit démarrée (PID: $streamlit_pid)"
        echo "$streamlit_pid" > streamlit.pid
    else
        print_error "Échec du démarrage de Streamlit"
        return 1
    fi
}


run_health_checks() {
    print_header "Vérifications de santé du système"
    
    local all_checks_passed=true
    
    print_info "Test de l'application Streamlit..."
    if curl -s "http://localhost:$STREAMLIT_PORT" > /dev/null; then
        print_success "✅ Application Streamlit accessible"
    else
        print_error "❌ Application Streamlit inaccessible"
        all_checks_passed=false
    fi
    
    if [ "$SKIP_OSRM" = false ]; then
        print_info "Test du backend OSRM..."
        if curl -s "http://localhost:$OSRM_PORT/health" > /dev/null; then
            print_success "✅ Backend OSRM opérationnel"
        else
            print_error "❌ Backend OSRM inaccessible"
            all_checks_passed=false
        fi
    fi
    
    if [ "$PROD_MODE" = true ] || [ "$DEV_MODE" = false ]; then
        print_info "Test de la connexion base de données..."
        if python3 -c "
import sys
sys.path.append('.')
from db_connection import get_connection
conn = get_connection()
if conn:
    print('✅ Connexion base de données OK')
    conn.close()
else:
    print('❌ Connexion base de données échouée')
    sys.exit(1)
" 2>/dev/null; then
            print_success "✅ Base de données accessible"
        else
            print_warning "⚠️  Base de données inaccessible - mode CSV de secours"
        fi
    fi
    
    if [ "$all_checks_passed" = true ]; then
        print_success "Tous les tests de santé sont passés !"
    else
        print_warning "Certains tests ont échoué, mais l'application peut fonctionner"
    fi
}


show_final_info() {
    print_header "Déploiement terminé !"
    
    echo -e "${GREEN}🎉 L'application de sectorisation territoriale est prête !${NC}"
    echo ""
    echo -e "${BLUE}📋 Informations d'accès:${NC}"
    echo -e "   🌐 Application Streamlit: ${GREEN}http://localhost:$STREAMLIT_PORT${NC}"
    
    if [ "$SKIP_OSRM" = false ]; then
        echo -e "   🗺️  API OSRM: ${GREEN}http://localhost:$OSRM_PORT${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}📁 Fichiers importants:${NC}"
    echo -e "   📄 Logs Streamlit: ${SCRIPT_DIR}/streamlit.log"
    echo -e "   ⚙️  Configuration: ${SCRIPT_DIR}/.streamlit/secrets.toml"
    
    if [ "$SKIP_OSRM" = false ]; then
        echo -e "   🗂️  Données OSRM: ${SCRIPT_DIR}/osrm-data/"
    fi
    
    echo ""
    echo -e "${BLUE}🔧 Commandes utiles:${NC}"
    echo -e "   📊 Voir les logs: ${YELLOW}tail -f streamlit.log${NC}"
    echo -e "   🛑 Arrêter l'app: ${YELLOW}kill \$(cat streamlit.pid)${NC}"
    
    if [ "$SKIP_OSRM" = false ]; then
        echo -e "   🐳 Arrêter OSRM: ${YELLOW}docker stop osrm-backend-new${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}📖 Documentation complète: ${GREEN}OSRM_SETUP_GUIDE.md${NC}"
    
    if [ "$DEV_MODE" = true ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Mode développement activé - utilisation des données CSV de test${NC}"
    fi
    
    if [ "$SKIP_OSRM" = true ]; then
        echo ""
        echo -e "${YELLOW}⚠️  OSRM désactivé - temps de trajet fixes utilisés (25 secondes)${NC}"
    fi
}


cleanup_on_error() {
    print_error "Erreur détectée - nettoyage en cours..."
    
    if [ -f streamlit.pid ]; then
        kill "$(cat streamlit.pid)" 2>/dev/null || true
        rm -f streamlit.pid
    fi
    
    docker stop osrm-backend-new 2>/dev/null || true
    docker rm osrm-backend-new 2>/dev/null || true
    
    print_info "Nettoyage terminé"
    exit 1
}

trap cleanup_on_error ERR


main() {
    print_header "🚀 Déploiement Automatisé - Sectorisation Territoriale"
    
    parse_arguments "$@"
    
    echo -e "${BLUE}Configuration du déploiement:${NC}"
    echo -e "   Mode développement: $([ "$DEV_MODE" = true ] && echo "${GREEN}Activé${NC}" || echo "${RED}Désactivé${NC}")"
    echo -e "   Mode production: $([ "$PROD_MODE" = true ] && echo "${GREEN}Activé${NC}" || echo "${RED}Désactivé${NC}")"
    echo -e "   OSRM: $([ "$SKIP_OSRM" = true ] && echo "${RED}Désactivé${NC}" || echo "${GREEN}Activé${NC}")"
    echo ""
    
    check_prerequisites
    install_python_dependencies
    setup_database_config
    setup_osrm
    start_application
    
    sleep 3
    
    run_health_checks
    show_final_info
    
    print_success "🎯 Déploiement réussi !"
}


if [ ! -f "home.py" ]; then
    print_error "Ce script doit être exécuté depuis le répertoire racine du projet"
    print_info "Répertoire actuel: $(pwd)"
    print_info "Fichiers attendus: home.py, requirements.txt"
    exit 1
fi

main "$@"
