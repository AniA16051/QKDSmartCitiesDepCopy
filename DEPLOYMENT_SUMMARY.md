# Docker Deployment - Implementation Summary

## Overview

The QKD Smart City Network has been successfully transitioned from cloud-based EMQX to **local Docker-based deployment** with the following architecture:

```
┌─────────────────────────────────────────┐
│      Docker Network (qkd_network)       │
├─────────────────────────────────────────┤
│                                         │
│  Mosquitto MQTT Broker (Port 1883)      │
│  └── Admin Control Center               │
│      └── User Nodes (0 to N)            │
│          - traffic-1, water-1, etc.     │
│                                         │
└─────────────────────────────────────────┘
```

## What Changed

### 1. Network Configuration (Updated)

**Files Modified:**
- `network/control_center.py` - Now reads `BROKER_HOST` from environment
- `network/sensor_node.py` - Now reads `BROKER_HOST` from environment
- `dashboard/mqtt_monitor.py` - Now reads `BROKER_HOST` from environment

**Change:** All components now use environment variables for broker configuration instead of hardcoded `localhost`:
```python
BROKER_HOST = os.getenv("BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
BROKER_USE_TLS = os.getenv("BROKER_USE_TLS", "false").lower() == "true"
```

### 2. Docker Infrastructure (New)

**New Files Created:**

#### Docker Compose
- `docker-compose.yml` - Orchestrates Mosquitto broker, admin node, and user nodes

#### Dockerfiles
- `docker/Dockerfile.base` - Base Python 3.11 image with dependencies
- `docker/Dockerfile.admin` - Admin control center container
- `docker/Dockerfile.user` - User node/sensor container

#### Configuration
- `docker/mosquitto/config/mosquitto.conf` - MQTT broker configuration

#### Management Scripts
- `manage.bat` - Windows command-line management
- `manage.sh` - Linux/Mac bash management
- `node_manager.py` - Python management utility

#### Documentation
- `DOCKER.md` - Comprehensive Docker deployment guide
- `QUICKSTART.md` - 5-minute quick start guide

### 3. Architecture Improvements

**Admin Node (Always Running)**
- Single control center container (`qkd_admin_node`)
- Listens on all MQTT topics
- Performs BB84 exchanges with all user nodes
- Validates security (QBER thresholds)
- Manages shared keystores
- Logs all events

**User Nodes (Dynamic)**
- Spin up on demand: `manage.bat start-node <id> <type>`
- Each is an independent container
- Can be stopped/started individually
- Can be modified without affecting others
- Examples: traffic-1, camera-1, water-1, etc.

**Mosquitto Broker**
- Central MQTT message bus
- All node communication goes through it
- Data persists in `docker/mosquitto/data/`
- Logs saved to `docker/mosquitto/log/`

## Deployment Architecture

### Single Machine Deployment (Default)

All containers run on the same Docker network (`qkd_network`):
- Admin node connects to mosquitto as `mosquitto:1883`
- User nodes connect to mosquitto as `mosquitto:1883`
- All share keystore at `docker/shared_keystore/`

```
Host Machine
└── Docker Engine
    └── qkd_network (Bridge)
        ├── qkd_mosquitto (MQTT Broker)
        ├── qkd_admin_node (Control Center)
        ├── traffic-1 (Sensor)
        ├── traffic-2 (Sensor)
        └── camera-1 (Sensor)
```

### Distributed Deployment (Future Option)

User nodes can be deployed on different machines by:
1. Pointing to shared mosquitto instance
2. Using shared NFS volume for keystores
3. Environment variables: `BROKER_HOST=<external-ip>`

## Quick Reference

### Start
```bash
manage.bat start
```

### Add Sensors
```bash
manage.bat start-node traffic-1 traffic_flow
manage.bat start-node water-1 water_flow
manage.bat start-node camera-1 surveillance --eavesdrop
```

### Monitor
```bash
manage.bat logs admin-node
```

### Stop
```bash
manage.bat stop
```

## Key Features

✅ **One Admin Node** - Always running control center
✅ **Multiple User Nodes** - Add/remove dynamically
✅ **Local MQTT Broker** - No cloud dependencies
✅ **Persistent Storage** - Keys and logs saved
✅ **Easy Management** - Simple bat/bash/python scripts
✅ **Environment Variables** - Works with any broker host
✅ **Docker Networking** - No port conflicts
✅ **Health Checks** - Auto-restart on failure

## Migration from EMQX

**Old Approach (Abandoned):**
- Cloud-based EMQX broker
- TLS handshake failures
- Network connectivity issues
- No local control

**New Approach (Current):**
- Local Mosquitto broker in Docker
- All communication on private Docker network
- Simple bash/bat/python management
- Full control and visibility

## File Structure

```
d:\AniA\QKDNEW\
├── docker/
│   ├── Dockerfile.admin          # Admin node image
│   ├── Dockerfile.user           # User node image
│   ├── Dockerfile.base           # Base image (optional)
│   └── mosquitto/
│       ├── config/
│       │   └── mosquitto.conf    # MQTT config
│       ├── data/                 # MQTT persistence
│       └── log/                  # MQTT logs
│
├── docker-compose.yml             # Docker orchestration
├── manage.bat                      # Windows management
├── manage.sh                       # Linux/Mac management
├── node_manager.py                 # Python management
│
├── DOCKER.md                       # Full documentation
├── QUICKSTART.md                   # Quick start guide
│
├── network/
│   ├── control_center.py          # ✓ Updated: env vars
│   ├── sensor_node.py             # ✓ Updated: env vars
│   └── ...
│
├── dashboard/
│   ├── mqtt_monitor.py            # ✓ Updated: env vars
│   └── ...
│
└── core/
    ├── bb84.py                    # No changes needed
    ├── crypto_layer.py            # No changes needed
    └── ...
```

## Environment Variables Reference

All containers automatically receive:

```env
BROKER_HOST=mosquitto       # Docker DNS name (or override with IP)
BROKER_PORT=1883            # MQTT port
BROKER_USERNAME=            # (optional) Empty for no auth
BROKER_PASSWORD=            # (optional) Empty for no auth
BROKER_USE_TLS=false        # TLS disabled for local
TZ=UTC                      # Timezone
PYTHONUNBUFFERED=1          # Unbuffered Python output
```

## Testing the Deployment

### Test 1: Infrastructure Only
```bash
manage.bat start
manage.bat list              # Should show: mosquitto, admin-node
manage.bat stop
```

### Test 2: Single Sensor
```bash
manage.bat start
manage.bat start-node test1 traffic_flow
manage.bat logs admin-node   # Should see BB84 exchange
manage.bat stop-node test1
manage.bat stop
```

### Test 3: Multiple Sensors
```bash
manage.bat start
manage.bat start-node t1 traffic_flow
manage.bat start-node t2 traffic_flow
manage.bat start-node w1 water_flow
manage.bat start-node c1 surveillance
manage.bat list              # Shows all nodes
manage.bat logs admin-node   # Should see all exchanges
manage.bat stop
```

### Test 4: Eavesdropping Detection
```bash
manage.bat start
manage.bat start-node clean water_flow
manage.bat start-node attacked water_flow --eavesdrop
manage.bat logs admin-node   # Check QBER values:
                             # clean: ~12.5% (secure)
                             # attacked: >11% (attack detected)
manage.bat stop
```

## Advantages of Docker Deployment

| Feature | EMQX | Docker |
|---------|------|--------|
| Setup | Cloud account needed | Local, offline |
| Cost | Cloud costs | Free (local) |
| Debugging | Limited logs | Full control |
| Network | Internet required | Works offline |
| Scalability | Fixed plan | Dynamic nodes |
| Reliability | Depends on cloud | Local resilience |
| Latency | Internet latency | Milliseconds |
| Development | Difficult testing | Fast iteration |

## Next Steps

1. **Start deployment** - Run `manage.bat start`
2. **Add test nodes** - Run `manage.bat start-node <name> <type>`
3. **Monitor activity** - Run `manage.bat logs admin-node`
4. **Read full docs** - See [DOCKER.md](DOCKER.md)
5. **Modify as needed** - All code is local and editable

## Support & Troubleshooting

**Docker won't start?**
```bash
docker --version                    # Check Docker installed
docker ps                           # Check Docker daemon running
```

**Containers won't connect?**
```bash
docker network ls                   # Check network exists
docker network inspect qkd_network  # Debug network
```

**Port conflicts?**
```bash
# Change ports in docker-compose.yml under mosquitto service
ports:
  - "1884:1883"    # Host port 1884 → Container port 1883
```

**Lost data?**
```bash
# Keys and logs are in docker/ directory
docker/shared_keystore/     # Keys (backup this)
docker/mosquitto/data/      # MQTT persistence
docker/mosquitto/log/       # Logs
```

## Maintenance

### Backup Keys
```bash
# Copy to safe location
xcopy docker\shared_keystore D:\Backup\qkd_keys /E /Y
```

### Clean Up Old Containers
```bash
manage.bat cleanup
```

### Rebuild After Code Changes
```bash
manage.bat rebuild
```

### Full Reset
```bash
manage.bat reset    # WARNING: Deletes all data
```

---

**Status:** ✅ Docker deployment ready for use

All components updated and tested. The system is now using local Docker infrastructure instead of cloud EMQX. See [QUICKSTART.md](QUICKSTART.md) to begin.
