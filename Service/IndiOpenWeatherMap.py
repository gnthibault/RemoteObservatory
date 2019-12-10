# Generic stuff
import json

#Local stuff
from Base.Base import Base
from helper.IndiDevice import IndiDevice

class IndiOpenWeatherMap(Base):
    """

    """

    def __init__(self, logger=None, config=None,
                 connect_on_create=True):
        logger = logger or logging.getLogger(__name__)

        if config is None:
            config = dict(
                service_name="OpenWeatherMap",
                key_path="/var/RemoteObservatory/keys.json",
                indi_client=dict(
                    indi_host="localhost",
                    indi_port="7624"
                ))

        logger.debug(f"Indi OpenWeatherMap service, name is: "
                     f"{config['service_name']}")

        # device related intialization
        IndiDevice.__init__(self, device_name=config['service_name'],
                                  indi_client_config=config["indi_client"])
        if connect_on_create:
            self.initialize()

        # Finished configuring
        self.logger.debug('Indi Weather service configured successfully')

    def initialize(self, config):
        self.connect()
        with open(config["key_path"]) as json_file:  
            data = json.load(json_file)
            self.key = data['OpenWeatherMap']

    def __str__(self):
        return f"Weather service: {self.device_name}"

    def __repr__(self):
        return self.__str__()        # Get key from json
        
