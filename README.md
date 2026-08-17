# QKD Cyber Defense Operations Center

A high-density, mission-critical Streamlit dashboard simulating a Smart City IoT Network secured by **BB84 Quantum Key Distribution (QKD)**. Designed as a professional SOC (Security Operations Center) terminal, it demonstrates how quantum channels detect and isolate eavesdropping attempts in real-time.

## Features

*   **Integrated BB84 Protocol Simulation:** Mathematically faithful simulation of the BB84 protocol (state preparation, transmission, measurement, sifting, and QBER estimation) entirely within the browser/server process.
*   **Real-time MQTT Telemetry:** Automatically publishes encrypted smart-city sensor data (traffic flow, water utility, surveillance cameras) to a public MQTT broker (`broker.emqx.io`).
*   **Threat Engine (Eve Eavesdropper):** Target a specific node (e.g., Surveillance Camera) with an intercept-resend attack. Watch the Quantum Bit Error Rate (QBER) spike above the 11% security threshold and automatically abort the key exchange.
*   **Cryptographic Pinging:** Send cryptographic challenges to nodes to prove their secure status. Compromised nodes lose their encryption keys and will fail the challenge.
*   **Active Countermeasures:** Failsafe mechanisms such as "Quantum Rerouting" and "Standby Node Provisioning" to restore network continuity when an attack is detected.

## Getting Started

### Local Deployment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Cloud Deployment
This repository is configured for immediate deployment on **Streamlit Community Cloud** or **Render**. 
- To deploy on Render, connect your GitHub repository and it will automatically build using the included `Dockerfile` and `render.yaml`.

## Technical Architecture
- **Frontend:** Streamlit with custom injected CSS, utilizing `JetBrains Mono` for a tactile, monospace cryptographic terminal aesthetic. No external frontend dependencies.
- **Backend Simulation:** Custom lightweight NumPy/Python implementation of BB84 and AES-256 payload encryption.
- **Message Broker:** `paho-mqtt` continuously broadcasting JSON payloads to `broker.emqx.io`.
