"""
Classical key exchange baselines -- RSA key transport and ECDH (Elliptic
Curve Diffie-Hellman) -- implemented so they can be benchmarked directly
against BB84 QKD (core/bb84.py) on equal footing: same task (two parties
agree on a shared AES-256 key), different mechanism.

WHY BOTH RSA AND ECDH:
  - RSA key transport is the older, still-common approach (e.g. classic TLS
    key exchange, some legacy IoT stacks): one side generates the AES key
    and encrypts it with the other side's RSA public key.
  - ECDH is the modern standard (e.g. TLS 1.3): both sides derive a shared
    secret via elliptic curve math, neither ever transmits the key itself.
    ECDH is faster and has smaller keys than RSA at equivalent security
    levels, which is why it's preferred in real IoT deployments today.

THE SECURITY ARGUMENT (for your report):
  Both RSA and ECDH rely on computational hardness assumptions -- RSA on
  integer factorization, ECDH on the elliptic curve discrete logarithm
  problem. Both are broken by Shor's algorithm on a sufficiently large
  fault-tolerant quantum computer. BB84's security instead rests on the
  laws of physics (no-cloning theorem, measurement disturbance) and holds
  regardless of an attacker's future computational power -- classical OR
  quantum. This is what "post-quantum-safe" means in the QKD context.

NOTE: this benchmark measures LOCAL computation only (key generation,
encryption/decryption, key derivation) -- it does not simulate real network
latency for either side. BB84 here also runs as local Qiskit simulation
rather than real photon transmission. Both are measured on the same
footing, which is the point: it isolates protocol overhead, not network
conditions.
"""

import hashlib
import time

from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

from core.bb84 import run_bb84
from core.crypto_layer import derive_aes_key


# ---------------------------------------------------------------------------
# RSA key transport
# ---------------------------------------------------------------------------

def rsa_key_exchange(key_size=2048):
    """
    Simulates RSA key transport: Bob generates an RSA keypair, Alice
    generates a random AES-256 key and encrypts it with Bob's public key.
    Returns timing breakdown and the resulting shared AES key.
    """
    t0 = time.perf_counter()
    bob_private = rsa.generate_private_key(public_exponent=65537, key_size=key_size,
                                            backend=default_backend())
    bob_public = bob_private.public_key()
    t_keygen = time.perf_counter() - t0

    t0 = time.perf_counter()
    import os
    aes_key = os.urandom(32)  # Alice generates the actual session key
    ciphertext = bob_public.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                     algorithm=hashes.SHA256(), label=None),
    )
    t_encrypt = time.perf_counter() - t0

    t0 = time.perf_counter()
    recovered_key = bob_private.decrypt(
        ciphertext,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                     algorithm=hashes.SHA256(), label=None),
    )
    t_decrypt = time.perf_counter() - t0

    assert recovered_key == aes_key, "RSA key transport failed round-trip"

    return {
        "protocol": "RSA-2048" if key_size == 2048 else f"RSA-{key_size}",
        "final_key": aes_key,
        "t_keygen": t_keygen,
        "t_encrypt": t_encrypt,
        "t_decrypt": t_decrypt,
        "t_total": t_keygen + t_encrypt + t_decrypt,
        "wire_bytes": len(ciphertext),  # what actually crosses the network
    }


# ---------------------------------------------------------------------------
# ECDH (Elliptic Curve Diffie-Hellman)
# ---------------------------------------------------------------------------

def ecdh_key_exchange(curve=ec.SECP256R1()):
    """
    Simulates ECDH: both Alice and Bob generate ephemeral EC keypairs,
    exchange public keys, and independently derive the same shared secret.
    The secret is then run through HKDF to get a clean 256-bit AES key
    (mirrors how TLS 1.3 derives session keys from the raw ECDH output).
    """
    t0 = time.perf_counter()
    alice_private = ec.generate_private_key(curve, default_backend())
    bob_private = ec.generate_private_key(curve, default_backend())
    t_keygen = time.perf_counter() - t0

    alice_public_bytes = alice_private.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    bob_public_bytes = bob_private.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )

    t0 = time.perf_counter()
    alice_public = ec.EllipticCurvePublicKey.from_encoded_point(curve, bob_public_bytes)
    bob_public = ec.EllipticCurvePublicKey.from_encoded_point(curve, alice_public_bytes)

    alice_shared = alice_private.exchange(ec.ECDH(), alice_public)
    bob_shared = bob_private.exchange(ec.ECDH(), bob_public)
    t_exchange = time.perf_counter() - t0

    assert alice_shared == bob_shared, "ECDH shared secrets don't match"

    t0 = time.perf_counter()
    aes_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                    info=b"qkd-smart-city-ecdh").derive(alice_shared)
    t_derive = time.perf_counter() - t0

    return {
        "protocol": "ECDH-P256",
        "final_key": aes_key,
        "t_keygen": t_keygen,
        "t_encrypt": t_exchange,  # exchange step, kept in same field name for uniform comparison
        "t_decrypt": 0.0,          # ECDH has no separate decrypt step
        "t_derive": t_derive,
        "t_total": t_keygen + t_exchange + t_derive,
        "wire_bytes": len(alice_public_bytes) + len(bob_public_bytes),
    }


# ---------------------------------------------------------------------------
# QKD (BB84) wrapped with the same timing/measurement interface
# ---------------------------------------------------------------------------

def qkd_key_exchange(n_qubits=512, eavesdropper=False, depolarizing_prob=0.0):
    """Runs BB84 and reports it using the same metrics as the classical baselines."""
    t0 = time.perf_counter()
    result = run_bb84(n_qubits=n_qubits, eavesdropper=eavesdropper,
                       depolarizing_prob=depolarizing_prob)
    t_total = time.perf_counter() - t0

    if result["aborted"] or len(result["final_key"]) == 0:
        return {
            "protocol": "BB84 (QKD)",
            "final_key": None,
            "t_total": t_total,
            "aborted": True,
            "qber": result["qber"],
            "wire_bytes": n_qubits,  # one "qubit slot" per photon-equivalent transmitted
        }

    aes_key = derive_aes_key(result["final_key"])
    return {
        "protocol": "BB84 (QKD)",
        "final_key": aes_key,
        "t_total": t_total,
        "aborted": False,
        "qber": result["qber"],
        "final_key_bits": len(result["final_key"]),
        "wire_bytes": n_qubits,
    }


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def run_comparison(trials=20, n_qubits=512):
    """
    Runs all three protocols `trials` times each (clean channel, no attacker)
    and returns averaged timing + overhead stats for a side-by-side table.
    """
    results = {"RSA-2048": [], "ECDH-P256": [], "BB84 (QKD)": []}

    for _ in range(trials):
        r = rsa_key_exchange()
        results["RSA-2048"].append(r)

        r = ecdh_key_exchange()
        results["ECDH-P256"].append(r)

        r = qkd_key_exchange(n_qubits=n_qubits)
        results["BB84 (QKD)"].append(r)

    summary = {}
    for protocol, runs in results.items():
        times = [r["t_total"] for r in runs]
        wire = [r["wire_bytes"] for r in runs]
        summary[protocol] = {
            "avg_time_ms": (sum(times) / len(times)) * 1000,
            "min_time_ms": min(times) * 1000,
            "max_time_ms": max(times) * 1000,
            "avg_wire_bytes": sum(wire) / len(wire),
            "trials": trials,
        }

    return summary


def print_comparison_table(summary):
    print(f"{'Protocol':<14} {'Avg time (ms)':>15} {'Min (ms)':>12} "
          f"{'Max (ms)':>12} {'Wire size':>12}")
    print("-" * 70)
    for protocol, stats in summary.items():
        print(f"{protocol:<14} {stats['avg_time_ms']:>15.3f} "
              f"{stats['min_time_ms']:>12.3f} {stats['max_time_ms']:>12.3f} "
              f"{stats['avg_wire_bytes']:>10.0f}B")


if __name__ == "__main__":
    print("Running classical vs quantum key exchange comparison "
          "(20 trials each, clean channel)...\n")
    summary = run_comparison(trials=20, n_qubits=512)
    print_comparison_table(summary)

    import json
    with open("comparison_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved: comparison_results.json (used by the dashboard)")

    print("\nNote: BB84 total time includes the full simulated qubit-by-qubit "
          "Qiskit circuit execution for each of the 512 qubits, which is why "
          "it is dramatically slower than RSA/ECDH here -- on REAL quantum "
          "hardware, qubits travel as physical photons at the speed of light "
          "and this gap does not exist in the same form. This local-simulation "
          "overhead is an honest limitation to state in the report.")

    try:
        import matplotlib.pyplot as plt
        import numpy as np

        protocols = list(summary.keys())
        avg_times = [summary[p]["avg_time_ms"] for p in protocols]
        wire_sizes = [summary[p]["avg_wire_bytes"] for p in protocols]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

        colors = ["#d97706", "#2563eb", "#16a34a"]
        ax1.bar(protocols, avg_times, color=colors)
        ax1.set_ylabel("Average time (ms, log scale)")
        ax1.set_yscale("log")
        ax1.set_title("Key exchange time (local computation)")
        ax1.grid(axis="y", alpha=0.3)

        ax2.bar(protocols, wire_sizes, color=colors)
        ax2.set_ylabel("Data exchanged (bytes)")
        ax2.set_title("Wire overhead per key exchange")
        ax2.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        plt.savefig("classical_vs_quantum_comparison.png", dpi=150)
        print("\nSaved: classical_vs_quantum_comparison.png")
    except ImportError:
        pass