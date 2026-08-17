"""
Sensor Node -- runs as its own standalone process representing one IoT
device (traffic light, water meter, camera, etc).

On startup:
  1. Runs a BB84 key exchange (via core.bb84.run_bb84) to establish a shared
     secret with the control center.
  2. Publishes the exchange METADATA (QBER, success/fail, key fingerprint) to
     MQTT for the control center and any monitoring dashboard to see.
  3. Saves the derived AES key to the shared keystore (standing in for the
     physical quantum channel -- see shared_keystore.py for why).
  4. Periodically publishes encrypted sensor readings.

Requires the control center to be running first, and a local MQTT broker
(Mosquitto) on localhost:1883.

Usage:
    python3 -m network.sensor_node --id traffic-node-07 --type traffic_flow
    python3 -m network.sensor_node --id camera-22 --type surveillance --eavesdrop
    python3 -m network.sensor_node --id water-meter-14 --type water_flow --noise 0.05
"""

import argparse
import hashlib
import json
import random
import sys
import os
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.bb84 import run_bb84
from core.crypto_layer import derive_aes_key, encrypt_payload
from network.shared_keystore import save_key, revoke_key

# Support both environment variables (Docker) and defaults (local)
BROKER_HOST = os.getenv("BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
BROKER_USERNAME = os.getenv("BROKER_USERNAME", None)
BROKER_PASSWORD = os.getenv("BROKER_PASSWORD", None)
BROKER_USE_TLS = os.getenv("BROKER_USE_TLS", "false").lower() == "true"




READING_GENERATORS = {
    "traffic_flow": lambda: {
        "vehicles_per_min": random.randint(5, 60),
        "avg_speed_kmph": round(random.uniform(15, 55), 1),
        "signal_state": random.choice(["green", "yellow", "red"]),
    },
    "water_flow": lambda: {
        "flow_rate_lpm": round(random.uniform(2, 40), 2),
        "cumulative_liters": round(random.uniform(1000, 50000), 1),
    },
    "surveillance": lambda: {
        "motion_detected": random.choice([True, False]),
        "object_count": random.randint(0, 12),
    },
}


class SensorNode:
    def __init__(self, node_id, sensor_type, eavesdrop=False, noise=0.0,
                 n_qubits=512, interval=5):
        if sensor_type not in READING_GENERATORS:
            raise ValueError(f"Unknown sensor_type '{sensor_type}'. "
                              f"Choose from: {list(READING_GENERATORS)}")

        self.node_id = node_id
        self.sensor_type = sensor_type
        self.eavesdrop = eavesdrop
        self.noise = noise
        self.n_qubits = n_qubits
        self.interval = interval
        self.session_key = None

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=node_id)
        if BROKER_USERNAME and BROKER_PASSWORD:
            self.client.username_pw_set(BROKER_USERNAME, BROKER_PASSWORD)
        if BROKER_USE_TLS:
            self.client.tls_set()

    def establish_session(self):
        """Runs BB84 (with optional Eve / channel noise) and publishes the result."""
        print(f"[{self.node_id}] Running BB84 key exchange "
              f"{'(EAVESDROPPER ACTIVE)' if self.eavesdrop else '(clean channel)'}"
              f"{f', noise={self.noise:.0%}' if self.noise else ''}...")

        result = run_bb84(
            n_qubits=self.n_qubits,
            eavesdropper=self.eavesdrop,
            depolarizing_prob=self.noise,
        )

        qber = result["qber"]

        if result["aborted"] or len(result["final_key"]) == 0:
            print(f"[{self.node_id}] Session ABORTED. QBER={qber:.2%} exceeded "
                  f"security threshold -- refusing to establish a key.")
            revoke_key(self.node_id)
            self._publish_session_status(status="aborted", qber=qber)
            self._publish_security_event(reason="qber_threshold_exceeded", qber=qber)
            self.session_key = None
            return False

        key = derive_aes_key(result["final_key"])
        self.session_key = key
        save_key(self.node_id, key)

        fingerprint = hashlib.sha256(key).hexdigest()[:16]
        print(f"[{self.node_id}] Session established. QBER={qber:.2%}, "
              f"final key length={len(result['final_key'])} bits, "
              f"fingerprint={fingerprint}")

        self._publish_session_status(status="ok", qber=qber, fingerprint=fingerprint)
        return True

    def _publish_session_status(self, status, qber, fingerprint=None):
        meta = {
            "node_id": self.node_id,
            "status": status,
            "qber": qber,
            "key_fingerprint": fingerprint,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.client.publish(f"smartcity/{self.node_id}/session_key",
                             json.dumps(meta), qos=1)

    def _publish_security_event(self, reason, qber):
        event = {
            "node_id": self.node_id,
            "reason": reason,
            "qber": qber,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.client.publish("smartcity/security/events", json.dumps(event), qos=1)

    def send_reading(self):
        if self.session_key is None:
            print(f"[{self.node_id}] No active session -- skipping transmission "
                  f"(will retry key exchange next cycle)")
            return

        reading = READING_GENERATORS[self.sensor_type]()
        payload = {
            "sensor_id": self.node_id,
            "type": self.sensor_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **reading,
        }
        encrypted = encrypt_payload(self.session_key, payload)
        self.client.publish(f"smartcity/{self.node_id}/data",
                             json.dumps(encrypted), qos=1)
        print(f"[{self.node_id}] Sent encrypted reading: {reading}")

    def run(self):
        self.client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        self.client.loop_start()
        time.sleep(0.5)  # let the connection settle before publishing

        try:
            while True:
                self.establish_session()
                if self.session_key:
                    self.send_reading()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print(f"\n[{self.node_id}] Shutting down.")
        finally:
            self.client.loop_stop()
            self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Run a smart city sensor node")
    parser.add_argument("--id", required=True, help="Unique node ID, e.g. traffic-node-07")
    parser.add_argument("--type", required=True, choices=list(READING_GENERATORS),
                         help="Sensor type")
    parser.add_argument("--eavesdrop", action="store_true",
                         help="Simulate an eavesdropper (Eve) on this node's channel")
    parser.add_argument("--noise", type=float, default=0.0,
                         help="Channel depolarizing noise probability (0.0-0.3)")
    parser.add_argument("--qubits", type=int, default=512,
                         help="Number of qubits per BB84 exchange")
    parser.add_argument("--interval", type=int, default=10,
                         help="Seconds between key-refresh + reading cycles")
    args = parser.parse_args()

    node = SensorNode(
        node_id=args.id,
        sensor_type=args.type,
        eavesdrop=args.eavesdrop,
        noise=args.noise,
        n_qubits=args.qubits,
        interval=args.interval,
    )
    node.run()


if __name__ == "__main__":
    main()