class Speaker(object):
    def __init__(self, event_queue):
        self.namespace='ai.dueros.device_interface.speaker_controller'

    def AdjustVolume(self):
        pass

    def VolumeChanged(self):
        pass

    def SetMute(self):
        pass

    def MuteChanged(self):
        pass

    @property
    def context(self):
        return {
            "header": {
                "namespace": self.namespace,
                "name": "VolumeState"
            },
            "payload": {
                "volume": 50,
                "muted": False
            }
        }
