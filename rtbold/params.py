import os
import logging
from pubsub import pub

logger = logging.getLogger('params')

ACCEPTABLE = [
    ('Head_32', 'HEA;HEP')
]

class Params:
    def __init__(self, broker=None):
        self._checked = False
        self._broker = broker
        pub.subscribe(self.listener, 'params')
        pub.subscribe(self.reset, 'reset')
    
    def reset(self):
        self._checked = False

    def listener(self, ds):
        key = ds.SeriesInstanceUID
        if self._checked:
            logger.info(f'already checked instance from series {ds.SeriesNumber}')
            return
        coil = self.getcoil(ds)
        elements = self.getcoilelements(ds)
        message = f'detected unacceptable coil elements "{elements}" for coil "{coil}"'
        if (coil, elements) not in ACCEPTABLE:
            logger.warning(message)
            self._broker.publish('scanbuddy_messages', message)
        self._checked = True

    def getcoil(self, ds):
        seq = ds[(0x5200, 0x9229)][0]
        seq = seq[(0x0018, 0x9042)][0]
        return seq[(0x0018, 0x1250)].value
   
    def getcoilelements(self, ds):
        seq = ds[(0x5200, 0x9230)][0]
        seq = seq[(0x0021, 0x11fe)][0]
        return seq[(0x0021, 0x114f)].value

