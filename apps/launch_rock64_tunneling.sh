#!/bin/bash

ssh -L 7624:localhost:7624 gnthibault@192.168.0.176 -N
ssh -L 8624:localhost:8624 gnthibault@192.168.0.176 -N
