#out libraries
import socket
import json
from transitions import Machine

#local libs
from Base.Base import Base

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
        State        Description
        Stopped      PHD is idle
        Selected     A star is selected but PHD is neither looping exposures,
                     calibrating, or guiding
        Calibrating  PHD is calibrating
        Guiding      PHD is guiding
        LostLock     PHD is guiding, but the frame was dropped
        Paused       PHD is paused
        Looping      PHD is looping exposures
    """
    states = ['NotConnected', 'Guiding', 'Paused', 'Calibrating', 'Looping',
              'Stopped']
    transitions = [
        { 'trigger': 'GuideStep', 'source': '*', 'dest': 'Guiding' },
        { 'trigger': 'Paused', 'source': '*', 'dest': 'Paused' },
        { 'trigger': 'StartCalibration', 'source': '*', 'dest': 'Calibrating' },
        { 'trigger': 'LoopingExposure', 'source': '*', 'dest': 'Looping' },
        { 'trigger': 'LoopingExposuresStoped', 'source': '*', 'dest': 'Stopped' },
        { 'trigger': 'StarLost', 'source': '*', 'dest': 'LostLock' },
        { 'trigger': 'ConnectionLost', 'source': '*', 'dest': 'NotConnected' }
        ]

    def __init__(self, name, config=None):
        if config is None:
            config = dict(
                phd_port = 4400,
            )
        # Initialize the state machine
        self.machine = Machine(model = self,
                               states = GuiderPHD2.states,
                               transitions = GuiderPHD2.transitions,
                               initial = GuiderPHD2.states[0])

    def handle_event(self, event):
        method_name = "handle_{}.format"(event["event"])
        if hasattr(self, method_name):
            getattr(self, method_name)(event)
        else:
            self.logger.warning("No method called {} to handle event !".format(
                method_name))

    def handle_Version(self, event):
        """Describes the PHD and message protocol versions.
           Attribute   Type   Description
           PHDVersion  string the PHD version number
           PHDSubver   string the PHD sub-version number
           MsgVersion  number the version number of the event message protocol.
                              The current version is 1. We will bump this
                              number if the message protocol changes
        """
    def handle_LockPositionSet(self, event):
        """The lock position has been established.
           Attribute Type    Description
           X         number  lock position X-coordinate
           Y         number  lock position Y-coordinate
        """
        self.logger.debug("Lock position X:{} , Y:{} has been established"
                          "".format(event["X"], event["Y"])
                          
    def handle_Calibrating(self, event):
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
            [event[key] for key in ["Mount","pos","step","State"]]))



    def handle_CalibrationComplete(self, event):
        """Calibration completed successfully.
           Attribute Type    Descriptiondd
           Mount     string  name of the mount that was calibrated
        """
        self.logger.debug("Successfully calibrated mount {}".format(
            event["Mount"]))

    def handle_StartGuiding(self, event):
        """Guiding begins.
           (no message attributes)
        """
        self.logger.debug("Guiding started !")

    def handle_Paused(self, event):
        """Guiding has been paused.
        """
        self.logger.debug("Guiding has been paused. {}")

    def handle_StartCalibration(self, event):
        """Calibration begins.
           Attribute  Type    Description
           Mount      string  the name of the mount being calibrated
        """
        self.logger.debug("Calibration is starting for mount {}".format(
            event["Mount"]))

    def handle_AppState(self, event):
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
        

    def handle_CalibrationFailed(self, event):
        """Calibration failed.
           Attribute  Type    Description
           Reason     string  an error message string
        """
        self.logger.debug("Calibration failed ! Reason: {}".format(
            event["Reason"]))

    def handle_CalibrationDataFlipped
        """Calibration data has been flipped.
           Attribute   Type    Description
           Mount       string  the name of the mount
        """
        self.logger.debug("Calibration data flipped for mount {}".format(
            event["Mount"]))

    def handle_LoopingExposures(self, event):
        """Sent for each exposure frame while looping exposures.
           Attribute  Type   Description
           Frame      number the exposure frame number; starts at 1 each time
                             looping starts
        """
        self.logger.debug("Looping on exposure, frame number: {}".format(
            event["Frame"]))

    def handle_LoopingExposuresStopped(self, event):
        """Looping exposures has stopped.
           (no event attributes)
        """
        self.logger.debug("Looping exposure has stopped ")

    def handle_SettleBegin(self, event):
        """Sent when settling begins after a dither or guide method invocation.
           (no event attributes)
        """
        self.logger.debug("Settling begin, now proper autoguiding, exposure "
                          "can start ")

    def handle_Settling(self, event):
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
            " star status (is found?): {}".format([event[key] for key in
            ["Distance", "Time", "SettleTime", "StarLocked"]]))

    def handle_SettleDone(self, event):
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
        self.logger.debug("Done with settling,  status: {}. Dropped frames: "
            "{}/{}. Error: {}".format([event[key] for key in
            ["Status","DroppedFrames","TotalFrames","Error"]]))

    def handle_StarLost(self, event):
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
            " SNR was {} and average distance was {}".format([event[key] for
            key in ["ErrorCode","Status","Frame","SNR","AvgDist"]]))
            event[""]))

    def handle_GuidingStopped(self, event):
        """Guiding has stopped.
           (no event attributes)
        """
        self.logger.debug("Guiding has stopped {}".format(
            event[""]))

    def handle_Resumed(self, event):
        """PHD has been resumed after having been paused.
           (no attributes)
        """
        self.logger.debug("Guiding has resumed {}".format(
            event[""]))

    def handle_GuideStep(self, event):
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
            "dx: {}, dy: {}, StarMass: {}, SNR".format([event[key] for key in
            ["Frame","Mount","dx","dy","StarMass","SNR"]))

    def handle_GuidingDithered(self, event):
        """The lock position has been dithered.
           Attribute  Type    Description
           dx         number  the dither X-offset in pixels
           dy         number  the dither Y-offset in pixels
        """
        self.logger.debug("Dithering from current position by x:{} pix, and "
            "y:{} pix".format([event[key] for key in ["dx", "dy"]]))

    def handle_LockPositionLost(self, event):
        """The lock position has been lost.
           (no attributes)
        """
        self.logger.warning("PHD2: The lock position has been lost")

    def handle_Alert(self, event):
        """An alert message was displayed in PHD2.
           Attribute  Type    Description
           Msg        string  the text of the alert message
           Type       string  The type of alert: "info", "question", "warning",
                              or "error"
        """
        self.logger.warning("PHD2 Alert {}:{}".format(
            [event[key] for key in ["Msg","Type"]]))

    def handle_GuideParamChange(self, event):
        """A guiding parameter has been changed.
           Attribute  Type    Description
           Name       string  the name of the parameter that changed
           Value      any     the new value of the parameter
        """
        self.logger.debug("PHD2 parameter {} changed: {}".format(
            [event[key] for key in ["Name","Value"]]))

