# 通过"小度小度"来触发唤醒
WORK_PATH="${PWD}"
export PYTHONPATH=${WORK_PATH}:${PYTHONPATH}

python ./app/wakeup_trigger_main.py
