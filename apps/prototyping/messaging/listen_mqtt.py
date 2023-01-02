from utils.config import load_config
from utils import load_module
import time

config = load_config("config")
subscriber_name = config["paws_subscriber"]['module']
subscriber_module = load_module('Service.' + subscriber_name)
msg_subscriber = getattr(subscriber_module, subscriber_name)(
    config=config["paws_subscriber"])

def on_data(data):
    print(f"Received: {data}")
    msg = data[0].decode('UTF-8')
msg_subscriber.register_callback(callback=on_data)
while True:
    time.sleep(60)
