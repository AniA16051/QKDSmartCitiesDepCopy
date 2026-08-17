# Streamlit Cloud Deployment Guide

## 🚀 Free Forever Deployment on Streamlit Cloud

This guide shows how to deploy the QKD Smart City dashboard to Streamlit Cloud completely free, with no infrastructure costs.

## 📋 Prerequisites

- GitHub account
- Streamlit Cloud account (free at [streamlit.io/cloud](https://streamlit.io/cloud))
- This repository pushed to GitHub

## 🛠️ Architecture Overview

**Single-Process Design:**
- All sensor nodes merged into the dashboard process
- No Docker or complex infrastructure needed
- Uses free cloud MQTT broker for real-time communication
- Lightweight BB84 simulation (no heavy Qiskit dependencies)
- Completely free forever on Streamlit Cloud

**Components:**
- **Unified Dashboard**: Merges sensor simulation, control center, and visualization
- **Cloud MQTT Broker**: Uses free public broker (broker.emqx.io) or your own free EMQX Cloud instance
- **Simplified QKD**: Lightweight BB84 simulation optimized for cloud deployment

## 📦 Deployment Steps

### 1. Prepare Your Repository

1. **Push this code to GitHub:**
   ```bash
   git add .
   git commit -m "Add Streamlit Cloud deployment"
   git push origin main
   ```

2. **Ensure these files are in your repo:**
   - `app.py` (the main application file)
   - `requirements_streamlit.txt` (dependencies)
   - `.streamlit/config.toml` (Streamlit configuration)

### 2. Deploy to Streamlit Cloud

1. **Go to [share.streamlit.io](https://share.streamlit.io)**
2. **Click "New app"**
3. **Connect your GitHub account** if not already connected
4. **Select your repository** and branch (usually `main`)
5. **Set the main file path to:** `app.py`
6. **Click "Deploy"**

Streamlit Cloud will automatically:
- Install dependencies from `requirements_streamlit.txt`
- Deploy the app to their free cloud infrastructure
- Provide a public URL

### 3. Configure MQTT Broker (Optional)

The app works with the default free public broker, but you can configure your own:

**Option A: Use Free Public Broker (Default)**
- No configuration needed
- Uses `broker.emqx.io` (free public MQTT broker)
- Works immediately

**Option B: Use EMQX Cloud Free Tier**

1. **Sign up at [cloud.emqx.com](https://cloud.emqx.com)**
2. **Create a Serverless deployment** (free tier)
3. **Get connection details from Deployment Overview:**
   - Broker address (from MQTT Connection Information)
   - Port: `8883` (TLS/SSL) or `8084` (WebSocket TLS)
   - Username/password (from Access Control)

4. **Add environment variables in Streamlit Cloud:**
   - Go to your app → Settings → Secrets
   - Add these secrets:
     ```
     MQTT_BROKER=your-emqx-broker-address
     MQTT_PORT=8883
     MQTT_USERNAME=your-username
     MQTT_PASSWORD=your-password
     MQTT_USE_TLS=true
     ```

### 4. Access Your Dashboard

After deployment, Streamlit Cloud will provide a URL like:
```
https://your-app-name.streamlit.app
```

## 🔧 Configuration Options

### Environment Variables

Configure these in Streamlit Cloud → Settings → Secrets:

```bash
# MQTT Broker Configuration
MQTT_BROKER=broker.emqx.io          # Default free public broker
MQTT_PORT=1883                      # Default port (use 8883 for TLS)
MQTT_USERNAME=                      # Leave empty for public broker
MQTT_PASSWORD=                      # Leave empty for public broker
MQTT_USE_TLS=false                  # Set to true for EMQX Cloud (port 8883)
```

### Streamlit Configuration

Edit `.streamlit/config.toml` to customize:

```toml
[general]
title = "Your Custom Title"

[theme]
primaryColor = "#your-color"
```

## 🎯 Features

### Real-time Sensor Simulation
- **Traffic Light**: Monitors traffic flow (cars/minute)
- **Water Meter**: Tracks water consumption (L/hour)  
- **Surveillance**: Security monitoring status

### QKD Security Features
- **BB84 Protocol Simulation**: Lightweight quantum key distribution
- **QBER Monitoring**: Real-time Quantum Bit Error Rate tracking
- **Attack Detection**: Automatic eavesdropping detection
- **Key Derivation**: SHA-256 based key generation

### Interactive Controls
- **Attack Simulation**: Launch/stop eavesdropping attacks
- **Live Updates**: Manual or auto-update sensor data
- **MQTT Integration**: Real-time data publishing to cloud broker
- **Visual Analytics**: Interactive charts and security logs

## 📊 Usage

### Basic Operation
1. **Open your dashboard URL**
2. **Click "Update All Sensors"** to generate initial data
3. **Enable "Auto-update"** for continuous monitoring
4. **Use "Launch Attack"** to simulate eavesdropping

### MQTT Data Format
The app publishes sensor data to MQTT topic `qkd/smartcity/data/{sensor_name}`:

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

## 🔒 Security Considerations

### Free Tier Limitations
- **Public Broker**: Default broker is public, suitable for demos
- **No Authentication**: Public broker doesn't require credentials
- **Shared Resources**: Free tier has resource limits

### Production Recommendations
- **Use Private Broker**: Set up EMQX Cloud with authentication
- **Enable TLS**: Use port 8883 with SSL/TLS
- **Add Authentication**: Configure username/password
- **Monitor Resources**: Watch for free tier limits

## 🐛 Troubleshooting

### MQTT Connection Issues
**Problem**: "MQTT connection failed" warning
**Solution**: 
- Use default public broker (no config needed)
- Or configure your own EMQX Cloud instance correctly

### App Not Updating
**Problem**: Data not refreshing
**Solution**:
- Click "Update All Sensors" manually
- Enable "Auto-update" checkbox
- Check browser console for errors

### Deployment Failures
**Problem**: Streamlit Cloud deployment fails
**Solution**:
- Ensure `app.py` is in repository root
- Check `requirements_streamlit.txt` is valid
- Verify all files are pushed to GitHub

## 📈 Scaling Options

### Beyond Free Tier
When you need more resources:

1. **Streamlit Cloud Pro**: More resources and priority support
2. **Multi-instance**: Deploy multiple instances for load balancing
3. **Private MQTT**: Use dedicated MQTT broker for better performance
4. **Database Integration**: Add persistent storage for historical data

### Advanced Features
- **Real WebSocket**: Enable real-time updates across multiple users
- **Authentication**: Add user authentication for access control
- **Custom Broker**: Deploy your own MQTT infrastructure
- **Data Persistence**: Add database for long-term data storage

## 🎉 Advantages of This Approach

### Cost Benefits
- **100% Free**: No infrastructure costs ever
- **No Servers**: No server management required
- **Auto-scaling**: Streamlit Cloud handles scaling automatically

### Technical Benefits
- **Simple Architecture**: Single process, no complexity
- **Easy Maintenance**: Minimal dependencies and configuration
- **Fast Deployment**: Deploy in minutes with GitHub integration

### Educational Benefits
- **Accessible**: Easy to share with students and researchers
- **Interactive**: Real-time demonstrations of QKD concepts
- **Visual**: Clear visualization of quantum security principles

## 📚 Additional Resources

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-cloud)
- [EMQX Cloud Free Tier](https://www.emqx.com/en/cloud/pricing)
- [MQTT Protocol Info](https://mqtt.org/)
- [BB84 Protocol Details](https://en.wikipedia.org/wiki/BB84)

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Streamlit Cloud logs in the dashboard
3. Test MQTT connection using online MQTT clients
4. Check environment variables in Streamlit Cloud settings

---

**Ready to deploy?** Push your code to GitHub and deploy to Streamlit Cloud in minutes! 🚀