#launches everything
sudo ifconfig eth0 192.168.1.1
LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH INDISKEL=conf_files/indi_driver_conf/scope_controller_sk.xml indiserver -v indi_duino indi_lx200gemini indi_canon_ccd indi_asi_ccd
