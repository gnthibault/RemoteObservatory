import PyIndi
import time

class Device:
    DEFAULT_TIMEOUT=30

    def __init__(self, name, indiClient):
      self.logger = logger or logging.getLogger(__name__)
  
      self.name = name
      self.indiClient = indiClient
      self.timeout = Device.DEFAULT_TIMEOUT

      # Ask indiClient for device
      self.__find_device()

    def __find_device(self):
      self.device = None
      while not self.device:
        self.device = self.indiClient.getDevice(self.name)

    def connect(self):
      if self.device.isConnected():
        return
      self.set_switch('CONNECTION', ['CONNECT'])

    def values(self, ctlName, ctlType):
      ''''''
      return dict(map(lambda c:\
        (c.name, c.value), self.getControl(ctlName, ctlType)))

    def switch_values(self, switch_name):
      return dict(map(lambda sw:\
        (sw.name, sw.s == PyIndi.ISS_ON), self.getControl(switch_name, 'switch')))

    def set_switch(self, name, on_switches = [], off_switches = [], sync = True, timeout=None):
      c = self.getControl(name, 'switch')
      if c.r == PyIndi.ISR_ATMOST1 or c.r == PyIndi.ISR_1OFMANY:
        on_switches = on_switches[0:1]
        off_switches = [s.name for s in c if s.name not in on_switches]
      for index in range(0, len(c)):
        c[index].s = PyIndi.ISS_ON if c[index].name in on_switches else PyIndi.ISS_OFF
      self.indiClient.sendNewSwitch(c)
      if sync:
        self.__waitCtlStatus(c, statuses=[PyIndi.IPS_IDLE, PyIndi.IPS_OK],\
          timeout=timeout)
      return c
        
    def setNumber(self, name, values, sync = True, timeout=None):
      c = self.getControl(name, 'number')
      for controlName, index in self.__mapIndices(c, values.keys()).items():
        c[index].value = values[controlName]
      self.indiClient.sendNewNumber(c)
      if sync:
        self.__wait_for_ctl_statuses(c, timeout=timeout)
      return c

    def setText(self, controlName, values, sync=True, timeout=None):
      c = self.getControl(controlName, 'text')
      for controlName, index in self.__mapIndices(c, values.keys()).items():
        c[index].text = values[control_name]
      self.indiClient.sendNewText(c)
      if sync:
        self.__waitCtlStatus(c, timeout=timeout)
      return c

    def __waitCtlStatus(self, ctl,
      statuses=[PyIndi.IPS_OK, PyIndi.IPS_IDLE], timeout=None):
      '''Wait for the specified control to take one of the statuses in param'''

      started = time.time()
      if timeout is None:
        timeout = self.timeout
        while ctl.s not in statuses:
          if 0 < timeout < time.time() - started:
            self.logger.debug('IndiDevice: Timeout while waiting for control status '+\
              name+' of type '+ctlType+' for device '+self.name)
            raise RuntimeError('Timeout error while changing property {}'.format(ctl.name))
         time.sleep(0.01)

    def __mapIndices(self, ctl, values):
      ''' return dict of name-index of ctl that are in values'''
      result = {}
      for i, c in enumerate(ctl):
        if c.name in values:
          result[c.name] = i
      return result

    def getControl(self, name, ctlType, timeout=None):
      ''' Return the value corresponding to the given control'''
      ctl = None
      attr = {
        'number': 'getNumber',
        'switch': 'getSwitch',
        'text': 'getText',
        'blob': 'getBlob'
      }[ctlType]
      if timeout is None:
        timeout = self.timeout
      started = time.time()
      while not(ctl):
        ctl = getattr(self.device, attr)(name)
        if not ctl and 0 < timeout < time.time() - started:
          self.logger.debug('IndiDevice: Tiemout while waiting for control '+\
            name+' of type '+ctlType+' for device '+self.name)
          raise RuntimeError('Timeout finding control {}'.format(name))
        time.sleep(0.01)
      return ctl

    def has_control(self, name, ctl_type):
      try:
        self.getControl(name, ctl_type, timeout=0.1)
        return True
      except:
        return False

