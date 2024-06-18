import os
import glob
import shutil
import logging
import pydicom
from pubsub import pub
from pathlib import Path
from pydicom.errors import InvalidDicomError
from watchdog.observers.polling import PollingObserver
from watchdog.events import PatternMatchingEventHandler

logger = logging.getLogger('directory_watcher')


class Consumer:
    def __init__(self, directory):
        self._directory = directory
        self._observer = PollingObserver(timeout=1)