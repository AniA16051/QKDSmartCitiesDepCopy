"""
Enhanced QKD Dashboard with Authentication and Role-Based Access

Run with:
    streamlit run dashboard/app_enhanced.py --logger.level=warning

Features:
- Login/authentication system
- Role-based access (Admin/User)
- Interactive controls for admin
- Real-time monitoring
- Multi-computer sync via MQTT
"""

import sys
import os
import subprocess
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import paho.mqtt.client as mqtt

from dashboard.auth import get_auth_manager
from dashboard.mqtt_monitor import MqttMonitor
from dashboard.node_locations import get_location, CITY_CENTER

# Page config
st.set_page_config(
    page_title="QKD Smart City Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .login-container {
        max-width: 400px;
        margin: 50px auto;
        padding: 40px;
        border: 1px solid #ddd;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .admin-badge { 
        background: #FF6B6B; 
        color: white; 
        padding: 4px 8px; 
        border-radius: 4px; 
        font-size: 12px;
        font-weight: bold;
    }
    .user-badge { 
        background: #4ECDC4; 
        color: white; 
        padding: 4px 8px; 
        border-radius: 4px; 
        font-size: 12px;
        font-weight: bold;
    }
    .status-ok { color: #06D6A0; font-weight: bold; }
    .status-alert { color: #FF6B6B; font-weight: bold; }
    .metric-card {
        padding: 20px;
        border-radius: 10px;
        background: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Session State Management
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if "auth_manager" not in st.session_state:
        st.session_state.auth_manager = get_auth_manager()
    
    if "session_token" not in st.session_state:
        st.session_state.session_token = None
    
    if "username" not in st.session_state:
        st.session_state.username = None
    
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    
    if "mqtt_monitor" not in st.session_state:
        st.session_state.mqtt_monitor = MqttMonitor()
    
    if "mqtt_client" not in st.session_state:
        st.session_state.mqtt_client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="dashboard-control"
        )
        broker_host = os.getenv("BROKER_HOST", "localhost")
        broker_port = int(os.getenv("BROKER_PORT", "1883"))
        # connect_async keeps the web server available while the broker service
        # is starting (especially important on Railway, which has no Compose
        # startup ordering).
        st.session_state.mqtt_client.connect_async(broker_host, broker_port, keepalive=60)
        st.session_state.mqtt_client.loop_start()


init_session_state()


# ============================================================================
# Authentication Pages
# ============================================================================

def render_login_page():
    """Render login page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        # 🔐 QKD Dashboard
        ### Quantum Key Distribution Security Monitoring
        """)
        
        with st.container(border=True):
            st.markdown("### Login")
            
            username = st.text_input(
                "Username",
                placeholder="admin or user",
                key="login_username"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )
            
            if st.button("Login", use_container_width=True, type="primary"):
                success, token, message = st.session_state.auth_manager.authenticate(
                    username, password
                )
                
                if success:
                    st.session_state.session_token = token
                    st.session_state.username = username
                    st.session_state.user_role = st.session_state.auth_manager.get_user_role(username)
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        st.markdown("""
        ---
        **Demo Credentials:**
            - **Admin:** `admin` / the `QKD_ADMIN_PASSWORD` deployment variable
            - **User:** `user` / the `QKD_USER_PASSWORD` deployment variable
        """)


# ============================================================================
# Dashboard Pages
# ============================================================================

def render_header():
    """Render dashboard header"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🔐 Smart City QKD Network")
        st.caption("Real-time quantum key distribution monitoring & control")
    
    with col2:
        monitor = st.session_state.mqtt_monitor
        state = monitor.snapshot()
        status = "🟢 Online" if state["connected"] else "🔴 Offline"
        st.metric("Broker Status", status)
    
    with col3:
        role_badge = f'<span class="admin-badge">ADMIN</span>' if st.session_state.user_role == 'admin' else f'<span class="user-badge">USER</span>'
        st.markdown(f"""
        {st.session_state.username}
        
        {role_badge}
        """, unsafe_allow_html=True)
        
        if st.button("Logout", key="logout_btn"):
            st.session_state.auth_manager.logout(st.session_state.session_token)
            st.session_state.session_token = None
            st.session_state.username = None
            st.session_state.user_role = None
            st.rerun()


def render_overview_tab():
    """Overview tab - Metrics and status"""
    monitor = st.session_state.mqtt_monitor
    state = monitor.snapshot()
    nodes = state["nodes"]
    readings = state["readings"]
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_nodes = len(nodes)
    healthy_nodes = sum(1 for info in nodes.values() if info.get("status") == "ok")
    compromised = total_nodes - healthy_nodes
    
    with col1:
        st.metric("Total Nodes", total_nodes, delta="nodes active")
    with col2:
        st.metric("✓ Healthy", healthy_nodes)
    with col3:
        delta_text = "⚠️ Attention" if compromised > 0 else "Secure"
        st.metric("⚠️ Compromised", compromised, delta=delta_text, delta_color="inverse" if compromised > 0 else "off")
    with col4:
        total_readings = sum(len(v) for v in readings.values())
        st.metric("📊 Readings", total_readings)
    
    st.divider()
    
    # Alert banner if needed
    if compromised > 0:
        st.warning(f"🔴 **SECURITY ALERT:** {compromised} node(s) showing potential eavesdropping (QBER > 11%)")
    
    # Node status table
    st.subheader("Node Status")
    
    node_data = []
    for node_id, info in sorted(nodes.items()):
        status_icon = "✓ Healthy" if info.get("status") == "ok" else "⚠️ Alert"
        qber = info.get("qber_last", "N/A")
        last_seen = info.get("last_seen", "N/A")
        
        node_data.append({
            "Node ID": node_id,
            "Status": status_icon,
            "QBER": f"{qber:.2f}%" if isinstance(qber, (int, float)) else qber,
            "Last Seen": last_seen
        })
    
    if node_data:
        df = pd.DataFrame(node_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No nodes currently connected")


def render_nodes_tab():
    """Nodes tab - Detailed node information"""
    monitor = st.session_state.mqtt_monitor
    state = monitor.snapshot()
    nodes = state["nodes"]
    
    if not nodes:
        st.info("No nodes connected")
        return
    
    # Select node
    selected_node = st.selectbox("Select Node", list(nodes.keys()))
    
    if selected_node:
        node_info = nodes[selected_node]
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Node ID", selected_node)
        with col2:
            status = node_info.get("status", "unknown")
            st.metric("Status", "✓ OK" if status == "ok" else "⚠️ ALERT")
        with col3:
            qber = node_info.get("qber_last", 0)
            st.metric("QBER", f"{qber:.2f}%")
        with col4:
            st.metric("Last Seen", node_info.get("last_seen", "N/A"))
        
        # QBER History Chart
        st.subheader("QBER History")
        qber_history = state.get("qber_history", {}).get(selected_node, [])
        
        if qber_history:
            timestamps = [item[0] for item in qber_history]
            qber_values = [item[1] for item in qber_history]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timestamps, y=qber_values,
                mode='lines+markers',
                name='QBER',
                line=dict(color='#FF6B6B', width=2),
                fill='tozeroy'
            ))
            fig.add_hline(y=11, line_dash="dash", line_color="red", annotation_text="Threshold (11%)")
            fig.update_layout(
                title="",
                xaxis_title="Time",
                yaxis_title="QBER (%)",
                height=300,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No QBER history available")


def render_admin_controls_tab():
    """Admin controls tab - Start/stop nodes, attack simulation"""
    st.subheader("🔧 Admin Controls")
    
    col1, col2 = st.columns(2)
    
    # Node Management
    with col1:
        st.markdown("### Node Management")
        
        with st.form("start_node_form"):
            node_id = st.text_input("Node ID", value="test-node-1")
            sensor_type = st.selectbox("Sensor Type", ["traffic_flow", "water_flow", "surveillance"])
            submitted = st.form_submit_button("Start Node")
            
            if submitted:
                # Publish MQTT command
                command = {
                    "action": "start_node",
                    "node_id": node_id,
                    "sensor_type": sensor_type
                }
                st.session_state.mqtt_client.publish(
                    "smartcity/commands/start_node",
                    json.dumps(command)
                )
                st.success(f"Command sent to start {node_id}")
    
    # Attack Simulation
    with col2:
        st.markdown("### Attack Simulation")
        
        monitor = st.session_state.mqtt_monitor
        nodes = monitor.snapshot()["nodes"]
        
        if nodes:
            selected_node = st.selectbox("Target Node", list(nodes.keys()), key="attack_node")
            attack_type = st.selectbox("Attack Type", ["eavesdrop", "noise"])
            
            if attack_type == "noise":
                noise_level = st.slider("Noise Level", 0.0, 0.5, 0.05)
            
            if st.button("Simulate Attack", type="primary"):
                command = {
                    "action": "attack",
                    "node_id": selected_node,
                    "type": attack_type,
                    "noise": noise_level if attack_type == "noise" else 0.0
                }
                st.session_state.mqtt_client.publish(
                    "smartcity/commands/attack",
                    json.dumps(command)
                )
                st.warning(f"Attack simulation started on {selected_node}")
    
    st.divider()
    
    # Settings
    st.markdown("### System Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        qber_threshold = st.slider("QBER Threshold (%)", 0.05, 0.20, 0.11, step=0.01)
        if st.button("Apply QBER Threshold"):
            st.session_state.mqtt_client.publish(
                "smartcity/settings/qber_threshold",
                str(qber_threshold)
            )
            st.success(f"QBER threshold set to {qber_threshold*100:.1f}%")
    
    with col2:
        st.info("💡 Tip: Higher threshold = less sensitive, lower threshold = more sensitive")


def render_security_log_tab():
    """Security log tab - Event history"""
    st.subheader("📋 Security Events")
    
    monitor = st.session_state.mqtt_monitor
    state = monitor.snapshot()
    events = list(state.get("events", []))
    
    if events:
        # Convert events to dataframe
        event_data = []
        for event in reversed(events):
            event_data.append({
                "Timestamp": event.get("timestamp", "N/A"),
                "Type": event.get("type", "Unknown"),
                "Node": event.get("node_id", "N/A"),
                "Details": event.get("message", "")
            })
        
        df = pd.DataFrame(event_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Export button
        if st.button("📥 Export Events as CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"security_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No events logged yet")


def render_settings_tab():
    """Settings tab - User and admin settings"""
    st.subheader("⚙️ Settings")
    
    # User settings (available to all)
    with st.expander("User Settings"):
        st.info("Refresh interval: 2 seconds (auto)")
        st.info("Theme: Auto (follows system)")
    
    # Admin settings
    if st.session_state.user_role == 'admin':
        with st.expander("Admin Settings"):
            st.markdown("### User Management")
            
            tab1, tab2 = st.tabs(["Create User", "Manage Users"])
            
            with tab1:
                with st.form("create_user_form"):
                    new_username = st.text_input("Username")
                    new_password = st.text_input("Password", type="password")
                    new_role = st.selectbox("Role", ["user", "admin"])
                    
                    if st.form_submit_button("Create User"):
                        success, message = st.session_state.auth_manager.create_user(
                            new_username, new_password, new_role
                        )
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            
            with tab2:
                users = st.session_state.auth_manager.users
                user_list = [
                    {
                        "Username": username,
                        "Role": user.role,
                        "Last Login": user.last_login or "Never"
                    }
                    for username, user in users.items()
                ]
                st.dataframe(pd.DataFrame(user_list), use_container_width=True, hide_index=True)


# ============================================================================
# Main App Logic
# ============================================================================

def main():
    """Main app logic"""
    # Check authentication
    valid_session, username = st.session_state.auth_manager.verify_session(
        st.session_state.session_token
    )
    
    if not valid_session:
        render_login_page()
        return
    
    # Render authenticated dashboard
    render_header()
    
    st.markdown("---")
    
    # Tab layout
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "📈 Nodes",
        "🔧 Admin Controls" if st.session_state.user_role == 'admin' else "ℹ️ Info",
        "📋 Security Log",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_overview_tab()
    
    with tab2:
        render_nodes_tab()
    
    with tab3:
        if st.session_state.user_role == 'admin':
            render_admin_controls_tab()
        else:
            st.info("Admin controls are only available to administrators.")
            st.markdown("""
            ### User Capabilities
            - View real-time monitoring dashboard
            - Check node status and QBER metrics
            - View security logs
            - Export data for analysis
            
            ### Admin-Only Features
            - Start/stop sensor nodes
            - Simulate attacks
            - Adjust security thresholds
            - Manage users
            """)
    
    with tab4:
        render_security_log_tab()
    
    with tab5:
        render_settings_tab()


if __name__ == "__main__":
    main()
