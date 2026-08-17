"""
CLEAN RELAY -- stands in for the physical fiber/channel between Alice and Bob.

Run this on a THIRD machine (or the same as Alice/Bob if you only have two)
whenever you want a normal, un-attacked run. Whichever of this script OR
eve_eavesdropper.py is running determines whether the channel is clean or
compromised for that run -- only run ONE of them at a time.

Usage:
    python3 -m network.live_demo.relay_clean
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from network.live_demo.common import make_client, connect_and_wait, TOPIC_RELAY, TOPIC_TO_BOB


def main():
    def on_message(client, userdata, msg):
        data = json.loads(msg.payload.decode())
        n = len(data.get("qubits", []))
        client.publish(TOPIC_TO_BOB, msg.payload, qos=1)
        print(f"[Relay] Forwarded {n} qubits unchanged (clean channel).")

    client = make_client("clean-relay")
    client.on_message = on_message
    connect_and_wait(client)
    client.subscribe(TOPIC_RELAY, qos=1)

    print("[Relay] Connected. Acting as a clean, un-attacked channel. "
          "Waiting for Alice's transmission...")
    client.loop_forever()


if __name__ == "__main__":
    main()
