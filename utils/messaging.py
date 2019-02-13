# General stuff
import datetime
import logging
import zmq
import yaml

from astropy import units as u
from astropy.time import Time
from bson import ObjectId
from json import dumps
from json import loads

#from pocs.utils import current_time
from Service.NTPTimeService import NTPTimeService


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
    #TODO TN URGENT
    #logger = logging.getLogger(self.__class__.__name__)

    def __init__(self, **kwargs):
        # Create a new context
        self.context = zmq.Context()
        self.socket = None
        self.serv_time = NTPTimeService()

    @classmethod
    def create_forwarder(cls, sub_port, pub_port, ready_fn=None, done_fn=None):
        subscriber, publisher = PanMessaging.create_forwarder_sockets(sub_port, pub_port)
        PanMessaging.run_forwarder(subscriber, publisher, ready_fn=ready_fn, done_fn=done_fn)

    @classmethod
    def create_forwarder_sockets(cls, sub_port, pub_port):
        subscriber = PanMessaging.create_subscriber(sub_port, bind=True, connect=False)
        publisher = PanMessaging.create_publisher(pub_port, bind=True, connect=False)
        return subscriber, publisher

    @classmethod
    def run_forwarder(cls, subscriber, publisher, ready_fn=None, done_fn=None):
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

    @classmethod
    def create_publisher(cls, port, bind=False, connect=True):
        """ Create a publisher

        Args:
            port (int): The port (on localhost) to bind to.

        Returns:
            A ZMQ PUB socket
        """
        obj = cls()
        obj.logger.debug("Creating publisher. Binding to port {} ".format(port))

        socket = obj.context.socket(zmq.PUB)

        if bind:
            socket.bind('tcp://*:{}'.format(port))
        elif connect:
            socket.connect('tcp://localhost:{}'.format(port))

        obj.socket = socket

        return obj

    @classmethod
    def create_subscriber(cls, port, channel='', bind=False, connect=True):
        """ Create a listener

        Args:
            port (int):         The port (on localhost) to bind to.
            channel (str):      Which topic channel to subscribe to.

        """
        obj = cls()
        obj.logger.debug("Creating subscriber. Port: {} \tChannel: {}".format(
            port, channel))

        socket = obj.context.socket(zmq.SUB)

        if bind:
            try:
                socket.bind('tcp://*:{}'.format(port))
            except zmq.error.ZMQError:
                obj.logger.debug('Problem binding port {}'.format(port))
        elif connect:
            socket.connect('tcp://localhost:{}'.format(port))

        socket.setsockopt_string(zmq.SUBSCRIBE, channel)

        obj.socket = socket

        return obj

    def send_message(self, channel, message):
        """ Responsible for actually sending message across a channel

        Args:
            channel(str):   Name of channel to send on.
            message(str):   Message to be sent.

        """
        assert channel > '', self.logger.warning("Cannot send blank channel")

        if isinstance(message, str):
            current_time = self.serv_time.getUTCFromNTP()
            message = {
                'message': message,
                'timestamp': current_time.isoformat().replace(
                    'T',
                    ' ').split('.')[0]}
        else:
            message = self.scrub_message(message)

        msg_object = dumps(message, skipkeys=True)

        full_message = '{} {}'.format(channel, msg_object)

        if channel == 'PANCHAT':
            self.logger.info("{} {}".format(channel, message['message']))

        # Send the message
        self.socket.send_string(full_message, flags=zmq.NOBLOCK)

    def receive_message(self, blocking=True, flags=0):
        """Receive a message

        Receives a message for the current subscriber. Blocks by default, pass
        `flags=zmq.NOBLOCK` for non-blocking.

        Args:
            flag (int, optional): Any valid recv flag, e.g. zmq.NOBLOCK

        Returns:
            tuple(str, dict): Tuple containing the channel and a dict
        """
        msg_type = None
        msg_obj = None
        if not blocking:
            flags = flags | zmq.NOBLOCK
        try:
            message = self.socket.recv_string(flags=flags)
        except Exception as e:
            pass
        else:
            msg_type, msg = message.split(' ', maxsplit=1)
            try:
                msg_obj = loads(msg)
            except Exception:
                msg_obj = yaml.load(msg)

        return msg_type, msg_obj

    def close(self):
        """Close the socket """
        self.socket.close()
        self.context.term()

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
