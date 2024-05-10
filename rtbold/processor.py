import time
import math
import json
import logging
import numpy as np
from pubsub import pub

logger = logging.getLogger('processor')

class Processor:
    def __init__(self):
        self._instances = list()

    def listener(self, ds, path):
        instance = ds.InstanceNumber
        index = instance - 1
        currlen = len(self._instances)
        pad = instance - currlen
        if pad > 0:
            self.pad(pad)
        self._instances[index] = {
            'path': path, 
            'volreg': None
        }
        logger.debug('array after insertion')
        logger.debug(json.dumps(self._instances, indent=2))
        tasks = self.check_volreg(index)
        pub.sendMessage('volreg', tasks=tasks)

    def check_volreg(self, index):
        tasks = list()

        current = self._instances[index]

        # need to run volreg on current index relative to parent index
        i = max(0, index - 1)
        parent = self._instances[i]
        if parent:
            tasks.append((current, parent))

        # check if child index has been waiting for the current index
        i = index + 1
        try:
            child = self._instances[i]
            if not child['volreg']:
                tasks.append((child, current))
        except IndexError:
            pass
        
        return tasks
        
    def pad(self, n):
        for i in range(n):
            self._instances.append(None)
        logger.debug(f'array after padding')
        logger.debug(json.dumps(self._instances, indent=2))
