# General stuff
from bson import ObjectId
import datetime
import json
import logging
import random
import yaml

# Astropy
from astropy import units as u
from astropy.time import Time

# MQTT
import paho.mqtt.client as mqttclient
import paho.mqtt.subscribe as mqttsubscribe

# Local
from Service.NTPTimeService import HostTimeService
from Service.PanMessaging import PanMessaging

class PanMessagingMQTT(PanMessaging):

    """Messaging class for PANOPTES project. Creates a new MQTT
    context that can be shared across parent application.
    """
    logger = logging.getLogger('PanMessaging')

    def __init__(self, **kwargs):
        super().__init__(kwargs["config"])

        # Create helper objects
        self.default_topic = "remoteobservatory"
        self.default_cmd_topic = "remoteobservatory/cmd"
        self.client = None
        self.broker = None
        self.client_id = None
        self.mqtt_host = kwargs["config"]["mqtt_host"]
        self.mqtt_port = kwargs["config"]["mqtt_port"]
        self.create_client(connect=True)

    def create_client(self, connect=True):
        """ Create a publisher

        Args:
            connect (bool): Wether to immediatly connect to broker or not

        """
        self.logger.debug(f"Creating client")
        self.broker = {"host": self.mqtt_host, "port": self.mqtt_port}
        self.client_id = hex(random.getrandbits(128))[2:-1]
        client = mqttclient.Client(self.client_id)

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        def on_connect(client, userdata, flags, rc):
          self.logger.debug(f"MQTT Connected with result code {rc} on {self.mqtt_host}:{self.mqtt_port}")
          client.subscribe(f"{self.default_cmd_topic}/#")
        client.on_connect = on_connect
        if connect:
            client.connect(**self.broker)
            client.loop_start()
            #assert client.is_connected(), "Client cannot connect"
        self.client = client

    def send_message(self, channel, message):
        """ Responsible for actually sending message across a channel
        Args:
            channel(str):   Name of channel to send on.
            message(str):   Message to be sent.
        """
        assert channel > '', "Cannot send blank channel"
        assert self.client.is_connected(), "Client should be connected before sending a message"

        if isinstance(message, str):
            current_time = self.serv_time.get_utc()
            message = {
                'message': message,
                'timestamp': current_time.isoformat().replace('T', ' ').split('.')[0]}
        else:
            message = self.scrub_message(message)

        msg_object = json.dumps(message, skipkeys=True)
        self.logger.debug(f"PanMessaging - sending - {channel}: {message}")

        # Send the message
        self.client.publish(
            topic=f"{self.default_topic}/{channel}",
            payload=msg_object, qos=0, retain=False)

    def register_callback(self, callback, cmd_type=None):
        """
        Callback should have a form like:
        callback(msg_type, msg_obj)
        but mqtt callback looks like
        def on_message(client, userdata, message):
            print("received message =",str(message.payload.decode("utf-8")))
        :return:
        """
        assert self.client.is_connected(), "Client should be connected before starting loop"
        def on_message_callback(client, userdata, message):
            msg_type, msg_data = self.parse_msg(message)
            callback(msg_type, msg_data)
        self.client.loop_stop()
        if cmd_type is None:
            self.client.on_message(on_message_callback)
        else:
            self.client.message_callback_add(
                f"{self.default_cmd_topic}/{cmd_type}", on_message_callback)
        self.client.loop_start()

    def receive_message(self, blocking=True):
        """Receive a message

        Receives a message for the current subscriber. Blocks by default

        Args:
            blocking (bool, optional): expected behaviour

        Returns:
            tuple(str, dict): Tuple containing the channel and a dict
        """
        assert self.client.is_connected(), "Client should be connected before receiving a message"
        topic = f"{self.default_cmd_topic}/#"
        try:
            msg = mqttsubscribe.simple(
                topics=topic, qos=0, msg_count=1, retained=False,
                hostname=self.broker["host"], port=self.broker["port"], client_id=self.client_id)
            msg_type, msg_data = self.parse_msg(msg)
        except Exception as e:
            self.logger.error(f"MQTT error while handling cmd message: {e}")
        return msg_type, msg_data

    def parse_msg(self, msg):
        msg_type, msg_payload = msg.topic.split(f"{self.default_cmd_topic}/")[1], msg.payload
        try:
            msg_data = json.loads(msg_payload)
        except json.decoder.JSONDecodeError as e:
            msg_data = yaml.safe_load(msg_payload)
        except Exception as e:
            print(f"MQTT error while handling cmd message: {e}")
        return msg_type, msg_data

    def close_connection(self):
        """Close the client connection """
        self.client.loop_stop()
        self.client.disconnect()