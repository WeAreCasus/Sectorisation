#!/bin/bash

#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAMLIT_PID_FILE="${SCRIPT_DIR}/streamlit.pid"

FORCE_STOP=false
KEEP_OSRM=false


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


show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --force         Forcer l'arrêt des processus"
    echo "  --keep-osrm     Garder OSRM en fonctionnement"
    echo "  --help          Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0                    # Arrêt normal"
    echo "  $0 --force           # Arrêt forcé"
    echo "  $0 --keep-osrm       # Arrêter seulement Streamlit"
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                FORCE_STOP=true
                shift
                ;;
            --keep-osrm)
                KEEP_OSRM=true
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


stop_streamlit() {
    print_header "Arrêt de l'application Streamlit"
    
    local stopped=false
    
    if [ -f "$STREAMLIT_PID_FILE" ]; then
        local pid=$(cat "$STREAMLIT_PID_FILE")
        print_info "Arrêt du processus Streamlit (PID: $pid)..."
        
        if kill "$pid" 2>/dev/null; then
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
            done
            
            if ! kill -0 "$pid" 2>/dev/null; then
                print_success "Streamlit arrêté proprement"
                rm -f "$STREAMLIT_PID_FILE"
                stopped=true
            fi
        fi
    fi
    
    if [ "$stopped" = false ]; then
        print_info "Recherche des processus Streamlit en cours..."
        
        local pids=$(pgrep -f "streamlit run" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            print_info "Processus Streamlit trouvés: $pids"
            
            if [ "$FORCE_STOP" = true ]; then
                print_warning "Arrêt forcé des processus Streamlit..."
                echo "$pids" | xargs kill -9 2>/dev/null || true
            else
                print_info "Arrêt normal des processus Streamlit..."
                echo "$pids" | xargs kill 2>/dev/null || true
                
                sleep 3
                local remaining_pids=$(pgrep -f "streamlit run" 2>/dev/null || true)
                if [ -n "$remaining_pids" ]; then
                    print_warning "Arrêt forcé des processus restants..."
                    echo "$remaining_pids" | xargs kill -9 2>/dev/null || true
                fi
            fi
            
            print_success "Processus Streamlit arrêtés"
            stopped=true
        fi
    fi
    
    rm -f "$STREAMLIT_PID_FILE"
    
    if [ "$stopped" = false ]; then
        print_info "Aucun processus Streamlit en cours d'exécution"
    fi
    
    if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Le port 8501 est encore utilisé"
        if [ "$FORCE_STOP" = true ]; then
            local port_pid=$(lsof -Pi :8501 -sTCP:LISTEN -t)
            print_warning "Arrêt forcé du processus utilisant le port 8501 (PID: $port_pid)"
            kill -9 "$port_pid" 2>/dev/null || true
        fi
    else
        print_success "Port 8501 libéré"
    fi
}

stop_osrm() {
    if [ "$KEEP_OSRM" = true ]; then
        print_header "Conservation du backend OSRM"
        print_info "Le conteneur OSRM reste en fonctionnement"
        return 0
    fi
    
    print_header "Arrêt du backend OSRM"
    
    local containers_stopped=false
    
    local container_names=("osrm-backend-new" "osrm-backend" "osrm_osrm-backend_1")
    
    for container_name in "${container_names[@]}"; do
        if docker ps -q -f name="$container_name" | grep -q .; then
            print_info "Arrêt du conteneur $container_name..."
            
            if [ "$FORCE_STOP" = true ]; then
                docker kill "$container_name" 2>/dev/null || true
            else
                docker stop "$container_name" 2>/dev/null || true
            fi
            
            docker rm "$container_name" 2>/dev/null || true
            print_success "Conteneur $container_name arrêté et supprimé"
            containers_stopped=true
        fi
    done
    
    if [ "$containers_stopped" = false ]; then
        print_info "Aucun conteneur OSRM en cours d'exécution"
    fi
    
    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Le port 5000 est encore utilisé"
        if [ "$FORCE_STOP" = true ]; then
            local port_pid=$(lsof -Pi :5000 -sTCP:LISTEN -t)
            print_warning "Arrêt forcé du processus utilisant le port 5000 (PID: $port_pid)"
            kill -9 "$port_pid" 2>/dev/null || true
        fi
    else
        print_success "Port 5000 libéré"
    fi
}

cleanup_temp_files() {
    print_header "Nettoyage des fichiers temporaires"
    
    if [ -f "${SCRIPT_DIR}/streamlit.log" ]; then
        print_info "Archivage des logs Streamlit..."
        mv "${SCRIPT_DIR}/streamlit.log" "${SCRIPT_DIR}/streamlit.log.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
        print_success "Logs archivés"
    fi
    
    rm -f "$STREAMLIT_PID_FILE"
    
    find "${SCRIPT_DIR}" -name "*.pyc" -delete 2>/dev/null || true
    find "${SCRIPT_DIR}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    print_success "Nettoyage terminé"
}


verify_shutdown() {
    print_header "Vérification de l'arrêt des services"
    
    local all_stopped=true
    
    if pgrep -f "streamlit run" >/dev/null 2>&1; then
        print_error "❌ Des processus Streamlit sont encore actifs"
        all_stopped=false
    else
        print_success "✅ Aucun processus Streamlit actif"
    fi
    
    if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "❌ Port 8501 encore utilisé"
        all_stopped=false
    else
        print_success "✅ Port 8501 libéré"
    fi
    
    if [ "$KEEP_OSRM" = false ]; then
        if docker ps -q -f name="osrm" | grep -q .; then
            print_error "❌ Des conteneurs OSRM sont encore actifs"
            all_stopped=false
        else
            print_success "✅ Aucun conteneur OSRM actif"
        fi
        
        if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_error "❌ Port 5000 encore utilisé"
            all_stopped=false
        else
            print_success "✅ Port 5000 libéré"
        fi
    else
        print_info "ℹ️  Vérification OSRM ignorée (conservation demandée)"
    fi
    
    if [ "$all_stopped" = true ]; then
        print_success "Tous les services sont correctement arrêtés"
    else
        print_warning "Certains services ne sont pas complètement arrêtés"
        if [ "$FORCE_STOP" = false ]; then
            print_info "Essayez avec l'option --force pour un arrêt forcé"
        fi
    fi
}


show_final_info() {
    print_header "Arrêt terminé"
    
    echo -e "${GREEN}🛑 Services de sectorisation territoriale arrêtés${NC}"
    echo ""
    
    if [ "$KEEP_OSRM" = true ]; then
        echo -e "${BLUE}📋 Services encore actifs:${NC}"
        echo -e "   🗺️  Backend OSRM: ${GREEN}http://localhost:5000${NC} (conservé)"
        echo ""
    fi
    
    echo -e "${BLUE}🔧 Pour redémarrer l'application:${NC}"
    echo -e "   🚀 Déploiement complet: ${YELLOW}./deploy.sh${NC}"
    echo -e "   🧪 Mode développement: ${YELLOW}./deploy.sh --dev${NC}"
    echo -e "   ⚡ Sans OSRM: ${YELLOW}./deploy.sh --skip-osrm${NC}"
    echo ""
    
    echo -e "${BLUE}📁 Fichiers conservés:${NC}"
    echo -e "   ⚙️  Configuration: ${SCRIPT_DIR}/.streamlit/secrets.toml"
    echo -e "   🗂️  Données OSRM: ${SCRIPT_DIR}/osrm-data/"
    
    if [ -f "${SCRIPT_DIR}/streamlit.log."* ]; then
        echo -e "   📄 Logs archivés: ${SCRIPT_DIR}/streamlit.log.*"
    fi
    
    echo ""
    echo -e "${BLUE}📖 Documentation: ${GREEN}OSRM_SETUP_GUIDE.md${NC}"
}


main() {
    print_header "🛑 Arrêt des Services - Sectorisation Territoriale"
    
    parse_arguments "$@"
    
    echo -e "${BLUE}Configuration de l'arrêt:${NC}"
    echo -e "   Arrêt forcé: $([ "$FORCE_STOP" = true ] && echo "${YELLOW}Activé${NC}" || echo "${GREEN}Normal${NC}")"
    echo -e "   Conserver OSRM: $([ "$KEEP_OSRM" = true ] && echo "${GREEN}Oui${NC}" || echo "${RED}Non${NC}")"
    echo ""
    
    stop_streamlit
    stop_osrm
    cleanup_temp_files
    
    sleep 2
    
    verify_shutdown
    show_final_info
    
    print_success "🎯 Arrêt réussi !"
}


if [ ! -f "home.py" ]; then
    print_error "Ce script doit être exécuté depuis le répertoire racine du projet"
    print_info "Répertoire actuel: $(pwd)"
    exit 1
fi

main "$@"
