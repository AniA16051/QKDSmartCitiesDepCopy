#!/bin/bash
# Docker deployment management script for QKD Smart City Network

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Commands
start_services() {
    print_header "Starting QKD Smart City Network"
    
    print_info "Starting Mosquitto broker..."
    docker-compose up -d mosquitto
    sleep 2
    
    print_info "Starting admin control center..."
    docker-compose up -d admin-node
    
    print_success "All services started"
    docker-compose ps
}

stop_services() {
    print_header "Stopping QKD Smart City Network"
    
    docker-compose down
    
    print_success "All services stopped"
}

start_user_node() {
    if [ -z "$1" ]; then
        print_error "Usage: ./manage.sh start-node <node-name> <sensor-type> [options]"
        echo "  Sensor types: traffic_flow, water_flow, surveillance"
        echo "  Options: --eavesdrop --noise 0.05"
        exit 1
    fi
    
    NODE_NAME=$1
    SENSOR_TYPE=$2
    shift 2
    EXTRA_ARGS="$@"
    
    print_info "Starting user node: $NODE_NAME (type: $SENSOR_TYPE)"
    
    docker-compose run -d --name "$NODE_NAME" \
        -e BROKER_HOST=mosquitto \
        -e BROKER_PORT=1883 \
        -v ./docker/shared_keystore:/app/network/shared_keystore_data \
        --network qkd_network \
        --rm \
        -f docker/Dockerfile.user \
        python -m network.sensor_node --id "$NODE_NAME" --type "$SENSOR_TYPE" $EXTRA_ARGS
    
    print_success "User node '$NODE_NAME' started"
}

stop_user_node() {
    if [ -z "$1" ]; then
        print_error "Usage: ./manage.sh stop-node <node-name>"
        exit 1
    fi
    
    NODE_NAME=$1
    
    print_info "Stopping user node: $NODE_NAME"
    docker stop "$NODE_NAME" 2>/dev/null || print_error "Node '$NODE_NAME' not found or already stopped"
    
    print_success "User node '$NODE_NAME' stopped"
}

list_nodes() {
    print_header "Running Containers"
    docker-compose ps
}

view_logs() {
    SERVICE=$1
    if [ -z "$SERVICE" ]; then
        SERVICE="admin-node"
    fi
    
    print_header "Logs for $SERVICE"
    docker-compose logs -f "$SERVICE"
}

view_broker_logs() {
    print_header "Mosquitto Broker Logs"
    docker-compose logs -f mosquitto
}

rebuild() {
    print_header "Rebuilding Docker Images"
    docker-compose build --no-cache
    print_success "Rebuild complete"
}

reset() {
    print_header "Resetting Deployment (This will delete all data)"
    read -p "Are you sure? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        rm -rf docker/mosquitto/data/* docker/mosquitto/log/* docker/shared_keystore/*
        print_success "Reset complete"
    else
        print_error "Reset cancelled"
    fi
}

# Main command router
COMMAND=$1

case "$COMMAND" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    start-node)
        start_user_node "$2" "$3" "${@:4}"
        ;;
    stop-node)
        stop_user_node "$2"
        ;;
    list)
        list_nodes
        ;;
    logs)
        view_logs "$2"
        ;;
    broker-logs)
        view_broker_logs
        ;;
    rebuild)
        rebuild
        ;;
    reset)
        reset
        ;;
    *)
        cat << EOF
${BLUE}QKD Smart City Network - Docker Management${NC}

Usage: ./manage.sh <command> [options]

Commands:
    start               Start admin node and Mosquitto broker
    stop                Stop all services
    start-node          Start a new user node
                        Usage: ./manage.sh start-node <name> <type> [--eavesdrop] [--noise N]
                        Types: traffic_flow, water_flow, surveillance
    stop-node           Stop a specific user node
                        Usage: ./manage.sh stop-node <name>
    list                List all running containers
    logs                View logs for a service (default: admin-node)
                        Usage: ./manage.sh logs [service-name]
    broker-logs         View Mosquitto broker logs
    rebuild             Rebuild all Docker images
    reset               Reset deployment (WARNING: deletes all data)

Examples:
    ./manage.sh start
    ./manage.sh start-node traffic-1 traffic_flow
    ./manage.sh start-node camera-1 surveillance --eavesdrop
    ./manage.sh start-node water-1 water_flow --noise 0.05
    ./manage.sh logs admin-node
    ./manage.sh stop

EOF
        exit 1
        ;;
esac
