#!/usr/bin/env python
"""EMQX connection using MQTT v3.1.1 explicitly."""

import paho.mqtt.client as mqtt
import time
import ssl

# Test with MQTT 3.1.1
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id='qkd_demo_test',
    protocol=mqtt.MQTTv311  # Explicit MQTT 3.1.1
)

# Set credentials
client.username_pw_set('AnirudhAshokAdmin', 'anirudh@1610')

# Disable cert verification
try:
    client.tls_insecure_set(True)
    client.tls_set(
        ca_certs=None,
        certfile=None, 
        keyfile=None,
        cert_reqs=ssl.CERT_NONE,
        tls_version=ssl.PROTOCOL_TLS,  # Use automatic TLS version
        ciphers=None
    )
except Exception as e:
    print(f'TLS setup warning: {e}')

print('=' * 70)
print('EMQX Connection Test - MQTT v3.1.1')
print('=' * 70)
print('Host: l3607181.ala.asia-southeast1.emqxsl.com:8883')
print('Port: 8883 (TLS)')
print('Protocol: MQTT 3.1.1')
print('Username: AnirudhAshokAdmin')
print('=' * 70 + '\n')

connected = False

def on_connect(client, userdata, flags, reason_code, properties):
    global connected
    connected = True
    print(f'✓✓✓ CONNECTED! ✓✓✓')
    print(f'CONNACK reason code: {reason_code}')
    print(f'Connection flags: {flags}')
    if reason_code == 0:
        print('✓ Connection successful - authentication OK!')
    else:
        print(f'⚠ Non-zero reason code. Check EMQX logs.')

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f'\nDisconnected with reason code: {reason_code}')

def on_message(client, userdata, msg):
    print(f'Message received: {msg.topic} = {msg.payload.decode()}')

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

try:
    print('Initiating TLS connection...')
    client.connect('l3607181.ala.asia-southeast1.emqxsl.com', 8883, keepalive=60)
    client.loop_start()
    
    print('Waiting for connection...')
    wait_count = 0
    while not connected and wait_count < 30:  # Wait up to 15 seconds
        time.sleep(0.5)
        wait_count += 1
        print('.', end='', flush=True)
    
    print()
    
    if connected:
        print('\n✓ Successfully connected to EMQX!')
        print('\nPublishing test message...')
        
        # Publish a test message
        result = client.publish(
            'test/hotspot_connection',
            'Connection successful from hotspot',
            qos=1
        )
        print(f'Published with message ID: {result.mid}')
        
        # Keep connected for a bit
        time.sleep(3)
    else:
        print('\n✗ Connection timeout - check network and credentials')
    
    client.loop_stop()
    client.disconnect()
    print('Disconnected.')
    
except ssl.SSLError as ssl_err:
    print(f'\n✗ SSL/TLS Error: {ssl_err}')
    print('This might indicate:')
    print('  - EMQX server certificate issue')
    print('  - Incompatible TLS version')
    print('  - Server rejecting the connection')
    
except ConnectionRefusedError:
    print(f'\n✗ Connection Refused')
    print('The server is actively rejecting connections.')
    print('Check: 1) Hostname/port  2) Firewall rules  3) Credentials')
    
except Exception as e:
    print(f'\n✗ Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
