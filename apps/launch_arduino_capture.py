# This script is used by peas_shell to record the readings from an
# Arduino, and to send commands to the Arduino (e.g. to open and
# close relays).

# Generic stuff
import argparse
import logging
import serial
import sys

# Local stuff
from Base.Base import Base
from helper import ArduinoIO
from utils.config import load_config
from utils.database import DB
from utils.messaging import PanMessaging


def main(board, port, cmd_port, msg_port):
    config = load_config(config_files=['peas'])
    serial_config = config.get('environment', {}).get('serial', {})
    logging.basicConfig(format='%(levelname)s:%(message)s')
    logger = logging.getLogger('arduino_capture')
    serial_data = ArduinoIO.open_serial_device(
        port, serial_config=serial_config, name=board)
    sub = PanMessaging.create_subscriber(cmd_port)
    pub = PanMessaging.create_publisher(msg_port, bind=True)
    aio = ArduinoIO.ArduinoIO(board, serial_data, pub, sub)
    aio.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Record sensor data from an Arduino and send it relay commands.')
    parser.add_argument(
        '--board', help="Name of the board attached to the port."
             " default 'scope_controller'", default='scope_controller')
    parser.add_argument('--port', help='Port (device path) to connect to.',
                        default='/dev/ttyACM0')
    parser.add_argument(
        '--cmd-sub-port',
        dest='cmd_port',
        default=6501,
        help='Port (e.g. 6501) on which to listen for commands.')
    parser.add_argument(
        '--msg-pub-port',
        dest='msg_port',
        default=6510,
        help='Port (e.g. 6510) to which to publish readings.')
    args = parser.parse_args()

    def arg_error(msg):
        print(msg, file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if args.board in ('scope_controller'): #additional accepted names ?
        board = 'scope_controller'
    else:
        arg_error("--board must be 'scope_controller'")

    if args.port:
        port = args.port
    else:
        arg_error('Must specify exactly one of --port')

    if not args.cmd_port or not args.msg_port:
        arg_error('Must specify both --cmd-port and --msg-port')

    print('args: {!r}'.format(args))
    print('board:', board)
    print('port:', port)
    # sys.exit(1)

    # To provide distinct log file names for each board, change argv
    # so that the board name is used as the invocation name.
    sys.argv[0] = board

    main(board, port, args.cmd_port, args.msg_port)

#launch with PYTHONPATH=. python3 ./apps/launch_arduino_capture.py --board scope_controller
