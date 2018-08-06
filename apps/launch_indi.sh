#!/bin/bash
cd ~/projects/indi/build/libindi
indiserver indi_simulator_ccd indi_simulator_telescope indi_simulator_focus indi_simulator_wheel 
cd -
