#!/usr/bin/env python
"""EMQX connection test with updated credentials."""

import paho.mqtt.client as mqtt
import time
import ssl

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id='qkd_test_new_creds'
)

# Set new credentials
client.username_pw_set('AnirudhAshokAdmin', 'AnirudhMQTT2026!')

# Configure TLS
client.tls_set(
    ca_certs=None,
    certfile=None, 
    keyfile=None,
    cert_reqs=ssl.CERT_NONE,
    tls_version=ssl.PROTOCOL_TLS,
    ciphers=None
)
client.tls_insecure_set(True)

print('=' * 70)
print('EMQX Connection Test - Updated Credentials')
print('=' * 70)
print('Host: l3607181.ala.asia-southeast1.emqxsl.com:8883')
print('Port: 8883 (TLS)')
print('Username: AnirudhAshokAdmin')
print('Password: AnirudhMQTT2026!')
print('=' * 70 + '\n')

connected = False

def on_connect(client, userdata, flags, reason_code, properties):
    global connected
    connected = True
    print(f'✓✓✓ CONNECTED SUCCESSFULLY! ✓✓✓')
    print(f'CONNACK reason code: {reason_code}')
    if reason_code == 0:
        print('✓ Authentication successful!')
    else:
        print(f'⚠ Reason code {reason_code}')

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f'\nDisconnected: {reason_code}')

def on_message(client, userdata, msg):
    print(f'Message: {msg.topic} = {msg.payload.decode()}')

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

try:
    print('Connecting to EMQX...\n')
    client.connect('l3607181.ala.asia-southeast1.emqxsl.com', 8883, keepalive=60)
    client.loop_start()
    
    wait_count = 0
    while not connected and wait_count < 40:  # Wait up to 20 seconds
        time.sleep(0.5)
        wait_count += 1
        print('.', end='', flush=True)
    
    print()
    
    if connected:
        print('\n✓ Successfully connected to EMQX!')
        print('\nPublishing test message...')
        
        result = client.publish(
            'test/hotspot_connection',
            'Connected successfully with new credentials!',
            qos=1
        )
        print(f'Published message with ID: {result.mid}')
        print('✓ Ready to use MQTT for QKD demo')
        
        time.sleep(2)
    else:
        print('\n✗ Connection failed - check credentials and network')
    
    client.loop_stop()
    client.disconnect()
    
except Exception as e:
    print(f'\n✗ Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
