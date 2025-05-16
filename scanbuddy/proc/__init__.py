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
from scanbuddy.proc.bold import BoldProcessor
from scanbuddy.proc.localizer import LocalizerProcessor

logger = logging.getLogger(__name__)

class Processor:
    def __init__(self, config, debug_display=False):
        pub.subscribe(self.listener, 'parent-proc')
        self._config=config
        self.start_processors()

    def listener(self, ds, path, modality):
        logger.info(f'parent proc received message for {path}')
        logger.info(f'publishing to {modality}-proc topic')
        pub.sendMessage(f'{modality}-proc', ds=ds, path=path, modality=modality)

    def start_processors(self):
        self._modalities = self._config.find_one('$.modalities', dict())    
        for modality in self._modalities:
            if modality in self.mapping:
                module_path, class_name = self.mapping[modality]
                try:
                    # Dynamically import the module and class
                    mod = __import__(module_path, fromlist=[class_name])
                    processor_class = getattr(mod, class_name)
                    processor_instance = processor_class(self._config)
                    self.processor_instances[modality] = processor_instance
                    logger.info(f'Initialized {class_name} for {modality} modality')
                except ImportError:
                    logger.error(f'Could not import module for modality "{modality}": {module_path}.{class_name}')
                except AttributeError:
                    logger.error(f'Class "{class_name}" not found in module "{module_path}"')
            else:
                logger.warning(f'No processor mapping found for modality "{modality}"(i.e. that modality is not supported or there is a typo somewhere)') 

    processor_instances = {}            

    mapping = {
        'bold': ('scanbuddy.proc.bold', 'BoldProcessor'),
        'localizer': ('scanbuddy.proc.localizer', 'LocalizerProcessor'),
    }