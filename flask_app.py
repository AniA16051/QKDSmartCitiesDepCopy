#!/usr/bin/env python3
"""
Flask-based QKD Dashboard for Cloud Deployment
Production-ready alternative to Streamlit that works consistently across all platforms
"""

import os
import json
import random
import time
import threading
import ssl
import hashlib
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import paho.mqtt.client as mqtt

app = Flask(__name__)

# Configuration for MQTT broker
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
MQTT_TOPIC = "qkd/smartcity/data"

# Global state for dashboard
dashboard_state = {
    'sensor_data': [],
    'qkd_metrics': [],
    'mqtt_connected': False,
    'last_update': None
}

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
        alice_bits = UnifiedBB84.generate_key(key_length)
        alice_bases = UnifiedBB84.generate_bases(key_length)
        bob_bases = UnifiedBB84.generate_bases(key_length)
        
        bob_bits = np.zeros(key_length, dtype=int)
        
        if attack:
            eve_bases = UnifiedBB84.generate_bases(key_length)
            eve_bits = np.zeros(key_length, dtype=int)
            for i in range(key_length):
                if alice_bases[i] == eve_bases[i]:
                    eve_bits[i] = alice_bits[i]
                else:
                    eve_bits[i] = random.randint(0, 1)
            
            for i in range(key_length):
                if eve_bases[i] == bob_bases[i]:
                    bob_bits[i] = eve_bits[i]
                else:
                    bob_bits[i] = random.randint(0, 1)
        else:
            for i in range(key_length):
                if alice_bases[i] == bob_bases[i]:
                    bob_bits[i] = alice_bits[i]
                else:
                    bob_bits[i] = random.randint(0, 1)
        
        matching_bases = (alice_bases == bob_bases)
        sifted_alice = alice_bits[matching_bases]
        sifted_bob = bob_bits[matching_bases]
        
        if len(sifted_alice) == 0:
            return {
                'key_length': key_length,
                'sifted_key_length': 0,
                'qber': 1.0,
                'matching_bases': 0,
                'attack_detected': True,
                'alice_bits': alice_bits.tolist(),
                'bob_bits': bob_bits.tolist(),
                'sifted_key': []
            }
        
        errors = np.sum(sifted_alice != sifted_bob)
        qber = float(errors) / len(sifted_alice)
        
        return {
            'key_length': key_length,
            'sifted_key_length': len(sifted_alice),
            'qber': qber,
            'matching_bases': int(matching_bases.sum()),
            'attack_detected': qber >= 0.11,
            'alice_bits': alice_bits.tolist(),
            'bob_bits': bob_bits.tolist(),
            'sifted_key': sifted_alice.tolist()
        }

# MQTT Client setup
mqtt_client = None

def setup_mqtt():
    """Setup MQTT client with TLS support"""
    global mqtt_client
    
    def on_connect(client, userdata, flags, rc, properties=None):
        global dashboard_state
        if rc == 0:
            dashboard_state['mqtt_connected'] = True
            client.subscribe(MQTT_TOPIC)
        else:
            dashboard_state['mqtt_connected'] = False
    
    def on_message(client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            dashboard_state['sensor_data'].append(data)
            if len(dashboard_state['sensor_data']) > 100:
                dashboard_state['sensor_data'].pop(0)
            dashboard_state['last_update'] = datetime.now().isoformat()
        except:
            pass
    
    try:
        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="qkd_dashboard_flask")
    except AttributeError:
        mqtt_client = mqtt.Client(client_id="qkd_dashboard_flask")
        
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    if MQTT_USERNAME and MQTT_PASSWORD:
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    if MQTT_USE_TLS or MQTT_PORT == 8883:
        try:
            mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
            mqtt_client.tls_insecure_set(True)
        except Exception:
            pass
    
    try:
        mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"MQTT connection failed: {e}")
        dashboard_state['mqtt_connected'] = False

# Background simulation thread
def simulate_sensor_data():
    """Simulate IoT sensor data in background"""
    sensor_types = ['traffic_flow', 'water_consumption', 'security_monitoring']
    locations = ['Main St & 5th Ave', 'Downtown Reservoir', 'Central Park']
    
    while True:
        try:
            attack_active = random.random() < 0.1
            qkd_result = UnifiedBB84.simulate_bb84_protocol(attack=attack_active)
            
            sensor_data = {
                'timestamp': datetime.now().isoformat(),
                'sensor_type': random.choice(sensor_types),
                'location': random.choice(locations),
                'value': round(random.uniform(20, 80), 1),
                'qkd_status': 'encrypted' if not attack_active else 'compromised',
                'qber': qkd_result['qber'],
                'attack_detected': qkd_result['attack_detected']
            }
            
            dashboard_state['sensor_data'].append(sensor_data)
            dashboard_state['qkd_metrics'].append(qkd_result)
            
            if len(dashboard_state['sensor_data']) > 100:
                dashboard_state['sensor_data'].pop(0)
            if len(dashboard_state['qkd_metrics']) > 100:
                dashboard_state['qkd_metrics'].pop(0)
            
            dashboard_state['last_update'] = datetime.now().isoformat()
            
            if mqtt_client and dashboard_state['mqtt_connected']:
                try:
                    mqtt_client.publish(MQTT_TOPIC, json.dumps(sensor_data))
                except Exception:
                    pass
        except Exception as e:
            print(f"Simulation error: {e}")
        
        time.sleep(3)

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    """API endpoint for real-time data"""
    return jsonify({
        'sensor_data': dashboard_state['sensor_data'][-20:],
        'qkd_metrics': dashboard_state['qkd_metrics'][-10:],
        'mqtt_connected': dashboard_state['mqtt_connected'],
        'last_update': dashboard_state['last_update']
    })

@app.route('/api/qkd-simulate')
def simulate_qkd():
    """Manually trigger QKD simulation"""
    attack = request.args.get('attack', 'false').lower() == 'true'
    result = UnifiedBB84.simulate_bb84_protocol(attack=attack)
    return jsonify(result)

@app.route('/api/chart/<chart_type>')
def get_chart(chart_type):
    """Generate Plotly charts"""
    if not dashboard_state['sensor_data']:
        return jsonify({'error': 'No data available'})
    
    df = pd.DataFrame(dashboard_state['sensor_data'])
    
    if chart_type == 'sensor-timeline':
        fig = px.line(df, x='timestamp', y='value', color='sensor_type',
                     title='Sensor Data Timeline')
    elif chart_type == 'qber-trend':
        fig = px.line(df, x='timestamp', y='qber',
                     title='Quantum Bit Error Rate Trend')
    elif chart_type == 'attack-status':
        attack_counts = df['attack_detected'].value_counts()
        fig = px.pie(values=attack_counts.values, names=attack_counts.index,
                     title='Attack Detection Status')
    else:
        return jsonify({'error': 'Invalid chart type'})
    
    return jsonify({'chart': fig.to_json()})

# Start background services once on module load
_bg_started = False
if not _bg_started:
    _bg_started = True
    setup_mqtt()
    sim_thread = threading.Thread(target=simulate_sensor_data, daemon=True)
    sim_thread.start()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)