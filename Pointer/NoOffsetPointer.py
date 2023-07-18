# Generic
from time import sleep
import threading

# Local
from Base.Base import Base


class NoOffsetPointer(Base):
    def __init__(self, config=None):
        super().__init__()

    def offset_points(self, *args, **kwargs):
        pointing_event = threading.Event()
        pointing_status = [True]
        pointing_event.set()
        return pointing_event, pointing_status
