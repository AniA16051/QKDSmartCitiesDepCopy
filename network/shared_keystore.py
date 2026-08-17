"""
Stands in for the physical quantum channel (the fiber-optic link) between a
sensor node and the control center.

WHY THIS EXISTS (be upfront about this in your report):
Real BB84 needs an actual quantum channel -- photons physically travelling
from Alice to Bob -- which is what lets Bob's measurement depend on Alice's
qubit and Eve's interference. We don't have real photons or two independent
quantum simulators wired together over a network in this project, so BB84
itself still runs as ONE combined simulation (Alice+Bob+optional Eve, all
inside core/bb84.py) at the sensor-node process. This file is where that
run's *result* (the shared secret key) is deposited, standing in for "the
photons arrived and both sides now share a secret."

MQTT, in contrast, plays the role of the AUTHENTICATED CLASSICAL CHANNEL that
real QKD systems also require -- it only ever carries metadata (QBER, whether
the session succeeded, key fingerprints) and the AES-encrypted sensor data.
The raw key bits are never published to MQTT. This mirrors the real-world
fact that QKD's classical channel is public but authenticated, while the key
material itself never leaves the quantum channel.

Honest limitation for the report: because both "ends" of the quantum channel
are simulated in the same process/machine, this does not model quantum-channel
attacks that depend on physical distance, fiber loss over real hardware, or
network-level tampering with the key material itself -- only the classical
metadata channel (MQTT) is exposed to that kind of tampering here.
"""

import json
import os
import threading

_LOCK = threading.Lock()
_STORE_PATH = os.path.join(os.path.dirname(__file__), ".keystore.json")


def _read_store():
    if not os.path.exists(_STORE_PATH):
        return {}
    with open(_STORE_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _write_store(data):
    with open(_STORE_PATH, "w") as f:
        json.dump(data, f)


def save_key(node_id, key_bytes):
    """Persist a node's derived AES key (as hex) after a successful BB84 run."""
    with _LOCK:
        store = _read_store()
        store[node_id] = key_bytes.hex()
        _write_store(store)


def load_key(node_id):
    """Retrieve a node's AES key. Returns None if no valid session exists."""
    with _LOCK:
        store = _read_store()
        hex_key = store.get(node_id)
        if hex_key is None:
            return None
        return bytes.fromhex(hex_key)


def revoke_key(node_id):
    """Remove a node's session key (e.g. after an aborted/compromised exchange)."""
    with _LOCK:
        store = _read_store()
        if node_id in store:
            del store[node_id]
            _write_store(store)
