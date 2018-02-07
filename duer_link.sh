#!/bin/sh

ifconfig | grep wlan0
if [ $? != "0" ]; then
	modprobe -r brcmfmac
	modprobe brcmfmac
fi

WORK_PATH="${PWD}"
export PYTHONPATH=${WORK_PATH}:${PYTHONPATH}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${WORK_PATH}/app/framework/duerLink/

python ./app/duer_link.py
