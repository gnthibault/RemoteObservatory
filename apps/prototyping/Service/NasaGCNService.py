# Basic stuff
import os
import time

# Local stuff : Service
from Service.NasaGCNService import NasaGCNService

if __name__ == '__main__':

    # nasa broker
    s = NasaGCNService(config=dict(
        module="NasaGCNService",
        delay_sec=5,
        client_info=dict(
            client_id=os.getenv("NASA_GCN_CLIENT_ID"),
            client_secret=os.getenv("NASA_GCN_CLIENT_SECRET")),
        messaging_publisher=dict(
            module="PanMessagingMQTT",
            mqtt_host="localhost",
            mqtt_port="1883",
            com_mode="publisher")
        ),
        loop_on_create=False,
    )
    s.start()

    for i in range(5*60):
        time.sleep(1)