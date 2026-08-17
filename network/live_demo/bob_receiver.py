"""
BOB / RECEIVER -- run this on the receiving computer.

Usage:
    python3 -m network.live_demo.bob_receiver

Steps:
  1. Waits for the qubit stream (from Alice directly, or via Eve if she's
     running in the middle), measures each with a random basis
  2. Publishes its bases publicly for reconciliation
  3. Waits for Alice's sample reveal, computes and reports QBER
  4. If QBER is safe, waits for and decrypts the message
"""

import json
import sys
import os
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from network.live_demo.common import (
    make_client, connect_and_wait, measure_qubits, sift_key,
    TOPIC_TO_BOB, TOPIC_ALICE_BASES, TOPIC_BOB_BASES, TOPIC_SAMPLE_REVEAL,
    TOPIC_MESSAGE, TOPIC_STATUS, QBER_THRESHOLD,
)
from core.crypto_layer import derive_aes_key, decrypt_payload
import numpy as np


def main():
    received = {
        "qubits": None, "alice_bases": None, "sample_reveal": None, "message": None,
    }

    def on_message(client, userdata, msg):
        if msg.topic == TOPIC_TO_BOB:
            received["qubits"] = json.loads(msg.payload.decode())["qubits"]
        elif msg.topic == TOPIC_ALICE_BASES:
            received["alice_bases"] = json.loads(msg.payload.decode())
        elif msg.topic == TOPIC_SAMPLE_REVEAL and msg.payload.decode().startswith("ALICE:"):
            received["sample_reveal"] = json.loads(msg.payload.decode()[6:])
        elif msg.topic == TOPIC_MESSAGE:
            received["message"] = json.loads(msg.payload.decode())

    client = make_client("bob-receiver")
    client.on_message = on_message
    connect_and_wait(client)
    client.subscribe(TOPIC_TO_BOB, qos=1)
    client.subscribe(TOPIC_ALICE_BASES, qos=1)
    client.subscribe(TOPIC_SAMPLE_REVEAL, qos=1)
    client.subscribe(TOPIC_MESSAGE, qos=1)

    print("[Bob] Connected. Waiting for the qubit stream...")
    waited = 0
    while received["qubits"] is None and waited < 30:
        time.sleep(0.2)
        waited += 0.2
    if received["qubits"] is None:
        print("[Bob] Timed out waiting for qubits. Is alice_sender.py (and a relay, "
              "if Eve isn't running) active?")
        sys.exit(1)

    n = len(received["qubits"])
    print(f"[Bob] Received {n} qubits. Measuring with random bases...")
    my_bases = [random.randint(0, 1) for _ in range(n)]
    my_bits = measure_qubits(received["qubits"], my_bases)

    client.publish(TOPIC_BOB_BASES, json.dumps(my_bases), qos=1)
    print("[Bob] Published my bases. Waiting for Alice's bases...")

    waited = 0
    while received["alice_bases"] is None and waited < 15:
        time.sleep(0.2)
        waited += 0.2
    if received["alice_bases"] is None:
        print("[Bob] Timed out waiting for Alice's bases.")
        sys.exit(1)

    sifted = sift_key(my_bits, my_bases, received["alice_bases"])
    print(f"[Bob] Sifted key length: {len(sifted)} bits")

    print("[Bob] Waiting for Alice's QBER sample reveal...")
    waited = 0
    while received["sample_reveal"] is None and waited < 20:
        time.sleep(0.2)
        waited += 0.2
    if received["sample_reveal"] is None:
        print("[Bob] Timed out waiting for sample reveal.")
        sys.exit(1)

    indices = received["sample_reveal"]["indices"]
    alice_sample_bits = received["sample_reveal"]["bits"]
    my_sample_bits = [sifted[i] for i in indices]

    errors = sum(1 for a, b in zip(alice_sample_bits, my_sample_bits) if a != b)
    qber = errors / len(indices) if indices else 0.0
    print(f"[Bob] Computed QBER = {qber:.2%}")

    client.publish(TOPIC_SAMPLE_REVEAL, "BOB:" + json.dumps({"qber": qber}), qos=1)

    if qber > QBER_THRESHOLD:
        print(f"[Bob] QBER exceeds {QBER_THRESHOLD:.0%} -- channel compromised. "
              f"Will NOT trust any incoming message, even if one arrives.")
        sys.exit(0)

    remaining = [b for i, b in enumerate(sifted) if i not in indices]
    print(f"[Bob] Channel secure. Final key length: {len(remaining)} bits. "
          f"Waiting for encrypted message...")

    key = derive_aes_key(np.array(remaining))

    waited = 0
    while received["message"] is None and waited < 20:
        time.sleep(0.2)
        waited += 0.2
    if received["message"] is None:
        print("[Bob] No message arrived.")
        sys.exit(0)

    try:
        payload = decrypt_payload(key, received["message"])
        print(f"\n[Bob] DECRYPTED MESSAGE: \"{payload['message']}\"\n")
    except Exception as e:
        print(f"[Bob] Decryption FAILED ({e}) -- key mismatch, message rejected.")

    client.loop_stop()


if __name__ == "__main__":
    main()
