#!/bin/bash
sextractor ./20190110T213958.fits -c ./default.sex ; psfex ./test.cat -c ./default.psfex
