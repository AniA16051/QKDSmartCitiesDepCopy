#!/usr/bin/env python
"""Test EMQX connection with detailed logging."""

import paho.mqtt.client as mqtt
import time
import logging
import ssl

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='test_emqx_hotspot')
client.enable_logger(logging.getLogger())
client.username_pw_set('AnirudhAshokAdmin', 'anirudh@1610')

# Setup TLS with certificate verification disabled
try:
    client.tls_set(
        ca_certs=None, 
        certfile=None, 
        keyfile=None, 
        cert_reqs=ssl.CERT_NONE, 
        tls_version=ssl.PROTOCOL_TLSv1_2,
        ciphers=None
    )
    client.tls_insecure_set(True)
except Exception as e:
    print(f"TLS setup error: {e}")

print('=' * 70)
print('EMQX Connection Test')
print('=' * 70)
print('Host: l3607181.ala.asia-southeast1.emqxsl.com:8883')
print('User: AnirudhAshokAdmin')
print('TLS: Enabled (Certificate verification disabled)')
print('=' * 70)

def on_connect(client, userdata, flags, reason_code, properties):
    print(f'\n✓✓✓ CONNECTED SUCCESSFULLY! ✓✓✓')
    print(f'Reason code: {reason_code}')
    if reason_code == 0:
        print('✓ Authentication successful!')
        print('✓ Ready to publish/subscribe to MQTT topics')

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f'\nDisconnected: reason_code={reason_code}')

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    print(f'Subscribe acknowledged: {reason_code_list}')

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_subscribe = on_subscribe

try:
    print('\nInitiating connection...')
    client.connect('l3607181.ala.asia-southeast1.emqxsl.com', 8883, keepalive=60)
    client.loop_start()
    
    print('Waiting for connection to establish...')
    time.sleep(6)
    
    if client.is_connected():
        print('\n✓ Client is connected!')
        # Try to publish a test message
        try:
            result = client.publish('test/connection', 'Connection test from hotspot', qos=1)
            print(f'Published message with mid={result.mid}')
            time.sleep(2)
        except Exception as pub_err:
            print(f'Publish error: {pub_err}')
    else:
        print('\n✗ Client is not connected')
    
    client.loop_stop()
    client.disconnect()
    print('\nTest completed.')
    
except Exception as e:
    print(f'\n✗ Connection Error: {type(e).__name__}')
    print(f'Message: {e}')
    import traceback
    traceback.print_exc()
