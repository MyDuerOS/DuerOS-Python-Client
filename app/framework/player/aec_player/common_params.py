# coding:utf-8
###########################################################
# ProcessMessage Type
# 默认值
PROCESS_MESSAGE_TPYE_DEFAULT = 0

# 打断
PROCESS_MESSAGE_TPYE_INTERRUPT = 1000
# 恢复
PROCESS_MESSAGE_TPYE_RESUME = 1001
PROCESS_MESSAGE_TPYE_MUTE_CTL = 1002
# Speech 字段播放
PROCESS_MESSAGE_TPYE_SPEECH = 1003
# SpeechSynthesizer
# directives下面的SpeechSynthesizer
PROCESS_MESSAGE_TPYE_SPEECH_SYNTHESIZER = 1004
# SpeechSynthesizer停止
PROCESS_MESSAGE_TPYE_SPEECH_SYNTHESIZER_STOP = 1005
# AudioPlayer
PROCESS_MESSAGE_TPYE_AUDIO_PRE_DECODE = 1006
# 播放有声资源
PROCESS_MESSAGE_TPYE_AUDIO_PLAY = 1007
PROCESS_MESSAGE_TPYE_AUDIO_STOP = 1008
# Alerts
# 设置提醒
PROCESS_MESSAGE_TPYE_SET_ALERT = 1009
# 删除提醒
PROCESS_MESSAGE_TPYE_DELETE_ALERT = 1010
# Timer
# 提醒计时器指令
PROCESS_MESSAGE_TPYE_REMIND_UPDATE = 1011
# 提醒计时器指令
PROCESS_MESSAGE_TPYE_REMIND_STOP = 1012
# 修改音色
PROCESS_MESSAGE_TPYE_CHANGE_TONE = 1013

################################################
# http://wiki.baidu.com/pages/viewpage.action?pageId=268099035
SPEECH_TYPE = "type"
SPEECH_CONTENT = "content"
ID = "id"
LOGID = "logid";
START_PLAY_TIME = "start_play_time"
MESSAGE_ID = "message_id"
TOKEN = "token"
OFFSET_MS = "offset_ms"
FORMAT = "stream_format"
ALARM_ID = "alarm_id"
TONE = "tone"
ALERTS = "alerts"
AP_NAME = "ap_name"
PLAYER_COUNT = "player_count"
NETWORK_CONFIG_FAILED = "network_config_failed"
CUID = "cuid"

PLAY_BEHAVIOR = "play_behavior"
URL = "url"
PROCESS_REPORT_INTERVAL_MS = "progress_report_interval_ms"

###############################3
TYPE_STRING = 1
TYPE_INT = 2
TYPE_BUFFER = 3
