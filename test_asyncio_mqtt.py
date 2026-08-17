#!/usr/bin/env python
"""EMQX connection test using asyncio-mqtt."""

import asyncio
import ssl
import sys

try:
    import asyncio_mqtt as aiomqtt
except ImportError:
    print('Error: asyncio-mqtt not imported correctly')
    sys.exit(1)

HOST = 'l3607181.ala.asia-southeast1.emqxsl.com'
PORT = 8883
USERNAME = 'AnirudhAshokAdmin'
PASSWORD = 'AnirudhMQTT2026!'

async def main():
    print('=' * 70)
    print('EMQX Connection Test - asyncio-mqtt')
    print('=' * 70)
    print(f'Host: {HOST}')
    print(f'Port: {PORT}')
    print(f'Username: {USERNAME}')
    print('=' * 70 + '\n')
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        print('Connecting to EMQX...')
        async with aiomqtt.Client(
            HOST, 
            port=PORT,
            username=USERNAME, 
            password=PASSWORD,
            tls_context=ssl_context
        ) as client:
            print('✓✓✓ CONNECTED! ✓✓✓')
            
            # Publish a test message
            print('\nPublishing test message...')
            await client.publish(
                'test/asyncio_connection',
                'Connected with asyncio-mqtt!',
                qos=1
            )
            print('✓ Message published')
            
            # Wait a bit
            await asyncio.sleep(2)
            
            print('\n✓ EMQX Connection successful!')
            
    except Exception as e:
        print(f'✗ Error: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
