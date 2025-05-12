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
from sortedcontainers import SortedDict
from scanbuddy.proc.snr import SNR

logger = logging.getLogger(__name__)

class LocalizerProcessor:
    def __init__(self, config, debug_display=False):
        self._config = config
        pub.subscribe(self.listener, 'localizer-proc')


    def listener(self, ds, path, modality):
        logger.info('inside of the localizer-proc topic')
        pub.sendMessage('params', ds=ds, modality=modality)