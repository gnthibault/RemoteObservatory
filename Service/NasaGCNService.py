# Generic imports
import logging
import os
import threading
import time

# pip install gcn-kafka
from gcn_kafka import Consumer

# Astropy
import astropy.units as u

#Local stuff
from helper.IndiDevice import IndiDevice
from utils import load_module

class NasaGCNService(threading.Thread):

    def __init__(self, config=None, loop_on_create=True):
        self.logger = logging.getLogger(__name__)
        if config is None:
            config = dict(
                module="NasaGCNService",
                delay_sec=60,
                client_info=dict(
                    client_id=os.getenv("NASA_GCN_CLIENT_ID"),
                    client_secret=os.getenv("NASA_GCN_CLIENT_SECRET")),
                messaging_publisher=dict(
                    module="PanMessagingMQTT",
                    mqtt_host="localhost",
                    mqtt_port="1883",
                    com_mode="publisher")
            )
        self.config = config

        # Init parent thread
        threading.Thread.__init__(self, target=self.serve)
        self._stop_event = threading.Event()
        self._do_run = True
        self._delay_sec = config["delay_sec"]

        # Kafka stuff
        try:
            self.client_id = config["client_info"]["client_id"]
            self.client_secret = config["client_info"]["client_secret"]
        except Exception as e:
            self.client_id = os.getenv("NASA_GCN_CLIENT_ID"),
            self.client_secret = os.getenv("NASA_GCN_CLIENT_SECRET")
        self.consumer = None

        # Other tools
        self.messaging = None

        if loop_on_create:
            self.start()

    def initialize_messaging(self, config=None):
        if config is None:
            config = self.config
        if self.messaging is None:
            messaging_name = config["messaging_publisher"]['module']
            messaging_module = load_module('Service.'+messaging_name)
            self.messaging = getattr(messaging_module, messaging_name)(
                 config=config["messaging_publisher"])

    def send_message(self, msg, channel='BROKER'):
        if self.messaging is None:
            self.initialize_messaging()
        self.messaging.send_message(channel, msg)

    def capture(self, send_message=True):
        self.logger.debug("Updating weather")
        for message in self.consumer.consume():
            data = message.value()
            if send_message:
                self.send_message({'data': data.decode()}, channel='BROKER')

    def serve(self):
        """
        Continuously generates weather reports
        """
        self.initialize_messaging()
        self.connect()
        while not self.stopped():
            self.capture()
            time.sleep(self._delay_sec)

    def stop(self):
        """
        Stops the web server.
        """
        self._stop_event.set()

    def stopped(self):
        """
        Checks if server is stopped.

        :return: True if server is stopped, False otherwise
        """
        return self._stop_event.is_set()

    def connect(self):
        """
            Connect as a consumer.
            Warning: don't share the client secret with others.
        :return:
        """
        self.consumer = Consumer(client_id=self.client_id,
                                 client_secret=self.client_secret)
        # Subscribe to topics and receive alerts
        self.subscribe_list = [
#            'gcn.classic.text.AGILE_GRB_GROUND',
            'gcn.classic.text.AGILE_GRB_POS_TEST',
#            'gcn.classic.text.AGILE_GRB_REFINED',
#            'gcn.classic.text.AGILE_GRB_WAKEUP',
            'gcn.classic.text.AGILE_MCAL_ALERT',
#            'gcn.classic.text.AGILE_POINTDIR',
#            'gcn.classic.text.AGILE_TRANS',
#            'gcn.classic.text.AMON_ICECUBE_COINC',
#            'gcn.classic.text.AMON_ICECUBE_EHE',
#            'gcn.classic.text.AMON_ICECUBE_HESE',
            'gcn.classic.text.AMON_NU_EM_COINC',
            'gcn.classic.text.CALET_GBM_FLT_LC',
#            'gcn.classic.text.CALET_GBM_GND_LC',
            'gcn.classic.text.FERMI_GBM_ALERT',
            'gcn.classic.text.FERMI_GBM_FIN_POS',
            'gcn.classic.text.FERMI_GBM_FLT_POS',
            'gcn.classic.text.FERMI_GBM_GND_POS',
#            'gcn.classic.text.FERMI_GBM_LC',
            'gcn.classic.text.FERMI_GBM_POS_TEST',
            'gcn.classic.text.FERMI_GBM_SUBTHRESH',
#            'gcn.classic.text.FERMI_GBM_TRANS',
#            'gcn.classic.text.FERMI_LAT_GND',
            'gcn.classic.text.FERMI_LAT_MONITOR',
            'gcn.classic.text.FERMI_LAT_OFFLINE',
#            'gcn.classic.text.FERMI_LAT_POS_DIAG',
#            'gcn.classic.text.FERMI_LAT_POS_INI',
            'gcn.classic.text.FERMI_LAT_POS_TEST',
#            'gcn.classic.text.FERMI_LAT_POS_UPD',
#            'gcn.classic.text.FERMI_LAT_TRANS',
            'gcn.classic.text.FERMI_POINTDIR',
#            'gcn.classic.text.FERMI_SC_SLEW',
            'gcn.classic.text.GECAM_FLT',
            'gcn.classic.text.GECAM_GND',
            'gcn.classic.text.ICECUBE_ASTROTRACK_BRONZE',
            'gcn.classic.text.ICECUBE_ASTROTRACK_GOLD',
            'gcn.classic.text.ICECUBE_CASCADE',
            'gcn.classic.text.INTEGRAL_OFFLINE',
            'gcn.classic.text.INTEGRAL_POINTDIR',
            'gcn.classic.text.INTEGRAL_REFINED',
            'gcn.classic.text.INTEGRAL_SPIACS',
            'gcn.classic.text.INTEGRAL_WAKEUP',
            'gcn.classic.text.INTEGRAL_WEAK',
#            'gcn.classic.text.IPN_POS',
            'gcn.classic.text.IPN_RAW',
#            'gcn.classic.text.IPN_SEG',
#            'gcn.classic.text.LVC_COUNTERPART',
#            'gcn.classic.text.LVC_EARLY_WARNING',
            'gcn.classic.text.LVC_INITIAL',
            'gcn.classic.text.LVC_PRELIMINARY',
            'gcn.classic.text.LVC_RETRACTION',
#            'gcn.classic.text.LVC_TEST',
#            'gcn.classic.text.LVC_UPDATE',
            'gcn.classic.text.MAXI_KNOWN',
            'gcn.classic.text.MAXI_TEST',
            'gcn.classic.text.MAXI_UNKNOWN',
            'gcn.classic.text.SWIFT_ACTUAL_POINTDIR',
            #'gcn.classic.text.SWIFT_BAT_ALARM_LONG',
            #'gcn.classic.text.SWIFT_BAT_ALARM_SHORT',
            #'gcn.classic.text.SWIFT_BAT_GRB_ALERT',
            'gcn.classic.text.SWIFT_BAT_GRB_LC',
#            'gcn.classic.text.SWIFT_BAT_GRB_LC_PROC',
            'gcn.classic.text.SWIFT_BAT_GRB_POS_ACK',
            #'gcn.classic.text.SWIFT_BAT_GRB_POS_NACK',
            'gcn.classic.text.SWIFT_BAT_GRB_POS_TEST',
#            'gcn.classic.text.SWIFT_BAT_KNOWN_SRC',
#            'gcn.classic.text.SWIFT_BAT_MONITOR',
            'gcn.classic.text.SWIFT_BAT_QL_POS',
            'gcn.classic.text.SWIFT_BAT_SCALEDMAP',
#            'gcn.classic.text.SWIFT_BAT_SLEW_POS',
#            'gcn.classic.text.SWIFT_BAT_SUB_THRESHOLD',
#            'gcn.classic.text.SWIFT_BAT_SUBSUB',
            'gcn.classic.text.SWIFT_BAT_TRANS',
            'gcn.classic.text.SWIFT_FOM_OBS',
#            'gcn.classic.text.SWIFT_FOM_PPT_ARG_ERR',
#            'gcn.classic.text.SWIFT_FOM_SAFE_POINT',
#            'gcn.classic.text.SWIFT_FOM_SLEW_ABORT',
            'gcn.classic.text.SWIFT_POINTDIR',
            'gcn.classic.text.SWIFT_SC_SLEW',
            'gcn.classic.text.SWIFT_TOO_FOM',
            'gcn.classic.text.SWIFT_TOO_SC_SLEW',
            'gcn.classic.text.SWIFT_UVOT_DBURST',
            'gcn.classic.text.SWIFT_UVOT_DBURST_PROC',
            'gcn.classic.text.SWIFT_UVOT_EMERGENCY',
            'gcn.classic.text.SWIFT_UVOT_FCHART',
            'gcn.classic.text.SWIFT_UVOT_FCHART_PROC',
            'gcn.classic.text.SWIFT_UVOT_POS',
            'gcn.classic.text.SWIFT_UVOT_POS_NACK',
            'gcn.classic.text.SWIFT_XRT_CENTROID',
#            'gcn.classic.text.SWIFT_XRT_EMERGENCY',
            'gcn.classic.text.SWIFT_XRT_IMAGE',
            'gcn.classic.text.SWIFT_XRT_IMAGE_PROC',
            'gcn.classic.text.SWIFT_XRT_LC',
            'gcn.classic.text.SWIFT_XRT_POSITION',
            'gcn.classic.text.SWIFT_XRT_SPECTRUM',
            'gcn.classic.text.SWIFT_XRT_SPECTRUM_PROC',
            'gcn.classic.text.SWIFT_XRT_SPER',
            'gcn.classic.text.SWIFT_XRT_SPER_PROC',
            'gcn.classic.text.SWIFT_XRT_THRESHPIX',
            'gcn.classic.text.SWIFT_XRT_THRESHPIX_PROC',
#            'gcn.classic.text.AAVSO',
            #'gcn.classic.text.ALEXIS_SRC',
#            'gcn.classic.text.BRAD_COORDS',
#            'gcn.classic.text.CBAT',
            'gcn.classic.text.COINCIDENCE',
#            'gcn.classic.text.COMPTEL_SRC',
#            'gcn.classic.text.DOW_TOD',
            'gcn.classic.text.GRB_CNTRPART',
#            'gcn.classic.text.GRB_COORDS',
#            'gcn.classic.text.GRB_FINAL',
#            'gcn.classic.text.GWHEN_COINC',
            'gcn.classic.text.HAWC_BURST_MONITOR',
#            'gcn.classic.text.HUNTS_SRC',
            'gcn.classic.text.KONUS_LC',
#            'gcn.classic.text.MAXBC',
#            'gcn.classic.text.MILAGRO_POS',
#            'gcn.classic.text.MOA',
#            'gcn.classic.text.OGLE',
#            'gcn.classic.text.SIMBADNED',
            'gcn.classic.text.SK_SN',
            'gcn.classic.text.SNEWS',
#            'gcn.classic.text.SUZAKU_LC',
            'gcn.classic.text.TEST_COORDS']
        self.consumer.subscribe(self.subscribe_list)
