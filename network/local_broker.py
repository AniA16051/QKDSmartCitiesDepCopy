import asyncio

try:
    from amqtt.broker import Broker
    _AMQTT_AVAILABLE = True
except ImportError:
    _AMQTT_AVAILABLE = False

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
    if not _AMQTT_AVAILABLE:
        print("amqtt is not installed. For local development, please use Mosquitto (e.g. 'docker compose up mosquitto') or a cloud broker like broker.emqx.io.")
        return
    broker = Broker(config)
    await broker.start()
    print("Broker running on localhost:1883 (TCP)...")
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(start_broker())
