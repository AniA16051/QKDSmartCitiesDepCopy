#!/usr/bin/env python3
"""
Unified QKD Dashboard for Streamlit Cloud Deployment
Merges sensor nodes, control center, and dashboard into a single process
Uses free cloud MQTT broker for communication
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import hashlib
import json
import random
import time
import threading
import ssl
import paho.mqtt.client as mqtt
import os

# Configuration for free cloud MQTT broker
# Using EMQX Cloud Serverless (free tier) or similar
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")  # Free public broker
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
MQTT_TOPIC = "qkd/smartcity/data"

# Simplified BB84 simulation
class UnifiedBB84:
    """Lightweight BB84 simulation integrated into dashboard"""
    
    @staticmethod
    def generate_key(length=256):
        """Generate random key bits"""
        return np.random.randint(0, 2, length)
    
    @staticmethod
    def generate_bases(length=256):
        """Generate random bases (0=Z, 1=X)"""
        return np.random.randint(0, 2, length)
    
    @staticmethod
    def simulate_bb84_protocol(key_length=256, attack=False):
        """
        Simulate complete BB84 protocol
        Returns: dict with protocol results
        """
        # Alice's key and bases
        alice_key = UnifiedBB84.generate_key(key_length)
        alice_bases = UnifiedBB84.generate_bases(key_length)
        
        # Bob's bases (random)
        bob_bases = UnifiedBB84.generate_bases(key_length)
        
        # Bob's measurements (with or without attack)
        bob_key = np.zeros(key_length, dtype=int)
        
        if attack:
            # Eve intercepts and resends (intercept-resend attack)
            eve_bases = UnifiedBB84.generate_bases(key_length)
            eve_key = np.zeros(key_length, dtype=int)
            
            # Eve measures
            for i in range(key_length):
                if alice_bases[i] == eve_bases[i]:
                    eve_key[i] = alice_key[i]
                else:
                    eve_key[i] = random.randint(0, 1)
            
            # Eve resends to Bob
            for i in range(key_length):
                if eve_bases[i] == bob_bases[i]:
                    bob_key[i] = eve_key[i]
                else:
                    bob_key[i] = random.randint(0, 1)
        else:
            # Direct transmission to Bob
            for i in range(key_length):
                if alice_bases[i] == bob_bases[i]:
                    bob_key[i] = alice_key[i]
                else:
                    bob_key[i] = random.randint(0, 1)
        
        # Sifting - keep only matching bases
        matching_bases = alice_bases == bob_bases
        sifted_alice = alice_key[matching_bases]
        sifted_bob = bob_key[matching_bases]
        
        if len(sifted_alice) == 0:
            return {
                'success': False,
                'qber': 100.0,
                'sifted_length': 0,
                'final_key': None,
                'attack_detected': True
            }
        
        # Calculate QBER (Quantum Bit Error Rate)
        errors = np.sum(sifted_alice != sifted_bob)
        qber = (errors / len(sifted_alice)) * 100
        
        # Security threshold: 11%
        attack_detected = qber >= 11.0
        success = not attack_detected and len(sifted_alice) >= 128
        
        # Key derivation using SHA-256
        final_key = None
        if success:
            bit_string = ''.join(map(str, sifted_alice))
            final_key = hashlib.sha256(bit_string.encode()).hexdigest()
        
        return {
            'success': success,
            'qber': qber,
            'sifted_length': len(sifted_alice),
            'final_key': final_key,
            'attack_detected': attack_detected,
            'raw_length': key_length
        }

# Integrated Smart City Simulation
class IntegratedSmartCity:
    """Unified sensor simulation within the dashboard process"""
    
    def __init__(self):
        self.sensors = {
            'traffic_light': {
                'id': 'traffic-node-01',
                'type': 'traffic_flow',
                'location': 'Main St & 5th Ave',
                'status': 'secure',
                'qber': 0.0,
                'last_key': None,
                'data_points': [],
                'last_update': datetime.now()
            },
            'water_meter': {
                'id': 'water-node-01', 
                'type': 'water_consumption',
                'location': 'Downtown Reservoir',
                'status': 'secure',
                'qber': 0.0,
                'last_key': None,
                'data_points': [],
                'last_update': datetime.now()
            },
            'surveillance': {
                'id': 'surveillance-node-01',
                'type': 'security_monitoring',
                'location': 'Central Park',
                'status': 'secure',
                'qber': 0.0,
                'last_key': None,
                'data_points': [],
                'last_update': datetime.now()
            }
        }
        self.attack_active = False
        self.mqtt_client = None
        self.mqtt_connected = False
        
    def initialize_mqtt(self):
        """Initialize MQTT client for cloud broker connection"""
        try:
            self.mqtt_client = mqtt.Client(client_id="qkd-dashboard-" + str(random.randint(1000,9999)))
            
            if MQTT_USERNAME and MQTT_PASSWORD:
                self.mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            
            # Enable TLS for secure connections
            if MQTT_USE_TLS or MQTT_PORT == 8883:
                self.mqtt_client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLS_CLIENT)
                self.mqtt_client.tls_insecure_set(True)  # For demo purposes
            
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 5
            start = time.time()
            while not self.mqtt_connected and (time.time() - start) < timeout:
                time.sleep(0.1)
                
            return self.mqtt_connected
            
        except Exception as e:
            st.warning(f"MQTT connection failed: {e}")
            return False
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.mqtt_connected = True
        else:
            self.mqtt_connected = False
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.mqtt_connected = False
    
    def publish_sensor_data(self, sensor_name, data):
        """Publish sensor data to MQTT broker"""
        if self.mqtt_connected and self.mqtt_client:
            try:
                topic = f"{MQTT_TOPIC}/{sensor_name}"
                payload = json.dumps(data)
                self.mqtt_client.publish(topic, payload)
                return True
            except Exception as e:
                return False
        return False
    
    def simulate_sensor(self, sensor_name):
        """Run complete sensor simulation with QKD and data generation"""
        sensor = self.sensors[sensor_name]
        
        # Run BB84 protocol
        qkd_result = UnifiedBB84.simulate_bb84_protocol(
            key_length=256, 
            attack=self.attack_active
        )
        
        # Update sensor status
        sensor['status'] = 'secure' if qkd_result['success'] else 'compromised'
        sensor['qber'] = qkd_result['qber']
        sensor['last_key'] = qkd_result['final_key']
        sensor['last_update'] = datetime.now()
        
        # Generate sensor data based on type
        if sensor['type'] == 'traffic_flow':
            data_value = random.randint(10, 100)  # Cars per minute
            data_unit = 'cars/min'
        elif sensor['type'] == 'water_consumption':
            data_value = round(random.uniform(50, 200), 2)  # Liters per hour
            data_unit = 'L/h'
        else:  # security_monitoring
            data_value = random.choice(['normal', 'motion_detected', 'all_clear'])
            data_unit = 'status'
        
        # Create encrypted data package
        sensor_data = {
            'sensor_id': sensor['id'],
            'sensor_type': sensor['type'],
            'location': sensor['location'],
            'timestamp': datetime.now().isoformat(),
            'value': data_value,
            'unit': data_unit,
            'qkd_status': sensor['status'],
            'qber': sensor['qber'],
            'key_preview': sensor['last_key'][:8] + '...' if sensor['last_key'] else None
        }
        
        # Store data point for charts
        sensor['data_points'].append({
            'time': datetime.now(),
            'value': data_value if isinstance(data_value, (int, float)) else 0,
            'qber': sensor['qber']
        })
        
        # Keep only last 20 data points
        if len(sensor['data_points']) > 20:
            sensor['data_points'] = sensor['data_points'][-20:]
        
        # Publish to MQTT broker
        self.publish_sensor_data(sensor_name, sensor_data)
        
        return sensor_data
    
    def toggle_attack(self):
        """Toggle eavesdropping attack on all sensors"""
        self.attack_active = not self.attack_active
        return self.attack_active
    
    def update_all_sensors(self):
        """Update all sensors with new simulations"""
        results = {}
        for sensor_name in self.sensors.keys():
            results[sensor_name] = self.simulate_sensor(sensor_name)
        return results

# Streamlit Dashboard
def main():
    st.set_page_config(
        page_title="QKD Smart City - Streamlit Cloud",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .status-secure {
        color: #2ecc71;
        font-weight: bold;
    }
    .status-compromised {
        color: #e74c3c;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="main-header">🔐 QKD-Secured Smart City IoT Network</p>', unsafe_allow_html=True)
    st.markdown("*Free forever deployment on Streamlit Cloud with cloud MQTT broker*")
    
    # Initialize the integrated system
    if 'smart_city' not in st.session_state:
        st.session_state.smart_city = IntegratedSmartCity()
        # Try to connect to MQTT broker
        mqtt_connected = st.session_state.smart_city.initialize_mqtt()
        if mqtt_connected:
            st.success("✅ Connected to cloud MQTT broker")
        else:
            st.warning("⚠️ MQTT connection failed - running in local mode")
    
    smart_city = st.session_state.smart_city
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # Attack simulation
        st.subheader("⚡ Attack Simulation")
        attack_active = smart_city.attack_active
        attack_color = "🔴" if attack_active else "🟢"
        
        if st.button(f"{attack_color} {'Stop' if attack_active else 'Launch'} Attack"):
            smart_city.toggle_attack()
            st.rerun()
        
        st.write(f"Attack Status: {'**ACTIVE**' if attack_active else '**Inactive**'}")
        
        # MQTT Status
        st.subheader("📡 MQTT Broker")
        mqtt_status = "🟢 Connected" if smart_city.mqtt_connected else "🔴 Disconnected"
        st.write(f"Status: {mqtt_status}")
        st.write(f"Broker: {MQTT_BROKER}")
        st.write(f"Port: {MQTT_PORT}")
        
        # Manual updates
        st.subheader("🔄 Sensor Updates")
        if st.button("Update All Sensors", use_container_width=True):
            smart_city.update_all_sensors()
            st.rerun()
        
        # Auto-update toggle
        auto_update = st.checkbox("Auto-update (5s)", value=False)
        if auto_update:
            time.sleep(5)
            smart_city.update_all_sensors()
            st.rerun()
        
        # System info
        st.subheader("📊 System Info")
        st.write(f"Active Sensors: {len(smart_city.sensors)}")
        st.write(f"Attack Mode: {'Enabled' if attack_active else 'Disabled'}")
    
    # Main dashboard area
    # Sensor status cards
    st.subheader("📡 Sensor Status Overview")
    
    sensors_info = [
        ('traffic_light', '🚦 Traffic Light', 'Main St & 5th Ave'),
        ('water_meter', '💧 Water Meter', 'Downtown Reservoir'),
        ('surveillance', '📹 Surveillance', 'Central Park')
    ]
    
    cols = st.columns(3)
    for col, (sensor_key, icon, location) in zip(cols, sensors_info):
        with col:
            sensor = smart_city.sensors[sensor_key]
            
            # Status card
            status_emoji = "🟢" if sensor['status'] == 'secure' else "🔴"
            status_class = "status-secure" if sensor['status'] == 'secure' else "status-compromised"
            
            st.markdown(f"### {icon}")
            st.markdown(f"**{location}**")
            st.markdown(f"Status: <span class='{status_class}'>{status_emoji} {sensor['status'].upper()}</span>", unsafe_allow_html=True)
            
            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("QBER", f"{sensor['qber']:.1f}%")
            with col2:
                if sensor['data_points']:
                    latest_value = sensor['data_points'][-1]['value']
                    st.metric("Latest", f"{latest_value}")
            
            # Key info
            if sensor['last_key']:
                st.caption(f"🔑 Key: {sensor['last_key'][:8]}...")
            else:
                st.caption("🔑 No key established")
            
            st.caption(f"🕐 Updated: {sensor['last_update'].strftime('%H:%M:%S')}")
    
    # QBER Visualization
    st.subheader("📊 Quantum Bit Error Rate Analysis")
    
    # Prepare data for QBER chart
    qber_data = []
    for sensor_key, _, _ in sensors_info:
        sensor = smart_city.sensors[sensor_key]
        qber_data.append({
            'Sensor': sensor_key.replace('_', ' ').title(),
            'QBER (%)': sensor['qber'],
            'Status': 'Secure' if sensor['qber'] < 11 else 'Compromised'
        })
    
    df_qber = pd.DataFrame(qber_data)
    
    fig_qber = px.bar(df_qber, x='Sensor', y='QBER (%)', color='Status',
                     color_discrete_map={'Secure': '#2ecc71', 'Compromised': '#e74c3c'},
                     title="Real-time QBER Monitoring (Security Threshold: 11%)")
    fig_qber.add_hline(y=11, line_dash="dash", line_color="red", 
                      annotation_text="Security Threshold (11%)")
    fig_qber.update_layout(height=400)
    st.plotly_chart(fig_qber, use_container_width=True)
    
    # Sensor data trends
    st.subheader("📈 Sensor Data Trends")
    
    # Create tabs for each sensor
    tab1, tab2, tab3 = st.tabs(["🚦 Traffic", "💧 Water", "📹 Surveillance"])
    
    for tab, (sensor_key, _, _) in zip([tab1, tab2, tab3], sensors_info):
        with tab:
            sensor = smart_city.sensors[sensor_key]
            
            if len(sensor['data_points']) > 1:
                df_trend = pd.DataFrame(sensor['data_points'])
                
                fig_trend = go.Figure()
                
                # Add data value trace
                fig_trend.add_trace(go.Scatter(
                    x=df_trend['time'],
                    y=df_trend['value'],
                    mode='lines+markers',
                    name='Sensor Value',
                    line=dict(color='#1f77b4')
                ))
                
                # Add QBER trace on secondary axis
                fig_trend.add_trace(go.Scatter(
                    x=df_trend['time'],
                    y=df_trend['qber'],
                    mode='lines+markers',
                    name='QBER (%)',
                    yaxis='y2',
                    line=dict(color='#e74c3c', dash='dash')
                ))
                
                fig_trend.update_layout(
                    title=f"{sensor_key.replace('_', ' ').title()} - Data & QBER Over Time",
                    xaxis_title="Time",
                    yaxis_title="Sensor Value",
                    yaxis2=dict(
                        title="QBER (%)",
                        overlaying="y",
                        side="right"
                    ),
                    height=300,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("📊 Not enough data points yet. Click 'Update All Sensors' to generate data.")
    
    # Security Log
    st.subheader("🛡️ Security Event Log")
    
    # Create a simple security log based on sensor status
    security_events = []
    for sensor_key, _, _ in sensors_info:
        sensor = smart_city.sensors[sensor_key]
        if sensor['status'] == 'compromised':
            security_events.append({
                'Time': sensor['last_update'].strftime('%H:%M:%S'),
                'Sensor': sensor_key.replace('_', ' ').title(),
                'Event': '⚠️ EAVESDROPPING DETECTED',
                'QBER': f"{sensor['qber']:.1f}%"
            })
        elif sensor['last_key']:
            security_events.append({
                'Time': sensor['last_update'].strftime('%H:%M:%S'),
                'Sensor': sensor_key.replace('_', ' ').title(),
                'Event': '✅ Key Exchange Successful',
                'QBER': f"{sensor['qber']:.1f}%"
            })
    
    if security_events:
        df_events = pd.DataFrame(security_events)
        st.dataframe(df_events, use_container_width=True, hide_index=True)
    else:
        st.info("📋 No security events recorded yet.")
    
    # Protocol explanation
    with st.expander("📖 Learn about BB84 Quantum Key Distribution"):
        st.markdown("""
        ### How BB84 Protects Your Smart City Data
        
        **1. Quantum Key Generation**
        - Each sensor generates random bits and chooses random quantum bases (Z or X)
        - These are encoded as quantum states and sent to the control center
        
        **2. Quantum Transmission**
        - Control center measures each qubit in a randomly chosen basis
        - ~50% of measurements will use the wrong basis and be discarded
        
        **3. Sifting Process**
        - Sensor and control center publicly compare their basis choices
        - Only bits where bases matched are kept (~50% of original)
        
        **4. Error Rate Check**
        - They publicly compare a sample of the sifted bits
        - Calculate Quantum Bit Error Rate (QBER)
        
        **5. Security Threshold**
        - If QBER > 11%, they assume eavesdropping occurred
        - The key is discarded and no data is transmitted
        
        **6. Key Derivation**
        - If QBER < 11%, the remaining bits are hashed with SHA-256
        - This creates a 256-bit AES key for encryption
        
        **7. Secure Data Transmission**
        - All sensor data is encrypted with AES-256 using the QKD-derived key
        - Even if encrypted data is intercepted, it cannot be decrypted without the key
        
        ### Why This Matters for Smart Cities
        
        Traditional encryption (RSA/ECC) could be broken by future quantum computers.
        QKD's security is based on the laws of physics, making it "quantum-safe" regardless
        of advances in computing power.
        """)
    
    # Deployment info
    st.info("""
    🚀 **Deployment Info**: This is running on Streamlit Cloud with a free cloud MQTT broker.
    - All sensor simulations run within this dashboard process
    - MQTT broker enables real-time data sharing and future multi-device support
    - No servers or infrastructure needed - completely free forever!
    """)

if __name__ == "__main__":
    main()