"""
ALICE / SENDER -- run this on the sending computer.

Usage:
    python3 -m network.live_demo.alice_sender --message "Hello Bob, this is secret"

Steps:
  1. Generates random bits + bases, publishes them (as the 'quantum channel')
  2. Publishes its bases publicly for reconciliation
  3. Waits for Bob's bases, computes the sifted key
  4. Publicly reveals a sample to estimate QBER
  5. If QBER is safe, derives an AES key and sends the encrypted message
"""

import argparse
import json
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from network.live_demo.common import (
    make_client, connect_and_wait, generate_qubits, sift_key,
    TOPIC_RELAY, TOPIC_ALICE_BASES, TOPIC_BOB_BASES, TOPIC_SAMPLE_REVEAL,
    TOPIC_MESSAGE, TOPIC_STATUS, QBER_THRESHOLD, SAMPLE_FRACTION,
)
from core.crypto_layer import derive_aes_key, encrypt_payload
import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Alice (sender) for the live BB84 demo")
    parser.add_argument("--message", required=True, help="Message to send securely")
    parser.add_argument("--n-qubits", type=int, default=512)
    args = parser.parse_args()

    received = {"bob_bases": None, "sample_response": None}

    def on_message(client, userdata, msg):
        if msg.topic == TOPIC_BOB_BASES:
            received["bob_bases"] = json.loads(msg.payload.decode())
        elif msg.topic == TOPIC_SAMPLE_REVEAL and msg.payload.decode().startswith("BOB:"):
            received["sample_response"] = json.loads(msg.payload.decode()[4:])

    client = make_client("alice-sender")
    client.on_message = on_message
    connect_and_wait(client)
    client.subscribe(TOPIC_BOB_BASES, qos=1)
    client.subscribe(TOPIC_SAMPLE_REVEAL, qos=1)

    print(f"[Alice] Connected. Generating {args.n_qubits} qubits...")
    qubits = generate_qubits(args.n_qubits)
    my_bits = [q[0] for q in qubits]
    my_bases = [q[1] for q in qubits]

    client.publish(TOPIC_RELAY, json.dumps({"qubits": qubits}), qos=1)
    print(f"[Alice] Sent {args.n_qubits} qubits onto the channel.")

    client.publish(TOPIC_ALICE_BASES, json.dumps(my_bases), qos=1)
    print("[Alice] Published my bases. Waiting for Bob's bases...")

    waited = 0
    while received["bob_bases"] is None and waited < 30:
        time.sleep(0.2)
        waited += 0.2
    if received["bob_bases"] is None:
        print("[Alice] Timed out waiting for Bob. Is bob_receiver.py running?")
        sys.exit(1)

    bob_bases = received["bob_bases"]
    sifted = sift_key(my_bits, my_bases, bob_bases)
    print(f"[Alice] Sifted key length: {len(sifted)} bits")

    if len(sifted) < 16:
        print("[Alice] Sifted key too short, aborting.")
        client.publish(TOPIC_STATUS, "ALICE_ABORTED_SHORT_KEY", qos=1)
        sys.exit(1)

    sample_size = max(1, int(len(sifted) * SAMPLE_FRACTION))
    sample_indices = sorted(__import__("random").sample(range(len(sifted)), sample_size))
    sample_bits = [sifted[i] for i in sample_indices]

    client.publish(TOPIC_SAMPLE_REVEAL,
                    "ALICE:" + json.dumps({"indices": sample_indices, "bits": sample_bits}),
                    qos=1)
    print(f"[Alice] Revealed {sample_size} sample bits for QBER check. Waiting for Bob's comparison...")

    waited = 0
    while received["sample_response"] is None and waited < 15:
        time.sleep(0.2)
        waited += 0.2
    if received["sample_response"] is None:
        print("[Alice] Timed out waiting for Bob's QBER response.")
        sys.exit(1)

    qber = received["sample_response"]["qber"]
    print(f"[Alice] QBER = {qber:.2%}")

    if qber > QBER_THRESHOLD:
        print(f"[Alice] QBER exceeds {QBER_THRESHOLD:.0%} threshold -- "
              f"channel is compromised. ABORTING. Message will NOT be sent.")
        client.publish(TOPIC_STATUS, f"ABORTED_QBER_{qber:.4f}", qos=1)
        sys.exit(0)

    remaining = [b for i, b in enumerate(sifted) if i not in sample_indices]
    print(f"[Alice] Channel is secure. Final key length: {len(remaining)} bits")

    key = derive_aes_key(np.array(remaining))
    encrypted = encrypt_payload(key, {"message": args.message})
    client.publish(TOPIC_MESSAGE, json.dumps(encrypted), qos=1)
    client.publish(TOPIC_STATUS, "MESSAGE_SENT", qos=1)
    print(f"[Alice] Encrypted message sent: \"{args.message}\"")

    time.sleep(1)
    client.loop_stop()


if __name__ == "__main__":
    main()
