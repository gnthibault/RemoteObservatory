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
        "indi_server_fifo": "/tmp/INDI_FIFO",
        "indi_client": dict(indi_host = "192.168.0.34",
                            indi_port = 7624) }

    # Now test Mount
    controller = IndiScopeController(
        config=config,
        connect_on_create=True)

    delay_sec = 5
    print(f"Switching on flat panel {controller.status()}")
    controller.switch_on_flat_panel()
    print(f"{controller.status()}")
    time.sleep(delay_sec)
    controller.switch_off_flat_panel()
    print(f"Switching on scope fan {controller.status()}")
    controller.switch_on_scope_fan()
    print(f"{controller.status()}")
    time.sleep(delay_sec)
    controller.switch_off_scope_fan()
    print(f"Switching on scope dew heater {controller.status()}")
    controller.switch_on_scope_dew_heater()
    print(f"{controller.status()}")
    time.sleep(delay_sec)
    controller.switch_off_scope_dew_heater()
    print(f"Switching on corrector dew heater {controller.status()}")
    controller.switch_on_corrector_dew_heater()
    print(f"{controller.status()}")
    time.sleep(delay_sec)
    controller.switch_off_corrector_dew_heater()
    print(f"Switching on finder dew heater {controller.status()}")
    controller.switch_on_finder_dew_heater()
    print(f"{controller.status()}")
    time.sleep(delay_sec)
    controller.switch_off_finder_dew_heater()
    print(f"Switching on camera {controller.status()}")
    controller.switch_on_camera()
    print(f"{controller.status()}")
    time.sleep(delay_sec)
    controller.switch_off_camera()
    print(f"Switching on main mount {controller.status()}")
    controller.switch_on_mount()
    print(f"{controller.status()}")
    time.sleep(delay_sec)
    controller.switch_off_mount()
    print(f"Opening up main scope dustcap {controller.status()}")
    print(f"Before opening scope dustcap status: "
          f"{controller.get_switch('FINDER_SERVO_DUSTCAP_SWITCH')}")
    controller.open_finder_dustcap()
    print(f"{controller.status()}")
    time.sleep(delay_sec)
    print(f"After opening scope dustcap status: "
          f"{controller.get_switch('FINDER_SERVO_DUSTCAP_SWITCH')}")
    controller.close_finder_dustcap()
    print(f"After closing scope dustcap: "
          f"{controller.get_switch('FINDER_SERVO_DUSTCAP_SWITCH')}")
    print(f"{controller.status()}")
    print("Opening up finder dustcap")
    print(f"Before opening finder dustcap status: "
          f"{controller.get_switch('SCOPE_SERVO_DUSTCAP_SWITCH')}")
    controller.open_scope_dustcap()
    print(f"{controller.status()}")
    time.sleep(delay_sec)
    print(f"After opening finder dustcap status: "
          f"{controller.get_switch('SCOPE_SERVO_DUSTCAP_SWITCH')}")
    controller.close_scope_dustcap()
    print(f"After closing finder dustcap status: "
          f"{controller.get_switch('SCOPE_SERVO_DUSTCAP_SWITCH')}")
    print(f"{controller.status()}")
    time.sleep(delay_sec)

    #res = controller.get_switch("CAMERA_RELAY")
    #res = controller.device.getSwitch("CAMERA_RELAY")
    #print(res)
    #for i in res:
    #    print("======")
    #    print(i.name)
    #    print(i.s)

