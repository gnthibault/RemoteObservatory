#!/bin/bash
#cd ~/projects/indi/build/libindi
#indiserver -vvv indi_simulator_ccd indi_simulator_guide indi_simulator_telescope indi_simulator_focus indi_simulator_wheel indi_simulator_weather #indi_openweathermap_weather
indiserver indi_simulator_ccd indi_simulator_guide indi_simulator_telescope indi_simulator_focus indi_simulator_wheel indi_simulator_weather
#cd -

#indi_getprop "Weather Simulator.WEATHER_CONTROL.Precip"
#indi_setprop -n "Weather Simulator.WEATHER_CONTROL.Precip=0"
#indi_setprop -n "Weather Simulator.WEATHER_UPDATE.PERIOD=1"
