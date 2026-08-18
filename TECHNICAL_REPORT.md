# In-Depth Technical Report: QKD for Smart City IoT Security

## 1. Executive Summary & Problem Statement

**The Security Imperative:** Smart Cities integrate critical infrastructure (traffic control, water distribution, grid management, surveillance) with public Internet-of-Things (IoT) networks. Currently, these systems rely on classical cryptographic protocols like RSA, Diffie-Hellman, or Elliptic Curve Cryptography (ECC) for key exchange and encryption. 

**The Quantum Threat:** Classical encryption relies on the computational hardness of mathematical problems (like prime factorization). The advent of sufficiently powerful quantum computers running Shor's Algorithm renders these mathematical problems trivial to solve, meaning all intercepted encrypted data could be retrospectively decrypted ("Harvest Now, Decrypt Later" attacks).

**The Solution:** This project implements **Quantum Key Distribution (QKD)**—specifically simulating the **BB84 protocol**—to establish unconditionally secure communication channels between smart city sensors and a central Cyber Defense Operations Center (SOC). Because QKD relies on the fundamental laws of quantum physics (the No-Cloning Theorem and the Observer Effect) rather than computational complexity, it is mathematically proven to be unbreakable by any future computational power, ensuring future-proof security for critical infrastructure.

---

## 2. Implementation Technology Stack & Simulators

This project is built as a self-contained, high-performance web application, optimized for cloud deployment.

*   **Frontend UI:** **Streamlit (Python)**. Used to render a high-density, React-like Cyber Defense Operations Center interface without requiring external JavaScript/CSS frameworks.
*   **Quantum Simulation Engine:** **NumPy**. Instead of using heavy computational frameworks like IBM Qiskit (which often cause memory limits in cloud deployments), this project uses NumPy for ultra-fast, vectorized simulations of quantum superposition, basis measurements, and sifting logic.
*   **Key Derivation:** **Python `hashlib` (SHA-256)**. Used to extract a uniform 256-bit symmetric key from the raw sifted quantum bits.
*   **Networking & Messaging:** **Paho-MQTT (`paho.mqtt.client`)**. The industry standard lightweight messaging protocol for IoT devices.
*   **Cloud Broker:** **EMQX Cloud (`broker.emqx.io`)**. A public, serverless MQTT broker that handles the real-time global broadcast of the encrypted telemetry payloads.
*   **Data Visualization:** **Plotly (`plotly.graph_objects`)**. Used to render interactive Geospatial Maps (`Scattermapbox`) and dual-axis Time Series charts.
*   **Deployment Platforms:** **Streamlit Community Cloud** & **Render** (via `Dockerfile` and `render.yaml`).

---

## 3. How BB84 Works and is Simulated Here

The BB84 protocol allows two parties (Alice, the sensor node; and Bob, the central SOC) to generate a shared cryptographic key over a quantum channel. 

### The Quantum Mechanics Principle:
According to the Heisenberg Uncertainty Principle and the Observer Effect, observing a quantum state irreversibly alters it. Therefore, if an eavesdropper ("Eve") intercepts the quantum transmission between Alice and Bob, she is forced to measure it. Because she doesn't know Alice's original encoding bases, she will frequently guess wrong, collapsing the quantum state incorrectly. When she resends the qubit to Bob, Bob will measure anomalies (errors).

### Execution in the Code (`UnifiedBB84` Class):
1.  **State Preparation (`generate_key`, `generate_bases`):** 
    Alice generates an array of 256 random key bits (`0` or `1`) and 256 random measurement bases (`0` for Rectilinear `+`, `1` for Diagonal `x`) using `np.random.randint()`.
2.  **Eve's Intercept-Resend Attack (Threat Simulation):** 
    If the `attack` flag is `True`, Eve intercepts the array. She generates her own random bases and measures the states. If her basis matches Alice's, the bit passes perfectly. If it doesn't, the quantum state collapses into a random `0` or `1`. Eve then sends this collapsed string to Bob.
3.  **Measurement & Sifting:** 
    Bob measures the incoming qubits using his own random bases. Alice and Bob publicly compare their *bases* (but not the bit values). In the code, this is handled via a highly efficient vectorized array comparison: 
    `matching_bases = (alice_bases == bob_bases)`
    Bits measured with non-matching bases are discarded.
4.  **QBER Estimation (Quantum Bit Error Rate):** 
    The code calculates `errors = np.sum(sifted_alice != sifted_bob)`. 
    If Eve intercepted the channel, her incorrect basis guesses introduce an inevitable average error rate of ~25%.
    The code enforces a strict security threshold: **If QBER ≥ 11.0%, the key is aborted.**
5.  **Privacy Amplification:** 
    If the channel is clean, the surviving bits are merged into a string and hashed using `hashlib.sha256()`. This generates the final, secure `AES-256` key.

---

## 4. Code Architecture & Component Connections

The entire application runs from a single, highly integrated file (`app.py`), divided into Backend Logic and Frontend UI.

### A. The Backend: `IntegratedSmartCity` Class
This class is instantiated using Streamlit's `@st.cache_resource` decorator. This architectural decision makes the simulation engine a **Global Singleton**. Instead of being isolated per browser tab (`st.session_state`), it is shared across the entire server memory. This enables "Global Multiplayer" synchronization: if one user initiates an attack, all other connected clients will automatically see the breach via the Auto-Refresh loop without needing a database.
*   **`self.sensors`:** A dictionary holding the state, geo-coordinates, and rolling 25-point data history of three nodes: Traffic Signal, Water Utility, and Surveillance Camera.
*   **`simulate_sensor(sensor_name)`:** The core simulation loop.
    *   It triggers the `UnifiedBB84` key exchange.
    *   It updates the node's `status` (`secure` vs `compromised`) based on the QBER result.
    *   It generates mock physical telemetry (`random.randint(10, 100)` for traffic flow).
    *   It calls `publish_sensor_data()`.
*   **`initialize_mqtt()` & `publish_sensor_data()`:** Runs `paho.mqtt` on a background thread. Every time a new reading is generated, it converts the payload (which logically includes the AES-256 key digest) into JSON and publishes it to the EMQX cloud broker under the topic `qkd/smartcity/data/<sensor_name>`.
*   **`ping_node(sensor_name)`:** The Cryptographic Ping feature. Generates a random `nonce`. If the node is `secure`, it possesses a valid AES-256 key to encrypt the response, verifying the chain is unbroken. If compromised, it has no key, and the ping mathematically fails.

### B. The Frontend: Cyber Defense Operations Center UI
The Streamlit interface is aggressively styled using custom CSS injection to mimic a professional SOC terminal (e.g., Palantir Gotham, Databricks).

*   **Design System:** Stripped of all emojis and soft UI elements. Uses a dark `#080B10` canvas, sharp borders (`#1E293B`), and `JetBrains Mono` typography.
*   **Control Bar & `streamlit_autorefresh`:** Contains the primary interaction vectors. The `Auto-Refresh` dropdown uses a background component to trigger `st.rerun()` every 5/10 seconds. On each tick, the backend `update_all_sensors()` is called, making the dashboard a "live," breathing interface.
*   **Threat Vector Map (Geospatial):** Built with `Plotly Scattermapbox`. Uses `carto-darkmatter` styling. Clean nodes display green (`#10B981`); compromised nodes display red (`#EF4444`) with a glowing opacity halo representing the breached radius.
*   **QBER Threat Assessment Chart:** A Plotly Bar Chart mapping the QBER of each node. A critical red dashed line explicitly marks the `11%` BB84 security threshold. This visually proves to the operator exactly *why* a key was aborted.
*   **Telemetry & QBER Time Series:** Dual-axis Plotly line charts displaying historical telemetry values (blue) mapped directly against historical QBER (red dashed).
*   **Cryptographic Terminal Logs:** A custom CSS scrolling text box (`div.term-output`) that streams simulated backend logs, detailing the exact hex string of derived AES-256 keys or throwing `WARN` alerts when a key is destroyed.

---

## 5. Active Countermeasures & Incident Response

A major focus of the project is demonstrating how networks respond to quantum intrusion. 

When the user selects a node (e.g., `Surveillance Camera`) from the **Attack Target Node** dropdown and clicks **SIMULATE ATTACK**:
1.  The `attacked_target` property in the backend is updated.
2.  On the next telemetry cycle, Eve begins measuring the camera's quantum channel.
3.  The camera's QBER instantly spikes (typically ~25%).
4.  The key exchange is aborted; the node is marked `COMPROMISED`.
5.  **The Failsafe UI:** The interface dynamically injects an **"Active Countermeasures & Failsafes"** panel.
    *   The operator can click **INITIATE QUANTUM REROUTING**, which simulates bypassing the compromised physical fiber line, utilizing a secondary path. This clears the attack state and securely restores the node.
    *   Alternatively, **PROVISION STANDBY NODE** spins up a cold-spare, logging the incident response in the terminal.

---

## 6. Deployment Pipeline

The project is designed to deploy instantly to cloud infrastructure without complex continuous integration setups.

1.  **Dependencies (`requirements.txt`):** Explicitly locks versions for `streamlit`, `numpy`, `plotly`, and `paho-mqtt`.
2.  **Streamlit Community Cloud:** Pointing Streamlit Cloud to the GitHub repository automatically pulls the code, installs requirements, and runs `app.py`. The `os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"` line specifically prevents inotify exhaustion limits common in serverless environments.
3.  **Render Deployment:** The repository contains a lightweight `Dockerfile` based on `python:3.10-slim`. It sets `MPLBACKEND=Agg` (to prevent UI rendering crashes) and serves the Streamlit app on port `8501`. The `render.yaml` Blueprint file configures the exact CPU/RAM limits for one-click infrastructure-as-code deployment on Render's Web Services.

Because the MQTT broker (`broker.emqx.io`) is a decoupled cloud service, anyone opening the live deployment URL from any browser in the world will subscribe to the exact same live data stream, perfectly demonstrating edge-to-cloud IoT security.
