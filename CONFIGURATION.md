# Configuration Guide - QKD Dashboard Customization

Customize your dashboard for your specific deployment needs.

## 🔐 1. Change Default Credentials (IMPORTANT for Production)

**File:** `dashboard/auth.py`

### Step 1: Generate password hashes

Open PowerShell:
```python
# Run this in Python to hash your password
import hashlib
password = "your-new-password"
hash = hashlib.sha256(password.encode()).hexdigest()
print(f"Hash: {hash}")
```

Or online: https://www.sha256online.com

### Step 2: Update auth.py

Replace lines 23-31:
```python
DEFAULT_USERS = {
    'admin': {
        'password_hash': 'YOUR_ADMIN_HASH_HERE',  # Replace with hashed password
        'role': 'admin'
    },
    'user': {
        'password_hash': 'YOUR_USER_HASH_HERE',   # Replace with hashed password
        'role': 'user'
    }
}
```

### Example:
```python
# If password = "MySecure123!"
# Hash = "a1b2c3d4e5f6..."

DEFAULT_USERS = {
    'admin': {
        'password_hash': 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1',
        'role': 'admin'
    },
    'user': {
        'password_hash': 'b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
        'role': 'user'
    }
}
```

### Step 3: Rebuild Docker image
```bash
docker-compose build --no-cache dashboard
docker-compose restart dashboard
```

---

## 🌐 2. Configure MQTT Broker Settings

### For Docker (Same Network)
No changes needed - uses internal `mosquitto` hostname

### For External Connections (Different Computer)
**For sensor nodes connecting from outside Docker:**

Create `.env` file in project root:
```env
BROKER_HOST=192.168.1.100
BROKER_PORT=1883
BROKER_USERNAME=
BROKER_PASSWORD=
BROKER_USE_TLS=false
```

### For Cloud Deployment (Streamlit Cloud)
**Create `.streamlit/secrets.toml`:**
```toml
# MQTT Configuration
broker_host = "192.168.1.100"  # Your IP
broker_port = 1883
broker_username = ""
broker_password = ""
broker_use_tls = false

# Or use ngrok tunnel
broker_host = "0.tcp.ngrok.io"
broker_port = 12345
```

---

## 🎨 3. Customize Dashboard UI

### Change Theme Colors

**File:** `dashboard/app_enhanced.py`, line 23

Current colors:
```python
st.markdown("""
<style>
    .admin-badge { background: #FF6B6B; }      /* Red */
    .user-badge { background: #4ECDC4; }       /* Teal */
    .status-ok { color: #06D6A0; }             /* Green */
    .status-alert { color: #FF6B6B; }          /* Red */
</style>
""", unsafe_allow_html=True)
```

Popular color schemes:
- **Dark Blue:** #1E3A8A
- **Ocean Blue:** #0369A1
- **Forest Green:** #166534
- **Purple:** #7C3AED
- **Orange:** #EA580C

Example - Change to blue theme:
```python
.admin-badge { background: #1E3A8A; }
.user-badge { background: #0369A1; }
.status-ok { color: #00D084; }
.status-alert { color: #FF4D4D; }
```

### Change Page Title and Header

**File:** `dashboard/app_enhanced.py`, line 44
```python
st.set_page_config(
    page_title="Your Company - QKD Dashboard",  # Change this
    layout="wide",
    initial_sidebar_state="expanded"
)
```

**Line 95-99 - Header text:**
```python
st.title("🔐 Your Company QKD Network")  # Change this
st.caption("Real-time quantum security monitoring & control")  # Change this
```

### Add Logo

**File:** `dashboard/app_enhanced.py`, line 97

```python
# Add after st.title()
st.image("path/to/your/logo.png", width=100)
```

---

## 📊 4. Add Custom Metrics

### Add New Metric to Overview

**File:** `dashboard/app_enhanced.py`, around line 220

Current metrics:
```python
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Nodes", total_nodes, delta="nodes active")
```

Add a new metric:
```python
col1, col2, col3, col4, col5 = st.columns(5)

# ... existing metrics ...

with col5:
    avg_qber = sum(info.get("qber_last", 0) for info in nodes.values()) / max(len(nodes), 1)
    st.metric("Avg QBER", f"{avg_qber:.2f}%")
```

---

## 🔧 5. Configure Admin Controls

### Change QBER Threshold Range

**File:** `dashboard/app_enhanced.py`, line 372

```python
# Current:
qber_threshold = st.slider("QBER Threshold (%)", 0.05, 0.20, 0.11, step=0.01)

# More sensitive (detect attacks faster):
qber_threshold = st.slider("QBER Threshold (%)", 0.01, 0.10, 0.07, step=0.01)

# Less sensitive (allow more noise):
qber_threshold = st.slider("QBER Threshold (%)", 0.10, 0.30, 0.15, step=0.01)
```

### Add Custom Sensor Types

**File:** `dashboard/app_enhanced.py`, line 354

```python
# Current:
sensor_type = st.selectbox("Sensor Type", ["traffic_flow", "water_flow", "surveillance"])

# Add custom types:
sensor_type = st.selectbox("Sensor Type", [
    "traffic_flow",
    "water_flow",
    "surveillance",
    "temperature",      # New
    "humidity",         # New
    "air_quality"       # New
])
```

---

## 📈 6. Customize Monitoring Refresh Rate

### Change Dashboard Update Frequency

**File:** `dashboard/app_enhanced.py`, top of `main()` function

```python
# Add this line to change refresh interval
# Current: 2 seconds
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=2000, key="dashboard_refresh")

# Faster updates (1 second):
st_autorefresh(interval=1000, key="dashboard_refresh")

# Slower updates (5 seconds):
st_autorefresh(interval=5000, key="dashboard_refresh")
```

---

## 🔐 7. Add More Users Programmatically

**File:** `dashboard/auth.py`, in `DEFAULT_USERS`:

```python
DEFAULT_USERS = {
    'admin': {
        'password_hash': 'admin_hash_here',
        'role': 'admin'
    },
    'user': {
        'password_hash': 'user_hash_here',
        'role': 'user'
    },
    'observer': {                    # New user
        'password_hash': 'observer_hash_here',
        'role': 'user'
    },
    'manager': {                     # New user
        'password_hash': 'manager_hash_here',
        'role': 'admin'
    }
}
```

Or create users via dashboard (Admin → Settings → Create User)

---

## 📋 8. Customize Role Permissions

### Create Custom Roles

**File:** `dashboard/auth.py`, line 33-56

Add new permission set:
```python
PERMISSIONS = {
    'admin': {
        'view_dashboard': True,
        'view_logs': True,
        'view_settings': True,
        'modify_settings': True,
        'start_nodes': True,
        'stop_nodes': True,
        'simulate_attack': True,
        'export_data': True,
        'manage_users': True,
        'view_keystores': True,
    },
    'user': {
        'view_dashboard': True,
        'view_logs': True,
        'view_settings': True,
        'modify_settings': False,
        'start_nodes': False,
        'stop_nodes': False,
        'simulate_attack': False,
        'export_data': True,
        'manage_users': False,
        'view_keystores': False,
    },
    'operator': {                    # New role
        'view_dashboard': True,
        'view_logs': True,
        'view_settings': False,
        'modify_settings': False,
        'start_nodes': True,         # Can start nodes
        'stop_nodes': True,          # Can stop nodes
        'simulate_attack': False,
        'export_data': True,
        'manage_users': False,
        'view_keystores': False,
    }
}
```

Then update dashboard to use permission:
```python
if st.session_state.auth_manager.has_permission(st.session_state.username, 'start_nodes'):
    # Show "Start Node" button
```

---

## 🌍 9. Configure MQTT Topics

### Custom Topic Names

**File:** `dashboard/mqtt_monitor.py`, line ~90-95

```python
# Current subscriptions
self.client.subscribe("smartcity/+/session_key")
self.client.subscribe("smartcity/+/data")
self.client.subscribe("smartcity/security/events")

# Custom topics
self.client.subscribe("mycompany/+/session_key")
self.client.subscribe("mycompany/+/data")
self.client.subscribe("mycompany/security/events")
```

---

## 🐳 10. Docker Configuration

### Change Dashboard Port

**File:** `docker-compose.yml`, dashboard service

```yaml
dashboard:
  ports:
    - "0.0.0.0:3000:8501"  # Change 3000 to any port you want
```

### Change MQTT Port

**File:** `docker-compose.yml`, mosquitto service

```yaml
mosquitto:
  ports:
    - "0.0.0.0:1884:1883"  # External port 1884 → Internal 1883
    - "0.0.0.0:9002:9001"  # WebSocket on 9002
```

### Restrict Access to Specific IP

```yaml
# Only allow from 192.168.1.x network
ports:
  - "192.168.1.100:8501:8501"
  - "192.168.1.100:1883:1883"
```

### Add Resource Limits

```yaml
dashboard:
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 512M
      reservations:
        cpus: '0.5'
        memory: 256M
```

---

## 📝 11. MQTT Broker Configuration

### Enable Authentication

**File:** `docker/mosquitto/config/mosquitto.conf`

```
# Add username/password protection
allow_anonymous false
password_file /mosquitto/config/pw.txt

# To create password file:
# docker-compose exec mosquitto mosquitto_passwd -c /mosquitto/config/pw.txt username
```

### Enable TLS/SSL

```
# In mosquitto.conf
listener 8883 0.0.0.0
protocol mqtt
cafile /mosquitto/config/ca.crt
certfile /mosquitto/config/server.crt
keyfile /mosquitto/config/server.key
```

Then update docker-compose.yml to mount certificates:
```yaml
volumes:
  - ./docker/mosquitto/certs:/mosquitto/config
```

---

## 🔍 12. Environment Variables

### Create .env File

**File:** `.env` (in project root)

```env
# MQTT Configuration
BROKER_HOST=mosquitto
BROKER_PORT=1883
BROKER_USERNAME=
BROKER_PASSWORD=
BROKER_USE_TLS=false

# Dashboard
DASHBOARD_PORT=8501
DASHBOARD_THEME=light

# Logging
LOG_LEVEL=INFO
DEBUG=false

# Security
SESSION_TIMEOUT=86400  # 24 hours
```

Then load in docker-compose.yml:
```yaml
env_file:
  - .env
```

---

## 🚀 Deployment-Specific Configurations

### Development
```toml
# .streamlit/config.toml
[logger]
level = "debug"

[client]
showErrorDetails = true
```

### Production
```toml
[logger]
level = "warning"

[client]
showErrorDetails = false
toolbarMode = "viewer"  # Hide code and settings

[server]
enableCORS = false
enableXsrfProtection = true
```

---

## ✅ Configuration Checklist

- [ ] Changed default passwords (if production)
- [ ] Customized colors and branding
- [ ] Set correct MQTT broker host/port
- [ ] Configured refresh rates
- [ ] Set up resource limits (if needed)
- [ ] Tested authentication with new credentials
- [ ] Verified dashboard loads with custom settings
- [ ] Tested network access with custom ports
- [ ] Configured firewall for new ports (if changed)

---

## 📞 Getting Help

For each configuration:
1. Make a backup: `docker-compose down -v` (if safe)
2. Edit the file
3. Rebuild: `docker-compose build --no-cache`
4. Restart: `docker-compose up -d`
5. Test: `docker-compose logs -f dashboard`

---

**Need more help?** Check [DEPLOYMENT.md](DEPLOYMENT.md) or [QUICK_START.md](QUICK_START.md)
