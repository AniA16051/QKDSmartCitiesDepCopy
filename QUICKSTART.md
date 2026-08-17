# QKD Smart City Network - Quick Start Guide (Docker)

This is the fastest way to get the QKD network running with Docker.

## Prerequisites

- Docker installed and running
- Docker Compose installed
- Git (to clone the project)

## 5-Minute Startup

### Step 1: Start the Infrastructure (2 minutes)

```bash
# Navigate to project directory
cd d:\AniA\QKDNEW

# Start Mosquitto broker and admin control center
manage.bat start
# or on Linux/Mac:
./manage.sh start
```

You should see:
```
✓ All services started
CONTAINER ID   IMAGE           COMMAND                  NAMES
...            eclipse-mosquitto  mosquitto               qkd_mosquitto
...            qkdnew:latest   python -m network.co... qkd_admin_node
```

### Step 2: Add User Nodes (1 minute)

Open another terminal in the same directory and add sensors:

```bash
# Add a traffic light sensor
manage.bat start-node traffic-1 traffic_flow

# Add a water meter
manage.bat start-node water-1 water_flow

# Add a surveillance camera
manage.bat start-node camera-1 surveillance

# All three will now communicate via MQTT and perform BB84 key exchange
```

### Step 3: Monitor the Network (2 minutes)

```bash
# Watch admin logs to see BB84 exchanges happening
manage.bat logs admin-node

# You should see something like:
# [2026-08-17 12:34:56] New session from traffic-1
# [2026-08-17 12:34:56] BB84 exchange: 512 qubits
# [2026-08-17 12:34:56] QBER: 12.5% (SECURE)
# [2026-08-17 12:34:57] Received encrypted data from traffic-1
```

## Key Commands

### Infrastructure
```bash
manage.bat start          # Start broker + admin
manage.bat stop           # Stop everything
manage.bat list           # List running containers
```

### User Nodes
```bash
# Add sensor
manage.bat start-node <name> <type> [--eavesdrop] [--noise 0.05]

# Example nodes:
manage.bat start-node traffic-2 traffic_flow
manage.bat start-node camera-2 surveillance --eavesdrop
manage.bat start-node water-2 water_flow --noise 0.1

# Stop sensor
manage.bat stop-node <name>
```

### Monitoring
```bash
manage.bat logs admin-node          # Admin logs
manage.bat logs <node-name>         # Specific node logs
manage.bat broker-logs              # Mosquitto logs
```

## Using Python Node Manager (Alternative)

Instead of `.bat` scripts, you can use Python:

```bash
# Start infrastructure
python node_manager.py start

# Add nodes
python node_manager.py add-node traffic-1 traffic_flow
python node_manager.py add-node camera-1 surveillance --eavesdrop

# View status
python node_manager.py status

# View logs
python node_manager.py logs admin-node

# Stop everything
python node_manager.py stop
```

## Sensor Types

- **traffic_flow**: Generates vehicle count, speed, signal state
- **water_flow**: Generates flow rate, cumulative volume  
- **surveillance**: Generates motion detection, object count

## Advanced Options

### Simulate Eavesdropper
```bash
manage.bat start-node sensor-eve surveillance --eavesdrop
# Admin logs will show high QBER (>11%) → attack detected
```

### Simulate Noisy Channel
```bash
manage.bat start-node sensor-noisy water_flow --noise 0.05
# 5% bit error rate in quantum channel
```

### Combine Options
```bash
manage.bat start-node attacked-sensor traffic_flow --eavesdrop --noise 0.02
```

## What's Happening

1. **Mosquitto Broker**: MQTT message bus (localhost:1883)
2. **Admin Node**: Control center listening for BB84 exchanges
3. **User Nodes**: Sensors performing BB84 with admin, then sending encrypted data

Each sensor:
1. Performs BB84 quantum key exchange with admin → derive shared key
2. If QBER < 11% → secure (accept key)
3. If QBER ≥ 11% → eavesdropping detected (reject key)
4. Uses derived key to encrypt sensor readings
5. Publishes encrypted data to MQTT

## Viewing Data Flow

```bash
# Terminal 1: Watch admin receive BB84 exchanges
manage.bat logs admin-node

# Terminal 2: Add a sensor
manage.bat start-node demo traffic_flow

# Terminal 3: Watch all MQTT messages
docker exec qkd_mosquitto mosquitto_sub -t "smartcity/#" -v
```

## Project Structure

```
docker/
├── Dockerfile.admin         # Admin node image
├── Dockerfile.user          # User node image
├── mosquitto/
│   ├── config/mosquitto.conf
│   ├── data/                # MQTT persistent storage
│   └── log/                 # MQTT logs
└── shared_keystore/         # QKD keys (persistent)

manage.bat                  # Windows management script
manage.sh                   # Linux/Mac management script
node_manager.py            # Python management tool
docker-compose.yml         # Docker orchestration
DOCKER.md                  # Full Docker documentation
```

## Stopping & Cleanup

```bash
# Stop all containers (data persists)
manage.bat stop

# Stop specific node
manage.bat stop-node traffic-1

# Full reset (deletes all data)
manage.bat reset

# Rebuild images after code changes
manage.bat rebuild
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "docker not found" | Install Docker Desktop |
| "Connection refused" | Check if broker is running: `manage.bat list` |
| Node won't start | Check logs: `docker logs <node-name>` |
| "Port 1883 in use" | Change port in docker-compose.yml |
| Out of memory | Close other apps or increase Docker memory |

## Next Steps

- Read [DOCKER.md](DOCKER.md) for detailed documentation
- Check [network/README.md](network/README.md) for network architecture
- Review [BB84 implementation](core/bb84.py) to understand QKD

## Getting Help

```bash
# Show available commands
manage.bat

# Show help in Python
python node_manager.py

# Check Docker logs
docker logs <container-name>
docker logs -f <container-name>        # Follow logs

# Docker commands
docker ps                               # List containers
docker ps -a                            # All containers
docker network ls                       # List networks
docker volume ls                        # List volumes
```

## One-Liner Examples

```bash
# Complete demo in one go
manage.bat start && manage.bat start-node t1 traffic_flow && manage.bat start-node c1 surveillance --eavesdrop && manage.bat logs admin-node

# Reset everything
manage.bat reset

# See all MQTT messages
docker exec qkd_mosquitto mosquitto_sub -t "smartcity/#" -v
```

---

**That's it!** You now have a fully functional QKD-secured smart city network running in Docker.

For detailed configuration and production deployment, see [DOCKER.md](DOCKER.md).
