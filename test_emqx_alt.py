#!/usr/bin/env python
"""Alternative EMQX connection test using SSL context directly."""

import paho.mqtt.client as mqtt
import time
import ssl

# Create a more permissive SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='test_alt_connection')
client.tls_set_context(ssl_context)
client.username_pw_set('AnirudhAshokAdmin', 'anirudh@1610')

print('EMQX Connection Test (Alternative SSL Method)')
print('=' * 60)
print('Host: l3607181.ala.asia-southeast1.emqxsl.com:8883')
print('User: AnirudhAshokAdmin')
print('Method: Direct SSL context (permissive)')
print('=' * 60)

connected = {'flag': False}

def on_connect(client, userdata, flags, reason_code, properties):
    connected['flag'] = True
    print(f'\n✓✓✓ CONNECTED! ✓✓✓')
    print(f'Reason code: {reason_code}')
    if reason_code == 0:
        print('✓ Authentication successful!')
    else:
        print(f'Note: Non-zero reason code: {reason_code}')

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f'Disconnected: {reason_code}')

client.on_connect = on_connect
client.on_disconnect = on_disconnect

try:
    print('\nAttempting connection...')
    client.connect('l3607181.ala.asia-southeast1.emqxsl.com', 8883, keepalive=60)
    client.loop_start()
    
    for i in range(10):
        time.sleep(0.5)
        if connected['flag']:
            print('\n✓ Connected successfully!')
            time.sleep(2)
            break
        print('.', end='', flush=True)
    
    if not connected['flag']:
        print('\n✗ Connection timed out after 5 seconds')
    
    client.loop_stop()
    client.disconnect()
    
except Exception as e:
    print(f'\n✗ Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
