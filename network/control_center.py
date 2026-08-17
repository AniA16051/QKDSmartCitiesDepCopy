"""
Control Center -- runs as its own standalone process.

Listens on MQTT for:
  1. Key-exchange session announcements from sensor nodes (so it knows which
     AES key belongs to which node)
  2. Encrypted sensor readings, which it decrypts and logs

This replaces the in-process ControlCenter class from smart_city_sim.py with
a real network service reachable over MQTT.

Run this FIRST, before starting any sensor nodes, and leave it running.

Requires a local MQTT broker (Mosquitto) running on localhost:1883.
"""

import json
import sys
import os

import paho.mqtt.client as mqtt

# Allow running this file directly (python3 network/control_center.py)
# as well as as a module (python3 -m network.control_center)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.crypto_layer import decrypt_payload
from network.shared_keystore import load_key

# Support both environment variables (Docker) and defaults (local)
BROKER_HOST = os.getenv("BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
BROKER_USERNAME = os.getenv("BROKER_USERNAME", None)
BROKER_PASSWORD = os.getenv("BROKER_PASSWORD", None)
BROKER_USE_TLS = os.getenv("BROKER_USE_TLS", "false").lower() == "true"



TOPIC_SESSION_KEY = "smartcity/+/session_key"     # + = wildcard for node_id
TOPIC_SENSOR_DATA = "smartcity/+/data"
TOPIC_SECURITY_EVENTS = "smartcity/security/events"


class ControlCenterService:
    def __init__(self):
        self.session_keys = {}  # node_id -> bytes (AES key)
        self.received_log = []

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="control-center")
        if BROKER_USERNAME and BROKER_PASSWORD:
            self.client.username_pw_set(BROKER_USERNAME, BROKER_PASSWORD)
        if BROKER_USE_TLS:
            self.client.tls_set()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"[control-center] Connected to broker at {BROKER_HOST}:{BROKER_PORT}")
        else:
            print(f"[control-center] Connection failed: {reason_code}")
            return

        client.subscribe(TOPIC_SESSION_KEY, qos=1)
        client.subscribe(TOPIC_SENSOR_DATA, qos=1)
        client.subscribe(TOPIC_SECURITY_EVENTS, qos=1)
        print(f"[control-center] Subscribed to: {TOPIC_SESSION_KEY}, "
              f"{TOPIC_SENSOR_DATA}, {TOPIC_SECURITY_EVENTS}")
        print("[control-center] Waiting for sensor nodes...\n")

    def on_message(self, client, userdata, msg):
        try:
            parts = msg.topic.split("/")
            node_id = parts[1]
            channel = parts[2] if len(parts) > 2 else None

            if msg.topic == TOPIC_SECURITY_EVENTS:
                event = json.loads(msg.payload.decode("utf-8"))
                print(f"[SECURITY EVENT] node={event.get('node_id')} "
                      f"reason={event.get('reason')} qber={event.get('qber')}")
                return

            if channel == "session_key":
                self._handle_session_key(node_id, msg.payload)
            elif channel == "data":
                self._handle_sensor_data(node_id, msg.payload)

        except Exception as e:
            print(f"[control-center] Error handling message on {msg.topic}: {e}")

    def _handle_session_key(self, node_id, payload_bytes):
        """
        The session key itself is never sent over MQTT in the clear --
        this message just carries METADATA about a completed BB84 exchange
        (QBER, key length, success/fail). The actual key bytes are derived
        independently on each side from the BB84 protocol run, mirroring
        how real QKD systems never transmit the key over the classical
        channel at all -- only basis-reconciliation and QBER-check data does.

        For this simulation, since Alice and Bob are separate OS processes,
        we take a pragmatic shortcut: the node includes the derived key's
        SHA-256 fingerprint so we can log/verify, but for actual decryption
        capability in this local demo, run_bb84() is executed at the node
        and the control center trusts the registered key hash.

        NOTE: see README for the honest caveat this implies for a real
        deployment vs. this local simulation.
        """
        meta = json.loads(payload_bytes.decode("utf-8"))
        status = meta.get("status")
        qber = meta.get("qber")

        if status == "aborted":
            print(f"[{node_id}] Session ABORTED -- QBER={qber:.2%} exceeded threshold. "
                  f"No key registered, this node cannot send data.")
            self.session_keys.pop(node_id, None)
            return

        print(f"[{node_id}] Secure session established. QBER={qber:.2%}, "
              f"key_fingerprint={meta.get('key_fingerprint')}")
        # Register that this node now has a valid session (key itself
        # arrives via the local key-store file the node also writes --
        # see sensor_node.py / shared_keystore.py)
        self.session_keys[node_id] = meta.get("key_fingerprint")

    def _handle_sensor_data(self, node_id, payload_bytes):
        key = load_key(node_id)
        if key is None:
            print(f"[{node_id}] REJECTED message -- no valid session key on file "
                  f"(possible replay or the session was never established)")
            return

        encrypted = json.loads(payload_bytes.decode("utf-8"))
        try:
            payload = decrypt_payload(key, encrypted)
        except Exception as e:
            print(f"[{node_id}] REJECTED message -- decryption failed ({e}). "
                  f"Possible tampering or wrong key.")
            return

        self.received_log.append((node_id, payload))
        print(f"[{node_id}] Decrypted reading: {payload}")

    def run(self):
        self.client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        self.client.loop_forever()


if __name__ == "__main__":
    service = ControlCenterService()
    try:
        service.run()
    except KeyboardInterrupt:
        print("\n[control-center] Shutting down.")