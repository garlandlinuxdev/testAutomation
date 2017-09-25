#!/bin/bash

BASEDIR="$( cd "$( dirname "$0" )" && pwd )"

python2.7 $BASEDIR
pip2.7 install importlib
pip2.7 install modbus_tk