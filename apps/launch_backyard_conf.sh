#!/bin/bash
# run ssh -L 8080:192.168.1.2:80 192.168.0.29; and the connect http://localhost:8080/ to access gemini interface, default conf is udp 11110 or tcp 4030 login is admin with no passwd
# edit, only udp conf works
# you can also play with canon dslr / do a check with rm -rf ./test.cr2 && gphoto2 --capture-image-and-download --filename "test.cr2"
indiserver indi_lx200gemini indi_canon_ccd indi_asi_ccd


# To tunnel connections to remote host
# ssh -L 8624:192.168.8.247:8624 192.168.0.176
# ssh -L 7624:192.168.8.247:7624 192.168.0.176

# Another config also with ssh tunnel
# ssh -L 7625:127.0.0.1:7624 192.168.8.247
# ssh -L 8624:127.0.0.1:8624 192.168.8.247
# ssh -L 4400:127.0.0.1:4400 192.168.8.247

# export REMOTE_OBSERVATORY_CONFIG=config_backyard
# Other wise in simulation, you might want to set this variable
# export REMOTE_OBSERVATORY_IS_DARK=0
