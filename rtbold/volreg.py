import json
import logging
import random

logger = logging.getLogger('registration')

class VolReg:
    def listener(self, tasks):
        for task in tasks:
            task[0]['volreg'] = self.mock()

    def mock(self):
        return [
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0)
        ]

