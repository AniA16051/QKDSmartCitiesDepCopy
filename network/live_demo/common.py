"""
Shared configuration and helpers for the live, real-network BB84 demo.

This is a DIFFERENT implementation from core/bb84.py. That file simulates
the entire Alice-Bob(-Eve) exchange inside one Qiskit function call on one
machine. This one genuinely splits Alice, Bob, and (optionally) Eve into
three separate programs that pass real messages over MQTT across real
computers on your network.

IMPORTANT HONEST LIMITATION (put this in your report):
Real BB84 security depends on transmitting actual quantum states -- copying
a qubit mid-transit is physically impossible (no-cloning theorem), which is
what makes eavesdropping detectable. Here, since qubits must travel over an
ordinary WiFi network as normal computer messages, they are represented as
plain classical data (a bit + a basis choice). Classical data CAN be copied
perfectly by anyone with network access -- there is no physics stopping it.

So this demo faithfully reproduces the PROTOCOL LOGIC of BB84 (basis
reconciliation, the QBER security check, error rates from basis mismatches)
across real separate machines, but it is a network simulation of the
mechanics, not a cryptographically secure implementation -- exactly the
same honest caveat as running Qiskit's simulator, just now distributed
across hardware instead of one process. State this plainly if asked.
"""

import json
import random
import sys

import paho.mqtt.client as mqtt

# --- EDIT THIS before running on each machine -------------------------
# Set this to the LAN IP address of whichever computer is running Mosquitto.
# Find it on that machine with: `ipconfig getifaddr en0` (Mac) or `ipconfig` (Windows).
# Do NOT use "localhost" here -- that only works if everything is on one machine.
BROKER_HOST = "l3607181.ala.asia-southeast1.emqxsl.com"
BROKER_PORT = 8883
BROKER_USERNAME = "AnirudhAshokAdmin"
BROKER_PASSWORD = "AnirudhMQTT2026!"
BROKER_USE_TLS = True


# ------------------------------------------------------------------------

SESSION_ID = "demo1"  # change this if you want to run multiple sessions without collisions

TOPIC_RELAY = f"qkd/{SESSION_ID}/relay"          # Alice -> whoever is in the middle
TOPIC_TO_BOB = f"qkd/{SESSION_ID}/to_bob"        # middle -> Bob
TOPIC_ALICE_BASES = f"qkd/{SESSION_ID}/alice_bases"
TOPIC_BOB_BASES = f"qkd/{SESSION_ID}/bob_bases"
TOPIC_SAMPLE_REVEAL = f"qkd/{SESSION_ID}/sample_reveal"
TOPIC_MESSAGE = f"qkd/{SESSION_ID}/message"
TOPIC_STATUS = f"qkd/{SESSION_ID}/status"

QBER_THRESHOLD = 0.11
SAMPLE_FRACTION = 0.25  # fraction of the sifted key publicly revealed to estimate QBER


def make_client(client_id):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    if BROKER_USERNAME and BROKER_PASSWORD:
        client.username_pw_set(BROKER_USERNAME, BROKER_PASSWORD)
    if BROKER_USE_TLS:
        # Disable certificate verification for EMQX Cloud (self-signed certs common in test environments)
        client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_NONE, tls_version=mqtt.ssl.PROTOCOL_TLSv1_2, ciphers=None)
        client.tls_insecure_set(True)
    return client


def connect_and_wait(client, on_connect_extra=None):
    """Connects and blocks until on_connect has actually fired, so callers
    don't publish/subscribe before the connection is ready."""
    connected = {"done": False}

    def _on_connect(c, userdata, flags, reason_code, properties):
        if reason_code != 0:
            print(f"Connection failed: {reason_code}")
            sys.exit(1)
        connected["done"] = True
        if on_connect_extra:
            on_connect_extra(c, userdata, flags, reason_code, properties)

    client.on_connect = _on_connect
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    import time
    waited = 0
    while not connected["done"] and waited < 10:
        time.sleep(0.1)
        waited += 0.1
    if not connected["done"]:
        print(f"Could not connect to broker at {BROKER_HOST}:{BROKER_PORT}. "
              f"Check BROKER_HOST in common.py and that Mosquitto is running "
              f"and reachable on the network (not just localhost).")
        sys.exit(1)
    return client


def generate_qubits(n):
    """Each 'qubit' is represented as [bit, basis] -- see the module docstring
    for why this is a classical stand-in, not a real quantum state."""
    return [[random.randint(0, 1), random.randint(0, 1)] for _ in range(n)]


def measure_qubits(incoming_qubits, measurement_bases):
    """
    Simulates measuring each incoming qubit with a locally-chosen basis.
    If the measurement basis matches the basis the qubit was encoded with,
    the original bit is recovered correctly. If not, the result is random
    (mirroring real quantum measurement collapse in a mismatched basis).
    """
    results = []
    for (bit, encode_basis), my_basis in zip(incoming_qubits, measurement_bases):
        if my_basis == encode_basis:
            results.append(bit)
        else:
            results.append(random.randint(0, 1))
    return results


def sift_key(my_bits, my_bases, other_bases):
    """Keeps only the bit positions where both sides used the same basis."""
    return [b for b, mb, ob in zip(my_bits, my_bases, other_bases) if mb == ob]