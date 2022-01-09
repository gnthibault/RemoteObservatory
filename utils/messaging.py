# General stuff
import datetime
import logging
import paho.mqtt.client as mqttclient
import paho.mqtt.subscribe as mqttsubscribe
import random
import yaml

from astropy import units as u
from astropy.time import Time
from bson import ObjectId
import json

#from pocs.utils import current_time
from Service.NTPTimeService import HostTimeService

class PanMessaging(object):

    """Messaging class for PANOPTES project. Creates a new ZMQ
    context that can be shared across parent application.

    Bind vs Connect, extract of 0MZ doc:

    **Why do I see different behavior when I bind a socket versus connect a socket?

    ZeroMQ creates queues per underlying connection, e.g. if your socket is
    connected to 3 peer sockets there are 3 messages queues.
    With bind, you allow peers to connect to you, thus you don't know how many
    peers there will be in the future and you cannot create the queues in advance.
    Instead, queues are created as individual peers connect to the bound socket.

    With connect, ZeroMQ knows that there's going to be at least a single peer
    and thus it can create a single queue immediately. This applies to all
    socket types except ROUTER, where queues are only created after the peer
    we connect to has acknowledge our connection.

    Consequently, when sending a message to bound socket with no peers, or a
    ROUTER with no live connections, there's no queue to store the message to.

    **When should I use bind and when connect?

    As a very general advice: use bind on the most stable points in your
    architecture and connect from the more volatile endpoints. For
    request/reply the service provider might be point where you bind and the
    client uses connect. Like plain old TCP.

    If you can't figure out which parts are more stable (i.e. peer-to-peer)
    think about a stable device in the middle, where boths sides can connect to.

    The question of bind or connect is often overemphasized. It's really just
    a matter of what the endpoints do and if they live long — or not. And this
    depends on your architecture. So build your architecture to fit your
    problem, not to fit the tool.

    """
    logger = logging.getLogger('PanMessaging')

    def __init__(self, **kwargs):
        # Create helper objects
        self.default_topic = "remoteobservatory"
        self.default_cmd_topic = "remoteobservatory/cmd"
        self.client = None
        self.broker = None
        self.client_id = None
        self.serv_time = HostTimeService()

    @classmethod
    def create_client(cls, mqtt_host, mqtt_port, connect=True):
        """ Create a publisher

        Args:
            port (int): The port (to bind to)

        """
        obj = cls()
        obj.logger.debug(f"Creating client")
        obj.broker = {"host": mqtt_host, "port": mqtt_port}
        obj.client_id = hex(random.getrandbits(128))[2:-1]
        client = mqttclient.Client(obj.client_id)

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        def on_connect(client, userdata, flags, rc):
          #print(f"MQTT Connected with result code {str(rc)}")
          client.subscribe(f"{obj.default_cmd_topic}/#")
        client.on_connect = on_connect
        if connect:
            client.connect(**obj.broker)
            client.loop_start()
            #assert client.is_connected(), "Client cannot connect"
        obj.client = client
        return obj

    def send_message(self, channel, message):
        """ Responsible for actually sending message across a channel

        Args:
            channel(str):   Name of channel to send on.
            message(str):   Message to be sent.

        """
        assert channel > '', "Cannot send blank channel"
        #assert self.client.is_connected(), "Client should be connected before sending a message"

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
        #assert self.client.is_connected(), "Client should be connected before starting loop"
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

    def receive_message(self):
        """Receive a message

        Receives a message for the current subscriber. Blocks by default

        Args:
            blocking (bool, optional): expected behaviour

        Returns:
            tuple(str, dict): Tuple containing the channel and a dict
        """
        #assert self.client.is_connected(), "Client should be connected before receiving a message"
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

    def scrub_message(self, message):

        for k, v in message.items():
            if isinstance(v, dict):
                v = self.scrub_message(v)

            if isinstance(v, u.Quantity):
                v = v.value

            if isinstance(v, datetime.datetime):
                v = v.isoformat()

            if isinstance(v, ObjectId):
                v = str(v)

            if isinstance(v, Time):
                v = str(v.isot).split('.')[0].replace('T', ' ')

            # Hmmmm
            if k.endswith('_time'):
                v = str(v).split(' ')[-1]

            if isinstance(v, float):
                v = round(v, 3)

            message[k] = v

        return message
