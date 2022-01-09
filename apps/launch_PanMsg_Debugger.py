# Generic import
import json
import time

#Local utils
from utils.messaging import PanMessaging

msg_client = PanMessaging.create_client("192.168.0.48", 1883, connect=True)

# while True:
#   msg_type, msg_data = msg_client.receive_message()
#   print(json.dumps(msg_data, indent=4, sort_keys=True))
#   time.sleep(1)

def new_sched_callback(msg_type, msg_obj):
  print(f"Type is {msg_type} and obj is {msg_obj}")

msg_client.register_callback(callback=new_sched_callback, cmd_type="POCS-SCHED/#")
while True:
  try:
    time.sleep(1)
  except KeyboardInterrupt as e:
    break


#mosquitto_pub -h 192.168.0.48 -p 1883 -t remoteobservatory/cmd/POCS-CMD -m "{\"value" -d
#mosquitto_pub -h 192.168.0.48 -p 1883 -t remoteobservatory/cmd/POCS-CMD -m "{\"value\": 3.2}" -d
#mosquitto_pub -h 192.168.0.48 -p 1883 -t remoteobservatory/cmd/POCS-SCHED/GOTO -m "{\"value\": 3.2}" -d
