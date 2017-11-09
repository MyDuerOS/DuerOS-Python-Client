# coding:utf-8
import time
from app.framework.player.aec_player.player import Player

URL = 'http://yinyueshiting.baidu.com/data2/music/31e2c3833449a76c94327b47ebf0637d/551729523/551729523.mp3?xcode=1aa6ee0550da1b5a43e6e1d8249fc792'
player = Player()


def test_play():
    player.play(URL)


if __name__ == "__main__":
    test_play()

    while True:
        time.sleep(1)
