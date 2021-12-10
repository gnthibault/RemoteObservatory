#!/bin/bash
# run ssh -L 8080:192.168.1.2:80 192.168.0.29; and the connect http://localhost:8080/ to access gemini interface, default conf is udp 11110 or tcp 4030 login is admin with no passwd
# edit, only udp conf works
# you can also play with canon dslr / do a check with rm -rf ./test.cr2 && gphoto2 --capture-image-and-download --filename "test.cr2"
indiserver indi_lx200gemini indi_canon_ccd indi_asi_ccd
