import logging
import pydicom
from pydicom.errors import InvalidDicomError

from pubsub import pub
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

logger = logging.getLogger('consumer')

class Consumer:
    def __init__(self, directory):
        self._observer = PollingObserver(timeout=1)
        self._observer.schedule(DicomHandler(), directory)

    def start(self):
        logger.info('starting watchdog observer')
        self._observer.start()

    def join(self):
        self._observer.join()

class DicomHandler(FileSystemEventHandler):
    def on_created(self, event):
        path = event.src_path
        try:
            ds = pydicom.dcmread(path, stop_before_pixels=True)
            logger.info(f'publishing message to topic=incoming with ds={path}')
            pub.sendMessage('incoming', ds=ds, path=path)
        except InvalidDicomError as e:
            logger.info(f'not a dicom file {path}')

