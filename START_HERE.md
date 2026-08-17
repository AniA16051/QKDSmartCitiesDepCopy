# 🚀 START HERE - Deploy Your QKD Dashboard

This guide will get your enhanced dashboard running in **5 minutes**.

## 📋 What You're Getting

Your QKD dashboard now includes:
- 🔐 **Login System** (Admin & User roles)
- 📊 **Real-time Monitoring** (MQTT-powered)
- 🕹️ **Admin Controls** (Start/stop nodes, simulate attacks)
- 📈 **QBER Metrics** (Quantum bit error rate tracking)
- 📋 **Security Logs** (Attack detection events)
- 🌐 **Multi-Computer Access** (Network-accessible)

---

## 🎯 Choose Your Deployment (Pick ONE)

### 🟢 Fastest & Easiest (Docker - Recommended)
**Best for:** Local team, on-premises, testing
**Time:** 5 minutes
**Cost:** $0

### 🔵 Global Access (Streamlit Cloud)
**Best for:** Quick demos, sharing with stakeholders
**Time:** 5 minutes + GitHub setup
**Cost:** Free (or $5+/month for upgrades)

### 🟡 Best of Both (Hybrid)
**Best for:** Production, teams in multiple locations
**Time:** 15 minutes
**Cost:** $0-10/month

---

## 🐳 Option 1: Docker Deployment (FASTEST)

### Prerequisites (Takes 5 minutes)
1. **Install Docker Desktop** (if not already installed)
   - Windows: https://www.docker.com/products/docker-desktop
   - Mac/Linux: https://docs.docker.com/install

2. **Verify installation:**
   ```bash
   docker --version
   docker-compose --version
   ```

### Deploy in 3 Steps

**Step 1:** Open PowerShell in your project folder
```bash
cd d:\AniA\QKDNEW
```

**Step 2:** Build the images (first time only, ~2 minutes)
```bash
docker-compose build
```

**Step 3:** Start the services
```bash
docker-compose up -d
```

### Access Your Dashboard

**From the same computer:**
```
http://localhost:8501
```

**From another computer on your network:**
```
ipconfig
```
Look for "IPv4 Address" (e.g., 192.168.1.100), then:
```
http://192.168.1.100:8501
```

### Login
- **Admin User:** admin / admin@qkd2026
- **Regular User:** user / user@qkd2026

---

## ☁️ Option 2: Streamlit Cloud (EASIEST SHARING)

### Prerequisites
- GitHub account (free: https://github.com/signup)
- 5 minutes

### Deploy in 4 Steps

**Step 1:** Create a GitHub repository
```bash
# On GitHub, create a new public repo
# Name: qkd-dashboard (or anything you want)
```

**Step 2:** Push your code
```bash
cd d:\AniA\QKDNEW
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/qkd-dashboard.git
git push -u origin main
```

**Step 3:** Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Select your repo and `dashboard/app_enhanced.py`
5. Click "Deploy"

**Step 4:** Configure MQTT access
1. In Streamlit Cloud settings → Secrets
2. Add:
```toml
broker_host = "192.168.1.100"  # Your computer's IP
broker_port = 1883
```

**Access:** Your app URL will be `https://<username>-qkd-dashboard.streamlit.app`

---

## 🔀 Option 3: Hybrid (PRODUCTION-READY)

**Run MQTT locally + Dashboard on Streamlit Cloud**

This is the best for production because:
- ✅ Keys never leave your network
- ✅ Dashboard accessible globally with HTTPS
- ✅ Can scale to many users
- ✅ Simple, cost-effective

### Step 1: Start MQTT locally
```bash
docker-compose build
docker-compose -f docker-compose-local.yml up -d
```

### Step 2: Create ngrok tunnel (makes MQTT accessible)
```bash
# Download ngrok: https://ngrok.com
# Run:
ngrok tcp 1883

# Copy the address: tcp://0.tcp.ngrok.io:xxxxx
```

### Step 3: Deploy to Streamlit Cloud
Follow "Option 2" above, but in Secrets use ngrok address:
```toml
broker_host = "0.tcp.ngrok.io"
broker_port = xxxxx
```

---

## 🎮 First Steps After Deployment

### 1. Verify Everything Works
- [ ] Open dashboard URL in browser
- [ ] See login page
- [ ] Login with admin/admin@qkd2026
- [ ] See monitoring dashboard
- [ ] Check "Broker Status" is green (Online)

### 2. Add a Test Sensor Node
**If using Docker:**
```bash
docker-compose run -d user-node-template \
  python -m network.sensor_node --id test-1 --type traffic_flow
```

**If using local Python (needs qiskit/paho-mqtt installed):**
```bash
python -m network.sensor_node --id test-1 --type traffic_flow
```

### 3. Watch It Work
- Dashboard should show "Total Nodes: 1"
- Node status appears in the "Nodes" tab
- QBER metrics update in real-time
- Security events appear in the log

### 4. Test Admin Features (if you're admin)
- Go to "Admin Controls" tab
- Try starting another node
- Try simulating an attack
- Adjust QBER threshold

---

## 🔄 Common Commands

### Docker Management

```bash
# View all services
docker-compose ps

# View dashboard logs
docker-compose logs -f dashboard

# View MQTT logs
docker-compose logs -f mosquitto

# Stop everything
docker-compose down

# Stop and delete all data
docker-compose down -v

# Restart a service
docker-compose restart dashboard
```

### Using Management Script (Windows)

```bash
# Start all services
manage.bat start

# Stop all services
manage.bat stop

# View dashboard logs
manage.bat dashboard-logs

# Add a sensor node
manage.bat add-node traffic-01 traffic_flow

# See all commands
manage.bat
```

---

## 🆘 Troubleshooting

### Dashboard won't load
```bash
# Check if services are running
docker-compose ps

# View dashboard logs
docker-compose logs dashboard

# Restart dashboard
docker-compose restart dashboard
```

### Can't connect from another computer
- Check your firewall allows ports 1883 and 8501
- Verify correct IP address with `ipconfig`
- Make sure `docker-compose.yml` has `0.0.0.0` in ports
- Test: `http://192.168.1.100:8501` (use YOUR IP)

### MQTT connection fails
```bash
# Check broker health
docker-compose ps mosquitto

# View broker logs
docker-compose logs mosquitto

# Test MQTT directly
docker-compose exec mosquitto mosquitto_sub -h localhost -t "#"
```

### Slow or freezing
- Check CPU usage: `docker stats`
- Check memory: `docker stats`
- Restart services: `docker-compose restart`

---

## 📊 Architecture Overview

```
┌────────────────────────────┐
│   Your Web Browser         │
│  (any computer/phone)      │
└────────────┬───────────────┘
             │
             │ http://IP:8501
             │
┌────────────▼───────────────────────┐
│  Streamlit Dashboard (app_enhanced) │
│  - Login page                       │
│  - Admin controls                   │
│  - Real-time monitoring             │
│  - Security logs                    │
└────────────┬───────────────────────┘
             │
             │ MQTT (port 1883)
             │
┌────────────▼───────────────────────┐
│  MQTT Broker (Mosquitto)            │
│  - Receives sensor data             │
│  - Broadcasts events                │
│  - Manages subscriptions            │
└────────────┬───────────────────────┘
             │
     ┌───────┼───────┐
     │       │       │
 ┌───▼──┐┌──▼───┐┌──▼───┐
 │Node 1││Node 2││Node N │
 │(BB84)││(BB84)││(BB84) │
 └──────┘└──────┘└──────┘
```

---

## 🔐 Security Notes

### For Development
- Default credentials are fine for testing
- Run only on trusted networks
- No HTTPS needed (local only)

### For Production
- **MUST** change default passwords in `dashboard/auth.py`
- **MUST** enable MQTT authentication in mosquitto config
- **SHOULD** use HTTPS/TLS
- **SHOULD** restrict firewall to trusted IPs
- **SHOULD** enable audit logging
- **SHOULD** use VPN for remote access

---

## 📈 Next Steps

1. ✅ **Deploy** using your chosen option (Docker/Cloud/Hybrid)
2. ✅ **Verify** dashboard loads and MQTT is connected
3. ✅ **Add sensors** and watch data flow in real-time
4. ✅ **Test admin features** (start nodes, simulate attacks)
5. ✅ **Change credentials** if deploying to production

---

## 📚 Full Documentation

For more details, see:
- [QUICK_START.md](QUICK_START.md) - 5-minute reference
- [DEPLOYMENT.md](DEPLOYMENT.md) - All deployment options & troubleshooting
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - What was built
- [DOCKER.md](DOCKER.md) - Container orchestration details

---

## ✅ Validation Checklist

After deployment, check:

- [ ] Services running: `docker-compose ps` shows 3+ containers
- [ ] Dashboard loads: `http://localhost:8501` or network IP
- [ ] Login works with admin credentials
- [ ] Dashboard shows monitoring page
- [ ] Broker status is green (Online)
- [ ] Can add sensor nodes
- [ ] Can view security logs
- [ ] Can logout and login as different user

**All checked? 🎉 You're ready!**

---

## 💡 Quick Tips

- **Dashboard not responding?** Refresh your browser or restart Docker
- **Want to add more nodes?** Use `manage.bat add-node` or docker CLI
- **Need to see logs?** Use `docker-compose logs -f [service]`
- **Forgot IP address?** Run `ipconfig` in PowerShell
- **Want to scale?** Add more computers running sensor nodes, all connected to same MQTT broker

---

## 🎯 Your Next 5 Minutes

```bash
# 1. Enter project folder
cd d:\AniA\QKDNEW

# 2. Build images (2 minutes)
docker-compose build

# 3. Start services (1 minute)
docker-compose up -d

# 4. Open dashboard
# http://localhost:8501

# 5. Login
# admin / admin@qkd2026

# Done! 🎉
```

---

**Questions?** Check the [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive troubleshooting.

**Ready to deploy?** Run the 3 commands above. You'll have your dashboard running in 5 minutes!

🚀 Let's go!
