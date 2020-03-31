# Basic stuff
import logging
import logging.config
import sys
import time

# Local stuff : IndiClient
from helper.IndiClient import IndiClient

# Local stuff : Mount
from Observatory.IndiScopeController import IndiScopeController

#Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord

if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')

    # test indi client
    #indi_client_config = 
    #indiCli = IndiClient(config=config)
    #indiCli.connect()

    config = {
        "port": "/dev/ttyUSB0",
        "controller_name": "Arduino",
        "indi_client": dict(indi_host = "192.168.0.33",
                            indi_port = 7624) }

    # Now test Mount
    controller = IndiScopeController(
        config=config,
        connect_on_create=True)

    delay_sec = 5
    #print("Switching on flat panel")
    #controller.switch_on_flat_panel()
    #time.sleep(delay_sec)
    #controller.switch_off_flat_panel()
    #print("Switching on scope fan")
    #controller.switch_on_scope_fan()
    #time.sleep(delay_sec)
    #controller.switch_off_scope_fan()
    #print("Switching on scope dew heater")
    #controller.switch_on_scope_dew_heater()
    #time.sleep(delay_sec)
    #controller.switch_off_scope_dew_heater()
    #print("Switching on corrector dew heater")
    #controller.switch_on_corrector_dew_heater()
    #time.sleep(delay_sec)
    #controller.switch_off_corrector_dew_heater()
    #print("Switching on finder dew heater")
    #controller.switch_on_finder_dew_heater()
    #time.sleep(delay_sec)
    #controller.switch_off_finder_dew_heater()
    #print("Switching on camera")
    #controller.switch_on_camera()
    #time.sleep(delay_sec)
    #controller.switch_off_camera()
    print("Switching on main mount")
    controller.switch_on_mount()
    time.sleep(delay_sec)
    controller.switch_off_mount()
    print("Opening up main scope dustcap")
    controller.open_scope_dustcap()
    time.sleep(delay_sec)
    controller.close_scope_dustcap()
    print("Opening up finder dustcap")
    controller.open_finder_dustcap()
    time.sleep(delay_sec)
    controller.close_finder_dustcap()
    time.sleep(delay_sec)

