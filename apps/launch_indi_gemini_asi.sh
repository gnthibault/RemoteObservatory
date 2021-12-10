#!/bin/bash
# run ssh -L 8080:192.168.1.2:80 192.168.0.29; and the connect http://localhost:8080/ to access gemini interface, default conf is udp 11110 or tcp 4030 login is admin with no passwd
# edit, only udp conf works
indiserver indi_lx200gemini indi_asi_ccd
