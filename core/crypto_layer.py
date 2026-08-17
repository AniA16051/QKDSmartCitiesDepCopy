"""
Bridges the QKD-derived key into usable AES-256-GCM symmetric encryption
for actual IoT sensor payloads.
"""

import os
import hashlib
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.bb84 import bits_to_bytes


def derive_aes_key(bit_array):
    """
    Turn the final BB84 key bits into a proper 256-bit AES key.
    We hash the raw key bytes with SHA-256 for key derivation / privacy
    amplification (also smooths out cases where the raw key isn't
    exactly 32 bytes long).
    """
    raw_bytes = bits_to_bytes(bit_array)
    if len(raw_bytes) == 0:
        raise ValueError("Cannot derive AES key: BB84 key is empty (likely aborted due to high QBER)")
    return hashlib.sha256(raw_bytes).digest()  # 32 bytes = 256 bits


def encrypt_payload(key_bytes, plaintext_dict):
    """Encrypt a sensor payload (dict) with AES-256-GCM using the QKD-derived key."""
    aesgcm = AESGCM(key_bytes)
    nonce = os.urandom(12)
    plaintext_bytes = json.dumps(plaintext_dict).encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, associated_data=None)
    return {
        "nonce": nonce.hex(),
        "ciphertext": ciphertext.hex(),
    }


def decrypt_payload(key_bytes, encrypted_dict):
    """Decrypt a payload; raises if the key is wrong or data was tampered with."""
    aesgcm = AESGCM(key_bytes)
    nonce = bytes.fromhex(encrypted_dict["nonce"])
    ciphertext = bytes.fromhex(encrypted_dict["ciphertext"])
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    return json.loads(plaintext_bytes.decode("utf-8"))


if __name__ == "__main__":
    from core.bb84 import run_bb84

    result = run_bb84(n_qubits=1024, eavesdropper=False)
    print(f"Final QKD key length: {len(result['final_key'])} bits")

    key = derive_aes_key(result["final_key"])
    print(f"Derived AES-256 key: {key.hex()}")

    payload = {
        "sensor_id": "traffic-node-07",
        "type": "traffic_flow",
        "vehicles_per_min": 42,
        "avg_speed_kmph": 38.5,
        "timestamp": "2026-08-12T10:00:00Z",
    }

    enc = encrypt_payload(key, payload)
    print(f"\nEncrypted payload: {enc}")

    dec = decrypt_payload(key, enc)
    print(f"\nDecrypted payload: {dec}")

    assert dec == payload
    print("\nRound-trip verified: payload matches.")
