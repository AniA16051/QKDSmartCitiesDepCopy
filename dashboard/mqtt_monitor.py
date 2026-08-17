"""
Background MQTT listener for the dashboard.

Runs a paho-mqtt client on its own thread, subscribing to the same topics
control_center.py listens to (session status, sensor data, security events),
and keeps a thread-safe in-memory snapshot of the latest state per node.

The Streamlit app polls this snapshot on every rerun -- it never talks to
MQTT directly, so the dashboard stays responsive even if the broker is slow.
"""

import json
import threading
import time
import os
from collections import deque
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from core.crypto_layer import decrypt_payload
from network.shared_keystore import load_key

# Support both environment variables (Docker) and defaults (local)
BROKER_HOST = os.getenv("BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
BROKER_USERNAME = os.getenv("BROKER_USERNAME", None)
BROKER_PASSWORD = os.getenv("BROKER_PASSWORD", None)
BROKER_USE_TLS = os.getenv("BROKER_USE_TLS", "false").lower() == "true"



MAX_EVENT_LOG = 30
MAX_READINGS_PER_NODE = 20
MAX_QBER_HISTORY = 40


class MqttMonitor:
    def __init__(self):
        self._lock = threading.Lock()
        self._nodes = {}          # node_id -> dict(status, qber, fingerprint, last_seen)
        self._readings = {}       # node_id -> deque of recent decrypted readings
        self._qber_history = {}   # node_id -> deque of (timestamp, qber)
        self._events = deque(maxlen=MAX_EVENT_LOG)
        self._connected = False

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="dashboard-monitor")
        if BROKER_USERNAME and BROKER_PASSWORD:
            self._client.username_pw_set(BROKER_USERNAME, BROKER_PASSWORD)
        if BROKER_USE_TLS:
            self._client.tls_set()
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while True:
            try:
                self._client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
                self._client.loop_forever()
            except Exception:
                with self._lock:
                    self._connected = False
                time.sleep(3)  # retry if the broker isn't up yet

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        with self._lock:
            self._connected = (reason_code == 0)
        client.subscribe("smartcity/+/session_key", qos=1)
        client.subscribe("smartcity/+/data", qos=1)
        client.subscribe("smartcity/security/events", qos=1)

    def _on_message(self, client, userdata, msg):
        try:
            parts = msg.topic.split("/")
            node_id = parts[1]
            channel = parts[2] if len(parts) > 2 else None

            if msg.topic == "smartcity/security/events":
                event = json.loads(msg.payload.decode("utf-8"))
                with self._lock:
                    self._events.appendleft(event)
                return

            if channel == "session_key":
                meta = json.loads(msg.payload.decode("utf-8"))
                now = datetime.now(timezone.utc)
                new_status = meta.get("status")
                with self._lock:
                    prev = self._nodes.get(node_id)
                    was_aborted = prev is not None and prev.get("status") == "aborted"
                    recovered = was_aborted and new_status == "ok"

                    self._nodes[node_id] = {
                        "status": new_status,
                        "qber": meta.get("qber"),
                        "fingerprint": meta.get("key_fingerprint"),
                        "last_seen": now.isoformat(),
                        "just_recovered": recovered,
                    }
                    qber_val = meta.get("qber")
                    if qber_val is not None:
                        if node_id not in self._qber_history:
                            self._qber_history[node_id] = deque(maxlen=MAX_QBER_HISTORY)
                        self._qber_history[node_id].append((now, qber_val))

                    if recovered:
                        self._events.appendleft({
                            "node_id": node_id,
                            "reason": "recovered",
                            "qber": qber_val,
                            "timestamp": now.isoformat(),
                        })

            elif channel == "data":
                key = load_key(node_id)
                if key is None:
                    with self._lock:
                        self._events.appendleft({
                            "node_id": node_id,
                            "reason": "rejected_no_key",
                            "qber": None,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    return
                encrypted = json.loads(msg.payload.decode("utf-8"))
                try:
                    payload = decrypt_payload(key, encrypted)
                except Exception:
                    with self._lock:
                        self._events.appendleft({
                            "node_id": node_id,
                            "reason": "decrypt_failed",
                            "qber": None,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    return

                with self._lock:
                    if node_id not in self._readings:
                        self._readings[node_id] = deque(maxlen=MAX_READINGS_PER_NODE)
                    self._readings[node_id].appendleft(payload)

        except Exception as e:
            with self._lock:
                self._events.appendleft({
                    "node_id": "dashboard",
                    "reason": f"internal_error: {e}",
                    "qber": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    def snapshot(self):
        """Returns a plain-data copy of current state, safe to read from Streamlit."""
        with self._lock:
            return {
                "connected": self._connected,
                "nodes": dict(self._nodes),
                "readings": {k: list(v) for k, v in self._readings.items()},
                "qber_history": {k: list(v) for k, v in self._qber_history.items()},
                "events": list(self._events),
            }