"""
Simulates a smart city network: several IoT sensor nodes (traffic light,
water meter, surveillance camera) each independently perform a BB84 key
exchange with a central control center, then use the derived key to send
an encrypted sensor reading. Includes an optional eavesdropper on any node's
channel and an optional noisy channel.
"""

import random
import time
from datetime import datetime, timezone

from core.bb84 import run_bb84
from core.crypto_layer import derive_aes_key, encrypt_payload, decrypt_payload


class ControlCenter:
    """Represents 'Bob' -- the central hub receiving sensor data."""

    def __init__(self):
        self.session_keys = {}   # node_id -> AES key
        self.received_log = []

    def register_session_key(self, node_id, key_bytes):
        self.session_keys[node_id] = key_bytes

    def receive(self, node_id, encrypted_payload):
        key = self.session_keys.get(node_id)
        if key is None:
            raise RuntimeError(f"No session key established for {node_id} -- rejecting message")
        payload = decrypt_payload(key, encrypted_payload)
        self.received_log.append((node_id, payload))
        return payload


class SensorNode:
    """Represents 'Alice' -- an IoT device in the smart city."""

    def __init__(self, node_id, sensor_type, reading_fn):
        self.node_id = node_id
        self.sensor_type = sensor_type
        self.reading_fn = reading_fn
        self.session_key = None
        self.qkd_status = None

    def establish_session(self, control_center, n_qubits=512, eavesdropper=False,
                           depolarizing_prob=0.0):
        result = run_bb84(
            n_qubits=n_qubits,
            eavesdropper=eavesdropper,
            depolarizing_prob=depolarizing_prob,
        )
        self.qkd_status = result

        if result["aborted"] or len(result["final_key"]) == 0:
            self.session_key = None
            return False

        key = derive_aes_key(result["final_key"])
        self.session_key = key
        control_center.register_session_key(self.node_id, key)
        return True

    def send_reading(self, control_center):
        if self.session_key is None:
            raise RuntimeError(
                f"[{self.node_id}] No secure session -- refusing to transmit "
                f"(QKD failed or was aborted, likely due to eavesdropping/noise)"
            )
        payload = {
            "sensor_id": self.node_id,
            "type": self.sensor_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **self.reading_fn(),
        }
        encrypted = encrypt_payload(self.session_key, payload)
        return control_center.receive(self.node_id, encrypted)


# --- Simulated sensor reading generators -----------------------------------

def traffic_light_reading():
    return {
        "vehicles_per_min": random.randint(5, 60),
        "avg_speed_kmph": round(random.uniform(15, 55), 1),
        "signal_state": random.choice(["green", "yellow", "red"]),
    }


def water_meter_reading():
    return {
        "flow_rate_lpm": round(random.uniform(2, 40), 2),
        "cumulative_liters": round(random.uniform(1000, 50000), 1),
    }


def surveillance_camera_reading():
    return {
        "motion_detected": random.choice([True, False]),
        "object_count": random.randint(0, 12),
    }


def run_smart_city_simulation(eavesdrop_on=None, depolarizing_prob=0.0):
    """
    eavesdrop_on: list of node_ids that Eve is attacking, or None for a clean run.
    """
    eavesdrop_on = eavesdrop_on or []

    control_center = ControlCenter()

    nodes = [
        SensorNode("traffic-node-07", "traffic_flow", traffic_light_reading),
        SensorNode("water-meter-14", "water_flow", water_meter_reading),
        SensorNode("camera-22", "surveillance", surveillance_camera_reading),
    ]

    print("=" * 70)
    print("SMART CITY QKD-SECURED IoT NETWORK -- SESSION START")
    print("=" * 70)

    for node in nodes:
        is_attacked = node.node_id in eavesdrop_on
        print(f"\n[{node.node_id}] Initiating BB84 key exchange with control center "
              f"{'(EAVESDROPPER PRESENT)' if is_attacked else '(clean channel)'}...")

        success = node.establish_session(
            control_center,
            n_qubits=512,
            eavesdropper=is_attacked,
            depolarizing_prob=depolarizing_prob,
        )

        qber = node.qkd_status["qber"]
        print(f"  QBER measured: {qber:.2%}" if qber is not None else "  QBER: N/A (no sifted bits)")

        if success:
            print(f"  Session key established ({len(node.qkd_status['final_key'])} bits -> AES-256 key)")
            try:
                received = node.send_reading(control_center)
                print(f"  Encrypted reading sent and decrypted successfully by control center:")
                print(f"    {received}")
            except Exception as e:
                print(f"  ERROR sending reading: {e}")
        else:
            print(f"  ABORTED -- QBER exceeded security threshold. "
                  f"Node will NOT transmit data over a compromised channel.")

    print("\n" + "=" * 70)
    print(f"SESSION SUMMARY: {len(control_center.received_log)}/{len(nodes)} "
          f"nodes successfully transmitted secure data")
    print("=" * 70)

    return control_center


if __name__ == "__main__":
    print("\n\n########## SCENARIO 1: Normal operation, no eavesdropper ##########\n")
    run_smart_city_simulation(eavesdrop_on=None)

    print("\n\n########## SCENARIO 2: Eve attacks the camera node ##########\n")
    run_smart_city_simulation(eavesdrop_on=["camera-22"])
