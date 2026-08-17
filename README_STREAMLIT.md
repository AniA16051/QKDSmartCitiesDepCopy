# 🔐 QKD Smart City Dashboard - Streamlit Cloud Deployment

A free forever deployment of a Quantum Key Distribution (QKD) secured smart city IoT network simulation, running on Streamlit Cloud with cloud MQTT broker integration.

## ✨ Features

- **🎯 Single-Process Architecture**: All components merged into one dashboard - no Docker complexity
- **🆓 Completely Free**: Runs on Streamlit Cloud free tier forever
- **📡 Cloud MQTT Integration**: Real-time communication via free cloud MQTT broker
- **🔬 Lightweight QKD**: Simplified BB84 simulation optimized for cloud deployment
- **📊 Real-time Dashboard**: Live sensor monitoring with security analytics
- **⚡ Attack Simulation**: Interactive eavesdropping detection demonstration
- **📈 Visual Analytics**: Interactive charts showing QBER and sensor data trends

## 🚀 Quick Start

### 1. Deploy to Streamlit Cloud (5 minutes)

1. **Fork/clone this repository**
2. **Push to your GitHub account**
3. **Go to [share.streamlit.io](https://share.streamlit.io)**
4. **Click "New app" and connect your GitHub**
5. **Select your repository and click "Deploy"**

That's it! Your dashboard will be live at `https://your-app.streamlit.app`

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements_streamlit.txt

# Run locally
streamlit run app.py
```

## 📋 What's Included

- **`app.py`**: Main unified dashboard application
- **`requirements_streamlit.txt`**: Minimal dependencies for cloud deployment
- **`.streamlit/config.toml`**: Streamlit configuration
- **`STREAMLIT_CLOUD_DEPLOYMENT.md`**: Detailed deployment guide

## 🎛️ Dashboard Features

### Sensor Monitoring
- **🚦 Traffic Light**: Traffic flow monitoring (cars/minute)
- **💧 Water Meter**: Water consumption tracking (L/hour)
- **📹 Surveillance**: Security status monitoring

### QKD Security
- **BB84 Protocol**: Quantum key distribution simulation
- **QBER Tracking**: Real-time quantum bit error rate monitoring
- **Attack Detection**: Automatic eavesdropping detection (>11% QBER threshold)
- **Key Management**: SHA-256 based key derivation

### Interactive Controls
- **Attack Simulation**: Launch/stop eavesdropping attacks
- **Live Updates**: Manual or automatic sensor data refresh
- **MQTT Publishing**: Real-time data to cloud broker
- **Security Logs**: Event tracking and monitoring

## 🔧 Configuration

### MQTT Broker (Optional)

**Default**: Uses free public broker (`broker.emqx.io`) - no configuration needed.

**Custom Broker**: Add these environment variables in Streamlit Cloud → Settings → Secrets:

```bash
MQTT_BROKER=your-broker.example.com
MQTT_PORT=1883
MQTT_USERNAME=your-username
MQTT_PASSWORD=your-password
```

### Streamlit Settings

Edit `.streamlit/config.toml` to customize appearance and behavior.

## 📊 MQTT Data Format

Sensor data is published to `qkd/smartcity/data/{sensor_name}`:

```json
{
  "sensor_id": "traffic-node-01",
  "sensor_type": "traffic_flow",
  "location": "Main St & 5th Ave", 
  "timestamp": "2024-01-01T12:00:00",
  "value": 45,
  "unit": "cars/min",
  "qkd_status": "secure",
  "qber": 2.5,
  "key_preview": "a1b2c3d4..."
}
```

## 🛡️ Security Features

### QKD Protocol Implementation
- **Quantum Key Generation**: Random bit and basis generation
- **Basis Sifting**: ~50% filter rate for matching bases
- **Error Rate Calculation**: QBER computation for security checks
- **Attack Detection**: Automatic eavesdropper identification
- **Key Derivation**: SHA-256 hashing for final encryption keys

### Attack Simulation
- **Intercept-Resend**: Simulates Eve's eavesdropping attack
- **QBER Impact**: Attack increases QBER to ~25% average
- **Security Response**: Automatic key rejection when QBER > 11%

## 📈 Performance

### Resource Usage
- **Memory**: ~200-300MB (well within free tier limits)
- **CPU**: Minimal load, efficient single-process design
- **Network**: Lightweight MQTT messaging

### Free Tier Limits
- **Streamlit Cloud**: Generous free tier for hobby projects
- **MQTT Broker**: Free public broker or EMQX Cloud serverless
- **No Time Limits**: Runs forever without expiration

## 🎓 Educational Use

Perfect for:
- **Quantum Security Education**: Demonstrating QKD principles
- **Smart City Research**: IoT security visualization
- **Classroom Demos**: Interactive security concepts
- **Research Prototypes**: Quick deployment and testing

## 🔍 Troubleshooting

### MQTT Connection Issues
- **Warning**: "MQTT connection failed" 
- **Solution**: App works fine in local mode without MQTT

### Deployment Issues
- **Problem**: Streamlit Cloud deployment fails
- **Solution**: Ensure `app.py` is in repo root and dependencies are correct

### Data Not Updating
- **Problem**: Charts not refreshing
- **Solution**: Click "Update All Sensors" or enable auto-update

## 📚 Documentation

- **Deployment Guide**: See `STREAMLIT_CLOUD_DEPLOYMENT.md` for detailed instructions
- **MQTT Setup**: Information on configuring custom MQTT brokers
- **Architecture**: Details on the unified single-process design

## 🌟 Advantages

### Over Traditional Deployment
- **No Infrastructure**: No servers, Docker, or DevOps needed
- **Zero Cost**: 100% free with no hidden charges
- **Instant Setup**: Deploy in minutes via GitHub
- **Auto-scaling**: Streamlit Cloud handles scaling automatically
- **Easy Sharing**: Simple URL sharing with students/colleagues

### Over Original Architecture
- **Simplified**: Removed heavy Qiskit dependencies
- **Unified**: Single process instead of multi-container Docker
- **Cloud-native**: Designed specifically for cloud deployment
- **Resource-efficient**: Optimized for free tier constraints

## 🚀 Next Steps

1. **Deploy Now**: Push to GitHub and deploy to Streamlit Cloud
2. **Customize**: Modify sensors, add new data types
3. **Integrate**: Connect to real MQTT brokers for multi-user demos
4. **Extend**: Add authentication, databases, or additional features

## 📄 License

This is a educational project demonstrating QKD concepts for smart city IoT security.

## 🤝 Contributing

Feel free to fork, modify, and use for educational purposes!

---

**Ready to deploy?** Get your free QKD dashboard running in minutes! 🎉