# Generic stuff
import logging
import sys

# The class to play with
import time

from Observatory.IndiDomeController import IndiDomeController

if __name__ == '__main__':

    # test indi client
    config = dict(
        dome_name="Dome Simulator",
        dome_movement_timeout_s=600,
        indi_client=dict(
            indi_host="localhost",
            indi_port=7624)
    )
    # Instanciate Dome
    dome = IndiDomeController(config=config)
    print(f"Check if dome is parked: {dome.is_parked}")
    print("Now unparking")
    # dome.unpark()
    # print(f"Check if dome is parked: {dome.is_parked}")
    # print(f"Check if dome is opened: {dome.is_open}")
    # print("Now opening")
    # dome.open()
    # print(f"Check if dome is opened: {dome.is_open}")
    # print("Now closing")
    # dome.close()
    # print(f"Check if dome is opened: {dome.is_open}")
    # print("Now parking")
    # dome.park()
    # print(f"Check if dome is parked: {dome.is_parked}")

    # Then play with dynamic position
    dome.park()
    print(f" Checking current dome position before open {dome.get_dome_position()}")
    h_name = "MY_VECTOR_HANDLER"
    dome.register_vector_handler_to_client(
        vector_name="ABS_DOME_POSITION",
        handler_name=h_name,
        callback=lambda x: print(f" RECEIVED VALUE: {x}")
    )
    time.sleep(5)
    # Play with Kstars client for instance
    dome.unregister_vector_handler_to_client(
        vector_name="ABS_DOME_POSITION",
        handler_name=h_name,
    )
    dome.indi_client.stop()