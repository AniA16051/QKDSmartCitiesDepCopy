# QKD-Secured Smart City IoT Network

Simulates smart city IoT sensors (traffic light, water meter, surveillance
camera) establishing secure communication with a control center using BB84
quantum key distribution, then using the derived key for AES-256 encrypted
data transmission. Detects eavesdropping via QBER (Quantum Bit Error Rate)
spikes, with a live dashboard, a real 3-device network demo, and a
classical vs quantum comparison.

## Project structure

```
core/
  bb84.py               BB84 protocol simulation (Qiskit)
  crypto_layer.py        AES-256 encryption using the QKD-derived key
  classical_baseline.py  RSA / ECDH comparison benchmarks
network/
  sensor_node.py          IoT sensor process (publishes over MQTT)
  control_center.py       Receives and decrypts sensor data
  shared_keystore.py      Local key handoff between sensor and control center
  live_demo/              Real 3-separate-computer BB84 demo (Alice/Bob/Eve)
dashboard/
  app.py                  Streamlit live dashboard
  mqtt_monitor.py         Background MQTT listener feeding the dashboard
  node_locations.py       Map coordinates for each sensor
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

If `requirements.txt` isn't present yet, install directly:
```bash
pip install qiskit qiskit-aer cryptography matplotlib numpy paho-mqtt \
            streamlit streamlit-autorefresh streamlit-folium folium pandas
pip freeze > requirements.txt
```

---

## Running locally (single machine, Mosquitto on localhost)

**1. Start a local broker**
```bash
mosquitto -v
```

**2. Run the core demo**
```bash
python3 -m network.control_center      # separate terminal, leave running
python3 -m network.sensor_node --id traffic-node-07 --type traffic_flow
```

**3. Generate the classical vs quantum comparison** (do this once, outside
the dashboard — Qiskit can crash if invoked from inside Streamlit's process
on some machines):
```bash
python3 -m core.classical_baseline
```

**4. Launch the dashboard**
```bash
export OMP_NUM_THREADS=1
export KMP_DUPLICATE_LIB_OK=TRUE
streamlit run dashboard/app.py
```

The dashboard has 5 tabs: **Overview** (alert banner + live map), **Nodes**
(sortable status table + per-node QBER chart / latest reading),
**Attack simulation** (launch/stop a real eavesdropping node with one
click), **Classical vs quantum** (the RSA/ECDH/BB84 comparison), and
**Security log** (tabular event history).

---

## Running as a real 3-device demo (same WiFi/LAN)

See `network/live_demo/` — genuinely separate Alice (sender), Bob
(receiver), and Eve (eavesdropper) processes, each meant to run on its own
physical computer. Edit `network/live_demo/common.py` on every machine to
point `BROKER_HOST` at whichever computer is running Mosquitto (its LAN IP,
not `localhost`). See the comments in that file for the full protocol
explanation and honest limitations of simulating a quantum channel over an
ordinary network.

---

## Deploying with a cloud broker (EMQX Cloud) — for a public, multi-location demo

Use this when you want the sender, receiver, and eavesdropper to run on
devices that are NOT on the same network (e.g. a real public demo, or
teammates in different locations).

### 1. Create your EMQX Cloud deployment
- Sign in at [cloud.emqx.com](https://cloud.emqx.com)
- Create a new deployment (the **Serverless** plan has a free tier — this
  is enough for this project)
- Wait for it to finish provisioning

### 2. Get your connection details
On your deployment's **Overview** page, under **Connection**, note down:
- **Broker host** (something like `xxxxxxxx.ala.dedicated.aws.emqxsl.com`
  or similar)
- **Port** — EMQX Cloud Serverless typically only exposes the **TLS port
  (8883)** for public/anonymous connections, not plaintext 1883. Use 8883
  unless your deployment's Overview page explicitly shows a working 1883
  listener.

### 3. Create broker credentials
In your deployment, go to **Authentication & ACL** (or **Access Control**)
→ add a new username/password credential. Note both values.

### 4. Update every file that connects to the broker
Every file below has a small config block near the top. Edit all of them
with the same values:

- `network/sensor_node.py`
- `network/control_center.py`
- `dashboard/mqtt_monitor.py`
- `network/live_demo/common.py`

```python
BROKER_HOST = "xxxxxxxx.ala.dedicated.aws.emqxsl.com"   # your EMQX host
BROKER_PORT = 8883
BROKER_USERNAME = "your-emqx-username"
BROKER_PASSWORD = "your-emqx-password"
BROKER_USE_TLS = True     # required for EMQX Cloud
```

That's the entire code change needed to move from local to cloud — nothing
else in the project needs to be touched.

### 5. Test before your actual demo
Run the sender, receiver, and dashboard from genuinely different networks
(e.g. your laptop on WiFi + a phone hotspot) at least once ahead of time.
Cloud networking issues (firewall rules, wrong port, TLS not enabled) are
much better discovered in a rehearsal than live.

### 6. Deploy the dashboard so others can view it
Push this repo to GitHub, then deploy `dashboard/app.py` on
[Streamlit Community Cloud](https://streamlit.io/cloud) (free) — it will
connect to your same EMQX broker and show the same live data to anyone
with the link.

---

## How it works

1. **Key exchange**: Each sensor node ("Alice") runs BB84 with the control
   center ("Bob") — random bits encoded in random bases (Z/X), sent as
   qubits, measured in randomly chosen bases.
2. **Sifting**: Bits are kept only where Alice's and Bob's basis choices
   matched (~50% of transmissions).
3. **QBER check**: A sample of the sifted key is compared publicly. If
   error rate > 11%, the channel is assumed compromised and the key is
   discarded — the node refuses to transmit.
4. **Key derivation**: The surviving key bits are hashed (SHA-256) into a
   256-bit AES key.
5. **Secure transmission**: Sensor readings are encrypted with AES-256-GCM
   using the QKD-derived key before being sent to the control center.
6. **Eve simulation**: An optional intercept-resend attacker measures
   qubits in a randomly guessed basis and forwards a re-prepared qubit —
   this introduces ~25% average error, which is what the QBER check
   detects.

## Key result

Across 30 trials: clean channels consistently measure 0% QBER; channels
under full intercept-resend attack consistently measure 15-38% QBER — all
well above the 11% BB84 security threshold, giving reliable eavesdropping
detection.

## Honest limitations (for the report)

- This is a **simulation**, not real quantum hardware or a real
  fiber-optic channel.
- The 3-device live demo (`network/live_demo/`) represents qubits as
  classical data (a bit + a basis) traveling over an ordinary network,
  since real quantum states cannot travel over MQTT/TCP. This faithfully
  reproduces BB84's protocol logic and error-detection behavior, but is
  not a cryptographically secure implementation the way real photon-based
  QKD is — anyone with network access could technically read the raw data,
  unlike a real quantum channel protected by the no-cloning theorem.
- The security argument for BB84 over classical key exchange: RSA/ECC rely
  on computational hardness (breakable by a sufficiently large quantum
  computer via Shor's algorithm). QKD's security instead rests on physics
  — making it "quantum-safe" regardless of future attacker compute power.
