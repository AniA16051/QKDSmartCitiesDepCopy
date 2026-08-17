#!/usr/bin/env python
"""EMQX connection with maximum SSL permissiveness."""

import paho.mqtt.client as mqtt
import time
import ssl

# Create a very permissive SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
# Allow older TLS versions
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id='qkd_test_ssl_context'
)

client.username_pw_set('AnirudhAshokAdmin', 'AnirudhMQTT2026!')
client.tls_set_context(ssl_context)

print('=' * 70)
print('EMQX Connection Test - Permissive SSL Context')
print('=' * 70)
print('Host: l3607181.ala.asia-southeast1.emqxsl.com:8883')
print('Port: 8883 (TLS)')
print('Username: AnirudhAshokAdmin')
print('Password: AnirudhMQTT2026!')
print('SSL: Permissive context (any TLS version, no cert check)')
print('=' * 70 + '\n')

connected = False
connected_time = None

def on_connect(client, userdata, flags, reason_code, properties):
    global connected, connected_time
    connected = True
    connected_time = time.time()
    print(f'\n✓✓✓ CONNECTED SUCCESSFULLY! ✓✓✓')
    print(f'CONNACK reason code: {reason_code}')
    if reason_code == 0:
        print('✓ Authentication successful!')
        print('✓ Ready to use MQTT')
    else:
        print(f'⚠ Connection with reason code: {reason_code}')

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f'Disconnected: {reason_code}')

client.on_connect = on_connect
client.on_disconnect = on_disconnect

try:
    print('Initiating connection...\n')
    client.connect('l3607181.ala.asia-southeast1.emqxsl.com', 8883, keepalive=60)
    client.loop_start()
    
    # Wait for connection
    wait_count = 0
    while not connected and wait_count < 60:  # Wait up to 30 seconds
        time.sleep(0.5)
        wait_count += 1
        if wait_count % 10 == 0:
            print(f'  Waiting... {wait_count/2} seconds')
        else:
            print('.', end='', flush=True)
    
    if connected:
        print(f'\n✓ Connection established in {connected_time}')
        
        # Publish a test message
        print('\nPublishing test message...')
        result = client.publish(
            'test/hotspot_success',
            'Successfully connected from hotspot!',
            qos=1
        )
        print(f'✓ Published message ID: {result.mid}')
        
        time.sleep(2)
        print('\n✓✓✓ EMQX Connection Successful! ✓✓✓')
    else:
        print(f'\n✗ Connection failed after {wait_count/2} seconds')
    
    client.loop_stop()
    client.disconnect()
    
except ssl.SSLError as e:
    print(f'\n✗ SSL Error: {e}')
except Exception as e:
    print(f'\n✗ Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
