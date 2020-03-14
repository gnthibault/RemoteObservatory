# Generic import
import json
import time

#Local utils
from utils.messaging import PanMessaging

msg_subscriber = PanMessaging.create_subscriber(6511)


while True:
  msg = msg_subscriber.receive_message()
  print(json.dumps(msg, indent=4, sort_keys=True))
  time.sleep(1)

