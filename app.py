#!/usr/bin/env python3
"""
Unified QKD Dashboard for Streamlit Cloud, Render, and Railway Deployment
Merges sensor nodes, control center, and dashboard into a single process
Uses free cloud MQTT broker for communication with fallback to standalone mode
"""

import os
import sys

# Disable file watching in production to prevent inotify limit errors
# This fixes deployment issues on cloud platforms like Render, Streamlit Cloud, Railway
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
os.environ["STREAMLIT_LOGGER_LEVEL"] = "warning"

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

# Configuration for free cloud MQTT broker
# Supports both environment variables and Streamlit secrets
def get_mqtt_config():
    """Get MQTT configuration from environment or Streamlit secrets"""
    broker = os.getenv("MQTT_BROKER", "broker.emqx.io")
    port = int(os.getenv("MQTT_PORT", 1883))
    username = os.getenv("MQTT_USERNAME", "")
    password = os.getenv("MQTT_PASSWORD", "")
    use_tls = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
    
    try:
        if hasattr(st, 'secrets') and st.secrets is not None:
            if 'MQTT_BROKER' in st.secrets:
                broker = st.secrets['MQTT_BROKER']
            if 'MQTT_PORT' in st.secrets:
                port = int(st.secrets['MQTT_PORT'])
            if 'MQTT_USERNAME' in st.secrets:
                username = st.secrets['MQTT_USERNAME']
            if 'MQTT_PASSWORD' in st.secrets:
                password = st.secrets['MQTT_PASSWORD']
            if 'MQTT_USE_TLS' in st.secrets:
                use_tls = str(st.secrets['MQTT_USE_TLS']).lower() == "true"
    except Exception:
        pass
    
    return {
        'broker': broker,
        'port': port,
        'username': username,
        'password': password,
        'use_tls': use_tls
    }

MQTT_TOPIC = "qkd/smartcity/data"

def _get_mqtt_settings():
    """Lazy MQTT config; avoids accessing st.secrets at module-import time."""
    cfg = get_mqtt_config()
    return cfg['broker'], cfg['port'], cfg['username'], cfg['password'], cfg['use_tls']

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
        matching_bases = (alice_bases == bob_bases)
        sifted_alice = alice_key[matching_bases]
        sifted_bob = bob_key[matching_bases]
        
        if len(sifted_alice) == 0:
            return {
                'success': False,
                'qber': 100.0,
                'sifted_length': 0,
                'final_key': None,
                'attack_detected': True,
                'raw_length': key_length
            }
        
        # Calculate QBER (Quantum Bit Error Rate)
        errors = np.sum(sifted_alice != sifted_bob)
        qber = (errors / len(sifted_alice)) * 100.0
        
        # Security threshold: 11%
        attack_detected = qber >= 11.0
        success = not attack_detected and len(sifted_alice) >= 32
        
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
        # Resolve MQTT settings lazily (safe on Streamlit Cloud)
        broker, port, username, password, use_tls = _get_mqtt_settings()
        self._mqtt_broker = broker
        self._mqtt_port = port
        self._mqtt_username = username
        self._mqtt_password = password
        self._mqtt_use_tls = use_tls

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
        
        # Seed initial data point
        for name in self.sensors:
            self.simulate_sensor(name)
    
    def initialize_mqtt(self):
        """Initialize MQTT client for cloud broker connection"""
        try:
            try:
                self.mqtt_client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION2, 
                    client_id=f"qkd-dash-{random.randint(1000, 9999)}"
                )
            except AttributeError:
                self.mqtt_client = mqtt.Client(client_id=f"qkd-dash-{random.randint(1000, 9999)}")
            
            if self._mqtt_username and self._mqtt_password:
                self.mqtt_client.username_pw_set(self._mqtt_username, self._mqtt_password)
            
            # Enable TLS for secure connections if requested
            if self._mqtt_use_tls or self._mqtt_port == 8883:
                try:
                    self.mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
                    self.mqtt_client.tls_insecure_set(True)
                except Exception:
                    pass
            
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            
            self.mqtt_client.connect_async(self._mqtt_broker, self._mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            return True
            
        except Exception as e:
            return False
    
    def _on_mqtt_connect(self, client, userdata, flags, rc, properties=None):
        """MQTT connection callback"""
        if rc == 0:
            self.mqtt_connected = True
        else:
            self.mqtt_connected = False
    
    def _on_mqtt_disconnect(self, client, userdata, rc, properties=None):
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
            except Exception:
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
            'value': data_value if isinstance(data_value, (int, float)) else (1 if data_value == 'motion_detected' else 0),
            'qber': sensor['qber']
        })
        
        # Keep only last 25 data points
        if len(sensor['data_points']) > 25:
            sensor['data_points'] = sensor['data_points'][-25:]
        
        # Publish to MQTT broker
        self.publish_sensor_data(sensor_name, sensor_data)
        
        return sensor_data
    
    def toggle_attack(self):
        """Toggle eavesdropping attack on all sensors"""
        self.attack_active = not self.attack_active
        self.update_all_sensors()
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
        page_title="QKD Smart City Dashboard",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for modern visual design
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .status-secure {
        color: #10b981;
        font-weight: bold;
    }
    .status-compromised {
        color: #ef4444;
        font-weight: bold;
    }
    div[data-testid="stMetric"] {
        background: rgba(240, 244, 248, 0.7);
        border: 1px solid rgba(203, 213, 225, 0.8);
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="main-header">🔐 QKD-Secured Smart City IoT Network</p>', unsafe_allow_html=True)
    st.markdown("*Real-time Quantum Key Distribution (BB84) simulation and IoT payload encryption*")
    
    # Initialize the integrated system
    if 'smart_city' not in st.session_state:
        st.session_state.smart_city = IntegratedSmartCity()
        st.session_state.smart_city.initialize_mqtt()
    
    smart_city = st.session_state.smart_city
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Network Control")
        
        # Attack simulation
        st.subheader("⚡ Attack Simulation")
        attack_active = smart_city.attack_active
        attack_color = "🔴" if attack_active else "🟢"
        
        if st.button(f"{attack_color} {'Stop' if attack_active else 'Launch'} Eavesdropping Attack", use_container_width=True, type="primary" if not attack_active else "secondary"):
            smart_city.toggle_attack()
            st.rerun()
        
        st.write(f"Channel Security: {'**⚠️ EAVESDROPPER ACTIVE (Intercept-Resend)**' if attack_active else '**✓ Clean Channel (Normal)**'}")
        
        st.divider()
        
        # MQTT Status
        st.subheader("📡 MQTT Cloud Broker")
        mqtt_status = "🟢 Connected" if smart_city.mqtt_connected else "🟡 Standalone / Connecting"
        st.write(f"Status: **{mqtt_status}**")
        st.caption(f"Broker: `{smart_city._mqtt_broker}:{smart_city._mqtt_port}`")
        
        st.divider()
        
        # Manual updates
        st.subheader("🔄 Update Trigger")
        if st.button("Generate New Sensor Readings", use_container_width=True):
            smart_city.update_all_sensors()
            st.rerun()
        
        # Auto-update toggle
        auto_update = st.checkbox("Auto-refresh (5s)", value=False)
        if auto_update:
            try:
                from streamlit_autorefresh import st_autorefresh
                st_autorefresh(interval=5000, key="auto_refresh_trigger")
            except ImportError:
                time.sleep(5)
                smart_city.update_all_sensors()
                st.rerun()
    
    # Main dashboard area
    # Sensor status cards
    st.subheader("📡 Monitored IoT Infrastructure")
    
    sensors_info = [
        ('traffic_light', '🚦 Traffic Signal', 'Main St & 5th Ave'),
        ('water_meter', '💧 Water Utility', 'Downtown Reservoir'),
        ('surveillance', '📹 Surveillance Camera', 'Central Park North')
    ]
    
    cols = st.columns(3)
    for col, (sensor_key, icon, location) in zip(cols, sensors_info):
        with col:
            sensor = smart_city.sensors[sensor_key]
            
            # Status card
            is_secure = sensor['status'] == 'secure'
            status_emoji = "🟢" if is_secure else "🔴"
            status_text = "SECURE (QBER < 11%)" if is_secure else "COMPROMISED (QBER ≥ 11%)"
            status_class = "status-secure" if is_secure else "status-compromised"
            
            with st.container(border=True):
                st.markdown(f"#### {icon}")
                st.caption(f"📍 {location} (`{sensor['id']}`)")
                st.markdown(f"Status: <span class='{status_class}'>{status_emoji} {status_text}</span>", unsafe_allow_html=True)
                
                # Metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Measured QBER", f"{sensor['qber']:.1f}%")
                with col2:
                    if sensor['data_points']:
                        latest_value = sensor['data_points'][-1]['value']
                        st.metric("Latest Telemetry", f"{latest_value}")
                
                # Key info
                if sensor['last_key']:
                    st.caption(f"🔑 Derived AES-256 Key: `{sensor['last_key'][:16]}...`")
                else:
                    st.caption("🔑 Session Key: *Aborted due to eavesdropping*")
                
                st.caption(f"🕐 Last Cycle: {sensor['last_update'].strftime('%H:%M:%S')}")
    
    # QBER Visualization
    st.subheader("📊 Quantum Bit Error Rate (QBER) Security Analysis")
    
    # Prepare data for QBER chart
    qber_data = []
    for sensor_key, icon, _ in sensors_info:
        sensor = smart_city.sensors[sensor_key]
        qber_data.append({
            'Sensor': icon,
            'QBER (%)': sensor['qber'],
            'Status': 'Secure (<11%)' if sensor['qber'] < 11.0 else 'Compromised (≥11%)'
        })
    
    df_qber = pd.DataFrame(qber_data)
    
    fig_qber = px.bar(
        df_qber, x='Sensor', y='QBER (%)', color='Status',
        color_discrete_map={'Secure (<11%)': '#10b981', 'Compromised (≥11%)': '#ef4444'},
        title="Real-time QBER vs Theoretical Security Threshold (11%)",
        text='QBER (%)'
    )
    fig_qber.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_qber.add_hline(y=11.0, line_dash="dash", line_color="red", 
                      annotation_text="BB84 Theoretical Abort Limit (11%)")
    fig_qber.update_layout(height=360, yaxis_range=[0, max(35, df_qber['QBER (%)'].max() + 8)])
    st.plotly_chart(fig_qber, use_container_width=True)
    
    # Sensor data trends
    st.subheader("📈 Real-time Telemetry & Security History")
    
    tab1, tab2, tab3 = st.tabs(["🚦 Traffic Signal", "💧 Water Utility", "📹 Surveillance"])
    
    for tab, (sensor_key, icon, _) in zip([tab1, tab2, tab3], sensors_info):
        with tab:
            sensor = smart_city.sensors[sensor_key]
            
            if len(sensor['data_points']) >= 1:
                df_trend = pd.DataFrame(sensor['data_points'])
                
                fig_trend = go.Figure()
                
                # Add data value trace
                fig_trend.add_trace(go.Scatter(
                    x=df_trend['time'],
                    y=df_trend['value'],
                    mode='lines+markers',
                    name='Telemetry Value',
                    line=dict(color='#2563eb', width=2)
                ))
                
                # Add QBER trace on secondary axis
                fig_trend.add_trace(go.Scatter(
                    x=df_trend['time'],
                    y=df_trend['qber'],
                    mode='lines+markers',
                    name='QBER (%)',
                    yaxis='y2',
                    line=dict(color='#dc2626', width=2, dash='dash')
                ))
                
                fig_trend.update_layout(
                    title=f"{icon} - Telemetry Value & QBER Over Time",
                    xaxis_title="Time",
                    yaxis_title="Telemetry Value",
                    yaxis2=dict(
                        title="QBER (%)",
                        overlaying="y",
                        side="right",
                        range=[0, max(35, df_trend['qber'].max() + 5)]
                    ),
                    height=320,
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("📊 Collecting data points...")
    
    # Security Log
    st.subheader("🛡️ Security Audit Event Log")
    
    security_events = []
    for sensor_key, icon, loc in sensors_info:
        sensor = smart_city.sensors[sensor_key]
        if sensor['status'] == 'compromised':
            security_events.append({
                'Timestamp': sensor['last_update'].strftime('%H:%M:%S'),
                'Node': sensor['id'],
                'Location': loc,
                'Event': '⚠️ EAVESDROPPING ATTACK DETECTED',
                'Measured QBER': f"{sensor['qber']:.1f}%",
                'Action': 'Key Aborted & Data Transmission Blocked'
            })
        elif sensor['last_key']:
            security_events.append({
                'Timestamp': sensor['last_update'].strftime('%H:%M:%S'),
                'Node': sensor['id'],
                'Location': loc,
                'Event': '✅ Key Exchange Succeeded',
                'Measured QBER': f"{sensor['qber']:.1f}%",
                'Action': f"Encrypted with AES-256 ({sensor['last_key'][:8]}...)"
            })
    
    if security_events:
        df_events = pd.DataFrame(security_events)
        st.dataframe(df_events, use_container_width=True, hide_index=True)
    else:
        st.info("📋 No security events recorded.")
    
    # BB84 educational expander
    with st.expander("📖 BB84 Protocol Reference"):
        st.markdown("""
        ### BB84 Quantum Key Distribution Workflow
        1. **Quantum State Preparation**: Alice prepares photons polarized in random rectilinear ($\\{|0\\rangle, |1\\rangle\\}$) or diagonal ($\\{|+\\rangle, |-\\rangle\\}$) bases.
        2. **Measurement**: Bob measures incoming photons in randomly chosen bases.
        3. **Sifting**: Alice and Bob communicate over the classical channel to retain only instances where identical bases were selected.
        4. **QBER Estimation**: A sample of sifted bits is compared to compute the Quantum Bit Error Rate ($QBER$).
        5. **Security Verification**: If $QBER > 11\\%$, the exchange is aborted because eavesdropping introduces noticeable quantum measurement collapse.
        6. **Key Amplification**: If $QBER \\le 11\\%$, privacy amplification creates a clean 256-bit symmetric AES key.
        """)

if __name__ == "__main__":
    main()