import time
import logging
from pathlib import Path
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from scanbuddy.watcher.dicom import DicomWatcher

logger = logging.getLogger(__name__)

class DirectoryWatcher:
    def __init__(self, directory, modality):
        self._directory = directory
        self._modality = modality
        self._observer = PollingObserver(timeout=1)
        self._observer.schedule(
            DirectoryHandler(modality),
            directory,
        )

    def _check_dir(self):
        if not self._directory.exists():
            raise DirectoryWatcherError(f'No such file or directory: {self._directory}')
        try:
            test = Path(self._directory, 'write.test')
            test.touch()
            test.unlink()
        except Exception as e:
            logger.error(e)
            raise DirectoryWatcherError(f'could not write test file {test}')

    def start(self):
        logger.info(f'starting directory watcher on {self._directory}')
        self._check_dir()
        self._observer.start()

    def join(self):
        self._observer.join()

class DirectoryHandler(FileSystemEventHandler):
    def __init__(self, modality, *args, **kwargs):
        self._dicomwatcher = None
        self._modality = modality
        super().__init__(*args, **kwargs)

    def on_created(self, event):
        if event.is_directory:
            logger.info(f'on_created fired on {event.src_path}')
            if self._dicomwatcher:
                logger.info('calling stop on dicomwatcher')
                self._dicomwatcher.stop()
            self._dicomwatcher = DicomWatcher(Path(event.src_path), self._modality)
            self._dicomwatcher.start()

class DirectoryWatcherError(Exception):
    pass
