# QKD Smart City Network - Docker Deployment Guide

This guide explains how to deploy and manage the QKD-secured smart city network using Docker with a local Mosquitto MQTT broker.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Docker Network                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────┐      ┌────────────────────┐  │
│  │  Admin Control Center │      │  Mosquitto Broker  │  │
│  │  (Always Running)    │      │  (Port 1883, 9001) │  │
│  └──────────┬───────────┘      └────────────────────┘  │
│             │                           ▲               │
│             │                           │               │
│             └───────────────────────────┘               │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │  User Node 1     │  │  User Node 2     │           │
│  │  (sensor)        │  │  (sensor)        │           │
│  └──────────────────┘  └──────────────────┘           │
│  ▲                     ▲                                │
│  │                     │                                │
│  └─────────────────────┴────────────────────────────┬──┘
│                                                     │
│                  (via MQTT topics)                  │
└─────────────────────────────────────────────────────┘
```

## Prerequisites

- Docker (v20.10+)
- Docker Compose (v1.29+)
- Git

### Install Docker

**Windows:**
1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Run installer and follow setup
3. Restart your computer

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Or use Docker Desktop for Mac
```

## Quick Start

### 1. Start the Infrastructure

```bash
# Start Mosquitto broker and admin control center
./manage.sh start      # Linux/Mac
manage.bat start       # Windows

# Or manually:
docker-compose up -d
```

Verify services are running:
```bash
./manage.sh list       # Linux/Mac
manage.bat list        # Windows
```

### 2. Start User Nodes

Create sensor nodes dynamically. Each command starts a new container:

```bash
# Linux/Mac
./manage.sh start-node traffic-1 traffic_flow
./manage.sh start-node camera-1 surveillance --eavesdrop
./manage.sh start-node water-1 water_flow --noise 0.05

# Windows
manage.bat start-node traffic-1 traffic_flow
manage.bat start-node camera-1 surveillance
manage.bat start-node water-1 water_flow
```

### 3. Monitor Logs

```bash
# Admin control center logs
./manage.sh logs admin-node       # Linux/Mac
manage.bat logs admin-node        # Windows

# Broker logs
./manage.sh broker-logs           # Linux/Mac
manage.bat broker-logs            # Windows

# Specific node logs
docker logs traffic-1
```

### 4. Stop Services

```bash
# Stop all services
./manage.sh stop                  # Linux/Mac
manage.bat stop                   # Windows

# Stop specific user node
./manage.sh stop-node traffic-1   # Linux/Mac
manage.bat stop-node traffic-1    # Windows

# Or manually:
docker-compose down
```

## Management Commands

### Start Services
```bash
./manage.sh start
# or
docker-compose up -d
```

### Add User Nodes

Sensor types: `traffic_flow`, `water_flow`, `surveillance`

```bash
# Basic traffic flow sensor
./manage.sh start-node traffic-2 traffic_flow

# Traffic sensor with eavesdropper simulation
./manage.sh start-node traffic-3 traffic_flow --eavesdrop

# Water meter with noise simulation (5% error rate)
./manage.sh start-node water-2 water_flow --noise 0.05

# Surveillance camera with custom QBER threshold
./manage.sh start-node camera-2 surveillance --eavesdrop --noise 0.02
```

### List Running Containers
```bash
./manage.sh list
# Shows: mosquitto, admin-node, and any user nodes
```

### View Logs
```bash
# Admin control center
./manage.sh logs admin-node

# Mosquitto broker
./manage.sh broker-logs

# Specific node
docker logs <node-name>

# Follow logs in real-time
docker logs -f <node-name>
```

### Remove User Nodes
```bash
./manage.sh stop-node <node-name>
# or
docker stop <node-name>
docker rm <node-name>
```

### Full Reset (Delete All Data)
```bash
./manage.sh reset
# Stops all containers, deletes data volumes, clears keystores
```

### Rebuild Images
```bash
./manage.sh rebuild
# Rebuilds Docker images (use after modifying code)
```

## Direct Docker Commands

If you prefer not to use the management script:

```bash
# Start services
docker-compose up -d

# Start a user node
docker run -d \
  --name traffic-1 \
  --network qkd_network \
  -e BROKER_HOST=mosquitto \
  -e BROKER_PORT=1883 \
  -v ./docker/shared_keystore:/app/network/shared_keystore_data \
  qkdnew:latest \
  python -m network.sensor_node --id traffic-1 --type traffic_flow

# Stop all
docker-compose down

# Stop single container
docker stop <container-name>

# View logs
docker logs -f <container-name>

# List running containers
docker ps
```

## Environment Variables

These are automatically set in Docker containers:

```
BROKER_HOST=mosquitto      # Hostname of MQTT broker (Docker DNS)
BROKER_PORT=1883           # MQTT port
BROKER_USERNAME=null       # No auth required locally
BROKER_PASSWORD=null       
BROKER_USE_TLS=false       # TLS disabled locally
```

To override (example with authentication):
```bash
docker-compose run -e BROKER_USERNAME=user -e BROKER_PASSWORD=pass \
  user-node python -m network.sensor_node --id test --type traffic_flow
```

## Shared Keystore

Keys are stored in `docker/shared_keystore/` on your host system. This directory:
- Is mounted into all containers at `/app/network/shared_keystore_data`
- Persists across container restarts
- Can be backed up/restored

To clear all keys:
```bash
rm -rf docker/shared_keystore/*    # Linux/Mac
rmdir /s docker\shared_keystore    # Windows
```

## Mosquitto Broker

Broker configuration: `docker/mosquitto/config/mosquitto.conf`

Access the broker:
- **MQTT clients**: `mosquitto` (Docker) or `localhost` (host machine) on port 1883
- **WebSocket clients**: Port 9001
- **Admin UI**: Use MQTT explorer or similar tool

Test connectivity from host:
```bash
# Linux/Mac
mosquitto_sub -h localhost -t "smartcity/#" -v

# Or use MQTT explorer GUI
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs <container-name>

# Verify network exists
docker network ls

# Restart services
docker-compose down
docker-compose up -d
```

### Connection Refused
```bash
# Verify Mosquitto is running
docker ps | grep mosquitto

# Check broker logs
docker logs qkd_mosquitto

# Test broker connectivity
docker exec qkd_mosquitto mosquitto_sub -h localhost -t test
```

### Keystore Permission Issues
```bash
# Fix ownership (Linux)
sudo chown -R $USER:$USER docker/shared_keystore

# Or run with sudo
sudo docker-compose up -d
```

### Out of Memory
```bash
# Increase Docker memory in Docker Desktop settings
# Or limit container memory:
docker-compose down
# Edit docker-compose.yml, add to services:
#   deploy:
#     resources:
#       limits:
#         memory: 1G
```

## Performance Tuning

### For High-Load Scenarios

Edit `docker-compose.yml`:

```yaml
admin-node:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

Edit `docker/mosquitto/config/mosquitto.conf`:

```conf
max_connections 1000
max_inflight_messages 100
max_queued_messages 10000
```

## Production Deployment

For production use:

1. **Enable Authentication** in `mosquitto.conf`
2. **Set up TLS/SSL** certificates for Mosquitto
3. **Use persistent volumes** for Mosquitto data and keystores
4. **Configure resource limits** for all containers
5. **Set up monitoring** with Prometheus/Grafana
6. **Enable logging** to centralized service (ELK stack, etc.)
7. **Use a container registry** (Docker Hub, ECR, etc.)
8. **Implement health checks** for all services

Example production docker-compose.yml snippet:
```yaml
mosquitto:
  image: eclipse-mosquitto:latest
  ports:
    - "1883:1883"
  volumes:
    - mosquitto_data:/mosquitto/data
    - mosquitto_config:/mosquitto/config
  healthcheck:
    test: ["CMD", "mosquitto_sub", "-h", "localhost", "-t", "test"]
    interval: 30s
    timeout: 10s
    retries: 3

volumes:
  mosquitto_data:
    driver: local
  mosquitto_config:
    driver: local
```

## File Structure

```
d:\AniA\QKDNEW\
├── docker-compose.yml              # Main Docker Compose config
├── manage.sh                        # Linux/Mac management script
├── manage.bat                       # Windows management script
├── docker/
│   ├── Dockerfile.admin             # Admin node image
│   ├── Dockerfile.user              # User node image
│   ├── mosquitto/
│   │   ├── config/
│   │   │   └── mosquitto.conf       # MQTT broker config
│   │   ├── data/                    # MQTT persistence (auto-created)
│   │   └── log/                     # MQTT logs (auto-created)
│   └── shared_keystore/             # QKD keys (auto-created)
├── network/
│   ├── control_center.py            # Admin control center
│   ├── sensor_node.py               # User node sensor
│   └── ...
└── ...
```

## Example Workflows

### Workflow 1: Single Traffic Light Demo
```bash
./manage.sh start
./manage.sh start-node traffic-demo traffic_flow
docker logs -f admin-node
docker logs -f traffic-demo
./manage.sh stop-node traffic-demo
./manage.sh stop
```

### Workflow 2: Multi-sensor Smart City
```bash
./manage.sh start

# Create diverse sensors
./manage.sh start-node traffic-center traffic_flow
./manage.sh start-node traffic-north traffic_flow
./manage.sh start-node water-main water_flow
./manage.sh start-node camera-north surveillance
./manage.sh start-node camera-south surveillance --eavesdrop

# Monitor
./manage.sh logs admin-node

# Clean up
./manage.sh stop
```

### Workflow 3: Security Testing
```bash
./manage.sh start

# Normal sensor
./manage.sh start-node sensor-clean water_flow

# With eavesdropper
./manage.sh start-node sensor-attacked water_flow --eavesdrop

# With noise
./manage.sh start-node sensor-noisy water_flow --noise 0.1

# Compare QBER values in admin logs
docker logs admin-node | grep -i qber

./manage.sh stop
```

## Support

For issues, check:
1. Docker daemon is running
2. Port 1883, 9001 not in use by other services
3. Disk space available for logs and keystores
4. Network connectivity between containers

## Next Steps

- [Monitoring Dashboard](../dashboard/README.md)
- [Network Protocol Details](../network/README.md)
- [BB84 Implementation](../core/bb84.py)
