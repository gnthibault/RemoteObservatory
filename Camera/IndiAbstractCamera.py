# Basic stuff

# Local stuff
from Camera.AbstractCamera import AbstractCamera
from Camera.IndiCamera import IndiCamera

class IndiAbstractCamera(IndiCamera, AbstractCamera):
    def __init__(self, indiClient, configFileName=None, connectOnCreate=True,
                 primary=False, serv_time):

        # Parent initialization
        AbstractCamera.__init__(self, serv_time=serv_time, primary=primary)

        # device related intialization
        IndiCamera.__init__(self, indiClient=indiClient, logger=self.logger,
                           configFileName=configFileName,
                           connectOnCreate=connectOnCreate)

