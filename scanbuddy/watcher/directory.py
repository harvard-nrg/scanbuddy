import time
import logging
from pathlib import Path
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from scanbuddy.watcher.dicom import DicomWatcher

logger = logging.getLogger(__name__)

class DirectoryWatcher:
    def __init__(self, directory):
        self._directory = directory
        self._observer = PollingObserver(timeout=1)
        self._observer.schedule(
            DirectoryHandler(),
            directory
        )

    def start(self):
        logger.info(f'starting directory watcher on {self._directory}')
        self._observer.start()

    def join(self):
        self._observer.join()

class DirectoryHandler(FileSystemEventHandler):
	def __init__(self, *args, **kwargs):
		self._dicomwatcher = None
		super().__init__(*args, **kwargs)

	def on_created(self, event):
		if event.is_directory:
			logger.debug(f'on_created fired on {event.src_path}')
			if self._dicomwatcher:
				self._dicomwatcher.stop()
			self._dicomwatcher = DicomWatcher(Path(event.src_path))
			self._dicomwatcher.start()


