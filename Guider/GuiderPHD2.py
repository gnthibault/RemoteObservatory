#Standard stuff
import json
import os 
import time
from transitions import Machine
import socket
import sys

#Astropy
import astropy.units as u

#local libs
from Base.Base import Base
from utils import Timeout
from utils import error
from utils.error import GuidingError

MAXIMUM_CALIBRATION_TIMEOUT = 4 * 60 * u.second
MAXIMUM_DITHER_TIMEOUT = 45 * u.second
STANDARD_TIMEOUT = 30 * u.second

class GuiderPHD2(Base):
    """
        From: https://github.com/OpenPHDGuiding/phd2/wiki/EventMonitoring:

        Attribute Type     Description
        Event     string   the name of the event
        Timestamp number   the timesamp of the event in seconds from the epoch,
                           including fractional seconds
        Host      string   the hostname of the machine running PHD
        Inst      number   the PHD instance number (1-based)
        
        List of states, according to openPHD2 documentation:
        State         Description
        Stopped       PHD is idle
        StarSelected  A star is selected but PHD is neither looping exposures,
                      calibrating, or guiding
        Calibrating   PHD is calibrating
        Guiding       PHD is guiding, but can still be shaky (while stabilizing)
        SteadyGuiding PHD is guiding, and settle conditions are met
        LostLock      PHD is guiding, but the frame was dropped
        Paused        PHD is paused
        Looping       PHD is looping exposures
    """
    states = ['NotConnected', 'Connected', 'Guiding', 'Settling',
              'SteadyGuiding', 'Paused', 'Calibrating',
              'StarSelected', 'LostLock', 'Looping', 'Stopped']
    transitions = [
        { 'trigger': 'connection_trig', 'source': '*', 'dest': 'Connected' },
        { 'trigger': 'disconnection_trig', 'source': '*', 'dest': 'NotConnected' },
        { 'trigger': 'GuideStep', 'source': 'SteadyGuiding', 'dest': 'SteadyGuiding' },
        # from https://github.com/pytransitions/transitions#transitioning-from-multiple-states:
        # Note that only the first matching transition will execute
        { 'trigger': 'GuideStep', 'source': '*', 'dest': 'Guiding' },
        { 'trigger': 'Paused', 'source': '*', 'dest': 'Paused' },
        { 'trigger': 'StartCalibration', 'source': '*', 'dest': 'Calibrating' },
        { 'trigger': 'LoopingExposures', 'source': '*', 'dest': 'Looping' },
        { 'trigger': 'LoopingExposureStopped', 'source': '*', 'dest': 'Stopped' },
        { 'trigger': 'SettleBegin', 'source': '*', 'dest': 'Settling' },
        { 'trigger': 'SettleDone', 'source': '*', 'dest': 'SteadyGuiding'},
        { 'trigger': 'StarLost', 'source': '*', 'dest': 'LostLock' },
        { 'trigger': 'StarSelected', 'source': '*', 'dest': 'StarSelected' },
        { 'trigger': 'ConnectionLost', 'source': '*', 'dest': 'NotConnected' }
        ]

    def __init__(self, config=None):
        super().__init__()
        if config is None:
            config = dict(
                host = "localhost",
                port = 4400,
                profile_id = '2',
                exposure_time_sec = '3',
                settle = {
                    "pixels": 1.5,
                    "time": 10,
                    "timeout": 60}
          )

        self.host = config["host"]
        self.port = config["port"]
        self.session = None
        self.sock = None
        self.recv_buffer = ''
        self.id = 1                            # message id
        self.profile_id = config["profile_id"] # profile id for equipment
        self.mount = None
        self.settle = config["settle"]
        self.exposure_time_sec = config['exposure_time_sec']

        # Initialize the state machine
        self.machine = Machine(model=self,
                               states=GuiderPHD2.states,
                               transitions=GuiderPHD2.transitions,
                               initial=GuiderPHD2.states[0])

    def launch_server(self):
        """
        Usage: phd2 [-i <num>] [-R]
          -i, --instanceNumber=<num>  sets the PHD2 instance number (default=1)
          -R, --Reset                 Reset all PHD2 settings to default values
        """
        cmd = 'phd2' 
        os.popen(cmd)
        time.sleep(10) #Did not found anything better than that...

    def terminate_server(self):
        self.shutdown()

    def connect(self):
        self.logger.info("Connect to server PHD2 {}:{}".format(self.host,
                         self.port))
        # Create a socket (SOCK_STREAM means a TCP socket)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(1.0)

        try:
            # Connect to server and send data
            #self.session = requests.sessions.Session()
            self.sock.connect((self.host, self.port))
            self._receive({"Event":"Version"})
            self.connection_trig()
            self._receive({"Event":"AppState"}) # get state
            # we make sure that we are starting from a "proper" state
            self.reset_profile(self.profile_id)
            self.reset_guiding()
        except Exception as e:
            msg = "PHD2 error connecting: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def disconnect_and_terminate_server(self):
        self.logger.info("Closing connection to server PHD2 {}:{}".format(
                         self.host,self.port))
        if self.state != 'NotConnected':
            self.reset_guiding()
            self.terminate_server()
            self.sock.close()
            self.disconnection_trig()

    def reset_profile(self, profile_id):
        self.set_connected(False)
        self.logger.debug("About to set profile with id {} among the following "
                          "list: {}".format(profile_id, self.get_profiles()))
        self.set_profile(profile_id)
        self.set_connected(True)

    def reset_guiding(self):
        """
            throw away calibration, current settle and current star
        """
        self.stop_capture()
        self.clear_calibration()

    def receive(self):
        return self._receive()

    def set_settle(self, pixels, time, timeout):
        """
           Settle parameter:
                    The SETTLE parameter is used by the guide and dither
                    commands to specify when PHD2 should consider guiding to be
                    stable enough for imaging. SETTLE is an object with the
                    following attributes:
                    *pixels - maximum guide distance for guiding to be
                     considered stable or "in-range"
                    *time - minimum time to be in-range before considering
                     guiding to be stable
                    *timeout - time limit before settling is considered to have
                     failed
                    So, for example, to request settling at less than 1.5
                    pixels for at least 10 seconds, with a time limit of 60
                    seconds, the settle object parameter would be:
                    {"pixels": 1.5, "time": 10, "timeout": 60}
        """
        self.settle = dict(pixels=pixels, time=time, timeout=timeout)

    ####    PHD2 rpc API methods ####

    def shutdown(self):
        """
           params: none 
           result: integer(0)
           desc. : Close PHD2
        """
        req={"method": "shutdown",
             "params": [],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to shutdown request: {}"
                                   "".format(data))
        except Exception as e:
            msg = "PHD2 error shutdown: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def set_connected(self, connect=True):
        """
           params: boolean: connect
           result: integer(0)
           desc. : connect or disconnect all equipment
        """
        req={"method": "set_connected",
             "params": [connect],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to set_connected request: {}"
                                   "".format(data))
        except Exception as e:
            msg = "PHD2 error set_connected: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def set_profile(self, profile_id=0):
        """
           params: integer: profile id
           result: integer(0)
           desc. : Select an equipment profile. All equipment must be
                   disconnected before switching profiles.
        """
        params = [int(profile_id)]
        req={"method": "set_profile",
             "params": params,
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to set_profile request: {}"
                                   "".format(data))
        except Exception as e:
            msg = "PHD2 error setting profile: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)


    def capture_single_frame(self, exp_time_sec=None):
        """
           params: exposure: exposure duration milliseconds (optional),
                   subframe: array [x,y,width,height] (optional)
           result: integer(0)
           desc. : captures a singe frame; guiding and looping must be stopped
                   first
        """
        params = []
        if exp_time_sec is not None:
            exp_time_milli = exp_time_sec*1000
            params.append(exp_time_milli)
        req={"method": "capture_single_frame",
             "params": params,
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to capture_single_frame "
                                   "request: {}".format(data))
        except Exception as e:
            msg = "PHD2 error capturing frame: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def clear_calibration(self):
        """
           params: string: "mount" or "ao" or "both"
           result: integer(0)
           desc. : if parameter is omitted, will clear both mount and AO.
                   Clearing calibration causes PHD2 to recalibrate next time
                   guiding starts.
        """
        req={"method": "clear_calibration",
             "params": [
                 "both"],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to clear_calibration request: "
                                   "{}".format(data))
        except Exception as e:
            msg = "PHD2 error clearing calibration: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def dither(self, pixels=3.0, ra_only=False):
        """
           params: PIXELS (float), RA_ONLY (boolean), SETTLE (object)
           result: integer(0)
           desc. : The dither method allows the client to request a random
                   shift of the lock position by +/- PIXELS on each of the RA
                   and Dec axes. If the RA_ONLY parameter is true, or if the
                   Dither RA Only option is set in the Brain, the dither will
                   only be on the RA axis. The PIXELS parameter is multiplied
                   by the Dither Scale value in the Brain.
                   Like the guide method, the dither method takes a SETTLE
                   object parameter. PHD will send Settling and SettleDone
                   events to indicate when guiding has stabilized after the
                   dither.
        """
        params = []
        params.append(pixels)
        params.append(ra_only)
        params.append(self.settle)
        req={"method": "dither",
             "params": params,
             "id":self.id}
        self.id+=1

        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to dither request: {}"
                                   "".format(data))
            timeout = Timeout(MAXIMUM_DITHER_TIMEOUT)
            while self.state != 'SteadyGuiding':
                self._receive(loop_mode=True)
                if timeout.expired():
                    raise error.Timeout("Timeout while waiting for settle "
                                        "after dither was sent to GuiderPHD2")
        except Exception as e:
            msg = "PHD2 error dithering: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)
        
    def find_star(self):
        """
           params: None
           result: on success: returns the lock position of the selected star,
                   otherwise returns an error object
           desc. : Auto-select a star
        """
        req={"method": "find_star",
             "params": [],
             "id":self.id}
        self.id+=1
        self._send_request(req)
        status = self._receive({"id":req["id"]})
        # Should generate an event like this:
        # {'Event': 'LockPositionSet', 'Timestamp': 15.16, 'Host': 'XXXX', 'Inst': 1, 'X': 1040.007, 'Y': 224.034}
        if 'result' in status:
            if not status["result"]:
                msg = "PHD2 find_star failed"
                self.logger.error(msg)
                raise GuidingError(msg)
        else:
            msg = "Cannot find guiding star automatically"
            self.logger.error(msg)
            raise GuidingError(msg)

    def set_dec_guide_mode(self, mode="Auto"):
        """
            params: string: mode ("Off"/"Auto"/"North"/"South") integer(0)
            result: integer(0)
            desc. : 
        """
        req={"method": "set_dec_guide_mode",
             "params": [mode],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to set_dec_guide_mode request:"
                                   " {}".format(data))
        except Exception as e:
            msg = "PHD2 error setting dec guide mode: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def set_lock_position(self, pos_x, pos_y):
        """
            params: X: float, Y: float,
                    EXACT: boolean (optional, default = true)
            result: integer(0)
            desc. : When EXACT is true, the lock position is moved to the exact
                    given coordinates. When false, the current position is moved
                    to the given coordinates and if a guide star is in range,
                    the lock position is set to the coordinates of the guide
                    star.
        """
        params = [{}]
        params[0]["X"] = pos_x
        params[0]["Y"] = pos_y
        params[0]["EXACT"] = False
        req={"method": "set_lock_position",
             "params": params,
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to set_lock_position request: "
                                   "{}".format(data))
        except Exception as e:
            msg = "PHD2 error setting lock position: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def set_exposure(self, exp_time_sec):
        """
            params: integer: exposure time in milliseconds
            result: integer(0)
            desc. : 
        """
        exp_time_milli = exp_time_sec*1000
        req={"method": "set_exposure",
             "params": [exp_time_milli],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to set_exposure request: {}"
                                   "".format(data))
        except Exception as e:
            msg = "PHD2 error setting exposure: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def loop(self):
        """
            params: none
            result: integer (0) 
            desc. : start capturing, or, if guiding, stop guiding but continue
                    capturing
        """
        req={"method": "loop",
             "params": [],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to loop request: {}"
                                   "".format(data))
        except Exception as e:
            msg = "PHD2 error looping: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def stop_capture(self):
        """
            params: none
            result: integer (0) 
            desc. : 
        """
        req={"method": "stop_capture",
             "params": [],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to stop_capture request: {}"
                                   "".format(data))
            timeout = Timeout(STANDARD_TIMEOUT)
            while self.state not in ['Stopped', 'GuidingStopped']:
                data = self._receive(loop_mode=True)
                if timeout.expired():
                    raise error.Timeout("Timeout while waiting for response "
                        "after stop_capture was sent to GuiderPHD2")
        except Exception as e:
            msg = "PHD2 error stopping capture: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def guide(self, recalibrate=True):
        """
            params: SETTLE (object), RECALIBRATE (boolean)
            result: integer (0)
            desc. : The guide method allows a client to request PHD2 to do
                    whatever it needs to start guiding and to report when
                    guiding is settled and stable.
                    When the guide method command is received, PHD2 will
                    respond immediately indicating that the guide sequence has
                    started. The guide method will return an error status if
                    equipment is not connected. PHD will then:
                    *start capturing if necessary
                    *auto-select a guide star if one is not already selected
                    *calibrate if necessary, or if the RECALIBRATE parameter is
                     true
                    *wait for calibration to complete
                    *start guiding if necessary
                    *wait for settle (or timeout)
                    *report progress of settling for each exposure (send
                     Settling events)
                    *report success or failure by sending a SettleDone event.
                    If the guide command is accepted, PHD is guaranteed to send
                    a SettleDone event some time later indicating the success
                    or failure of the guide sequence.
        """
        req={"method": "guide",
             "params": [self.settle,recalibrate],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError("Wrong answer to guide request: {}"
                                   "".format(data))

            timeout = Timeout(MAXIMUM_CALIBRATION_TIMEOUT)
            while self.state != 'SteadyGuiding':
                self._receive(loop_mode=True)
                if timeout.expired():
                    raise error.Timeout("Timeout while waiting for settle "
                                        "after guide was sent to GuiderPHD2")
        except Exception as e:
            msg = "PHD2 error guiding: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    #### Getters ####
    def get_app_state(self):
        """
            params: none
            result: string: current app state 
            desc. : same value that came in the last AppState notification
        """
        req={"method": "get_app_state",
             "params": [],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            return data["result"]
        except Exception as e:
            msg = "PHD2 error getting app state: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def get_calibrated(self):
        """
            params: none
            result: boolean: true if calibrated
            desc. : 
        """
        req={"method": "get_calibrated",
             "params": [],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            return data["result"]
        except Exception as e:
            msg = "PHD2 error getting calibration status: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def get_connected(self):
        """
            params: none
            result: boolean: true if all equipment is connected
            desc. : 
        """
        req={"method": "get_connected",
             "params": [],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            return data["result"]
        except Exception as e:
            msg = "PHD2 error getting connection status: {}".format(e)
            self.logger.warning(msg)
            return self.state != 'NotConnected'

    def get_profiles(self):
        """
            params: none  
            result: array of {"id":profile_id,"name":"profile_name"}
            desc. : 
        """
        req={"method": "get_profiles",
             "params": [],
             "id":self.id}
        self.id+=1
        try:
            self._send_request(req)
            data = self._receive({"id":req["id"]})
            return data["result"]
        except Exception as e:
            msg = "PHD2 error getting profiles list: {}".format(e)
            self.logger.warning(msg)
            return ''

    #### Some specific handle code for decoding messages ####

    def _receive(self, expected=None, loop_mode=False, timeout=STANDARD_TIMEOUT):
        timeout = Timeout(timeout)
        ret = None
        while not ret:
            ret = self._receive_from_socket(expected=expected, loop_mode=loop_mode)
            if not ret:
                self.logger.warning("Received {}, still waiting for expected {}".format(ret, expected))
            if timeout.expired():
                raise error.Timeout("Timeout while waiting for reception of "
                                    "response from GuiderPHD2")
        return ret

    def _receive_from_socket(self, expected=None, loop_mode=False):
        """

        :param expected: dictionary of expected keys/values. Those keys/values
                         are tested against each message
        :param loop_mode: wether an answer is expected soon (might timeout if
                          there is a problem) of if it should hand undefinitely
        :return: the first message that complies with expected dictionary
        """
        # Receive data from the server
        stop_receive = False
        while not stop_receive:
            try:
                self.recv_buffer += self.sock.recv(1024).decode()
            except socket.timeout:
                if loop_mode:
                    return
                else:
                    msg = "PHD2 Timeout: No response from server"
                    self.logger.error(msg)
                    raise GuidingError(msg)
            except Exception as e:
                msg = "PHD2 error {}".format(e)
                self.logger.error(msg)
                raise GuidingError(msg)
            # Check if we receive termination symbol
            msgs = self.recv_buffer.split('\r\n')
            if len(msgs) <= 1 :
                # no termination symbol has been received yet, continue
                self.recv_buffer = msgs[0]
            else:
                # termination symbol has been received, now can proceed
                stop_receive = True
        # eventually store beginning of next message in the current buffer
        # this is '' if only a single message has been received
        self.recv_buffer = msgs[-1]
        event = ""
        expected_event = ""
        expected_status = False
        for msg in msgs[:-1]:          
            try:
                event = json.loads(msg)
                self.logger.debug("Received event: {}".format(event))
                valid_status = self._check_event(event, expected)
                expected_status = (expected_status or valid_status)
                self._handle_event(event)
                if valid_status:
                    expected_event = event
            except Exception as e:
                msg = "PHD2 error on message {}:{}".format(msg, e)
                self.logger.error(msg)
                raise GuidingError(msg)
        return expected_event

    def _send_request(self, req):
        base = dict(jsonrpc="2.0")
        base.update(req)
        json_txt = json.dumps(base)+'\r\n'
        self.logger.debug("sending msg {}".format(json_txt[:-2]))
        try:
            self.sock.sendall(json_txt.encode())
        except Exception as e:
            msg = "PHD2 error sending request: {}".format(e)
            self.logger.error(msg)
            raise GuidingError(msg)

    def _check_event(self, event, expected=None):
        status = True
        # No check the expected
        if expected is not None:
            for k, v in expected.items():
                try:
                    status = (status and (event[k] == v))
                except KeyError as e:
                    status = False
        # Also check that there is no error
        if "error" in event:
            msg = "Received error msg: {}".format(event["error"])
            self.logger.error(msg)
        return status

    def _handle_event(self, event):
        if "Event" in event:
            method_name = "_handle_{}".format(event["Event"])
            if hasattr(self, method_name):
                getattr(self, method_name)(event)
            else:
                self.logger.warning("No method called {} to handle event !"
                    "".format(method_name))

    def _handle_Version(self, event):
        """Describes the PHD and message protocol versions.
           Attribute   Type   Description
           PHDVersion  string the PHD version number
           PHDSubver   string the PHD sub-version number
           MsgVersion  number the version number of the event message protocol.
                              The current version is 1. We will bump this
                              number if the message protocol changes
        """
        self.logger.debug("Received version {}:{} - msg ver {}".format(
                          *[event[key] for key in ["PHDVersion","PHDSubver",
                                                   "MsgVersion"]]))

    def _handle_LockPositionSet(self, event):
        """The lock position has been established.
           Attribute Type    Description
           X         number  lock position X-coordinate
           Y         number  lock position Y-coordinate
        """
        self.logger.debug("Lock position X:{} , Y:{} has been established"
                          "".format(event["X"], event["Y"]))
                          
    def _handle_Calibrating(self, event):
        """ Attribute Type            Description
            Mount     string          name of the mount that was calibrated
            dir       string          calibration direction (phase)
            dist      number          distance from starting location
            dx        number          x offset from starting position
            dy        number          y offset from starting position
            pos       [number,number] star coordinates
            step      number          step number
            State     string          calibration status message

        """
        self.logger.debug("Calibrating mount {}, on star position {}, "
            "step number {}, current state {} ".format(
            *[event[key] for key in ["Mount","pos","step","State"]]))
        self.StartCalibration()


    def _handle_CalibrationComplete(self, event):
        """Calibration completed successfully.
           Attribute Type    Descriptiondd
           Mount     string  name of the mount that was calibrated
        """
        self.logger.debug("Successfully calibrated mount {}".format(
            event["Mount"]))

    def _handle_StartGuiding(self, event):
        """Guiding begins.
           (no message attributes)
        """
        self.logger.debug("Guiding started !")

    def _handle_Paused(self, event):
        """Guiding has been paused.
        """
        self.logger.debug("Guiding has been paused. {}")

    def _handle_StartCalibration(self, event):
        """Calibration begins.
           Attribute  Type    Description
           Mount      string  the name of the mount being calibrated
        """
        self.logger.debug("Calibration is starting for mount {}".format(
            event["Mount"]))

    def _handle_AppState(self, event):
        """ The state at connection time
            Attribute  Type   Description
            State      string the current state of PHD

            The AppState notification is only sent when the client first
            connects to PHD2 (see #Initial_Messages). If an application would
            like to maintain an up-to-date AppState status, it will need to
            update its notion of AppState by handling individual notification
            events as follows:
            Event                    New AppState
            AppState                 <State>
            GuideStep                Guiding
            Paused                   Paused
            StartCalibration         Calibrating
            LoopingExposures         Looping
            LoopingExposuresStopped  Stopped
            StarLost                 LostLock
        """
        self.logger.debug("PHD2 state is {}".format(event["State"]))
        self.machine.set_state(event["State"])    

    def _handle_CalibrationFailed(self, event):
        """Calibration failed.
           Attribute  Type    Description
           Reason     string  an error message string
        """
        self.logger.debug("Calibration failed ! Reason: {}".format(
            event["Reason"]))

    def _handle_CalibrationDataFlipped(self, event):
        """Calibration data has been flipped.
           Attribute   Type    Description
           Mount       string  the name of the mount
        """
        self.logger.debug("Calibration data flipped for mount {}".format(
            event["Mount"]))

    def _handle_LoopingExposures(self, event):
        """Sent for each exposure frame while looping exposures.
           Attribute  Type   Description
           Frame      number the exposure frame number; starts at 1 each time
                             looping starts
        """
        self.logger.debug("Looping on exposure, frame number: {}".format(
            event["Frame"]))
        self.LoopingExposures()    

    def _handle_LoopingExposuresStopped(self, event):
        """Looping exposures has stopped.
           (no event attributes)
        """
        self.logger.debug("Looping exposure has stopped ")
        self.LoopingExposureStopped()

    def _handle_SettleBegin(self, event):
        """Sent when settling begins after a dither or guide method invocation.
           (no event attributes)
        """
        self.logger.debug("Settling begin, waiting for telescope to stabilize")
        self.SettleBegin()

    def _handle_Settling(self, event):
        """Sent for each exposure frame after a dither or guide method
           invocation until guiding has settled.
           Attribute   Type    Description
           Distance    number  the current distance between the guide star and
                               lock position
           Time        number  the elapsed time that the distance has been
                               below the settling tolerance distance (the
                               pixels attribute of the SETTLE parameter)
           SettleTime  number  the requested settle time (the time attribute
                               of the SETTLE parameter)
           StarLocked  boolean true if the guide star was found in the current
                               camera frame, false if the guide star was lost
        """
        self.logger.debug("Still in the process of settling, current distance "
            " is {}, time since settling process started {}/{}. Target guiding "
            " star status (is found?): {}".format(*[event[key] for key in
            ["Distance", "Time", "SettleTime", "StarLocked"]]))

    def _handle_SettleDone(self, event):
        """Sent after a dither or guide method invocation indicating whether
           settling was achieved, or if the guider failed to settle before the
           time limit was reached, or if some other error occurred preventing
           guide or dither to complete and settle.
           Attribute     Type    Description
           Status        number  0 if settling succeeded, non-zero if it failed
           Error         string  a description of the reason why the guide or
                                 dither command failed to complete and settle
           TotalFrames   number  the number of camera frames while settling
           DroppedFrames number  the number of dropped camera frames (guide
                                 star not found) while settling
        """
        self.logger.debug("Done with settling, status: {}. Dropped frames: "
            "{}/{}. Now proper imaging can start".format(*[event[key] for key in
            ["Status","DroppedFrames","TotalFrames"]]))
        self.SettleDone()

    def _handle_StarSelected(self, event):
        """A star has been selected.
           Attribute  Type    Description
           X          number  lock position X-coordinate
           Y          number  lock position Y-coordinate
        """
        self.logger.debug("Star has been selected at coordinates "
                          "x:{}, y:{}".format(event["X"], event["Y"]))
        self.StarSelected()

    def _handle_StarLost(self, event):
        """A frame has been dropped due to the star being lost.
           Attribute  Type    Description
           Frame      number  frame number
           Time       number  time since guiding started, seconds
           StarMass   number  star mass value
           SNR        number  star SNR value
           AvgDist    number  a smoothed average of the guide distance in
                              pixels (equivalent to value returned by socket
                              server MSG_REQDIST)
           ErrorCode  number  error code
           Status     string  error message
        """
        self.logger.debug("Error {}: {}. Frame {} dropped because of lost star"
            " SNR was {} and average distance was {}".format(*[event[key] for
            key in ["ErrorCode","Status","Frame","SNR","AvgDist"]]))
        self.StarLost()

    def _handle_GuidingStopped(self, event):
        """Guiding has stopped.
           (no event attributes)
        """
        self.logger.debug("Guiding has stopped {}".format(
            event[""]))

    def _handle_Resumed(self, event):
        """PHD has been resumed after having been paused.
           (no attributes)
        """
        self.logger.debug("Guiding has resumed {}".format(
            event[""]))

    def _handle_GuideStep(self, event):
        """This event corresponds to a line in the PHD Guide Log. The event is
           sent for each frame while guiding.
           Attribute        Type    Description
           Frame            number  The frame number; starts at 1 each time
                                    guiding starts
           Time             number  the time in seconds, including fractional
                                    seconds, since guiding started
           Mount            string  the name of the mount
           dx               number  the X-offset in pixels
           dy               number  the Y-offset in pixels
           RADistanceRaw    number  the RA distance in pixels of the guide
                                    offset vector
           DecDistanceRaw   number  the Dec distance in pixels of the guide
                                    offset vector
           RADistanceGuide  number  the guide algorithm-modified RA distance in
                                    pixels of the guide offset vector
           DecDistanceGuide number  the guide algorithm-modified Dec distance
                                    in pixels of the guide offset vector
           RADuration       number  the RA guide pulse duration in milliseconds
           RADirection      string  "East" or "West"
           DECDuration      number  the Dec guide pulse duration in milliseconds
           DECDirection     string  "South" or "North"
           StarMass         number  the Star Mass value of the guide star
           SNR              number  the computed Signal-to-noise ratio of the
                                    guide star
           AvgDist          number  a smoothed average of the guide distance in
                            pixels (equivalent to value returned by socket
                            server MSG_REQDIST)
           RALimited        boolean true if step was limited by the Max RA
                            setting (attribute omitted if step was not limited)
           DecLimited       boolean true if step was limited by the Max Dec
                            setting (attribute omitted if step was not limited)
           ErrorCode        number  the star finder error code
        """
        self.logger.debug("Guiding frame {}, for mount {} received."
            "dx: {}, dy: {}, StarMass: {}, SNR".format(*[event[key] for key in
            ["Frame","Mount","dx","dy","StarMass","SNR"]]))
        self.GuideStep()

    def _handle_GuidingDithered(self, event):
        """The lock position has been dithered.
           Attribute  Type    Description
           dx         number  the dither X-offset in pixels
           dy         number  the dither Y-offset in pixels
        """
        self.logger.debug("Dithering from current position by x:{} pix, and "
            "y:{} pix".format(*[event[key] for key in ["dx", "dy"]]))

    def _handle_LockPositionLost(self, event):
        """The lock position has been lost.
           (no attributes)
        """
        self.logger.warning("PHD2: The lock position has been lost")

    def _handle_Alert(self, event):
        """An alert message was displayed in PHD2.
           Attribute  Type    Description
           Msg        string  the text of the alert message
           Type       string  The type of alert: "info", "question", "warning",
                              or "error"
        """
        def _handle_Alert(self, event):
            """An alert message was displayed in PHD2.
               Msg     string the text of the alert message
               Type    string The type of alert: "info", "question", "warning",
                              or "error"
            """
            if event["Type"] == "info":
                self.logger.info("Received alert of type {} from PHD2: {}"
                    "".format(*[event[key] for key in ["Type","Msg"]]))
            if event["Type"] == "warning":
                self.logger.warning("Received alert of type {} from PHD2: {}"
                    "".format(*[event[key] for key in ["Type","Msg"]]))
            if event["Type"] == "info":
                self.logger.error("Received alert of type {} from PHD2: {}"
                    "".format(*[event[key] for key in ["Type","Msg"]]))
            else:
                self.logger.info("Received alert of type {} from PHD2: {}"
                    "".format(*[event[key] for key in ["Type","Msg"]]))

    def _handle_GuideParamChange(self, event):
        """A guiding parameter has been changed.
           Attribute  Type    Description
           Name       string  the name of the parameter that changed
           Value      any     the new value of the parameter
        """
        self.logger.debug("PHD2 parameter {} changed: {}".format(
            *[event[key] for key in ["Name","Value"]]))
