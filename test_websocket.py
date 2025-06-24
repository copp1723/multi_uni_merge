#!/usr/bin/env python3
"""
Simple WebSocket test client for testing the /swarm namespace
"""

import socketio
import time
import sys

# Create a Socket.IO client
sio = socketio.Client()

@sio.event(namespace='/swarm')
def connect():
    print('Connected to WebSocket server!')
    
@sio.event(namespace='/swarm')
def connection_status(data):
    print(f'Connection status received: {data}')
    
@sio.event(namespace='/swarm')
def disconnect():
    print('Disconnected from server')
    
@sio.event(namespace='/swarm')
def swarm_responses(data):
    print(f'Received swarm responses: {data}')
    
@sio.event(namespace='/swarm')
def message_received(data):
    print(f'Message acknowledgment: {data}')
    
@sio.event(namespace='/swarm')
def error(data):
    print(f'Error received: {data}')

def test_websocket():
    try:
        # Connect to the server
        print('Connecting to WebSocket server...')
        sio.connect('http://localhost:5000', namespaces=['/swarm'])
        
        # Wait for connection
        time.sleep(1)
        
        # Send a test message
        print('Sending test message...')
        sio.emit('swarm_message', {
            'message': 'Hello from test client!',
            'agent_ids': ['comms', 'coder']
        }, namespace='/swarm')
        
        # Wait for response
        time.sleep(2)
        
        # Disconnect
        print('Disconnecting...')
        sio.disconnect()
        
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    test_websocket()