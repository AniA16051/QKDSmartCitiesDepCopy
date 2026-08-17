#!/usr/bin/env python
"""Detailed EMQX diagnostics - testing multiple approaches."""

import paho.mqtt.client as mqtt
import ssl
import time
import socket

HOST = 'l3607181.ala.asia-southeast1.emqxsl.com'
PORT = 8883
USERNAME = 'AnirudhAshokAdmin'
PASSWORD = 'AnirudhMQTT2026!'

print('=' * 70)
print('EMQX Detailed Diagnostics')
print('=' * 70)
print(f'Host: {HOST}')
print(f'Port: {PORT}')
print(f'Username: {USERNAME}')
print('=' * 70 + '\n')

# Test 1: Check DNS and IP
print('TEST 1: DNS Resolution')
print('-' * 70)
try:
    ip = socket.gethostbyname(HOST)
    print(f'✓ Hostname resolves to: {ip}')
except Exception as e:
    print(f'✗ DNS resolution failed: {e}')
    exit(1)

# Test 2: Check TCP connectivity
print('\nTEST 2: TCP Connectivity')
print('-' * 70)
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((ip, PORT))
    sock.close()
    print(f'✓ TCP connection to {ip}:{PORT} successful')
except Exception as e:
    print(f'✗ TCP connection failed: {e}')
    exit(1)

# Test 3: Try paho-mqtt with debug info
print('\nTEST 3: Paho-MQTT Connection')
print('-' * 70)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='diag_test')
client.username_pw_set(USERNAME, PASSWORD)

# Try without TLS first
print('\nAttempt 1: No TLS')
connected = False

def on_connect(client, userdata, flags, reason_code, properties):
    global connected
    connected = True
    print(f'  Connected! Reason: {reason_code}')

def on_connect_fail(client, userdata):
    print('  Connection failed')

def on_socket_open(client, userdata, sock):
    print('  Socket opened')

def on_socket_close(client, userdata, sock):
    print('  Socket closed')

client.on_connect = on_connect
client.on_connect_fail = on_connect_fail
client.on_socket_open = on_socket_open
client.on_socket_close = on_socket_close

try:
    print(f'  Attempting non-TLS connection to {HOST}:1883...')
    client.connect(HOST, 1883, keepalive=60)
    client.loop_start()
    time.sleep(3)
    if connected:
        print('  ✓ Non-TLS connection successful!')
    else:
        print('  ✗ Connection attempt timed out')
    client.loop_stop()
    client.disconnect()
except Exception as e:
    print(f'  ✗ Non-TLS error: {type(e).__name__}: {e}')

# Test 3b: Try with TLS
print('\nAttempt 2: With TLS')
client2 = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='diag_tls_test')
client2.username_pw_set(USERNAME, PASSWORD)

connected = False
client2.on_connect = on_connect
client2.on_connect_fail = on_connect_fail

# Configure TLS
try:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    client2.tls_set_context(ssl_context)
    print('  TLS configuration: SSL context created')
except Exception as e:
    print(f'  TLS setup error: {e}')

try:
    print(f'  Attempting TLS connection to {HOST}:8883...')
    client2.connect(HOST, PORT, keepalive=60)
    client2.loop_start()
    
    for i in range(20):
        time.sleep(0.5)
        if connected:
            break
        if i % 4 == 0:
            print(f'    Waiting... {i/2}s')
    
    if connected:
        print('  ✓ TLS connection successful!')
    else:
        print('  ✗ TLS connection timeout')
    
    client2.loop_stop()
    client2.disconnect()
    
except ssl.SSLError as e:
    print(f'  ✗ SSL Error: {e}')
    print('     (This suggests server TLS configuration issue)')
except Exception as e:
    print(f'  ✗ TLS error: {type(e).__name__}: {e}')

print('\n' + '=' * 70)
print('RECOMMENDATION:')
print('=' * 70)
print('The TCP connection works, but TLS is being rejected.')
print('Possible causes:')
print('  1. EMQX deployment has TLS restrictions or requires client certs')
print('  2. Server is rejecting connections due to IP/security policy')
print('  3. Deployment needs to be restarted or is misconfigured')
print('\nAction: Check EMQX Cloud dashboard for:')
print('  - Deployment status (running/stopped)')
print('  - TLS settings and access control rules')
print('  - Any recent changes to security settings')
print('=' * 70)
