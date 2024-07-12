import os
import glob
import time
import shutil
import logging
import pydicom
from pubsub import pub
from retry import retry
from pathlib import Path
from pydicom.errors import InvalidDicomError
from watchdog.observers.polling import PollingObserver
from watchdog.events import PatternMatchingEventHandler


logger = logging.getLogger()

class DicomWatcher:
    def __init__(self, directory):
        self._directory = directory
        self._observer = PollingObserver(timeout=.01)
        self._observer.schedule(
            DicomHandler(ignore_directories=True),
            directory
        )

    def start(self):
        logger.info(f'starting dicom watcher on {self._directory}')
        self._directory.mkdir(parents=True, exist_ok=True)
        self._observer.start()

    def join(self):
        self._observer.join()

    def stop(self):
        logger.info(f'stopping dicom watcher on {self._directory}')
        self._observer.stop()
        logger.debug(f'removing {self._directory}')
        shutil.rmtree(self._directory)

class DicomHandler(PatternMatchingEventHandler):
    def on_created(self, event):
        path = Path(event.src_path)
        try:
            self.file_size = -1
            if not path.exists():
                logger.info(f'file {path} no longer exists')
                return
            ds = self.read_dicom(path)
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
            logger.exception(e, exc_info=True)


    @retry((IOError, InvalidDicomError), delay=.01, backoff=1.5, max_delay=1.5, tries=10)
    def read_dicom(self, dicom):
        new_file_size = dicom.stat().st_size
        if self.file_size != new_file_size:
            self.file_size = new_file_size
            raise IOError
        return pydicom.dcmread(dicom, stop_before_pixels=True)

    def check_series(self, ds, old_path):
        if not hasattr(self, 'first_dcm_series'):
            logger.info(f'found first series instance uid {ds.SeriesInstanceUID}')
            self.first_dcm_series = ds.SeriesInstanceUID
            self.first_dcm_study = ds.StudyInstanceUID
            return

        if self.first_dcm_series != ds.SeriesInstanceUID:
            logger.info(f'found new series instance uid: {ds.SeriesInstanceUID}')
            self.trigger_reset(ds, old_path)
            self.first_dcm_series = ds.SeriesInstanceUID
            self.first_dcm_study = ds.StudyInstanceUID

    def trigger_reset(self, ds, old_path):
        study_name = self.first_dcm_study
        series_name = self.first_dcm_series
        dicom_parent = old_path.parent
        new_path_no_dicom = Path.joinpath(dicom_parent, study_name)#, series_name)
        logger.debug(f'path to remove: {new_path_no_dicom}')
        shutil.rmtree(new_path_no_dicom)
        self.clean_parent(dicom_parent)
        logger.debug('making it out of clean_parent method')
        pub.sendMessage('reset')

    def clean_parent(self, path):
        logger.debug(f'cleaning target dir: {path}')
        for file in glob.glob(f'{path}/*.dcm'):
            logger.debug(f'removing {file}')
            os.remove(file)

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
