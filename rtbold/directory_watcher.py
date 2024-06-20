import os
import glob
import shutil
import logging
import pydicom
import time
from pubsub import pub
from pathlib import Path
from pydicom.errors import InvalidDicomError
from watchdog.observers.polling import PollingObserver
from watchdog.events import PatternMatchingEventHandler
from rtbold.consumer import Consumer

logger = logging.getLogger('directory_watcher')


class DirectoryWatcher:
    def __init__(self, directory):
        self._directory = directory
        self._observer = PollingObserver(timeout=1)
        self._observer.schedule(
            DirectoryHandler(ignore_directories=False),
            directory
        )

    def start(self):
        logger.info(f'starting watchdog directory observer on {self._directory}')
        self._observer.start()
      

    def join(self):
        self._observer.join()

class DirectoryHandler(PatternMatchingEventHandler):
	def __init__(self, *args, **kwargs):
		self._consumer = None
		super().__init__(*args, **kwargs)

	def on_created(self, event):
		if event.is_directory:
			logger.debug(f'on_created called on {event.src_path}')
			if self._consumer:
				self._consumer.stop()
			self._consumer = Consumer(Path(event.src_path))
			self._consumer.start()


