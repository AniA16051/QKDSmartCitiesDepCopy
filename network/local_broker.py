import asyncio
from amqtt.broker import Broker

config = {
    'listeners': {
        'default': {
            'type': 'tcp',
            'bind': '127.0.0.1:1883',
            'max_connections': 100
        }
    },
    'auth': {
        'allow-anonymous': True,
        'plugins': ['auth_anonymous']
    }
}

async def start_broker():
    broker = Broker(config)
    await broker.start()
    print("Broker running on localhost:1883 (TCP)...")
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(start_broker())
