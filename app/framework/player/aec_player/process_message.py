import app.framework.player.aec_player.common_params as common_params


class ProcessMessage(object):
    def __init__(self):
        self.type = common_params.PROCESS_MESSAGE_TPYE_DEFAULT
        self.map_int = {}
        self.map_str = {}
        self.send_len = ''
        self.send_data = ''

    def set_int_params(self, key, val):
        self.map_int[key] = val

    def set_str_params(self, key, val):
        self.map_str[key] = val
