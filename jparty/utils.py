import simpleaudio as sa
from threading import Thread
import os
import sys

class SongPlayer(object):
    def __init__(self):
        super().__init__()
        self.__wave_obj = sa.WaveObject.from_wave_file('/Users/stuart/Desktop/JParty/jparty/data/song.wav')
        self.__play_obj = None
        self.__repeating = False
        self.__repeat_thread = None

    @property
    def is_playing():
        return self.__play_obj.is_repeating()

    def play(self, repeat=False):
        self.__repeating = repeat
        self.__play_obj = self.__wave_obj.play()
        if repeat:
            self.__repeat_thread = Thread(target = self.__repeat)
            self.__repeat_thread.start()

    def stop(self):
        self.__repeating = False
        self.__play_obj.stop()

    def __repeat(self):
        while True:
            self.__play_obj.wait_done()
            if not self.__repeating:
                break
            self.__play_obj = self.__wave_obj.play()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        print("USING MEIPASS")
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, 'data', relative_path)
