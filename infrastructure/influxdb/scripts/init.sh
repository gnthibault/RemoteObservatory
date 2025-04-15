#!/bin/sh
# you might need to chmod +x this script

set -e
influx bucket create --name system --retention 52w || true #do not fail if bucket already exist