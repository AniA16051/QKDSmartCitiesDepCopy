#!/usr/bin/env python
"""Diagnose EMQX connection with raw socket."""

import socket
import time

HOST = 'l3607181.ala.asia-southeast1.emqxsl.com'
PORT = 8883

print('=' * 70)
print('Raw Socket Diagnostic')
print('=' * 70)
print(f'Host: {HOST}')
print(f'Port: {PORT}')
print('=' * 70 + '\n')

try:
    print('1. Resolving hostname...')
    ip_addr = socket.gethostbyname(HOST)
    print(f'   ✓ Resolved to: {ip_addr}')
    
    print('\n2. Creating socket...')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    print('   ✓ Socket created')
    
    print(f'\n3. Connecting to {ip_addr}:{PORT}...')
    sock.connect((ip_addr, PORT))
    print('   ✓ TCP connection established!')
    
    print('\n4. Receiving server banner...')
    sock.settimeout(2)
    try:
        banner = sock.recv(1024)
        if banner:
            print(f'   Server sent: {banner[:100]}')
        else:
            print('   (No banner received)')
    except socket.timeout:
        print('   (No data received - timeout)')
    
    print('\n5. Closing connection...')
    sock.close()
    print('   ✓ Connection closed')
    
    print('\n✓ TCP connection works - TLS issue must be at SSL/protocol level')
    
except socket.gaierror as e:
    print(f'   ✗ DNS resolution failed: {e}')
except socket.timeout:
    print(f'   ✗ Connection timeout')
except ConnectionRefusedError:
    print(f'   ✗ Connection refused')
except ConnectionResetError as e:
    print(f'   ✗ Connection reset: {e}')
except Exception as e:
    print(f'   ✗ Error: {type(e).__name__}: {e}')
