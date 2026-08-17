"""
Live dashboard for the QKD-secured smart city network -- professional edition.

Run with:
    streamlit run dashboard/app.py

Same functionality as before, reorganized into a cleaner, tabbed layout:
  - Top metrics strip (node counts, broker status)
  - Overview tab: alert banner + map
  - Nodes tab: sortable table + per-node QBER chart / latest reading on demand
  - Attack simulation tab: launch / stop attacker controls
  - Security log tab: tabular event history
"""

import sys
import os
import subprocess
import signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

from dashboard.mqtt_monitor import MqttMonitor
from dashboard.node_locations import get_location, CITY_CENTER

st.set_page_config(page_title="Smart City QKD Dashboard", layout="wide")

# --- Minimal professional styling (Databricks-esque: neutral, tabular, calm) ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 1200px; }
    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.06);
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-radius: 6px;
        padding: 0.75rem 1rem;
    }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_monitor():
    return MqttMonitor()


if "attack_processes" not in st.session_state:
    st.session_state.attack_processes = {}
if "was_aborted" not in st.session_state:
    st.session_state.was_aborted = set()

monitor = get_monitor()
st_autorefresh(interval=2000, key="dashboard_refresh")

state = monitor.snapshot()
nodes = state["nodes"]
readings = state["readings"]
qber_history = state["qber_history"]
events = state["events"]

# --- Header ------------------------------------------------------------
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("Smart city QKD network")
    st.caption("Quantum key distribution security monitoring for IoT infrastructure")
with header_col2:
    conn_label = "Connected" if state["connected"] else "Disconnected"
    conn_icon = "🟢" if state["connected"] else "🔴"
    st.markdown(f"<div style='text-align:right; padding-top: 1.5rem;'>"
                f"{conn_icon} <b>Broker: {conn_label}</b></div>", unsafe_allow_html=True)

# --- Top metrics strip ---------------------------------------------------
total_nodes = len(nodes)
healthy_nodes = sum(1 for info in nodes.values() if info.get("status") == "ok")
compromised_nodes_count = total_nodes - healthy_nodes
total_readings = sum(len(v) for v in readings.values())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total nodes", total_nodes)
m2.metric("Healthy", healthy_nodes)
m3.metric("Compromised", compromised_nodes_count,
          delta=None if compromised_nodes_count == 0 else "attention needed",
          delta_color="inverse")
m4.metric("Readings logged", total_readings)

st.write("")

# --- Tabs ----------------------------------------------------------------
tab_overview, tab_nodes, tab_attack, tab_log = st.tabs(
    ["Overview", "Nodes", "Attack simulation", "Security log"]
)

# ===== OVERVIEW TAB =====
with tab_overview:
    compromised_ids = [nid for nid, info in nodes.items() if info.get("status") != "ok"]
    if compromised_ids:
        st.error(f"**Operations alert** — {len(compromised_ids)} node(s) compromised or "
                 f"unreachable: {', '.join(compromised_ids)}. In a real deployment this "
                 f"would page the on-call security team.")
    else:
        st.success("All monitored nodes are currently secure.")

    st.subheader("Sensor map")
    if nodes:
        m = folium.Map(location=CITY_CENTER, zoom_start=13, tiles="CartoDB dark_matter")
        for node_id, info in nodes.items():
            lat, lon = get_location(node_id)
            status = info.get("status")
            qber = info.get("qber")
            color = "green" if status == "ok" else "red"
            qber_str = f"{qber:.2%}" if qber is not None else "N/A"
            folium.CircleMarker(
                location=(lat, lon),
                radius=12,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=f"{node_id}<br>Status: {status}<br>QBER: {qber_str}",
                tooltip=node_id,
            ).add_to(m)
        st_folium(m, width=None, height=380, key="city_map")
    else:
        st.caption("Map will populate once sensor nodes report in.")

# ===== NODES TAB =====
with tab_nodes:
    if not nodes:
        st.info("No sensor nodes have reported in yet. Start one with:\n\n"
                "`python3 -m network.sensor_node --id traffic-node-07 --type traffic_flow`\n\n"
                "or use the Attack simulation tab.")
    else:
        rows = []
        for node_id, info in sorted(nodes.items()):
            status = info.get("status")
            qber = info.get("qber")
            rows.append({
                "Node ID": node_id,
                "Status": "Recovered" if info.get("just_recovered") else
                          ("Secure" if status == "ok" else "Compromised"),
                "QBER": f"{qber:.2%}" if qber is not None else "N/A",
                "Key fingerprint": info.get("fingerprint", "—") if status == "ok" else "—",
                "Readings logged": len(readings.get(node_id, [])),
                "Last seen (UTC)": info.get("last_seen", "—"),
            })
        df = pd.DataFrame(rows)

        def _highlight(row):
            color = "background-color: rgba(220, 50, 47, 0.12)" if row["Status"] == "Compromised" \
                else "background-color: rgba(38, 166, 91, 0.10)" if row["Status"] in ("Secure", "Recovered") \
                else ""
            return [color] * len(row)

        st.dataframe(df.style.apply(_highlight, axis=1), use_container_width=True, hide_index=True)

        st.write("")
        st.subheader("Node detail")
        selected_node = st.selectbox("Select a node to inspect", sorted(nodes.keys()))

        if selected_node:
            detail_col1, detail_col2 = st.columns([1, 1])
            with detail_col1:
                history = qber_history.get(selected_node, [])
                if len(history) >= 2:
                    hist_df = pd.DataFrame(
                        [(ts, q * 100) for ts, q in history],
                        columns=["time", "QBER (%)"],
                    ).set_index("time")
                    st.caption("QBER history")
                    st.line_chart(hist_df, height=220)
                else:
                    st.caption("Not enough QBER history yet for a chart.")
            with detail_col2:
                node_readings = readings.get(selected_node, [])
                st.caption(f"Latest decrypted reading ({len(node_readings)} logged)")
                if node_readings:
                    st.json(node_readings[0], expanded=True)
                else:
                    st.caption("No decrypted readings yet.")

# ===== ATTACK SIMULATION TAB =====
with tab_attack:
    st.subheader("Launch a live eavesdropping attack")
    st.caption("Starts a real sensor-node process running BB84 with an active "
               "eavesdropper, exactly as it would run on separate hardware.")

    atk_col1, atk_col2, atk_col3 = st.columns([2, 2, 2])
    with atk_col1:
        attack_node_id = st.text_input("Node ID to attack", value="camera-22")
    with atk_col2:
        sensor_type = st.selectbox("Sensor type", ["surveillance", "traffic_flow", "water_flow"])
    with atk_col3:
        st.write("")
        st.write("")
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            launch = st.button("Simulate attacker", type="primary", use_container_width=True)
        with btn_col2:
            stop = st.button("Stop attacker", use_container_width=True)

    if launch:
        proc = subprocess.Popen(
            [sys.executable, "-m", "network.sensor_node",
             "--id", attack_node_id, "--type", sensor_type,
             "--eavesdrop", "--interval", "6"],
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        st.session_state.attack_processes[attack_node_id] = proc.pid
        st.success(f"Launched attacking sensor node '{attack_node_id}' (PID {proc.pid}). "
                   f"Check the Nodes tab — its status should flip to Compromised within "
                   f"a few seconds.")

    if stop:
        pid = st.session_state.attack_processes.get(attack_node_id)
        if pid is None:
            st.warning(f"No tracked attacker process for '{attack_node_id}' in this session.")
        else:
            try:
                os.kill(pid, signal.SIGTERM)
                del st.session_state.attack_processes[attack_node_id]
                st.success(f"Stopped attacker on '{attack_node_id}' (PID {pid}). "
                           f"It should recover to a clean session within a few cycles.")
            except ProcessLookupError:
                st.info(f"Process {pid} already stopped.")
                st.session_state.attack_processes.pop(attack_node_id, None)

    if st.session_state.attack_processes:
        st.write("")
        st.caption("Currently tracked attacker processes (this session)")
        proc_df = pd.DataFrame(
            [{"Node ID": nid, "PID": pid} for nid, pid in st.session_state.attack_processes.items()]
        )
        st.dataframe(proc_df, use_container_width=True, hide_index=True)

# ===== SECURITY LOG TAB =====
with tab_log:
    st.subheader("Security event log")

    if not events:
        st.caption("No security events recorded.")
    else:
        log_rows = []
        for event in events[:50]:
            reason = event.get("reason", "unknown")
            node_id = event.get("node_id", "?")
            qber = event.get("qber")
            ts = event.get("timestamp", "")
            log_rows.append({
                "Timestamp (UTC)": ts,
                "Node ID": node_id,
                "Event": "Recovered" if reason == "recovered" else reason.replace("_", " ").title(),
                "QBER": f"{qber:.2%}" if qber is not None else "—",
            })
        log_df = pd.DataFrame(log_rows)

        def _highlight_log(row):
            color = "background-color: rgba(38, 166, 91, 0.10)" if row["Event"] == "Recovered" \
                else "background-color: rgba(220, 50, 47, 0.10)"
            return [color] * len(row)

        st.dataframe(log_df.style.apply(_highlight_log, axis=1), use_container_width=True, hide_index=True)