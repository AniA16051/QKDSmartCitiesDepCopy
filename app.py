#!/usr/bin/env python3
"""
Unified QKD Dashboard for Streamlit Cloud, Render, and Railway Deployment
High-Density Cyber Defense Operations Center (SOC) Interface
Inspired by Bloomberg Terminal, Databricks, and Palantir Gotham
"""

import os
import sys

# Disable file watching in production to prevent inotify limit errors
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
        # Resolve MQTT settings lazily
        broker, port, username, password, use_tls = _get_mqtt_settings()
        self._mqtt_broker = broker
        self._mqtt_port = port
        self._mqtt_username = username
        self._mqtt_password = password
        self._mqtt_use_tls = use_tls

        self.sensors = {
            'traffic_light': {
                'id': 'NODE-TRF-01',
                'type': 'traffic_flow',
                'location': 'Main St & 5th Ave',
                'lat': 12.9756,
                'lon': 77.6006,
                'status': 'secure',
                'qber': 0.0,
                'last_key': None,
                'data_points': [],
                'last_update': datetime.now()
            },
            'water_meter': {
                'id': 'NODE-WTR-01', 
                'type': 'water_consumption',
                'location': 'Downtown Reservoir',
                'lat': 12.9698,
                'lon': 77.5910,
                'status': 'secure',
                'qber': 0.0,
                'last_key': None,
                'data_points': [],
                'last_update': datetime.now()
            },
            'surveillance': {
                'id': 'NODE-CAM-01',
                'type': 'security_monitoring',
                'location': 'Central Park North',
                'lat': 12.9741,
                'lon': 77.5983,
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
        self.terminal_logs = []
        
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
    
    def log_terminal(self, msg, level="INFO"):
        """Add timestamped terminal message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.terminal_logs.append(f"[{timestamp}] [{level}] {msg}")
        if len(self.terminal_logs) > 40:
            self.terminal_logs = self.terminal_logs[-40:]
    
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
            data_value = random.randint(10, 100)
            data_unit = 'cars/min'
        elif sensor['type'] == 'water_consumption':
            data_value = round(random.uniform(50, 200), 2)
            data_unit = 'L/h'
        else:
            data_value = random.choice(['NOMINAL', 'MOTION_DET', 'SECURE'])
            data_unit = 'state'
        
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
        
        # Log entry for cryptographic terminal
        if sensor['status'] == 'secure':
            self.log_terminal(f"BB84 HANDSHAKE OK :: {sensor['id']} :: QBER={sensor['qber']:.1f}% :: AES-256 HASH={sensor['last_key'][:8]}...{sensor['last_key'][-4:]}", "SECURE")
        else:
            self.log_terminal(f"BB84 ABORT DETECTED :: {sensor['id']} :: QBER={sensor['qber']:.1f}% >= 11.0% :: KEY DESTROYED", "WARN")
        
        sensor['data_points'].append({
            'time': datetime.now(),
            'value': data_value if isinstance(data_value, (int, float)) else (1 if data_value == 'MOTION_DET' else 0),
            'qber': sensor['qber']
        })
        
        if len(sensor['data_points']) > 25:
            sensor['data_points'] = sensor['data_points'][-25:]
        
        self.publish_sensor_data(sensor_name, sensor_data)
        return sensor_data
    
    def toggle_attack(self):
        """Toggle eavesdropping attack on all sensors"""
        self.attack_active = not self.attack_active
        status_msg = "INTERCEPT-RESEND EAVESDROPPER ACTIVATED" if self.attack_active else "CHANNEL RESTORED TO CLEAN STATE"
        self.log_terminal(f"THREAT ENGINE :: {status_msg}", "ALERT" if self.attack_active else "INFO")
        self.update_all_sensors()
        return self.attack_active
    
    def update_all_sensors(self):
        """Update all sensors with new simulations"""
        results = {}
        for sensor_name in self.sensors.keys():
            results[sensor_name] = self.simulate_sensor(sensor_name)
        return results

# Streamlit Cyber Operations Center UI
def main():
    st.set_page_config(
        page_title="CYBER DEFENSE OPERATIONS CENTER | QKD SOC",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Industrial Monospace CSS Design System
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&display=swap');
    
    * {
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace !important;
    }
    
    .stApp {
        background-color: #080B10 !important;
        color: #94A3B8 !important;
    }
    
    /* Hide top padding and header gap */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 98% !important;
    }
    
    /* Top Command Ribbon */
    .top-ribbon {
        background: #0E131F;
        border: 1px solid #1E293B;
        border-left: 4px solid #06B6D4;
        padding: 8px 16px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .top-ribbon-title {
        font-weight: 800;
        font-size: 1.1rem;
        color: #F3F4F6;
        letter-spacing: 1px;
    }
    
    /* Badges */
    .badge-secure {
        background: #06281E;
        color: #10B981;
        border: 1px solid #059669;
        padding: 2px 8px;
        font-weight: 700;
        font-size: 0.78rem;
    }
    .badge-attack {
        background: #3B0D0D;
        color: #EF4444;
        border: 1px solid #DC2626;
        padding: 2px 8px;
        font-weight: 700;
        font-size: 0.78rem;
        animation: blink 1.2s infinite alternate;
    }
    @keyframes blink {
        0% { opacity: 0.7; }
        100% { opacity: 1.0; }
    }
    .badge-amber {
        background: #2D1A00;
        color: #F59E0B;
        border: 1px solid #D97706;
        padding: 2px 8px;
        font-weight: 700;
        font-size: 0.78rem;
    }
    
    /* Containers & Cards */
    div[data-testid="stVerticalBlock"] > div {
        border-radius: 0px !important;
    }
    .soc-panel {
        background: #0E131F;
        border: 1px solid #1E293B;
        padding: 12px;
        margin-bottom: 12px;
    }
    .panel-header {
        font-size: 0.85rem;
        font-weight: 700;
        color: #06B6D4;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 1px solid #162032;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }
    
    /* Tactile Mechanical Switches & Buttons */
    .stButton > button {
        background: #0E131F !important;
        color: #F3F4F6 !important;
        border: 1px solid #334155 !important;
        border-radius: 2px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-size: 0.8rem !important;
        padding: 6px 14px !important;
        box-shadow: 0 2px 0 #1E293B !important;
        transition: all 0.05s ease !important;
    }
    .stButton > button:hover {
        border-color: #06B6D4 !important;
        color: #06B6D4 !important;
        box-shadow: 0 0 8px rgba(6, 182, 212, 0.4) !important;
    }
    .stButton > button:active {
        transform: translateY(1px) !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.8) !important;
    }
    
    /* Metric styling */
    div[data-testid="stMetric"] {
        background: #090D16 !important;
        border: 1px solid #1E293B !important;
        border-radius: 0px !important;
        padding: 8px 12px !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    div[data-testid="stMetricValue"] {
        color: #F3F4F6 !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
    }
    
    /* Databricks Grid Table */
    .data-grid {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.76rem;
        background: #090D16;
        border: 1px solid #1E293B;
    }
    .data-grid th {
        background: #111827;
        color: #06B6D4;
        text-align: left;
        padding: 6px 10px;
        border-bottom: 1px solid #1E293B;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .data-grid td {
        padding: 6px 10px;
        border-bottom: 1px solid #162032;
        color: #CBD5E1;
    }
    .data-grid tr:hover {
        background: #162032;
    }
    
    /* Terminal Output Box */
    .terminal-box {
        background: #05080E;
        border: 1px solid #1E293B;
        border-left: 3px solid #10B981;
        padding: 10px;
        font-size: 0.73rem;
        height: 200px;
        overflow-y: auto;
        color: #10B981;
        line-height: 1.4;
    }
    .term-sec { color: #10B981; }
    .term-warn { color: #EF4444; font-weight: 700; }
    .term-info { color: #06B6D4; }
    .term-alert { color: #F59E0B; font-weight: 700; }
    
    /* Sidebar Overrides */
    section[data-testid="stSidebar"] {
        background-color: #0B0F19 !important;
        border-right: 1px solid #1E293B !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize the integrated system
    if 'smart_city' not in st.session_state:
        st.session_state.smart_city = IntegratedSmartCity()
        st.session_state.smart_city.initialize_mqtt()
    
    smart_city = st.session_state.smart_city
    attack_active = smart_city.attack_active
    
    # TOP COMMAND RIBBON
    status_badge = '<span class="badge-attack">🚨 THREAT: INTERCEPTION ACTIVE</span>' if attack_active else '<span class="badge-secure">✓ STATUS: ACTIVE-DEFENSE</span>'
    broker_badge = f'<span class="badge-amber">BROKER: {smart_city._mqtt_broker}:{smart_city._mqtt_port} | TLS: {"ON" if smart_city._mqtt_use_tls or smart_city._mqtt_port == 8883 else "OFF"} | QKD: BB84-256</span>'
    
    col_rib1, col_rib2 = st.columns([3, 1])
    with col_rib1:
        st.markdown(f"""
        <div class="top-ribbon">
            <div class="top-ribbon-title">🛡️ QKD CYBER DEFENSE OPERATIONS CENTER</div>
            <div>{status_badge} &nbsp; {broker_badge}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_rib2:
        btn_label = "⚡ [ DISENGAGE ATTACK ]" if attack_active else "⚡ [ INITIATE EAVESDROPPING ]"
        if st.button(btn_label, use_container_width=True):
            smart_city.toggle_attack()
            st.rerun()

    # SIDEBAR CONTROL DECK
    with st.sidebar:
        st.markdown('<div class="panel-header">🎛️ DEFENSE COMMAND DECK</div>', unsafe_allow_html=True)
        
        st.caption("TACTILE OVERRIDES")
        if st.button("🔄 [ EXECUTE TELEMETRY CYCLE ]", use_container_width=True):
            smart_city.update_all_sensors()
            st.rerun()
            
        st.divider()
        
        st.caption("POLLING RATE CONTROL")
        poll_rate = st.radio("SELECT INTERVAL", ["MANUAL", "1s", "5s", "10s"], index=2, horizontal=True)
        
        if poll_rate != "MANUAL":
            seconds = 1 if poll_rate == "1s" else (5 if poll_rate == "5s" else 10)
            try:
                from streamlit_autorefresh import st_autorefresh
                st_autorefresh(interval=seconds * 1000, key="soc_refresh_trigger")
            except ImportError:
                time.sleep(seconds)
                smart_city.update_all_sensors()
                st.rerun()

        st.divider()
        
        st.caption("NETWORK TELEMETRY STATUS")
        mqtt_state_badge = '<span class="badge-secure">CONNECTED</span>' if smart_city.mqtt_connected else '<span class="badge-amber">STANDALONE</span>'
        st.markdown(f"MQTT GATEWAY: {mqtt_state_badge}", unsafe_allow_html=True)
        st.markdown(f"ACTIVE SENSORS: `<3/3 NOMINAL>`")
        st.markdown(f"CRYPTOGRAPHIC PROTOCOL: `BB84 + AES-GCM-256`")

    # SPLIT-SCREEN SOC WORKSPACE (60% / 40%)
    col_left, col_right = st.columns([6, 4])
    
    # -------------------------------------------------------------
    # LEFT PANE (60% Width — Geospatial & Threat Vectors)
    # -------------------------------------------------------------
    with col_left:
        # TOP GEOSPATIAL VECTOR MAP
        st.markdown('<div class="panel-header">📍 GEOSPATIAL THREAT VECTOR MATRIX</div>', unsafe_allow_html=True)
        
        map_lats = []
        map_lons = []
        map_names = []
        map_colors = []
        map_texts = []
        
        for key, s in smart_city.sensors.items():
            map_lats.append(s['lat'])
            map_lons.append(s['lon'])
            map_names.append(f"{s['id']} ({s['location']})")
            color = '#EF4444' if s['status'] == 'compromised' else '#10B981'
            map_colors.append(color)
            map_texts.append(f"QBER: {s['qber']:.1f}% | STATUS: {s['status'].upper()}")
            
        fig_map = go.Figure()
        
        # Node Vector Markers
        fig_map.add_trace(go.Scattermapbox(
            lat=map_lats,
            lon=map_lons,
            mode='markers+text',
            marker=dict(
                size=18,
                color=map_colors,
                opacity=0.9
            ),
            text=[f"  {n}" for n in map_names],
            textposition="top right",
            textfont=dict(size=11, color="#F3F4F6", family="JetBrains Mono"),
            hoverinfo='text',
            hovertext=map_texts
        ))
        
        # Pulsing Attack Circles for compromised nodes
        pulse_lats = [s['lat'] for s in smart_city.sensors.values() if s['status'] == 'compromised']
        pulse_lons = [s['lon'] for s in smart_city.sensors.values() if s['status'] == 'compromised']
        if pulse_lats:
            fig_map.add_trace(go.Scattermapbox(
                lat=pulse_lats,
                lon=pulse_lons,
                mode='markers',
                marker=dict(
                    size=38,
                    color='#EF4444',
                    opacity=0.35
                ),
                hoverinfo='none'
            ))
            
        fig_map.update_layout(
            mapbox_style="carto-darkmatter",
            mapbox=dict(
                center=dict(lat=12.9732, lon=77.5966),
                zoom=12.5
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=320,
            paper_bgcolor="#080B10",
            plot_bgcolor="#0E131F",
            showlegend=False
        )
        st.plotly_chart(fig_map, use_container_width=True)
        
        # BOTTOM QBER THREAT VECTOR MONITOR
        st.markdown('<div class="panel-header">📊 QUANTUM BIT ERROR RATE (QBER) THREAT VECTOR MONITOR</div>', unsafe_allow_html=True)
        
        sensors_list = list(smart_city.sensors.values())
        qber_df = pd.DataFrame([{
            'Node': s['id'],
            'QBER': s['qber'],
            'Color': '#EF4444' if s['qber'] >= 11.0 else '#10B981'
        } for s in sensors_list])
        
        fig_qber = go.Figure()
        fig_qber.add_trace(go.Bar(
            x=qber_df['Node'],
            y=qber_df['QBER'],
            marker_color=qber_df['Color'],
            text=[f"{v:.1f}%" for v in qber_df['QBER']],
            textposition='outside',
            textfont=dict(color='#F3F4F6', family="JetBrains Mono")
        ))
        
        # 11% Theoretical Interception Ceiling
        fig_qber.add_hline(
            y=11.0, 
            line_dash="dash", 
            line_color="#EF4444", 
            line_width=2,
            annotation_text="BB84 THEORETICAL ABORT CEILING (11.0%)", 
            annotation_font_color="#EF4444",
            annotation_font_family="JetBrains Mono"
        )
        
        fig_qber.update_layout(
            template="plotly_dark",
            paper_bgcolor="#080B10",
            plot_bgcolor="#0E131F",
            margin=dict(l=20, r=20, t=25, b=20),
            height=280,
            yaxis=dict(
                title="QBER (%)",
                range=[0, max(35, qber_df['QBER'].max() + 8)],
                gridcolor="#162032"
            ),
            xaxis=dict(gridcolor="#162032")
        )
        st.plotly_chart(fig_qber, use_container_width=True)

    # -------------------------------------------------------------
    # RIGHT PANE (40% Width — Telemetry Matrix & Cryptographic Stream)
    # -------------------------------------------------------------
    with col_right:
        # SNIP-TO-GRID NODE TELEMETRY TABLE
        st.markdown('<div class="panel-header">📋 DATABRICKS-STYLE TELEMETRY MATRIX</div>', unsafe_allow_html=True)
        
        table_rows = []
        for s in smart_city.sensors.values():
            status_html = f'<span class="badge-secure">SECURE</span>' if s['status'] == 'secure' else f'<span class="badge-attack">COMPROMISED</span>'
            key_hash = f"<code>{s['last_key'][:8]}...{s['last_key'][-4:]}</code>" if s['last_key'] else '<span style="color:#EF4444">ABORTED</span>'
            latest_val = s['data_points'][-1]['value'] if s['data_points'] else 'N/A'
            
            table_rows.append(f"""
            <tr>
                <td><b>{s['id']}</b></td>
                <td>{s['location']}</td>
                <td><b style="color:{'#EF4444' if s['qber']>=11.0 else '#10B981'}">{s['qber']:.1f}%</b></td>
                <td>{latest_val}</td>
                <td>{key_hash}</td>
                <td>{status_html}</td>
            </tr>
            """)
            
        table_html = f"""
        <table class="data-grid">
            <thead>
                <tr>
                    <th>NODE_ID</th>
                    <th>LOCATION</th>
                    <th>QBER</th>
                    <th>TELEMETRY</th>
                    <th>AES-256 HASH</th>
                    <th>STATE</th>
                </tr>
            </thead>
            <tbody>
                {''.join(table_rows)}
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # CRYPTOGRAPHIC HANDSHAKE TERMINAL STREAM
        st.markdown('<div class="panel-header">💻 LIVE CRYPTOGRAPHIC STREAM TERMINAL</div>', unsafe_allow_html=True)
        
        term_lines = []
        for log in reversed(smart_city.terminal_logs):
            if "SECURE" in log:
                term_lines.append(f'<div class="term-sec">{log}</div>')
            elif "WARN" in log or "ABORT" in log:
                term_lines.append(f'<div class="term-warn">{log}</div>')
            elif "ALERT" in log:
                term_lines.append(f'<div class="term-alert">{log}</div>')
            else:
                term_lines.append(f'<div class="term-info">{log}</div>')
                
        terminal_html = f"""
        <div class="terminal-box">
            {''.join(term_lines) if term_lines else '<div class="term-info">[SYSTEM READY] Awaiting handshake cycles...</div>'}
        </div>
        """
        st.markdown(terminal_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()