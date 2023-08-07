# General stuff
from bson import ObjectId
import datetime
import json
import logging
import multiprocessing
import random
import yaml

# Astropy
from astropy import units as u
from astropy.time import Time

# ZMQ
import zmq
from zmq.eventloop.zmqstream import ZMQStream

# Local
from Service.NTPTimeService import HostTimeService
from Service.PanMessaging import PanMessaging

class PanMessagingZMQ(PanMessaging):

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

    def __init__(self, config={}, **kwargs):
        super().__init__(**kwargs)
        self.serv_time = HostTimeService()
        # Create a new context
        self.context = zmq.Context()
        self.socket = None
        self.stream = None
        if config.get("com_mode", None) == "subscriber":
            self.create_subscriber(config["cmd_port"])
        elif config.get("com_mode", None) == "publisher":
            self.create_publisher(config["msg_port"])
        # else:
        #     msg = f"Messaging expect com_mode subscriber or publisher, {config['com_mode']} is not supported"
        #     self.logger.error(msg)
        #     raise RuntimeError(msg)

    def create_forwarder(self, sub_port, pub_port, ready_fn=None, done_fn=None):
        subscriber, publisher = self.create_forwarder_sockets(sub_port, pub_port)
        self.run_forwarder(subscriber, publisher, ready_fn=ready_fn, done_fn=done_fn)

    def create_forwarder_sockets(self, sub_port, pub_port):
        subscriber = PanMessagingZMQ()
        subscriber.create_subscriber(sub_port, bind=True, connect=False)
        publisher = PanMessagingZMQ()
        publisher.create_publisher(pub_port, bind=True, connect=False, create_forwarder=False)
        return subscriber, publisher

    def run_forwarder(self, subscriber, publisher, ready_fn=None, done_fn=None):
        try:
            if ready_fn:
                ready_fn()
            zmq.device(zmq.FORWARDER, subscriber.socket, publisher.socket)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            publisher.logger.warning(e)
            publisher.logger.warning("bringing down zmq device")
        finally:
            publisher.close()
            subscriber.close()
            if done_fn:
                done_fn()

    def register_callback(self, callback, cmd_type=None):
        if cmd_type is None:
            if self.stream is None:
                self.stream = ZMQStream(self.socket)
            self.stream.on_recv(callback)
        else:
            raise NotImplementedError

    def create_publisher(self, port, bind=False, connect=True, create_forwarder=True):
        """ Create a publisher

        Args:
            port (int): The port (on localhost) to bind to.

        Returns:
            A ZMQ PUB socket
        """
        self.logger.debug(f"Creating publisher. Binding to port {port}")
        socket = self.context.socket(zmq.PUB)
        if bind:
            socket.bind(f"tcp://*:{port}")
        elif connect:
            socket.connect(f"tcp://localhost:{port}")
        self.socket = socket

        if create_forwarder:
            def create_forwarder(fw_port):
                try:
                    self.create_forwarder(fw_port, fw_port+1)
                # The idea is to ignore the "Address already in use" error on bind
                # but there is no specific error class for this error in zmq
                except zmq.error.ZMQError as e:
                    pass
            msg_forwarder_process = multiprocessing.Process(
                target=create_forwarder, args=(
                    port,), name='MsgForwarder')
            msg_forwarder_process.start()


        return self

    def create_subscriber(self, port, channel='', bind=False, connect=True):
        """ Create a listener
        Args:
            port (int):         The port (on localhost) to bind to.
            channel (str):      Which topic channel to subscribe to.
        """
        self.logger.debug(f"Creating subscriber. Port: {port} \tChannel: {channel}")
        socket = self.context.socket(zmq.SUB)
        if bind:
            try:
                socket.bind(f"tcp://*:{port}")
            except zmq.error.ZMQError:
                self.logger.debug(f"Problem binding port {port}")
        elif connect:
            socket.connect(f"tcp://localhost:{port}")
        socket.setsockopt_string(zmq.SUBSCRIBE, channel)
        self.socket = socket

    def send_message(self, channel, message):
        """ Responsible for actually sending message across a channel

        Args:
            channel(str):   Name of channel to send on.
            message(str):   Message to be sent.

        """
        assert channel > '', self.logger.warning("Cannot send blank channel")
        if isinstance(message, str):
            current_time = self.serv_time.get_utc()
            message = {
                'message': message,
                'timestamp': current_time.isoformat().replace(
                    'T',
                    ' ').split('.')[0]}
        else:
            message = self.scrub_message(message)

        msg_object = json.dumps(message, skipkeys=True)
        full_message = f"{channel} {msg_object}"
        # self.logger.debug(f"PanMessaging - sending - {channel}: {message}")
        # Send the message
        self.socket.send_string(full_message, flags=zmq.NOBLOCK)

    def receive_message(self, blocking=True):
        """Receive a message

        Receives a message for the current subscriber. Blocks by default, pass
        `flags=zmq.NOBLOCK` for non-blocking.

        Args:
            blocking (bool, optional): expected behaviour

        Returns:
            tuple(str, dict): Tuple containing the channel and a dict
        """
        msg_type = None
        msg_obj = None
        flags = 0
        if not blocking:
            flags = flags | zmq.NOBLOCK
        try:
            message = self.socket.recv_string(flags=flags)
        except Exception as e:
            pass
        else:
            msg_type, msg = message.split(' ', maxsplit=1)
            try:
                msg_obj = json.loads(msg)
            except Exception:
                msg_obj = yaml.safe_load(msg)
        return msg_type, msg_obj

    def close(self):
        """Close the socket """
        self.socket.close()
        self.context.term()
