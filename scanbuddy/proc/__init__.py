import os
import logging
from pubsub import pub
from scanbuddy.proc.bold import BoldProcessor
from scanbuddy.proc.localizer import LocalizerProcessor
from scanbuddy.proc.vnav import VnavProcessor

logger = logging.getLogger(__name__)

class Processor:
    MAPPING = {
        'bold': BoldProcessor,
        'localizer': LocalizerProcessor,
        'vnav': VnavProcessor
    }

    def __init__(self, config, debug_display=False):
        pub.subscribe(self.listener, 'parent-proc')
        self._config = config
        self._processors = dict()
        self.start_processors()

    def listener(self, ds, path, modality):
        logger.info(f'parent proc received message for {path}')
        logger.info(f'publishing to {modality}-proc topic')
        pub.sendMessage(f'{modality}-proc', ds=ds, path=path, modality=modality)

    def get_modalities(self):
        modalities = self._config.find_one('$.modalities', dict())
        if not modalities:
            raise ProcessorError(f'no modalities were found in configuration '
                f'file {self._config._file}')
        modalities = set(map(str.lower, modalities.keys()))
        supported = set(Processor.MAPPING.keys())
        intersection = supported.intersection(modalities)
        if not supported.intersection(modalities):
            raise ProcessorError(f'config file contains {modalities} modalities, '
                f' but the only supported modalities are {supported}')
        return modalities

    def start_processors(self):
        for modality in self.get_modalities():
            if modality in Processor.MAPPING:
                class_ = Processor.MAPPING[modality]
                instance = class_(self._config)
                logger.debug(f'instantiated processor for {modality}')
                self._processors[modality] = instance
            else:
                logger.error(f'no processor mapping was found for modality "{modality}"')

class ProcessorError(Exception):
    pass

