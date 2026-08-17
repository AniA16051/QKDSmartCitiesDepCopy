"""
BB84 Quantum Key Distribution Protocol
Simulates Alice and Bob establishing a shared secret key using quantum states,
with optional eavesdropper (Eve) and optional noisy channel.

Supports both Qiskit Aer simulation (when Qiskit is available) and high-performance
pure-NumPy quantum simulation fallback (for lightweight / cloud deployments).
"""

import numpy as np

# Try importing Qiskit; fall back gracefully to pure NumPy if unavailable
try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    _HAS_QISKIT = True
except (ImportError, Exception):
    _HAS_QISKIT = False


# ---------------------------------------------------------------------------
# Basis encoding:
#   0 = Z basis (computational: |0>, |1>)
#   1 = X basis (Hadamard: |+>, |->)
# ---------------------------------------------------------------------------

def generate_random_bits(n):
    """Generate n random classical bits (0 or 1)."""
    return np.random.randint(0, 2, n)


def generate_random_bases(n):
    """Generate n random measurement/encoding bases (0=Z, 1=X)."""
    return np.random.randint(0, 2, n)


def build_noise_model(depolarizing_prob=0.0):
    """Optional depolarizing noise on the channel, to model fiber loss/decoherence."""
    if not _HAS_QISKIT or depolarizing_prob <= 0:
        return None
    noise_model = NoiseModel()
    error = depolarizing_error(depolarizing_prob, 1)
    noise_model.add_all_qubit_quantum_error(error, ["id", "x", "h"])
    return noise_model


def alice_prepare_qubit(bit, basis):
    """Alice encodes one classical bit into a qubit using her chosen basis (Qiskit)."""
    if not _HAS_QISKIT:
        return None
    qc = QuantumCircuit(1, 1)
    if bit == 1:
        qc.x(0)
    if basis == 1:
        qc.h(0)
    return qc


def eve_intercept(qc, eve_basis, simulator):
    """
    Eve measures the qubit in her guessed basis, then re-prepares a new qubit
    in that basis based on her measurement result, and forwards it on (Qiskit).
    """
    if not _HAS_QISKIT:
        return None, 0
    measure_qc = qc.copy()
    if eve_basis == 1:
        measure_qc.h(0)
    measure_qc.measure(0, 0)

    result = simulator.run(measure_qc, shots=1, memory=True).result()
    eve_bit = int(result.get_memory()[0])

    # Eve re-prepares a fresh qubit based on what she measured, and sends it on
    resend_qc = QuantumCircuit(1, 1)
    if eve_bit == 1:
        resend_qc.x(0)
    if eve_basis == 1:
        resend_qc.h(0)

    return resend_qc, eve_bit


def bob_measure_qubit(qc, basis, simulator, noise_model=None):
    """Bob measures the incoming qubit in his own randomly chosen basis (Qiskit)."""
    if not _HAS_QISKIT:
        return 0
    measure_qc = qc.copy()
    if basis == 1:
        measure_qc.h(0)
    measure_qc.measure(0, 0)

    if noise_model:
        result = simulator.run(
            measure_qc, shots=1, memory=True, noise_model=noise_model
        ).result()
    else:
        result = simulator.run(measure_qc, shots=1, memory=True).result()

    return int(result.get_memory()[0])


def _simulate_bb84_numpy(n_qubits, eavesdropper, eve_intercept_prob, depolarizing_prob):
    """
    Exact mathematical simulation of BB84 protocol using NumPy.
    Models quantum state collapse, basis reconciliation, and intercept-resend attack.
    """
    alice_bits = generate_random_bits(n_qubits)
    alice_bases = generate_random_bases(n_qubits)
    bob_bases = generate_random_bases(n_qubits)

    bob_results = np.zeros(n_qubits, dtype=int)

    for i in range(n_qubits):
        bit = alice_bits[i]
        basis = alice_bases[i]

        # Channel transmission (with optional Eve attack)
        if eavesdropper and np.random.random() < eve_intercept_prob:
            eve_basis = np.random.randint(0, 2)
            if eve_basis == basis:
                eve_measured_bit = bit
            else:
                eve_measured_bit = np.random.randint(0, 2)
            
            # Eve re-sends in her basis
            channel_bit = eve_measured_bit
            channel_basis = eve_basis
        else:
            channel_bit = bit
            channel_basis = basis

        # Channel noise (depolarizing error)
        if depolarizing_prob > 0 and np.random.random() < depolarizing_prob:
            channel_bit = 1 - channel_bit

        # Bob measures in bob_bases[i]
        if bob_bases[i] == channel_basis:
            bob_results[i] = channel_bit
        else:
            bob_results[i] = np.random.randint(0, 2)

    return alice_bits, alice_bases, bob_bases, bob_results


def run_bb84(
    n_qubits=200,
    eavesdropper=False,
    eve_intercept_prob=1.0,
    depolarizing_prob=0.0,
    verbose=False,
):
    """
    Runs a full BB84 exchange between Alice and Bob.

    Returns a dict with:
        sifted_key_alice, sifted_key_bob : the raw sifted keys (post basis-reconciliation)
        qber : quantum bit error rate measured on a sample of the sifted key
        final_key : the key after discarding the QBER-check sample
        aborted : True if QBER exceeded the security threshold (11%)
        n_sifted : count of sifted bits
    """
    if _HAS_QISKIT:
        try:
            simulator = AerSimulator()
            noise_model = build_noise_model(depolarizing_prob)

            alice_bits = generate_random_bits(n_qubits)
            alice_bases = generate_random_bases(n_qubits)
            bob_bases = generate_random_bases(n_qubits)

            bob_results = []
            for i in range(n_qubits):
                qc = alice_prepare_qubit(alice_bits[i], alice_bases[i])

                if eavesdropper and np.random.random() < eve_intercept_prob:
                    eve_basis = np.random.randint(0, 2)
                    qc, _ = eve_intercept(qc, eve_basis, simulator)

                bit = bob_measure_qubit(qc, bob_bases[i], simulator, noise_model)
                bob_results.append(bit)

            bob_results = np.array(bob_results)
        except Exception:
            # If Qiskit simulation fails for any reason, fallback to NumPy simulation
            alice_bits, alice_bases, bob_bases, bob_results = _simulate_bb84_numpy(
                n_qubits, eavesdropper, eve_intercept_prob, depolarizing_prob
            )
    else:
        alice_bits, alice_bases, bob_bases, bob_results = _simulate_bb84_numpy(
            n_qubits, eavesdropper, eve_intercept_prob, depolarizing_prob
        )

    # --- Sifting: keep only positions where Alice's and Bob's bases matched ---
    matching = alice_bases == bob_bases
    sifted_alice = alice_bits[matching]
    sifted_bob = bob_results[matching]

    if len(sifted_alice) == 0:
        return {
            "sifted_key_alice": np.array([]),
            "sifted_key_bob": np.array([]),
            "final_key": np.array([]),
            "qber": None,
            "aborted": True,
            "n_sifted": 0,
        }

    # --- QBER estimation: publicly compare a random sample of the sifted key ---
    sample_size = max(1, len(sifted_alice) // 4)
    sample_idx = np.random.choice(len(sifted_alice), sample_size, replace=False)
    errors = np.sum(sifted_alice[sample_idx] != sifted_bob[sample_idx])
    qber = errors / sample_size

    QBER_THRESHOLD = 0.11  # standard BB84 security bound (~11%)
    aborted = qber > QBER_THRESHOLD

    # Remove the disclosed sample bits from the final key
    keep_mask = np.ones(len(sifted_alice), dtype=bool)
    keep_mask[sample_idx] = False
    final_key = sifted_alice[keep_mask] if not aborted else np.array([])

    if verbose:
        print(f"Qubits sent: {n_qubits}")
        print(f"Sifted key length: {len(sifted_alice)}")
        print(f"QBER: {qber:.3%}")
        print(f"Aborted: {aborted}")
        print(f"Final key length: {len(final_key)}")

    return {
        "sifted_key_alice": sifted_alice,
        "sifted_key_bob": sifted_bob,
        "final_key": final_key,
        "qber": qber,
        "aborted": aborted,
        "n_sifted": len(sifted_alice),
    }


def bits_to_bytes(bit_array):
    """Convert a numpy array of 0/1 bits into raw bytes (truncated to a multiple of 8)."""
    if len(bit_array) == 0:
        return b""
    n = (len(bit_array) // 8) * 8
    if n == 0:
        return b""
    bit_array = np.array(bit_array[:n], dtype=np.uint8)
    packed = np.packbits(bit_array)
    return packed.tobytes()


if __name__ == "__main__":
    print("=== BB84 without Eve ===")
    run_bb84(n_qubits=300, eavesdropper=False, verbose=True)

    print("\n=== BB84 with Eve (full intercept-resend) ===")
    run_bb84(n_qubits=300, eavesdropper=True, eve_intercept_prob=1.0, verbose=True)
