# General stuff
import datetime
import json
import logging
import random
import ssl
import yaml

# Astropy
from astropy import units as u
from astropy.time import Time

# MQTT
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as mqttsubscribe
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

# Local
from Service.NTPTimeService import HostTimeService
from Service.PanMessaging import PanMessaging

class PanMessagingMQTT(PanMessaging):

    """Messaging class for PANOPTES project. Creates a new MQTT
    context that can be shared across parent application.

    Example to start the command line subscriber:
    mosquitto_sub -v -t 'test/topic'
    Publish test message with the command line publisher:
    mosquitto_pub -t 'test/topic' -m 'helloWorld'
    """
    logger = logging.getLogger('PanMessaging')

    def __init__(self, config={}, **kwargs):
        super().__init__(**kwargs)

        # Create helper objects
        self.default_topic = "observatory"
        #self.default_cmd_topic = "observatory/cmd"
        self.client = None
        self.broker = None
        self.client_id = None
        self.mqtt_host = config["mqtt_host"]
        self.mqtt_port = config["mqtt_port"]
        if config.get("com_mode", None) == "subscriber":
            self.create_client(connect=True, is_subscriber=True)
        elif config.get("com_mode", None) == "publisher":
            self.create_client(connect=True, is_subscriber=False)

    def default_on_connect_callback(self, client, userdata, flags, reason_codes, properties):
        self.logger.debug(f"MQTT Connected with result code {reason_codes} on {self.mqtt_host}:{self.mqtt_port}")

    def subscriber_on_connect_callback(self, client, userdata, flags, reason_codes, properties):
        self.default_on_connect_callback(client=client, userdata=userdata, flags=flags, reason_codes=reason_codes,
                                         properties=properties)
        client.subscribe(f"{self.default_topic}/#")

    def publisher_on_connect_callback(self, client, userdata, flags, reason_codes, properties):
        self.default_on_connect_callback(client=client, userdata=userdata, flags=flags, reason_codes=reason_codes,
                                         properties=properties)

    def create_client(self, connect=True, is_subscriber=False, version="5", transport="tcp"):
        """ Create a publisher

        Args:
            connect (bool) : Wether to immediatly connect to broker or not
            version (str)  : '5'  or '3'
            transport (str): 'websockets'  or 'tcp'

            Main doc f paho mqtt is there: https://pypi.org/project/paho-mqtt/

            MQTT v5 specs    : https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html
            MQTT v3.1.1 specs: http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html

            Websocket uses the HTTP protocol and has the following benefits: it is firewall-friendly, and one can
            utilize it with almost any internet connection. The TCP protocol performs better because the communication
            uses a lower layer – the TCP layer.
            
            Regarding callbacks, here is what you can define:
            on_connect
                If implemented, called when the broker responds to our connection request.
            on_connect_fail
                If implemented, called when the client failed to connect to the broker.
            on_disconnect
                If implemented, called when the client disconnects from the broker.
            on_log
                If implemented, called when the client has log information. Defined to allow debugging.
            on_message
                If implemented, called when a message has been received on a topic that the client subscribes to.
                This callback will be called for every message received. Use message_callback_add() to define multiple
                callbacks that will be called for specific topic filters.
            on_publish
                If implemented, called when a message that was to be sent using the publish() call has completed
                transmission to the broker. For messages with QoS levels 1 and 2, this means that the appropriate
                handshakes have completed. For QoS 0, this simply means that the message has left the client.
                This callback is important because even if the publish() call returns success, it does not always
                mean that the message has been sent.
            on_socket_close
                If implemented, called just before the socket is closed.
            on_socket_open
                If implemented, called just after the socket was opend.
            on_socket_register_write
                If implemented, called when the socket needs writing but can't.
            on_socket_unregister_write
                If implemented, called when the socket doesn't need writing anymore.
            on_subscribe
                If implemented, called when the broker responds to a subscribe
                request.
            on_unsubscribe
                If implemented, called when the broker responds to an unsubscribe request.
        """
        self.logger.debug(f"Creating client")
        self.broker = {"host": self.mqtt_host, "port": int(self.mqtt_port)}
        self.client_id = hex(random.getrandbits(128))[2:-1]

        if version == '5':
            client = mqtt.Client(client_id=self.client_id,
                                 transport=transport,
                                 protocol=mqtt.MQTTv5)
        if version == '3':
            client = mqtt.Client(client_id=self.client_id,
                                 transport=transport,
                                 protocol=mqtt.MQTTv311,
                                 clean_session=True)

        # You can customize the following callbacks:
        # client.on_message
        # client.on_connect
        # client.on_publish
        # client.on_subscribe
        if is_subscriber:
            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
            client.on_connect = self.subscriber_on_connect_callback
        else:
            client.on_connect = self.publisher_on_connect_callback

        if connect:
            if version == '5':
                properties = Properties(PacketTypes.CONNECT)
                properties.SessionExpiryInterval = 30 * 60  # in seconds
                client.connect(host=self.broker["host"],
                               port=self.broker["port"],
                               clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY,
                               properties=properties,
                               keepalive=60)
            if version == '3':
                client.connect(host=self.broker["host"],
                               port=self.broker["port"],
                               keepalive=60);
            client.connect(**self.broker)
            client.loop_start()
        self.client = client

    def send_message(self, channel, message):
        """ Responsible for actually sending message across a channel
        Args:
            channel(str):   Name of channel to send on.
            message(str):   Message to be sent.
        """
        assert channel > '', "Cannot send blank channel"

        if isinstance(message, str):
            current_time = self.serv_time.get_utc()
            message = {
                'message': message,
                'timestamp': current_time.isoformat().replace('T', ' ').split('.')[0]}
        else:
            message = self.scrub_message(message)

        msg_object = json.dumps(message, skipkeys=True)
        # self.logger.debug(f"PanMessaging - sending - {channel}: {message}")

        # Send the message
        self.client.publish(
            topic=f"{self.default_topic}/{channel}",
            payload=msg_object, qos=0, retain=False)

    def register_callback(self, callback, cmd_type="#", do_parsing=False):
        """
        Callback should have a form like:
        callback(msg_type, msg_obj)
        but mqtt callback looks like
        def on_message(client, userdata, message):
            print("received message =",str(message.payload.decode("utf-8")))
        :return:
        """
        def on_message_callback(client, userdata, message):
            self.logger.debug(f"Received message {message.payload} on topic {message.topic} with QoS {message.qos}")
            if do_parsing:
                msg_type, msg_data = self.parse_msg(message)
                callback(msg_type, msg_data)
            # TODO TN for ugly compatibility with old PAWS, to be removed in the future
            else:
                msg_type, msg_data = self.split_msg(message)
                callback([msg_type.encode()+b" "+msg_data])
        self.client.loop_stop()
        self.client.message_callback_add(f"{self.default_topic}/{cmd_type}", on_message_callback)
        self.client.loop_start()

    def receive_message(self, blocking=True):
        """Receive a message

        Receives a message for the current subscriber. Blocks by default

        Args:
            blocking (bool, optional): expected behaviour

        Returns:
            tuple(str, dict): Tuple containing the channel and a dict
        """
        topic = f"{self.default_topic}/#"
        try:
            msg = mqttsubscribe.simple(
                topics=topic, qos=0, msg_count=1, retained=False,
                hostname=self.broker["host"], port=self.broker["port"], client_id=self.client_id)
            msg_type, msg_data = self.parse_msg(msg)
        except Exception as e:
            self.logger.error(f"MQTT error while handling cmd message: {e}")
        return msg_type, msg_data

    def split_msg(self, msg):
        msg_type, msg_payload = msg.topic.split(f"{self.default_topic}/")[1], msg.payload
        return msg_type, msg_payload

    def parse_msg(self, msg):
        msg_type, msg_payload = self.split_msg(msg)
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