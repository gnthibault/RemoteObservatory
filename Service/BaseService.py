# Generic modules
import logging

# Local

class BaseService():
  """
    Define common stuff for services. Is mainly used for providing helpers for
    class that are needed by the Base.Base class, such that we avoid circular
    dependency
  """
  def __init__(self, logger=None):
      self.logger = logger or logging.getLogger(self.__class__.__name__)
