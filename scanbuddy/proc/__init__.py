import os
import sys
import pdb
import time
import math
import json
import shutil
import psutil
import logging
import datetime
import threading
import numpy as np
from pubsub import pub
from pathlib import Path

logger = logging.getLogger(__name__)

class Processor:
    def __init__(self, config, debug_display=False):
        pub.subscribe(self.listener, 'parent-proc')
        self._config=config

    def listener(self, ds, path, modality):
        logger.info(f'parent proc received message for {path}')
        logger.info(f'publishing to {modality}-proc topic')
        pub.sendMessage(f'{modality}-proc', ds=ds, path=path, modality=modality)

