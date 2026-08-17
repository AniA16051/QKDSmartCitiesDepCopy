"""
Generates the key result plots for the project report:
1. QBER vs Eve's interception probability
2. Final key length vs number of qubits sent
3. QBER vs channel noise (depolarizing probability), no Eve
4. Detection reliability: QBER distribution over many trials, with vs without Eve
"""

import numpy as np
import matplotlib.pyplot as plt

from core.bb84 import run_bb84


def plot_qber_vs_eve_intensity(n_qubits=400, trials=5, save_path="qber_vs_eve.png"):
    intercept_probs = np.linspace(0, 1, 6)
    mean_qbers = []
    std_qbers = []

    for p in intercept_probs:
        qbers = []
        for _ in range(trials):
            result = run_bb84(n_qubits=n_qubits, eavesdropper=(p > 0), eve_intercept_prob=p)
            if result["qber"] is not None:
                qbers.append(result["qber"])
        mean_qbers.append(np.mean(qbers))
        std_qbers.append(np.std(qbers))

    plt.figure(figsize=(7, 5))
    plt.errorbar(intercept_probs * 100, np.array(mean_qbers) * 100, yerr=np.array(std_qbers) * 100,
                 marker="o", capsize=4, color="#2563eb")
    plt.axhline(y=11, color="red", linestyle="--", label="Security threshold (11%)")
    plt.axhline(y=25, color="gray", linestyle=":", label="Theoretical max (full intercept-resend, 25%)")
    plt.xlabel("Eve's interception probability (%)")
    plt.ylabel("Measured QBER (%)")
    plt.title("QBER vs Eavesdropping Intensity")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Saved: {save_path}")


def plot_key_length_vs_qubits(save_path="key_length_vs_qubits.png"):
    qubit_counts = [50, 100, 200, 400, 800, 1600, 3200]
    final_lengths = []

    for n in qubit_counts:
        result = run_bb84(n_qubits=n, eavesdropper=False)
        final_lengths.append(len(result["final_key"]))

    plt.figure(figsize=(7, 5))
    plt.plot(qubit_counts, final_lengths, marker="o", color="#16a34a")
    plt.plot(qubit_counts, [n * 0.375 for n in qubit_counts], linestyle="--", color="gray",
              label="Theoretical expectation (~37.5%)")
    plt.xlabel("Qubits transmitted")
    plt.ylabel("Final usable key length (bits)")
    plt.title("Final Key Length vs Qubits Sent (No Eve)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Saved: {save_path}")


def plot_qber_vs_noise(n_qubits=500, trials=5, save_path="qber_vs_noise.png"):
    noise_levels = np.linspace(0, 0.15, 6)
    mean_qbers = []

    for noise in noise_levels:
        qbers = []
        for _ in range(trials):
            result = run_bb84(n_qubits=n_qubits, eavesdropper=False, depolarizing_prob=noise)
            if result["qber"] is not None:
                qbers.append(result["qber"])
        mean_qbers.append(np.mean(qbers))

    plt.figure(figsize=(7, 5))
    plt.plot(noise_levels * 100, np.array(mean_qbers) * 100, marker="s", color="#d97706")
    plt.axhline(y=11, color="red", linestyle="--", label="Security threshold (11%)")
    plt.xlabel("Channel depolarizing noise (%)")
    plt.ylabel("Measured QBER (%)")
    plt.title("QBER vs Channel Noise (No Eavesdropper)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Saved: {save_path}")


def plot_detection_reliability(n_qubits=400, trials=30, save_path="detection_reliability.png"):
    clean_qbers = []
    attacked_qbers = []

    for _ in range(trials):
        r_clean = run_bb84(n_qubits=n_qubits, eavesdropper=False)
        r_attacked = run_bb84(n_qubits=n_qubits, eavesdropper=True, eve_intercept_prob=1.0)
        if r_clean["qber"] is not None:
            clean_qbers.append(r_clean["qber"] * 100)
        if r_attacked["qber"] is not None:
            attacked_qbers.append(r_attacked["qber"] * 100)

    plt.figure(figsize=(7, 5))
    plt.hist(clean_qbers, bins=15, alpha=0.6, label="No Eve", color="#16a34a")
    plt.hist(attacked_qbers, bins=15, alpha=0.6, label="Eve present (full intercept-resend)", color="#dc2626")
    plt.axvline(x=11, color="black", linestyle="--", label="Security threshold (11%)")
    plt.xlabel("QBER (%)")
    plt.ylabel("Number of trials")
    plt.title(f"QBER Distribution Across {trials} Trials: Detection Reliability")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Saved: {save_path}")


if __name__ == "__main__":
    plot_qber_vs_eve_intensity()
    plot_key_length_vs_qubits()
    plot_qber_vs_noise()
    plot_detection_reliability()
