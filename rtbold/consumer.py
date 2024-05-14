import os
from pathlib import Path
import shutil
import logging
import pydicom
from pydicom.errors import InvalidDicomError

from pubsub import pub
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

logger = logging.getLogger('consumer')

class Consumer:
    def __init__(self, directory):
        self._directory = directory
        self._observer = PollingObserver(timeout=1)
        self._observer.schedule(
            DicomHandler(ignore_directories=True),
            directory
        )

    def start(self):
        logger.info('starting watchdog observer')
        self._directory.mkdir(parents=True, exist_ok=True)
        self._observer.start()

    def join(self):
        self._observer.join()

class DicomHandler(PatternMatchingEventHandler):
    def on_created(self, event):
        path = Path(event.src_path)
        try:
            ds = pydicom.dcmread(path, stop_before_pixels=True)
            self.check_series(ds, path)
            path = self.construct_path(path, ds)
            logger.info(f'publishing message to topic=incoming with ds={path}')
            pub.sendMessage('incoming', ds=ds, path=path)
        except InvalidDicomError as e:
            logger.info(f'not a dicom file {path}')
        except FileNotFoundError as e:
            pass
        except Exception as e:
            logger.info(f'An unexpected error occurred: {e}')

    def check_series(self, ds, old_path):
        if not hasattr(self, 'first_dcm_series'):
            logger.info(f'found first series instance uid {ds.SeriesInstanceUID}')
            self.first_dcm_series = ds.SeriesInstanceUID
            return

        if self.first_dcm_series != ds.SeriesInstanceUID:
            logger.info(f'found new series instance uid: {ds.SeriesInstanceUID}')
            self.trigger_reset(ds, old_path)
            self.first_dcm_series = ds.SeriesInstanceUID

    def trigger_reset(self, ds, old_path):
        study_name = ds.StudyInstanceUID
        series_name = self.first_dcm_series
        dicom_parent = old_path.parent
        new_path_no_dicom = Path.joinpath(dicom_parent, study_name, series_name)
        logger.info(f'path to remove: {new_path_no_dicom}')
        shutil.rmtree(new_path_no_dicom)
        pub.sendMessage('reset')

    def construct_path(self, old_path, ds):
        study_name = ds.StudyInstanceUID
        series_name = ds.SeriesInstanceUID
        dicom_filename = old_path.name
        dicom_parent = old_path.parent

        new_path_no_dicom = Path.joinpath(dicom_parent, study_name, series_name)

        logger.info(f'moving file from {old_path} to {new_path_no_dicom}')

        os.makedirs(new_path_no_dicom, exist_ok=True)

        try:
            shutil.move(old_path, new_path_no_dicom)
        except shutil.Error:
            pass
        
        new_path_with_dicom = Path.joinpath(dicom_parent, study_name, series_name, dicom_filename)

        return str(new_path_with_dicom)
