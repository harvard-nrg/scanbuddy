import time
import math
import json
import logging

logger = logging.getLogger('processor')

class Processor:
    def __init__(self):
        self._emit_every = 100
        self._instances = list()

    def listener(self, ds, path):
        instance = ds.InstanceNumber
        index = instance - 1
        currlen = len(self._instances)
        pad = instance - currlen
        if pad > 0:
            self.pad(pad)
        self._instances[index] = path
        logger.debug('array after insertion')
        logger.debug(json.dumps(self._instances, indent=2))
        todo = self.volreg_tasks(index)

    def volreg_tasks(self, index):
        a = index
        b = max(0, index - 1)
        volreg = [(a, b)]
        try:
            if self._instances[index + 1]:
                volreg.append((index + 1, index))
        except IndexError:
            pass
        logger.debug('indexes to run volreg')
        logger.debug(json.dumps(volreg, indent=2))
        return volreg

    def pad(self, n):
        for i in range(n):
            self._instances.append(None)
        logger.debug(f'array after padding')
        logger.debug(json.dumps(self._instances, indent=2))
