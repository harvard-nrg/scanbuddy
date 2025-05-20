import logging
from pubsub import pub

logger = logging.getLogger(__name__)

class LocalizerProcessor:
    def __init__(self, config, debug_display=False):
        self._config = config
        pub.subscribe(self.listener, 'localizer-proc')


    def listener(self, ds, path, modality):
        logger.info('inside of the localizer-proc topic')
        pub.sendMessage('params', ds=ds, modality=modality)