#!/usr/bin/env python3
"""
Unified QKD Dashboard for Streamlit Cloud, Render, and Railway Deployment
Cyber Defense Operations Center (SOC) Interface
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
        alice_key = UnifiedBB84.generate_key(key_length)
        alice_bases = UnifiedBB84.generate_bases(key_length)
        bob_bases = UnifiedBB84.generate_bases(key_length)
        bob_key = np.zeros(key_length, dtype=int)
        
        if attack:
            eve_bases = UnifiedBB84.generate_bases(key_length)
            eve_key = np.zeros(key_length, dtype=int)
            for i in range(key_length):
                if alice_bases[i] == eve_bases[i]:
                    eve_key[i] = alice_key[i]
                else:
                    eve_key[i] = random.randint(0, 1)
            for i in range(key_length):
                if eve_bases[i] == bob_bases[i]:
                    bob_key[i] = eve_key[i]
                else:
                    bob_key[i] = random.randint(0, 1)
        else:
            for i in range(key_length):
                if alice_bases[i] == bob_bases[i]:
                    bob_key[i] = alice_key[i]
                else:
                    bob_key[i] = random.randint(0, 1)
        
        matching_bases = (alice_bases == bob_bases)
        sifted_alice = alice_key[matching_bases]
        sifted_bob = bob_key[matching_bases]
        
        if len(sifted_alice) == 0:
            return {
                'success': False, 'qber': 100.0, 'sifted_length': 0,
                'final_key': None, 'attack_detected': True, 'raw_length': key_length
            }
        
        errors = np.sum(sifted_alice != sifted_bob)
        qber = (errors / len(sifted_alice)) * 100.0
        attack_detected = qber >= 11.0
        success = not attack_detected and len(sifted_alice) >= 32
        
        final_key = None
        if success:
            bit_string = ''.join(map(str, sifted_alice))
            final_key = hashlib.sha256(bit_string.encode()).hexdigest()
        
        return {
            'success': success, 'qber': qber, 'sifted_length': len(sifted_alice),
            'final_key': final_key, 'attack_detected': attack_detected, 'raw_length': key_length
        }

# Integrated Smart City Simulation
class IntegratedSmartCity:
    """Unified sensor simulation within the dashboard process"""
    
    def __init__(self):
        broker, port, username, password, use_tls = _get_mqtt_settings()
        self._mqtt_broker = broker
        self._mqtt_port = port
        self._mqtt_username = username
        self._mqtt_password = password
        self._mqtt_use_tls = use_tls

        self.sensors = {
            'traffic_light': {
                'id': 'NODE-TRF-01', 'type': 'traffic_flow',
                'location': 'Main St & 5th Ave',
                'lat': 12.9756, 'lon': 77.6006,
                'status': 'secure', 'qber': 0.0, 'last_key': None,
                'data_points': [], 'last_update': datetime.now()
            },
            'water_meter': {
                'id': 'NODE-WTR-01', 'type': 'water_consumption',
                'location': 'Downtown Reservoir',
                'lat': 12.9698, 'lon': 77.5910,
                'status': 'secure', 'qber': 0.0, 'last_key': None,
                'data_points': [], 'last_update': datetime.now()
            },
            'surveillance': {
                'id': 'NODE-CAM-01', 'type': 'security_monitoring',
                'location': 'Central Park North',
                'lat': 12.9741, 'lon': 77.5983,
                'status': 'secure', 'qber': 0.0, 'last_key': None,
                'data_points': [], 'last_update': datetime.now()
            }
        }
        self.attacked_target = "None"  # "None", "All Nodes", "traffic_light", "water_meter", "surveillance"
        self.mqtt_client = None
        self.mqtt_connected = False
        self.terminal_logs = []
        
        for name in self.sensors:
            self.simulate_sensor(name)

    @property
    def attack_active(self):
        return self.attacked_target != "None"
    
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
        except Exception:
            return False
    
    def _on_mqtt_connect(self, client, userdata, flags, rc, properties=None):
        self.mqtt_connected = (rc == 0)
    
    def _on_mqtt_disconnect(self, client, userdata, rc, properties=None):
        self.mqtt_connected = False
    
    def publish_sensor_data(self, sensor_name, data):
        if self.mqtt_connected and self.mqtt_client:
            try:
                self.mqtt_client.publish(f"{MQTT_TOPIC}/{sensor_name}", json.dumps(data))
                return True
            except Exception:
                return False
        return False
    
    def log_terminal(self, msg, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.terminal_logs.append({"ts": ts, "level": level, "msg": msg})
        if len(self.terminal_logs) > 50:
            self.terminal_logs = self.terminal_logs[-50:]
    
    def simulate_sensor(self, sensor_name):
        sensor = self.sensors[sensor_name]
        is_attacked = (self.attacked_target == "All Nodes") or (self.attacked_target == sensor_name)
        qkd_result = UnifiedBB84.simulate_bb84_protocol(key_length=256, attack=is_attacked)
        
        sensor['status'] = 'secure' if qkd_result['success'] else 'compromised'
        sensor['qber'] = qkd_result['qber']
        sensor['last_key'] = qkd_result['final_key']
        sensor['last_update'] = datetime.now()
        
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
            'sensor_id': sensor['id'], 'sensor_type': sensor['type'],
            'location': sensor['location'], 'timestamp': datetime.now().isoformat(),
            'value': data_value, 'unit': data_unit,
            'qkd_status': sensor['status'], 'qber': sensor['qber'],
            'key_preview': sensor['last_key'][:8] + '...' if sensor['last_key'] else None
        }
        
        if sensor['status'] == 'secure':
            self.log_terminal(
                f"BB84 OK  {sensor['id']}  QBER={sensor['qber']:.1f}%  KEY={sensor['last_key'][:8]}...{sensor['last_key'][-4:]}",
                "SECURE"
            )
        else:
            self.log_terminal(
                f"BB84 ABORT  {sensor['id']}  QBER={sensor['qber']:.1f}% >= 11.0%  KEY DESTROYED",
                "WARN"
            )
        
        sensor['data_points'].append({
            'time': datetime.now(),
            'value': data_value if isinstance(data_value, (int, float)) else (1 if data_value == 'MOTION_DET' else 0),
            'qber': sensor['qber']
        })
        if len(sensor['data_points']) > 25:
            sensor['data_points'] = sensor['data_points'][-25:]
        
        self.publish_sensor_data(sensor_name, sensor_data)
        return sensor_data
    
    def toggle_attack(self, target="All Nodes"):
        if self.attacked_target == target:
            self.attacked_target = "None"
            msg = f"ATTACK STOPPED :: CHANNEL RESTORED TO CLEAN STATE"
        else:
            self.attacked_target = target
            msg = f"INTERCEPT-RESEND ATTACK ACTIVATED ON {target.upper()}"
        self.log_terminal(f"THREAT ENGINE :: {msg}", "ALERT" if self.attack_active else "INFO")
        self.update_all_sensors()
        return self.attack_active
    
    def update_all_sensors(self):
        results = {}
        for sensor_name in self.sensors.keys():
            results[sensor_name] = self.simulate_sensor(sensor_name)
        return results

    def ping_node(self, sensor_name):
        """Simulate a cryptographic challenge-response ping"""
        sensor = self.sensors[sensor_name]
        nonce = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16].upper()
        
        if sensor['status'] == 'secure' and sensor['last_key']:
            self.log_terminal(f"PING :: [ {sensor['id']} ] CRYPTOGRAPHIC CHALLENGE (NONCE: {nonce})", "INFO")
            self.log_terminal(f"PING OK :: [ {sensor['id']} ] RESPONSE ENCRYPTED WITH KEY {sensor['last_key'][:8]}...", "SECURE")
            return True
        else:
            self.log_terminal(f"PING :: [ {sensor['id']} ] CRYPTOGRAPHIC CHALLENGE (NONCE: {nonce})", "INFO")
            self.log_terminal(f"PING FAILED :: [ {sensor['id']} ] NO VALID KEY TO ENCRYPT CHALLENGE", "WARN")
            return False


# ═══════════════════════════════════════════════════════════════════════
# STREAMLIT UI — Cyber Defense Operations Center
# ═══════════════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="QKD Cyber Defense Operations Center",
        page_icon="Q",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # ── CSS Design System ──
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    :root {
        --bg-canvas: #080B10;
        --bg-panel: #0E131F;
        --bg-card: #111827;
        --border: #1E293B;
        --border-subtle: #162032;
        --text-primary: #F1F5F9;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        --accent-cyan: #06B6D4;
        --accent-green: #10B981;
        --accent-red: #EF4444;
        --accent-amber: #F59E0B;
    }
    
    .stApp {
        background-color: var(--bg-canvas) !important;
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 96% !important;
    }
    
    /* ── Header ── */
    .soc-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: 2px;
        text-align: center;
        margin: 0;
    }
    .soc-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
        color: var(--text-muted);
        text-align: center;
        margin-top: 2px;
        margin-bottom: 14px;
    }
    
    /* ── Status Bar ── */
    .status-bar {
        background: var(--bg-panel);
        border: 1px solid var(--border);
        padding: 10px 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 24px;
        flex-wrap: wrap;
        margin-bottom: 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
    }
    .status-item {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .status-label {
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .status-val-green { color: var(--accent-green); font-weight: 700; }
    .status-val-red { color: var(--accent-red); font-weight: 700; }
    .status-val-amber { color: var(--accent-amber); font-weight: 700; }
    .status-val-cyan { color: var(--accent-cyan); font-weight: 700; }
    
    /* ── Section Headers ── */
    .section-hdr {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--accent-cyan);
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 1px solid var(--border);
        padding-bottom: 6px;
        margin-bottom: 12px;
        margin-top: 8px;
    }
    
    /* ── Metric Overrides ── */
    div[data-testid="stMetric"] {
        background: var(--bg-panel) !important;
        border: 1px solid var(--border) !important;
        border-radius: 0px !important;
        padding: 10px 14px !important;
    }
    div[data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    div[data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
    }
    
    /* ── Buttons ── */
    .stButton > button {
        background: var(--bg-panel) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 2px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding: 8px 16px !important;
        transition: all 0.08s ease !important;
    }
    .stButton > button:hover {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 12px rgba(6,182,212,0.25) !important;
    }
    .stButton > button:active {
        transform: translateY(1px) !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.6) !important;
    }
    
    /* ── Containers ── */
    div[data-testid="stExpander"] {
        border: 1px solid var(--border) !important;
        border-radius: 0px !important;
        background: var(--bg-panel) !important;
    }
    
    /* ── Terminal ── */
    .term-output {
        background: #05080E;
        border: 1px solid var(--border);
        padding: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        line-height: 1.6;
        max-height: 240px;
        overflow-y: auto;
        color: var(--text-secondary);
    }
    .tl-secure { color: var(--accent-green); }
    .tl-warn { color: var(--accent-red); font-weight: 600; }
    .tl-alert { color: var(--accent-amber); font-weight: 600; }
    .tl-info { color: var(--accent-cyan); }
    .tl-ts { color: var(--text-muted); }
    
    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: #0B0F19 !important;
        border-right: 1px solid var(--border) !important;
    }
    
    /* ── Dataframe ── */
    .stDataFrame {
        border: 1px solid var(--border) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ── Initialize Backend ──
    if 'smart_city' not in st.session_state:
        st.session_state.smart_city = IntegratedSmartCity()
        st.session_state.smart_city.initialize_mqtt()
    
    sc = st.session_state.smart_city
    attack_active = sc.attack_active
    
    # ══════════════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════════════
    st.markdown('<p class="soc-title">QKD CYBER DEFENSE OPERATIONS CENTER</p>', unsafe_allow_html=True)
    st.markdown('<p class="soc-subtitle">Real-time BB84 Quantum Key Distribution Simulation &mdash; IoT Sensor Network Security Monitor</p>', unsafe_allow_html=True)
    
    # ── Global Status Bar ──
    sys_status = '<span class="status-val-red">ATTACK ACTIVE</span>' if attack_active else '<span class="status-val-green">ACTIVE DEFENSE</span>'
    mqtt_status = '<span class="status-val-green">CONNECTED</span>' if sc.mqtt_connected else '<span class="status-val-amber">STANDALONE</span>'
    tls_val = "ON" if (sc._mqtt_use_tls or sc._mqtt_port == 8883) else "OFF"
    
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-item"><span class="status-label">System:</span> {sys_status}</div>
        <div class="status-item"><span class="status-label">Protocol:</span> <span class="status-val-cyan">BB84 + AES-GCM-256</span></div>
        <div class="status-item"><span class="status-label">Broker:</span> <span class="status-val-cyan">{sc._mqtt_broker}:{sc._mqtt_port}</span></div>
        <div class="status-item"><span class="status-label">TLS:</span> <span class="status-val-cyan">{tls_val}</span></div>
        <div class="status-item"><span class="status-label">MQTT:</span> {mqtt_status}</div>
        <div class="status-item"><span class="status-label">Sensors:</span> <span class="status-val-green">3 ONLINE</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════════
    # CONTROL BAR (Centered Row)
    # ══════════════════════════════════════════════════════════════
    c1, c2, c3, c4, c5 = st.columns([2.5, 2.5, 2, 2, 2])
    
    target_mapping = {
        "All Nodes": "All Nodes",
        "Surveillance Camera": "surveillance",
        "Traffic Signal": "traffic_light",
        "Water Utility": "water_meter"
    }

    with c1:
        selected_target_label = st.selectbox(
            "Attack Target Node",
            list(target_mapping.keys()),
            index=0,
            help="Select which IoT node to target with the Eve intercept-resend eavesdropping attack."
        )
        selected_target_key = target_mapping[selected_target_label]

    with c2:
        is_current_target_attacked = (sc.attacked_target == selected_target_key) or (sc.attacked_target == "All Nodes" and sc.attack_active)
        atk_label = f"STOP ATTACK ({sc.attacked_target.upper()})" if sc.attack_active else f"SIMULATE ATTACK"
        if st.button(
            atk_label,
            use_container_width=True,
            help="Toggles an intercept-resend (Eve) eavesdropper on the selected quantum channel target. When active, Eve measures each qubit in a random basis and resends it, causing QBER to exceed the 11% BB84 security threshold."
        ):
            sc.toggle_attack(target=selected_target_key)
            st.rerun()

    with c3:
        if st.button(
            "EXECUTE TELEMETRY CYCLE",
            use_container_width=True,
            help="Runs a fresh BB84 key exchange for every sensor node, generates new telemetry readings, and publishes encrypted payloads to the MQTT broker."
        ):
            sc.update_all_sensors()
            st.rerun()

    with c4:
        refresh = st.selectbox(
            "Auto-Refresh",
            ["Off", "5 seconds", "10 seconds"],
            index=0,
            help="Automatically re-runs the full telemetry cycle at the selected interval."
        )
        if refresh != "Off":
            ms = 5000 if refresh == "5 seconds" else 10000
            try:
                from streamlit_autorefresh import st_autorefresh
                count = st_autorefresh(interval=ms, key="soc_auto")
                if 'last_refresh_count' not in st.session_state:
                    st.session_state.last_refresh_count = 0
                
                if count > st.session_state.last_refresh_count:
                    sc.update_all_sensors()
                    st.session_state.last_refresh_count = count
            except ImportError:
                time.sleep(ms // 1000)
                sc.update_all_sensors()
                st.rerun()

    with c5:
        target_display = f"ACTIVE ({sc.attacked_target})" if sc.attack_active else "SECURED"
        st.metric(
            "Channel State",
            target_display,
            help="Reflects whether an active eavesdropper (Eve) is present on any quantum channel."
        )
    
    st.markdown("---")
    
    # ══════════════════════════════════════════════════════════════
    # THREAT REMEDIATION & FAILSAFES (Conditional)
    # ══════════════════════════════════════════════════════════════
    if sc.attack_active:
        st.markdown('<div class="section-hdr" style="color: var(--accent-amber);">Active Countermeasures & Failsafes</div>', unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns([1, 1, 2])
        with fc1:
            if st.button("INITIATE QUANTUM REROUTING", use_container_width=True, help="Bypass the compromised channel and reroute quantum transmission via a secondary secure path."):
                sc.log_terminal(f"FAILSAFE :: QUANTUM REROUTING INITIATED FOR {sc.attacked_target.upper()}", "SECURE")
                sc.toggle_attack(target=sc.attacked_target)
                st.rerun()
        with fc2:
            if st.button("PROVISION STANDBY NODE", use_container_width=True, help="Spin up a cold-spare node to maintain network continuity while the primary node is isolated."):
                sc.log_terminal(f"FAILSAFE :: STANDBY NODE PROVISIONED. NETWORK CONTINUITY MAINTAINED.", "SECURE")
                sc.toggle_attack(target=sc.attacked_target)
                st.rerun()
        with fc3:
            st.markdown(f'<div style="color: var(--accent-red); font-family: \'JetBrains Mono\', monospace; font-size: 0.8rem; padding-top: 10px;">&gt; Node \'{sc.attacked_target}\' is compromised. Awaiting manual remediation.</div>', unsafe_allow_html=True)
        st.markdown("---")
    
    # ══════════════════════════════════════════════════════════════
    # NODE STATUS CARDS (3-Column)
    # ══════════════════════════════════════════════════════════════
    st.markdown('<div class="section-hdr">IoT Sensor Node Status</div>', unsafe_allow_html=True)
    
    sensor_meta = [
        ('traffic_light', 'Traffic Signal', 'Monitors vehicle throughput at a signalized intersection.'),
        ('water_meter', 'Water Utility', 'Tracks volumetric water flow at a municipal reservoir pump station.'),
        ('surveillance', 'Surveillance Camera', 'Security feed status for a public area monitoring node.'),
    ]
    
    cols = st.columns(3)
    for col, (key, label, tooltip) in zip(cols, sensor_meta):
        s = sc.sensors[key]
        is_secure = s['status'] == 'secure'
        with col:
            with st.container(border=True):
                st.markdown(f"**{label}**")
                st.caption(f"{s['location']}  ·  `{s['id']}`")
                
                m1, m2 = st.columns(2)
                m1.metric(
                    "QBER",
                    f"{s['qber']:.1f}%",
                    help=f"Quantum Bit Error Rate for this node. {tooltip} Values below 11% indicate a secure channel."
                )
                m2.metric(
                    "Status",
                    "SECURE" if is_secure else "BREACH",
                    help="SECURE: QBER < 11%, key exchange succeeded. BREACH: QBER >= 11%, key was aborted to prevent information leakage."
                )
                
                if s['last_key']:
                    st.code(f"AES-256 Key: {s['last_key'][:12]}...{s['last_key'][-6:]}", language=None)
                else:
                    st.code("AES-256 Key: ABORTED — threshold exceeded", language=None)
                
                if st.button("CRYPTOGRAPHIC PING", key=f"ping_{key}", use_container_width=True, help="Send a cryptographic challenge to this node. It must encrypt the response using its valid AES-256 key."):
                    success = sc.ping_node(key)
                    if success:
                        st.toast(f"Ping OK for {s['id']}")
                    else:
                        st.toast(f"Ping FAILED for {s['id']}")
                    st.rerun()
                
                if s['data_points']:
                    val = s['data_points'][-1]['value']
                    st.caption(f"Latest telemetry: **{val}**  ·  Updated: {s['last_update'].strftime('%H:%M:%S')}")
    
    # ══════════════════════════════════════════════════════════════
    # GEOSPATIAL MAP + QBER CHART (Side by Side)
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    
    map_col, chart_col = st.columns([1, 1])
    
    with map_col:
        st.markdown('<div class="section-hdr">Geospatial Node Distribution</div>', unsafe_allow_html=True)
        
        lats, lons, names, colors, hovers = [], [], [], [], []
        for s in sc.sensors.values():
            lats.append(s['lat'])
            lons.append(s['lon'])
            names.append(s['id'])
            c = '#EF4444' if s['status'] == 'compromised' else '#10B981'
            colors.append(c)
            hovers.append(f"{s['id']}<br>{s['location']}<br>QBER: {s['qber']:.1f}%<br>Status: {s['status'].upper()}")
        
        fig_map = go.Figure()
        
        # Attack pulse rings
        for s in sc.sensors.values():
            if s['status'] == 'compromised':
                fig_map.add_trace(go.Scattermapbox(
                    lat=[s['lat']], lon=[s['lon']], mode='markers',
                    marker=dict(size=40, color='#EF4444', opacity=0.25),
                    hoverinfo='none', showlegend=False
                ))
        
        fig_map.add_trace(go.Scattermapbox(
            lat=lats, lon=lons, mode='markers+text',
            marker=dict(size=14, color=colors, opacity=0.9),
            text=names, textposition="top center",
            textfont=dict(size=10, color="#F3F4F6", family="JetBrains Mono"),
            hoverinfo='text', hovertext=hovers, showlegend=False
        ))
        
        fig_map.update_layout(
            mapbox_style="carto-darkmatter",
            mapbox=dict(center=dict(lat=12.9732, lon=77.5966), zoom=12.5),
            margin=dict(l=0, r=0, t=0, b=0),
            height=340,
            paper_bgcolor="#080B10",
        )
        st.plotly_chart(fig_map, use_container_width=True)
    
    with chart_col:
        st.markdown('<div class="section-hdr">QBER Threat Assessment</div>', unsafe_allow_html=True)
        
        sensors_list = list(sc.sensors.values())
        bar_colors = ['#EF4444' if s['qber'] >= 11.0 else '#10B981' for s in sensors_list]
        
        fig_qber = go.Figure(go.Bar(
            x=[s['id'] for s in sensors_list],
            y=[s['qber'] for s in sensors_list],
            marker_color=bar_colors,
            text=[f"{s['qber']:.1f}%" for s in sensors_list],
            textposition='outside',
            textfont=dict(color='#F3F4F6', family="JetBrains Mono", size=12),
            hovertemplate="Node: %{x}<br>QBER: %{y:.1f}%<extra></extra>"
        ))
        
        fig_qber.add_hline(
            y=11.0, line_dash="dash", line_color="#EF4444", line_width=2,
            annotation_text="BB84 Security Threshold (11%)",
            annotation_font=dict(color="#EF4444", family="JetBrains Mono", size=11),
            annotation_position="top left"
        )
        
        fig_qber.update_layout(
            template="plotly_dark",
            paper_bgcolor="#080B10", plot_bgcolor="#0E131F",
            margin=dict(l=40, r=20, t=20, b=40),
            height=340,
            yaxis=dict(title="QBER (%)", range=[0, max(35, max(s['qber'] for s in sensors_list) + 8)], gridcolor="#162032"),
            xaxis=dict(gridcolor="#162032"),
        )
        st.plotly_chart(fig_qber, use_container_width=True)
    
    # ══════════════════════════════════════════════════════════════
    # TELEMETRY TABLE + TERMINAL (Side by Side)
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    
    tbl_col, term_col = st.columns([1, 1])
    
    with tbl_col:
        st.markdown('<div class="section-hdr">Node Telemetry Matrix</div>', unsafe_allow_html=True)
        
        rows = []
        for s in sc.sensors.values():
            latest = s['data_points'][-1]['value'] if s['data_points'] else 'N/A'
            key_hash = f"{s['last_key'][:8]}...{s['last_key'][-4:]}" if s['last_key'] else "ABORTED"
            rows.append({
                'Node ID': s['id'],
                'Location': s['location'],
                'QBER (%)': round(s['qber'], 1),
                'Payload': str(latest),
                'AES-256 Key': key_hash,
                'State': s['status'].upper()
            })
        
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "QBER (%)": st.column_config.NumberColumn(format="%.1f%%", help="Quantum Bit Error Rate — percentage of mismatched sifted key bits between Alice and Bob"),
                "AES-256 Key": st.column_config.TextColumn(help="Truncated SHA-256 digest of the BB84 sifted key. Used for AES-GCM-256 payload encryption."),
                "State": st.column_config.TextColumn(help="SECURE if QBER < 11%, COMPROMISED if QBER >= 11%."),
                "Payload": st.column_config.TextColumn(help="Latest sensor telemetry reading from this node."),
            }
        )
    
    with term_col:
        st.markdown('<div class="section-hdr">Cryptographic Handshake Log</div>', unsafe_allow_html=True)
        
        lines = []
        for entry in reversed(sc.terminal_logs):
            ts = entry['ts']
            level = entry['level']
            msg = entry['msg']
            
            if level == "SECURE":
                lines.append(f'<span class="tl-ts">[{ts}]</span> <span class="tl-secure">{msg}</span>')
            elif level == "WARN":
                lines.append(f'<span class="tl-ts">[{ts}]</span> <span class="tl-warn">{msg}</span>')
            elif level == "ALERT":
                lines.append(f'<span class="tl-ts">[{ts}]</span> <span class="tl-alert">{msg}</span>')
            else:
                lines.append(f'<span class="tl-ts">[{ts}]</span> <span class="tl-info">{msg}</span>')
        
        term_content = "<br>".join(lines) if lines else '<span class="tl-info">Awaiting handshake cycles...</span>'
        st.markdown(f'<div class="term-output">{term_content}</div>', unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════════
    # TREND CHARTS (Tabbed)
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown('<div class="section-hdr">Telemetry & QBER Time Series</div>', unsafe_allow_html=True)
    
    tab_labels = ["Traffic Signal", "Water Utility", "Surveillance"]
    tab_keys = ['traffic_light', 'water_meter', 'surveillance']
    tabs = st.tabs(tab_labels)
    
    for tab, key in zip(tabs, tab_keys):
        with tab:
            s = sc.sensors[key]
            if len(s['data_points']) >= 2:
                df_t = pd.DataFrame(s['data_points'])
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_t['time'], y=df_t['value'],
                    mode='lines+markers', name='Telemetry',
                    line=dict(color='#3B82F6', width=2),
                    hovertemplate="Value: %{y}<br>Time: %{x}<extra></extra>"
                ))
                fig.add_trace(go.Scatter(
                    x=df_t['time'], y=df_t['qber'],
                    mode='lines+markers', name='QBER (%)', yaxis='y2',
                    line=dict(color='#EF4444', width=2, dash='dash'),
                    hovertemplate="QBER: %{y:.1f}%<br>Time: %{x}<extra></extra>"
                ))
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#080B10", plot_bgcolor="#0E131F",
                    margin=dict(l=40, r=40, t=20, b=40),
                    height=280,
                    yaxis=dict(title="Telemetry Value", gridcolor="#162032"),
                    yaxis2=dict(title="QBER (%)", overlaying="y", side="right",
                                range=[0, max(35, df_t['qber'].max() + 5)], gridcolor="#162032"),
                    xaxis=dict(gridcolor="#162032"),
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Collecting data points — click 'Execute Telemetry Cycle' to generate readings.")
    
    # ══════════════════════════════════════════════════════════════
    # SECURITY AUDIT LOG
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    
    with st.expander("Security Audit Event Log", expanded=False):
        events = []
        for s in sc.sensors.values():
            if s['status'] == 'compromised':
                events.append({
                    'Time': s['last_update'].strftime('%H:%M:%S'),
                    'Node': s['id'],
                    'Location': s['location'],
                    'Event': 'ATTACK DETECTED',
                    'QBER': f"{s['qber']:.1f}%",
                    'Action': 'Key aborted, transmission blocked'
                })
            elif s['last_key']:
                events.append({
                    'Time': s['last_update'].strftime('%H:%M:%S'),
                    'Node': s['id'],
                    'Location': s['location'],
                    'Event': 'KEY EXCHANGE OK',
                    'QBER': f"{s['qber']:.1f}%",
                    'Action': f"Encrypted via AES-256 ({s['last_key'][:8]}...)"
                })
        
        if events:
            st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
        else:
            st.caption("No security events recorded yet.")
    
    # ══════════════════════════════════════════════════════════════
    # BB84 PROTOCOL REFERENCE
    # ══════════════════════════════════════════════════════════════
    with st.expander("BB84 Protocol Reference", expanded=False):
        st.markdown("""
**BB84 Quantum Key Distribution Protocol**

1. **Quantum State Preparation** — Alice encodes random bits into photon polarization states using randomly chosen rectilinear or diagonal bases.
2. **Quantum Transmission** — Photons travel through the quantum channel to Bob.
3. **Measurement** — Bob measures each photon in a randomly chosen basis.
4. **Basis Reconciliation (Sifting)** — Alice and Bob publicly compare bases and keep only bits where they used the same basis.
5. **QBER Estimation** — A random sample of sifted bits is compared to estimate the Quantum Bit Error Rate.
6. **Security Decision** — If QBER ≥ 11%, the exchange is aborted (eavesdropper detected). If QBER < 11%, the remaining sifted bits undergo privacy amplification.
7. **Key Derivation** — SHA-256 hashing produces a 256-bit AES-GCM symmetric key for payload encryption.
        """)

if __name__ == "__main__":
    main()