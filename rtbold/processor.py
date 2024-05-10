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
        self._counter = 0
        self._pending = 0
        self._emit_every = 2

    def listener(self, ds, path):
        index = ds.InstanceNumber - 1
        currlen = len(self._instances)
        pad = (index + 1) - currlen
        if pad > 0:
            self.pad(pad)
        self._instances[index] = {
            'path': path, 
            'volreg': None
        }
        self._pending -= 1
        logger.debug(f'after insertion ({self._pending} pending)')
        logger.debug(json.dumps(self._instances, indent=2))

        tasks = self.check_volreg(index)
        logger.debug('volreg tasks')
        logger.debug(json.dumps(tasks, indent=2))
        pub.sendMessage('volreg', tasks=tasks)
        self._counter += len(tasks)
        logger.debug(f'after volreg ({self._pending} pending)')
        logger.debug(json.dumps(self._instances, indent=2))

        if self._pending == 0 and self._counter > self._emit_every:
            num_instances = len(self._instances)
            logger.debug(f'publishing message to topic=plot with {num_instances} instances')
            pub.sendMessage('plot', instances=self._instances)

    def check_volreg(self, index):
        tasks = list()
        current = self._instances[index]

        # run volreg on current relative to parent
        i = max(0, index - 1)
        parent = self._instances[i]
        if parent:
            tasks.append((current, parent))

        # check if child index has been waiting for current
        i = index + 1
        try:
            child = self._instances[i]
            if child and not child['volreg']:
                tasks.append((child, current))
        except IndexError:
            pass
        
        return tasks
        
    def pad(self, n):
        for i in range(n):
            self._pending += 1
            self._instances.append(None)
        logger.debug(f'array after padding')
        logger.debug(json.dumps(self._instances, indent=2))

