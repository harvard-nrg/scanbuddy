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

logger = logging.getLogger('directory_watcher')


class Directory_Watcher:
    def __init__(self, directory):
        self._directory = directory
        self._observer = PollingObserver(timeout=1)


    def on_created(self, event):
        if event.is_directory:
            logger.info(f"New directory {event.src_path} has been created.")
            return event.src_path

    def start(self):
        event_handler = PatternMatchingEventHandler(patterns=["*/"], ignore_directories=False, ignore_patterns=None, case_sensitive=True)
        event_handler.on_created = self.on_created

        self._observer.schedule(event_handler, self._directory, recursive=True)
        self._observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._observer.stop()
            self._observer.join()