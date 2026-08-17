# QKD Smart City Dashboard - Deployment Guide

Complete guide to deploying the enhanced dashboard with authentication and network access.

## 📋 Quick Summary

| Deployment Method | Setup Time | Best For | Multi-Computer | Cost |
|---|---|---|---|---|
| **Docker (Recommended)** | 10 min | Production, full control | ✅ Yes | $0-20 |
| **Streamlit Cloud** | 5 min | Quick demo, easy sharing | ✅ Yes (cloud) | Free/$5-50 |
| **Hybrid** | 15 min | Best of both worlds | ✅ Yes | $0-10 |
| **Local Dev** | 2 min | Testing, development | ❌ No | $0 |

---

## 🐳 Option 1: Docker Deployment (RECOMMENDED)

### Best For:
- Production environments
- On-premises deployment
- Full control over infrastructure
- Multi-computer network access
- Persistent data storage

### Prerequisites:
- Docker Desktop installed
- Docker Compose v1.29+
- 4GB+ RAM available
- Windows/Mac/Linux

### Quick Start (5 minutes)

```bash
# 1. Start all services
docker-compose up -d

# 2. Wait for services to initialize (30 seconds)
# Check status
docker-compose ps

# 3. Access dashboard
# From same computer: http://localhost:8501
# From other computers: http://<your-ip>:8501

# 4. Login with credentials:
# Admin: admin / admin@qkd2026
# User: user / user@qkd2026
```

### Step-by-Step Setup

#### Step 1: Verify Prerequisites

```bash
docker --version  # Should be 20.10+
docker-compose --version  # Should be 1.29+
```

#### Step 2: Build Docker Images

```bash
# Build all images (MQTT broker, admin node, dashboard)
docker-compose build

# Or rebuild with no cache
docker-compose build --no-cache
```

#### Step 3: Start Services

```bash
# Start in background
docker-compose up -d

# Watch logs
docker-compose logs -f

# Check status
docker-compose ps
```

**Expected output:**
```
NAME              STATUS         PORTS
qkd_mosquitto     Up (healthy)   0.0.0.0:1883->1883/tcp, 0.0.0.0:9001->9001/tcp
qkd_admin_node    Up (healthy)   
qkd_dashboard     Up             0.0.0.0:8501->8501/tcp
```

#### Step 4: Access Dashboard

From the machine running Docker:
- **Local access:** http://localhost:8501

From another computer on the network:
- **Network access:** http://<docker-host-ip>:8501
  - Find your IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
  - Example: http://192.168.1.100:8501

#### Step 5: Add Sensor Nodes (Optional)

```bash
# Start a traffic sensor node
docker-compose run -d --name traffic-node user-node-template \
  python -m network.sensor_node --id traffic-01 --type traffic_flow

# Start a water sensor node
docker-compose run -d --name water-node user-node-template \
  python -m network.sensor_node --id water-01 --type water_flow

# View all containers
docker-compose ps

# Stop a node
docker-compose stop traffic-node
```

### Docker Configuration Details

**Network Setup:**
- **Network Type:** Bridge network (`qkd_network`)
- **MQTT Broker:** Listens on `0.0.0.0:1883` (all interfaces)
- **Dashboard:** Listens on `0.0.0.0:8501` (all interfaces)
- **Shared Storage:** `docker/shared_keystore` volume for persistent keys

**Environment Variables in Containers:**
- `BROKER_HOST=mosquitto` (DNS name in Docker network)
- `BROKER_PORT=1883`
- All containers can communicate internally

**From Other Computers:**
- Replace `mosquitto` with host IP when connecting externally
- Modify `BROKER_HOST` in sensor nodes: `docker-compose run user-node-template python -m network.sensor_node --id test --type traffic_flow -e BROKER_HOST=192.168.1.100`

### Troubleshooting Docker Deployment

#### Dashboard not accessible from network

```bash
# Check if port 8501 is open
netstat -an | findstr 8501  # Windows
lsof -i :8501  # Mac/Linux

# Verify container is listening on 0.0.0.0
docker-compose logs dashboard

# Restart dashboard
docker-compose restart dashboard
```

#### MQTT connection failures

```bash
# Check broker logs
docker-compose logs mosquitto

# Test MQTT connection
docker-compose exec -it mosquitto mosquitto_sub -h localhost -t "#"

# Verify broker is healthy
docker-compose ps mosquitto
```

#### Slow performance or crashes

```bash
# Check resource usage
docker stats

# Increase resources in docker-compose.yml under dashboard:
# deploy:
#   resources:
#     limits:
#       memory: 1G
#     reservations:
#       memory: 512M
```

### Management Commands

```bash
# View logs
docker-compose logs -f dashboard          # Dashboard logs
docker-compose logs -f mosquitto          # MQTT broker logs
docker-compose logs -f admin-node         # Admin control center logs

# Stop all services
docker-compose down

# Remove all data (WARNING: deletes keys!)
docker-compose down -v

# Rebuild after code changes
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Access container shell
docker-compose exec dashboard bash
docker-compose exec mosquitto sh
```

---

## ☁️ Option 2: Streamlit Cloud Deployment

### Best For:
- Quick demos and sharing
- Global accessibility (HTTPS automatic)
- Zero infrastructure management
- Public dashboards

### Limitations:
- Public by default (need authentication for privacy)
- Cold starts (first load ~5 seconds)
- MQTT broker must be public or use ngrok
- Free tier limited to 3 apps

### Step-by-Step Setup

#### Step 1: Push Code to GitHub

```bash
# Create GitHub repository (https://github.com/new)

# Clone repo
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# Copy your code
cp -r d:\AniA\QKDNEW\* .

# Push to GitHub
git add .
git commit -m "Initial commit: QKD dashboard with auth"
git push origin main
```

#### Step 2: Configure for Streamlit Cloud

Create `.streamlit/secrets.toml`:

```toml
# MQTT Configuration
broker_host = "192.168.1.100"  # Your external IP or ngrok tunnel
broker_port = 1883
broker_username = ""
broker_password = ""
broker_use_tls = false

# App settings
admin_username = "admin"
admin_password = "admin@qkd2026"
user_username = "user"
user_password = "user@qkd2026"
```

**Important:** Add `.streamlit/secrets.toml` to `.gitignore`:

```
.streamlit/secrets.toml
```

#### Step 3: Update Streamlit Config

Create `.streamlit/config.toml`:

```toml
[theme]
base = "light"
primaryColor = "#FF6B6B"

[server]
headless = true
port = 8501
maxUploadSize = 200
enableCORS = false
enableXsrfProtection = true

[client]
showErrorDetails = true
```

#### Step 4: Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Select:
   - GitHub repo: `<your-username>/<your-repo>`
   - Branch: `main`
   - File path: `dashboard/app_enhanced.py`
4. Click "Deploy"

#### Step 5: Configure Secrets

1. In Streamlit Cloud dashboard, click "⚙️ Settings"
2. Go to "Secrets"
3. Paste contents of `.streamlit/secrets.toml`
4. Save

#### Step 6: Access Your Dashboard

Your app will be available at:
```
https://<your-username>-<app-name>.streamlit.app
```

### Making MQTT Accessible from Streamlit Cloud

**Problem:** Streamlit Cloud can't reach your local MQTT broker.

**Solution A: Use ngrok Tunnel (Free)**

```bash
# 1. Download ngrok from https://ngrok.com
# 2. Run tunnel for MQTT
ngrok tcp 1883

# 3. Copy the forwarding address (e.g., 0.tcp.ngrok.io:12345)
# 4. Update secrets in Streamlit Cloud:
#    broker_host = "0.tcp.ngrok.io"
#    broker_port = 12345
```

**Solution B: Use Public MQTT Service (Free)**

```bash
# Use free MQTT service
# In secrets.toml:
broker_host = "mqtt.example.com"
broker_port = 1883
```

**Solution C: Deploy MQTT to Cloud (Paid)**

- Azure IoT Hub
- AWS IoT Core
- HiveMQ Cloud (Free tier: 100 connections)

### Streamlit Cloud Costs

| Tier | Price | Apps | Resources |
|---|---|---|---|
| Free | $0/month | 3 | 1 vCPU, 512MB RAM |
| Pro | $5/month | Unlimited | 2 vCPU, 2GB RAM |
| Business | $25/month | Unlimited | Dedicated support |

---

## 🔀 Option 3: Hybrid Deployment (RECOMMENDED FOR MOST)

### Architecture:
- **MQTT Broker:** Docker (local, on-premises)
- **Dashboard:** Streamlit Cloud (accessible globally)
- **Admin Node:** Docker (local, processes commands)

### Benefits:
- ✅ Secure (keys never leave local network)
- ✅ Scalable (global dashboard access)
- ✅ Low cost (mostly free)
- ✅ Full control (local data)

### Setup Instructions

#### Step 1: Deploy MQTT Broker Locally

```bash
# Start only MQTT and admin node
cd d:\AniA\QKDNEW

# Create docker-compose-local.yml with only broker and admin:
docker-compose -f docker-compose-local.yml up -d mosquitto admin-node
```

Create `docker-compose-local.yml`:

```yaml
version: '3.8'

services:
  mosquitto:
    image: eclipse-mosquitto:latest
    container_name: qkd_mosquitto
    ports:
      - "0.0.0.0:1883:1883"
      - "0.0.0.0:9001:9001"
    volumes:
      - ./docker/mosquitto/config:/mosquitto/config
      - ./docker/mosquitto/data:/mosquitto/data
      - ./docker/mosquitto/log:/mosquitto/log
    networks:
      - qkd_network
    restart: unless-stopped

  admin-node:
    build:
      context: .
      dockerfile: docker/Dockerfile.admin
    container_name: qkd_admin_node
    depends_on:
      - mosquitto
    environment:
      - BROKER_HOST=mosquitto
      - BROKER_PORT=1883
    volumes:
      - ./:/app
      - ./docker/shared_keystore:/app/network/shared_keystore_data
    networks:
      - qkd_network
    command: python -m network.control_center
    restart: unless-stopped

networks:
  qkd_network:
    driver: bridge
```

#### Step 2: Expose MQTT Over Internet

**Using ngrok:**

```bash
# Start ngrok tunnel
ngrok tcp 1883

# Save the forwarding address
# Example: tcp://0.tcp.ngrok.io:12345
```

Or use **Tailscale** (more secure, VPN):

```bash
# Install Tailscale from https://tailscale.com
# Run: tailscale up
# Get your IP: tailscale ip -4
# Share your Tailscale IP with Streamlit Cloud
```

#### Step 3: Deploy Dashboard to Streamlit Cloud

Follow "Option 2: Streamlit Cloud Deployment" above, using:
- ngrok address OR
- Tailscale IP

### Hybrid Cost Analysis

| Component | Option | Cost |
|---|---|---|
| MQTT Broker | Docker (local) | $0 |
| Admin Node | Docker (local) | $0 |
| Dashboard | Streamlit Cloud Free | $0 |
| Internet Tunnel | ngrok Free | $0 |
| **Total** | | **$0/month** |

---

## 💻 Option 4: Local Development (No Network Access)

### Quick Start for Testing

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start MQTT broker (local)
docker run -d -p 1883:1883 eclipse-mosquitto:latest

# 3. Start admin node
python -m network.control_center

# 4. Start dashboard (in new terminal)
streamlit run dashboard/app_enhanced.py

# 5. Open browser
# http://localhost:8501

# 6. In another terminal, start a sensor node
python -m network.sensor_node --id test-1 --type traffic_flow
```

---

## 📊 Multi-Computer Access Comparison

| Scenario | Docker | Streamlit Cloud | Hybrid |
|---|---|---|---|
| **Same Network** | ✅ http://\<ip\>:8501 | ⚠️ Through cloud | ✅ Both options |
| **Different Networks** | ⚠️ Needs ngrok | ✅ Automatic | ✅ Yes |
| **Mobile Access** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Offline Use** | ✅ Yes | ❌ No | ✅ MQTT only |
| **Security Control** | ✅ Full | ⚠️ Cloud-managed | ✅ Both |

---

## 🔐 Security Considerations

### Docker Deployment (On-Premises)

```yaml
# In docker-compose.yml, restrict access:
ports:
  - "192.168.1.100:1883:1883"  # Only specific IP
  - "192.168.1.100:8501:8501"  # Only specific IP
```

### Streamlit Cloud

1. **Enable authentication:** The built-in login is enabled
2. **Use secrets:** Never commit credentials
3. **HTTPS:** Automatic on Streamlit Cloud
4. **Firewall rules:** Restrict MQTT connections

### Network Access

```bash
# Firewall rules (Windows)
netsh advfirewall firewall add rule name="QKD MQTT" dir=in action=allow protocol=tcp localport=1883

# Or use firewall GUI to allow only trusted IPs
```

---

## 🚀 Production Deployment Checklist

- [ ] Choose deployment method (Docker/Cloud/Hybrid)
- [ ] Update default credentials in `auth.py`
- [ ] Configure MQTT security (username/password)
- [ ] Set up SSL/TLS certificates
- [ ] Enable firewall rules
- [ ] Test multi-computer access
- [ ] Set up monitoring and logging
- [ ] Configure backups
- [ ] Document access procedures
- [ ] Train users

---

## 📞 Support & Troubleshooting

### Common Issues

**1. Can't connect from another computer**
- Verify firewall allows port 1883/8501
- Check if `0.0.0.0` in docker-compose.yml ports
- Use `ipconfig` to find your IP address

**2. Dashboard won't load**
- Check Streamlit is running: `docker-compose logs dashboard`
- Verify MQTT broker is healthy: `docker-compose ps`
- Try accessing: `http://localhost:8501`

**3. MQTT authentication fails**
- Check username/password in environment variables
- Verify mosquitto config has correct auth settings
- Test with: `mosquitto_sub -h localhost -t "#"`

### Debug Commands

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f

# Test MQTT
docker-compose exec mosquitto mosquitto_sub -h localhost -t "#"

# Test network connectivity
docker-compose exec dashboard ping mosquitto

# View shared keystore
ls -la docker/shared_keystore/
```

---

## 📚 Next Steps

1. **Choose your deployment method** (Docker recommended)
2. **Follow the setup instructions** for your choice
3. **Test with demo sensors** before production
4. **Configure custom credentials** in `auth.py`
5. **Set up monitoring** and alerts

For detailed information, see:
- DOCKER.md - Container orchestration details
- QUICKSTART.md - Quick reference commands
- README.md - Project overview
