import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import scanbuddy.config as config
from pygame import mixer

class Audio:
    def __init__(self):
        self._dir = os.path.dirname(__file__)
        self._has_audio = False
        if not config.no_sound:
            try:
                mixer.init()
                self._has_audio = True
            except:
                pass

    def chime(self):
        if not self._has_audio:
            return
        fname = os.path.join(self._dir, 'win98.mp3')
        mixer.music.load(fname)
        mixer.music.play()

