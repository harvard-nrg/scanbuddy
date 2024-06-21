import time
import math
import json
import logging
import numpy as np
from pubsub import pub
from sortedcontainers import SortedDict

logger = logging.getLogger('processor')

class Processor:
    def __init__(self):
        self.reset()
        pub.subscribe(self.reset, 'reset')
        pub.subscribe(self.listener, 'incoming')

    def reset(self):
        self._instances = SortedDict()
        logger.debug('received message to reset')

    def listener(self, ds, path):
        key = int(ds.InstanceNumber)
        self._instances[key] = {
            'path': path,
            'volreg': None
        }
        logger.info('current state of instances')
        logger.debug(json.dumps(self._instances, default=list, indent=2))

        tasks = self.check_volreg(key)
        logger.debug('volreg tasks')
        logger.debug(json.dumps(tasks, indent=2))
        pub.sendMessage('volreg', tasks=tasks)

        logger.debug(f'after volreg')
        logger.debug(json.dumps(self._instances, indent=2))
        subtitle_string = " ".join([f'Project: {ds.StudyDescription}, ', f'Series: {ds.SeriesDescription}, ', str(f'Scan Number: {ds.SeriesNumber}')])
        pub.sendMessage('plot', instances=self._instances, subtitle_string=subtitle_string)

    def check_volreg(self, key):
        tasks = list()
        current = self._instances[key]

        # get numerical index of key O(log n)
        i = self._instances.bisect_left(key)

        # always register current node to left node
        try:
            left_index = max(0, i - 1)
            left = self._instances.values()[left_index]
            logger.debug(f'to the left of {current["path"]} is {left["path"]}')
            tasks.append((current, left))
        except IndexError:
            pass

        # if there is a right node, re-register to current node
        try:
            right_index = i + 1
            right = self._instances.values()[right_index]
            logger.debug(f'to the right of {current["path"]} is {right["path"]}')
            tasks.append((right, current))
        except IndexError:
            pass

        return tasks

