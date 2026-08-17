# Quick Start - Enhanced Dashboard

Get your QKD dashboard running in minutes.

## 🚀 Fastest Way to Deploy (Docker - 5 minutes)

### Prerequisites
- Docker Desktop installed
- 4GB RAM available

### Three Commands to Deploy

```bash
# 1. Build Docker images
docker-compose build

# 2. Start all services
docker-compose up -d

# 3. Open dashboard
# Local: http://localhost:8501
# Network: http://<your-ip>:8501
```

**Login with:**
- **Admin:** `admin` / `admin@qkd2026`
- **User:** `user` / `user@qkd2026`

---

## 📊 Dashboard Features by Role

### Admin Access
- ✅ View real-time monitoring
- ✅ Start/stop sensor nodes
- ✅ Simulate attacks (eavesdropping, noise)
- ✅ Adjust QBER thresholds
- ✅ Manage users
- ✅ Export security logs

### User Access
- ✅ View monitoring dashboard
- ✅ Check node status
- ✅ View QBER metrics
- ✅ Export data
- ❌ Can't modify settings
- ❌ Can't start/stop nodes

---

## 🔧 Common Tasks

### Start Dashboard with All Services
```bash
docker-compose up -d
```

### Stop Dashboard
```bash
docker-compose down
```

### View Dashboard Logs
```bash
docker-compose logs -f dashboard
```

### Add a Sensor Node
```bash
# From Docker
docker-compose run -d user-node-template \
  python -m network.sensor_node --id traffic-01 --type traffic_flow

# Or from command line (needs Python installed)
python -m network.sensor_node --id traffic-01 --type traffic_flow
```

### Connect from Another Computer

**Same Network (WiFi/Ethernet):**
```
http://<your-computer-ip>:8501
```

**Find your IP:**
- Windows: `ipconfig` → look for IPv4 Address (192.168.x.x)
- Mac/Linux: `ifconfig` → look for inet

**Example:** If your IP is `192.168.1.100`, use `http://192.168.1.100:8501`

### Reset to Default State
```bash
# Warning: This deletes all stored keys!
docker-compose down -v
docker-compose up -d
```

---

## 🐳 Docker Service Status

```bash
# Check all services
docker-compose ps

# Expected output:
# mosquitto    (MQTT Broker)
# admin-node   (Control Center)  
# dashboard    (Web UI)
```

---

## 🎯 Next Steps

1. ✅ Dashboard deployed
2. ⏭️ [View Deployment Guide](DEPLOYMENT.md) for advanced options
3. ⏭️ [See Docker docs](DOCKER.md) for production setup
4. ⏭️ Change default credentials in `dashboard/auth.py` for production

---

## 📞 Troubleshooting

**Dashboard won't load:**
```bash
docker-compose logs dashboard
# Check for errors, usually port conflicts
```

**Can't access from another computer:**
- Verify: `docker-compose ps` shows dashboard port `0.0.0.0:8501`
- Check firewall allows port 8501
- Use correct IP address (not localhost)

**MQTT connection fails:**
```bash
docker-compose logs mosquitto
docker-compose ps mosquitto
```

---

## 🎓 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Docker Network                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Mosquitto   │  │  Admin Node  │  │Dashboard │ │
│  │  MQTT Broker │  │ (QKD Control)│  |(Streamlit)│ │
│  │              │  │              │  │          │ │
│  │ 1883 (MQTT)  │  │              │  │ 8501 (Web)│ │
│  │ 9001 (WebSock│  │              │  │          │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│       ▲                   ▲                ▲        │
│       │ MQTT              │ MQTT            │       │
│       └───────────────────┼────────────────┘       │
│                           │                         │
└─────────────────────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼────┐      ┌──────▼────┐      ┌─────▼─────┐
    │Sensor 1 │      │ Sensor 2  │      │ Sensor N  │
    │(BB84)   │      │  (BB84)   │      │  (BB84)   │
    │         │      │           │      │           │
    └─────────┘      └───────────┘      └───────────┘
    
    Publish encrypted data & session keys via MQTT
    ▶ Dashboard monitors in real-time
    ▶ Admin node decrypts and validates
    ▶ Security events logged
```

---

## 📝 Configuration

### Change Default Credentials

Edit `dashboard/auth.py`:

```python
DEFAULT_USERS = {
    'admin': {
        'password_hash': hashlib.sha256('YOUR_PASSWORD'.encode()).hexdigest(),
        'role': 'admin'
    },
    'user': {
        'password_hash': hashlib.sha256('YOUR_PASSWORD'.encode()).hexdigest(),
        'role': 'user'
    }
}
```

### Change MQTT Broker Settings

In containers, set environment variables:

```bash
# In docker-compose.yml
environment:
  - BROKER_HOST=mosquitto
  - BROKER_PORT=1883
  - BROKER_USERNAME=username  # if needed
  - BROKER_PASSWORD=password  # if needed
  - BROKER_USE_TLS=false
```

For external connections from another computer:

```bash
# Replace 'mosquitto' with your computer IP
BROKER_HOST=192.168.1.100
BROKER_PORT=1883
```

---

## 🔍 Monitoring & Debugging

### Real-time Dashboard Activity
```bash
# Watch all logs
docker-compose logs -f

# Watch specific service
docker-compose logs -f dashboard
docker-compose logs -f admin-node
docker-compose logs -f mosquitto
```

### Test MQTT Connection
```bash
# Enter MQTT container
docker-compose exec mosquitto bash

# Subscribe to all topics
mosquitto_sub -h localhost -t "#"

# In another terminal, publish test message
docker-compose exec mosquitto mosquitto_pub -h localhost -t "test/hello" -m "Hello World"
```

### Check Dashboard Health
```bash
# View metrics
docker stats qkd_dashboard

# Check connectivity
docker-compose exec dashboard ping mosquitto
```

---

## 📈 Performance Tips

- **Slow dashboard?** Reduce `st_autorefresh` interval in `app_enhanced.py` (default: 2 seconds)
- **High CPU?** Increase Docker memory allocation or reduce log size
- **Network lag?** Use Streamlit Cloud for global access

---

## 🎓 Learning Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Eclipse Mosquitto](https://mosquitto.org)
- [Docker Compose Guide](https://docs.docker.com/compose)
- [Quantum Key Distribution (BB84)](https://en.wikipedia.org/wiki/BB84)

---

## ✅ Quick Validation Checklist

- [ ] Docker Desktop running
- [ ] `docker-compose ps` shows 3 services
- [ ] Dashboard accessible on http://localhost:8501
- [ ] Can login with admin/admin@qkd2026
- [ ] Can view monitoring dashboard
- [ ] Can see "Broker Status: Online"
- [ ] Can export security events

**All checked? ✅ You're ready for production!**

---

For advanced deployment options and production setup, see [DEPLOYMENT.md](DEPLOYMENT.md)
