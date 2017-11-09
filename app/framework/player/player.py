from app.framework.player.aec_player.player import Player as DevicePlayer


# from app.framework.player.default_player.player import Player as DevicePlayer

class Player(object):
    def __init__(self):
        self.player = DevicePlayer()

    def play(self, uri):
        self.player.play(uri)

    def stop(self):
        self.player.stop()

    def pause(self):
        self.player.pause()

    def resume(self):
        self.player.resume()

    def add_callback(self, name, callback):
        self.player.add_callback(name, callback)

    @property
    def duration(self):
        self.player.duration

    @property
    def position(self):
        self.player.position

    @property
    def state(self):
        self.player.state
