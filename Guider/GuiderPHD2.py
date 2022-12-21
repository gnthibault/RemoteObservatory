#Standard stuff
import json
import time
from transitions import Machine
import socket
import subprocess

#Astropy
import astropy.units as u

#local libs
from Base.Base import Base
from utils import Timeout
from utils import error
from utils.error import GuidingError
from Service.PanMessagingZMQ import PanMessagingZMQ

MAXIMUM_CALIBRATION_TIMEOUT = 6 * 60 * u.second
MAXIMUM_DITHER_TIMEOUT = 45 * u.second
MAXIMUM_PAUSING_TIMEOUT = 30 * u.second
STANDARD_TIMEOUT = 120 * u.second
SOCKET_TIMEOUT = 120.0 #when launching set_connected sometimes response can take a lot of time

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
        { 'trigger': 'connection_trig', 'source': '*', 'dest': 'Connected'},
        { 'trigger': 'disconnection_trig', 'source': '*', 'dest': 'NotConnected'},
        { 'trigger': 'GuideStep', 'source': 'SteadyGuiding', 'dest': 'SteadyGuiding'},
        # from https://github.com/pytransitions/transitions#transitioning-from-multiple-states:
        # Note that only the first matching transition will execute
        { 'trigger': 'GuideStep', 'source': '*', 'dest': 'Guiding'},
        { 'trigger': 'Paused', 'source': '*', 'dest': 'Paused'},
        { 'trigger': 'StartCalibration', 'source': '*', 'dest': 'Calibrating'},
        { 'trigger': 'LoopingExposures', 'source': '*', 'dest': 'Looping'},
        { 'trigger': 'LoopingExposuresStopped', 'source': '*', 'dest': 'Stopped'},
        { 'trigger': 'SettleBegin', 'source': '*', 'dest': 'Settling'},
        { 'trigger': 'SettleDone', 'source': '*', 'dest': 'SteadyGuiding'},
        { 'trigger': 'StarLost', 'source': '*', 'dest': 'LostLock'},
        { 'trigger': 'StarSelected', 'source': '*', 'dest': 'StarSelected'},
        { 'trigger': 'ConnectionLost', 'source': '*', 'dest': 'NotConnected'}
        ]

    def __init__(self, config=None):
        super().__init__()
        if config is None:
            config = dict(
                host="localhost",
                port=4400,
                do_calibration=True,
                profile_name="",
                exposure_time_sec='3',
                settle={
                    "pixels": 1.5,
                    "time": 10,
                    "timeout": 60},
                dither={
                    "pixels": 3.0,
                    "ra_only": False}
            )

        self.host = config["host"]
        self.port = config["port"]
        self.process = None
        self.session = None
        self.sock = None
        self.recv_buffer = ''
        self.id = 1                                # message id
        self.do_calibration = config["do_calibration"]
        self.profile_id = None                     # yet to be defined
        self.profile_name = config["profile_name"] # profile name for equipment
        self.mount = None
        self.settle = config["settle"]
        self.exposure_time_sec = config['exposure_time_sec']

        # we broadcast data through a message queue style mecanism
        self.messaging = None

        # Initialize the state machine
        self.machine = Machine(model=self,
                               states=GuiderPHD2.states,
                               transitions=GuiderPHD2.transitions,
                               initial=GuiderPHD2.states[0])

    def __del__(self):
        self.terminate_server()

    def is_local_instance(self):
        return True if self.host == "localhost" else False

    def launch_server(self):
        """
        Usage: phd2 [-i <num>] [-R]
          -i, --instanceNumber=<num>  sets the PHD2 instance number (default=1)
          -R, --Reset                 Reset all PHD2 settings to default values
        """
        if self.is_local_instance() and self.process is None:
            cmd = 'phd2'
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            time.sleep(10) #Did not found anything better than that...

    def connect_server(self):
        self.logger.info(f"Connect to PHD2 server {self.host}:{self.port}")
        # Create a socket (SOCK_STREAM means a TCP socket)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(SOCKET_TIMEOUT)
        try:
            # Connect to server and send data
            #self.session = requests.sessions.Session()
            self.sock.connect((self.host, self.port))
            self._receive({"Event": "AppState"}) # get state
        except Exception as e:
            msg = f"PHD2 error connecting: {e}"
            self.logger.error(msg)
            raise GuidingError(msg)

    def connect_profile(self, profile_name=None):
        if profile_name is None:
            profile_name = self.profile_name
        self.logger.info(f"Connect profile {profile_name}")
        # Abstract from PHD2 documentation: https://github.com/OpenPHDGuiding/phd2/wiki/EventMonitoring
        # Select an equipment profile. All equipment must be disconnected before switching profiles.
        self.disconnect_profile()
        self.set_profile_from_name(profile_name)
        self.set_connected(True)

    def is_server_connected(self):
        return self.state != 'NotConnected'

    def is_profile_connected(self, profile_name=None):
        if profile_name is None:
            profile_name = self.profile_name
        try:
            profiles = self.get_profiles()
            is_profile_selected = [d["selected"] for d in profiles if ("selected" in d) and (d["name"] ==
                                                                                             profile_name)][0]
        except Exception as e:
            msg = f"Profile {profile_name} is not either not selected or not know to phd2, reported " \
                  f"profiles are {profiles}"
            self.logger.warning(msg)
            is_profile_selected = False
        try:
            is_equipment_connected = self.get_connected()
        except Exception as e:
            is_equipment_connected = False
        return is_profile_selected and is_equipment_connected

    def is_guiding_ok(self):
        return self.state in ["Guiding", "SteadyGuiding"]

    def disconnect_profile(self):
        if self.state != 'NotConnected':
            self.stop_capture()
            self.set_connected(False)

    def disconnect_server(self):
        self.logger.info(f"Closing connection to server PHD2 {self.host}:{self.port}")
        if self.state != 'NotConnected':
            self.stop_capture()
        if self.sock is not None:
            self.sock.close()
        self.disconnection_trig()

    def terminate_server(self):
        if self.state != 'NotConnected':
            self.shutdown()
            self.sock.close()
        self.disconnection_trig()

        if self.is_local_instance():
            self.force_kill_server()

    def get_profile_id_from_name(self, profile_name):
        profiles = self.get_profiles()
        try:
            profile_id = [d["id"] for d in profiles if d["name"] == profile_name][0]
        except IndexError as e:
            msg = f"Profile {profile_name} is not know to phd2, that reported the following profiles {profiles}"
            self.logger.error(msg)
            raise RuntimeError(msg)
        return profile_id, profiles

    def set_profile_from_name(self, profile_name):
        profile_id, profiles = self.get_profile_id_from_name(profile_name=profile_name)
        self.logger.debug(f"About to set profile with id {profile_name} among the following list: {profiles}")
        self.set_profile(profile_id)

    def status(self):
        return {'state': self.state}

    def send_message(self, data, channel='GUIDING'):
        if self.messaging is None:
            self.messaging = PanMessagingZMQ.create_publisher(self.config["messaging"]["msg_port"])
        self.messaging.send_message(channel, {"data": data})

    def receive(self):
        return self._receive()

    def wait_for_state(self, one_of_states, timeout=STANDARD_TIMEOUT):
        assert isinstance(one_of_states, list)
        tout = Timeout(timeout)
        while self.state not in one_of_states:
            try:
                self._receive(loop_mode=True)
            except error.Timeout as e:
                pass
            if tout.expired():
                raise error.Timeout(f"Timeout while waiting for one of "
                                    f"those states: {one_of_states}")

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

    def force_kill_server(self):
        if self.process is not None:
            self.process.kill()
            self.process = None

    ####    PHD2 rpc API methods ####

    def shutdown(self):
        """
           params: none 
           result: integer(0)
           desc. : Close PHD2
        """
        req={"method": "shutdown",
             "params": [],
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to shutdown request: {data}")
        except Exception as e:
            msg = f"PHD2 error shutdown: {e}"
            self.logger.error(msg)
            self.force_kill_server()

    def set_connected(self, connect=True):
        """
           params: boolean: connect
           result: integer(0)
           desc. : connect or disconnect all equipment
        """
        req={"method": "set_connected",
             "params": [connect],
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to set_connected request: {data}")
        except Exception as e:
            msg = f"PHD2 error set_connected: {e}"
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
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to set_profile request: "
                                   f"{data}")
            self.profile_id = profile_id
        except Exception as e:
            msg = f"PHD2 error setting profile: {e}"
            self.logger.error(msg)
            raise GuidingError(msg)

    def set_paused(self, paused=True, full="full"):
        """
           params: PAUSED: boolean, FULL: string (optional)
           result: integer(0)
           desc. : When setting paused to true, an optional
                second parameter with value "full" can be provided
                to fully pause phd, including pausing looping exposures.
                Otherwise, exposures continue to loop, and only
                guide output is paused. Example:
                {"method":"set_paused","params":[true,"full"],"id":42}
                {"method":"set_paused","params":[true,""],"id":42}
                {"method":"set_paused","params":[false,"whatever"],"id":42}
        """
        params = [paused, full]
        req={"method": "set_paused",
             "params": params,
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to set_paused request: {data}")
            timeout = Timeout(MAXIMUM_PAUSING_TIMEOUT)
            while self.state != 'Paused':
                self._receive(loop_mode=True)
                if timeout.expired():
                    raise error.Timeout(f"Timeout while waiting for Paused")
        except Exception as e:
            msg = f"PHD2 error setting paused status: {e}"
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
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to capture_single_frame "
                                   f"request: {data}")
        except Exception as e:
            msg = "PHD2 error capturing frame: {e}"
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
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
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
             "id": self.id}
        self.id += 1

        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to dither request: {data}")
            timeout = Timeout(MAXIMUM_DITHER_TIMEOUT)
            while self.state != 'SteadyGuiding':
                self._receive(loop_mode=True)
                if timeout.expired():
                    raise error.Timeout(f"Timeout while waiting for settle "
                                        f"after dither was sent to GuiderPHD2")
        except Exception as e:
            msg = "PHD2 error dithering: {e}"
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
             "id": self.id}
        self.id += 1
        self._send_request(req)
        status = self._receive({"id": req["id"]})
        # Should generate an event like this:
        # {'Event': 'LockPositionSet', 'Timestamp': 15.16, 'Host': 'XXXX', 'Inst': 1, 'X': 1040.007, 'Y': 224.034}
        if 'result' in status:
            if not status["result"]:
                msg = f"PHD2 find_star failed"
                self.logger.error(msg)
                raise GuidingError(msg)
        else:
            msg = f"Cannot find guiding star automatically"
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
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to set_dec_guide_mode "
                                   f"request: {data}")
        except Exception as e:
            msg = "PHD2 error setting dec guide mode: {e}"
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

                    from https://openphdguiding.org/manual/?section=Tools.htm#Lock_Positions
                    PHD2 normally sets a 'lock position' where the guide star is
                    located at the end of calibration.  Depending on the details
                    of the calibration sequence, this may not be exactly where
                    the star was located at the start of calibration - it could
                    be off by a few pixels.  If you are trying to precisely
                    center your target, you may want to use a
                    'sticky lock position.'
                    You do this by clicking on your guide star before
                    calibration, then setting the 'Sticky Lock Position' under
                    the 'Tools' menu.  After calibration is complete, PHD2 will
                    continue to move the mount until the star is located at the
                    sticky lock position.  So you may see an additional delay
                    after the calibration while PHD2 repositions the scope at
                    guide speed.  The sticky lock position will continue to be
                    used even as guiding is stopped and subsequently resumed.
                    Again, this insures a rigorous positioning of the guide star
                    (and presumably your image target) at the expense of delays
                    needed for PHD2 to reposition the mount.
                    If you need to  fine-tune the position of the guide star on
                    the camera sensor after guiding has begun, you can use the
                    'Adjust Lock Position' function under the Tools menu:
        """
        params = [{}]
        params[0]["X"] = pos_x
        params[0]["Y"] = pos_y
        params[0]["EXACT"] = False
        req={"method": "set_lock_position",
             "params": params,
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to set_lock_position "
                                   f"request: {data}")
        except Exception as e:
            msg = f"PHD2 error setting lock position: {e}"
            self.logger.error(msg)
            raise GuidingError(msg)

    def set_exposure(self, exp_time_sec):
        """
            params: integer: exposure time in milliseconds
            result: integer(0)
            desc. : 
        """
        exp_time_milli = int(exp_time_sec*1000)
        req={"method": "set_exposure",
             "params": [exp_time_milli],
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to set_exposure request: "
                                   f"{data}")
        except Exception as e:
            msg = f"PHD2 error setting exposure: {e}"
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
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to loop request: {data}")
        except Exception as e:
            msg = f"PHD2 error looping: {e}"
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
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to stop_capture request: {data}")
            timeout = Timeout(STANDARD_TIMEOUT)
            if self.state in ["Calibrating", "Guiding", "SteadyGuiding", "Looping", "LostLock", "Paused"]:
                while self.state not in ['Stopped']: #GuidingStopped
                    data = self._receive(loop_mode=True)
                    if timeout.expired():
                        raise error.Timeout(f"Timeout while waiting for response after stop_capture was sent to "
                                            f"GuiderPHD2")

        except Exception as e:
            msg = f"PHD2 error stopping capture: {e}"
            self.logger.error(msg)
            raise GuidingError(msg)

    def guide(self, recalibrate=None):
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
        if recalibrate is None:
            recalibrate = self.do_calibration
        req={"method": "guide",
             "params": [self.settle, recalibrate],
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            if "result" not in data or data["result"] != 0:
                raise GuidingError(f"Wrong answer to guide request: {data}")

            timeout = Timeout(MAXIMUM_CALIBRATION_TIMEOUT)
            while self.state != 'SteadyGuiding':
                try:
                    self._receive(loop_mode=True)
                except error.Timeout as e:
                    pass
                if timeout.expired():
                    raise error.Timeout(f"Timeout while waiting for settle "
                                        f"after guide was sent to GuiderPHD2")
        except Exception as e:
            msg = f"PHD2 error guiding: {e}"
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
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            return data["result"]
        except Exception as e:
            msg = f"PHD2 error getting app state: {e}"
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
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            return data["result"]
        except Exception as e:
            msg = f"PHD2 error getting calibration status: {e}"
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
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            return data["result"]
        except Exception as e:
            msg = f"PHD2 error getting connection status: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg)

    def get_profiles(self):
        """
            params: none  
            result: array of {"id":profile_id,"name":"profile_name"}
            desc. : 
        """
        req={"method": "get_profiles",
             "params": [],
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            return data["result"]
        except Exception as e:
            msg = f"PHD2 error getting profiles list: {e}"
            self.logger.warning(msg)
            raise RuntimeError(msg)

    def get_current_equipment(self):
        """
            params: none
            result: example  {
                              "camera": {
                                "name": "Simulator",
                                "connected": true
                              },
                              "mount": {
                                "name": "On Camera",
                                "connected": true
                              }
                            }
            desc. : get the devices selected in the current equipment profile
        """
        req={"method": "get_current_equipment",
             "params": [],
             "id": self.id}
        self.id += 1
        try:
            self._send_request(req)
            data = self._receive({"id": req["id"]})
            return data["result"]
        except Exception as e:
            msg = f"PHD2 error getting current equipment: {e}"
            self.logger.warning(msg)
            raise RuntimeError(msg)

    #### Some specific handle code for decoding messages ####

    def _receive(self, expected=None, loop_mode=False, timeout=STANDARD_TIMEOUT):
        timeout = Timeout(timeout)
        ret = None
        while not ret:
            ret = self._receive_from_socket(expected=expected, loop_mode=loop_mode)
            if not ret:
                self.logger.warning(f"Received {ret}, still waiting for "
                                    f"expected {expected} while loop mode is "
                                    f"{loop_mode}")
            if timeout.expired():
                raise error.Timeout(f"Timeout while waiting for reception of "
                                    f"response from GuiderPHD2")
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
                    msg = f"PHD2 Timeout: No response from server"
                    self.logger.error(msg)
                    raise GuidingError(msg)
            except Exception as e:
                msg = f"PHD2 error {e}"
                self.logger.error(msg)
                raise GuidingError(msg)
            # Check if we receive termination symbol
            msgs = self.recv_buffer.split('\r\n')
            if len(msgs) <= 1:
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
                self.logger.debug(f"Received event: {event}")
                valid_status = self._check_event(event, expected)
                expected_status = (expected_status or valid_status)
                self._handle_event(event)
                if valid_status:
                    expected_event = event
            except Exception as e:
                msg = f"PHD2 error on message {msg}:{e}"
                self.logger.error(msg)
                raise GuidingError(msg)
        return expected_event

    def _send_request(self, req):
        base = dict(jsonrpc="2.0")
        base.update(req)
        json_txt = json.dumps(base)+'\r\n'
        self.logger.debug(f"sending msg {json_txt[:-2]}")
        try:
            self.sock.sendall(json_txt.encode())
        except Exception as e:
            msg = f"PHD2 error sending request: {e}"
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
            msg = f"Received error msg: {event['error']}"
            self.logger.error(msg)
        return status

    def _handle_event(self, event):
        if "Event" in event:
            method_name = f"_handle_{event['Event']}"
            if hasattr(self, method_name):
                getattr(self, method_name)(event)
            else:
                self.logger.warning(f"While processing event {event}, no "
                    f"method called {method_name} to handle event !")

    def _handle_Version(self, event):
        """Describes the PHD and message protocol versions.
           Attribute   Type   Description
           PHDVersion  string the PHD version number
           PHDSubver   string the PHD sub-version number
           MsgVersion  number the version number of the event message protocol.
                              The current version is 1. We will bump this
                              number if the message protocol changes
        """
        self.logger.debug(f"Received version {event['PHDVersion']}:"
            f"{event['PHDSubver']} - msg ver {event['MsgVersion']}")
        self.connection_trig()

    def _handle_ConfigurationChange(self, event):
        """Waiting for more info: https://github.com/OpenPHDGuiding/phd2/issues/845
           Attribute   Type   Description
        """
        self.logger.debug(f"Received ConfigurationChange event: {event}")

    def _handle_LockPositionSet(self, event):
        """The lock position has been established.
           Attribute Type    Description
           X         number  lock position X-coordinate
           Y         number  lock position Y-coordinate
        """
        self.logger.debug(f"Lock position X:{event['X']} , Y:{event['Y']} "
                          f"has been established")
                          
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
        self.logger.debug(f"Calibrating mount {event['Mount']}, on star "
            f"position {event['pos']}, step number {event['step']}, current "
            f"state {event['State']}")
        self.StartCalibration()
        self.send_message(self.status(), channel='GUIDING_STATUS')

    def _handle_CalibrationComplete(self, event):
        """Calibration completed successfully.
           Attribute Type    Descriptiondd
           Mount     string  name of the mount that was calibrated
        """
        self.logger.debug("Successfully calibrated mount {event['Mount']}")

    def _handle_StartGuiding(self, event):
        """Guiding begins.
           (no message attributes)
        """
        self.logger.debug(f"Guiding started !")

    def _handle_Paused(self, event):
        """Guiding has been paused.
        """
        self.logger.debug(f"Guiding has been paused. {event}")
        self.Paused()
        self.send_message(self.status(), channel='GUIDING_STATUS')

    def _handle_StartCalibration(self, event):
        """Calibration begins.
           Attribute  Type    Description
           Mount      string  the name of the mount being calibrated
        """
        self.logger.debug(f"Calibration is starting for mount {event['Mount']}")
        self.StartCalibration()
        self.send_message(self.status(), channel='GUIDING_STATUS')

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
        self.logger.debug(f"PHD2 state is {event['State']}")
        self.machine.set_state(event["State"])    
        self.send_message(self.status(), channel='GUIDING_STATUS')

    def _handle_CalibrationFailed(self, event):
        """Calibration failed.
           Attribute  Type    Description
           Reason     string  an error message string
        """
        msg = f"Calibration failed ! Reason: {event['Reason']}"
        self.logger.error(msg)
        raise GuidingError(msg)

    def _handle_CalibrationDataFlipped(self, event):
        """Calibration data has been flipped.
           Attribute   Type    Description
           Mount       string  the name of the mount
        """
        self.logger.debug(f"Calibration data flipped for mount "
                          f"{event['Mount']}")

    def _handle_LoopingExposures(self, event):
        """Sent for each exposure frame while looping exposures.
           Attribute  Type   Description
           Frame      number the exposure frame number; starts at 1 each time
                             looping starts
        """
        self.logger.debug(f"Looping on exposure, frame number: "
                          f"{event['Frame']}")
        self.LoopingExposures()    
        self.send_message(self.status(), channel='GUIDING_STATUS')

    def _handle_LoopingExposuresStopped(self, event):
        """Looping exposures has stopped.
           (no event attributes)
        """
        self.logger.debug(f"Looping exposure has stopped ")
        self.LoopingExposuresStopped()
        self.send_message(self.status(), channel='GUIDING_STATUS')

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
            f"is {event['Distance']}, time since settling process started "
            f"{event['Time']}/{event['SettleTime']}. Target guiding "
            f"star status (is found?): {event['StarLocked']}")

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
        self.logger.debug(f"Done with settling, status: {event['Status']}. "
            f"Dropped frames: {event['DroppedFrames']}/{event['TotalFrames']}. "
            f"Now proper imaging can start")
        self.SettleDone()

    def _handle_StarSelected(self, event):
        """A star has been selected.
           Attribute  Type    Description
           X          number  lock position X-coordinate
           Y          number  lock position Y-coordinate
        """
        self.logger.debug(f"Star has been selected at coordinates "
                          f"x:{event['X']}, y:{event['Y']}")
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
        self.logger.debug(f"Error {event['ErrorCode']}: {event['Status']}. "
            f"Frame {event['Frame']} dropped because of lost star. SNR was "
            f"{event['SNR']} and average distance was {event['AvgDist']}")
        self.StarLost()
        self.send_message(self.status(), channel='GUIDING_STATUS')

    def _handle_GuidingStopped(self, event):
        """Guiding has stopped.
           (no event attributes)
        """
        self.logger.debug(f"Guiding has stopped {event}")

    def _handle_Resumed(self, event):
        """PHD has been resumed after having been paused.
           (no attributes)
        """
        self.logger.debug(f"Guiding has resumed {event}")

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
        self.logger.debug(f"Guiding frame {event['Frame']}, for mount "
            f"{event['Mount']} received. dx: {event['dx']}, dy: {event['dy']}, "
            f"StarMass: {event['StarMass']}, SNR: {event['SNR']}")
        self.GuideStep()
        self.send_message(self.status(), channel='GUIDING_STATUS')
        self.send_message(event, channel='GUIDING')

    def _handle_GuidingDithered(self, event):
        """The lock position has been dithered.
           Attribute  Type    Description
           dx         number  the dither X-offset in pixels
           dy         number  the dither Y-offset in pixels
        """
        self.logger.debug(f"Dithering from current position by x:{event['dx']} "
                          f"pix, and y:{event['dy']} pix")

    def _handle_LockPositionLost(self, event):
        """The lock position has been lost.
           (no attributes)
        """
        self.logger.warning(f"PHD2: The lock position has been lost")

    def _handle_Alert(self, event):
        """An alert message was displayed in PHD2.
           Attribute  Type    Description
           Msg        string  the text of the alert message
           Type       string  The type of alert: "info", "question", "warning",
                              or "error"
        """
        msg = f"Received alert of type {event['Type']} from PHD2: "\
              f"{event['Msg']}"
        if event["Type"] == "info":
            self.logger.info(msg)
        if event["Type"] == "warning":
            self.logger.warning(msg)
        if event["Type"] == "error":
            self.logger.error(msg)
        else:
            self.logger.info(msg)

    def _handle_GuideParamChange(self, event):
        """A guiding parameter has been changed.
           Attribute  Type    Description
           Name       string  the name of the parameter that changed
           Value      any     the new value of the parameter
        """
        self.logger.debug(f"PHD2 parameter {event['Name']} changed: "
                          f"{event['Value']}")
