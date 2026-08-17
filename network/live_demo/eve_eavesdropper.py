"""
EVE / EAVESDROPPER -- run this on the third computer to simulate a real
network eavesdropper sitting between Alice and Bob.

This performs a genuine intercept-resend attack: Eve receives Alice's
qubit stream, measures each one with her OWN randomly guessed basis
(she does not know Alice's real basis), then re-transmits her own
(possibly wrong) result onward to Bob. Whenever her guessed basis is
wrong, she introduces an error that Bob's later QBER check will detect.

Run this INSTEAD of relay_clean.py, not alongside it -- whichever one is
running determines whether this run is clean or attacked.

Usage:
    python3 -m network.live_demo.eve_eavesdropper
"""

import json
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from network.live_demo.common import make_client, connect_and_wait, TOPIC_RELAY, TOPIC_TO_BOB


def main():
    def on_message(client, userdata, msg):
        data = json.loads(msg.payload.decode())
        qubits = data.get("qubits", [])

        tampered = []
        correct_guesses = 0
        for bit, alice_basis in qubits:
            eve_basis = random.randint(0, 1)
            if eve_basis == alice_basis:
                measured_bit = bit
                correct_guesses += 1
            else:
                measured_bit = random.randint(0, 1)
            tampered.append([measured_bit, eve_basis])

        client.publish(TOPIC_TO_BOB, json.dumps({"qubits": tampered}), qos=1)

        n = len(qubits)
        print(f"[Eve] Intercepted {n} qubits. Guessed the correct basis for "
              f"{correct_guesses}/{n} ({correct_guesses/n:.0%}) -- re-transmitted "
              f"my own measured (and partly wrong) version to Bob.")
        print("[Eve] This will show up as an elevated QBER on both Alice's and "
              "Bob's side, which is how they'll detect me.")

    client = make_client("eve-eavesdropper")
    client.on_message = on_message
    connect_and_wait(client)
    client.subscribe(TOPIC_RELAY, qos=1)

    print("[Eve] Connected. Silently waiting to intercept the qubit stream...")
    client.loop_forever()


if __name__ == "__main__":
    main()
