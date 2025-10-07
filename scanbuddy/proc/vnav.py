import os
import sys
import pdb
import time
import math
import json
import shutil
import psutil
import logging
import datetime
import threading
import numpy as np
from pubsub import pub
from pathlib import Path
from sortedcontainers import SortedDict
from scanbuddy.proc.fdata import ExtractFdata

logger = logging.getLogger(__name__)

class VnavProcessor:
    def __init__(self, config, debug_display=False):
        self.reset()
        self._config = config
        self._debug_display = self._config.find_one('$.app.debug_display', default=debug_display)
        pub.subscribe(self.reset, 'reset')
        pub.subscribe(self.listener, 'vnav-proc')

    def reset(self):
        self._instances = SortedDict()
        logger.debug('received message to reset')

    def getsize(self, obj):
        size_in_bytes = sys.getsizeof(obj)
        return size_in_bytes

    def get_size_mask(self):
        total_size = 0
        for key in self._slice_means:
            mask = self._slice_means[key]['mask']
            if mask is not None:
                mb = mask.nbytes / (1024**2)
                shape = mask.shape
                logger.info(f'mask for instance {key} is dtype={mask.dtype}, shape={shape}, size={mb} MB')
                total_size += mask.nbytes
        return total_size

    def listener(self, ds, path, modality):
        logger.info('inside of the vnav-proc topic')
        key = int(ds.InstanceNumber)
        self._instances[key] = {
            'path': path,
            'volreg': None,
            'nii_path': None
        }
        logger.info('current state of instances')
        logger.info(json.dumps(self._instances, default=list, indent=2))

        tasks = self.check_volreg(key)
        logger.info('publishing message to volreg topic with the following tasks')
        logger.info(json.dumps(tasks, indent=2))
        pub.sendMessage('volreg', tasks=tasks, modality=modality)
        logger.info(f'after volreg')
        logger.debug(f'publishing message to params topic')
        pub.sendMessage('params', ds=ds, modality=modality)

        logger.debug(json.dumps(self._instances, indent=2))
        project = ds.get('StudyDescription', '[STUDY]')
        session = ds.get('PatientID', '[PATIENT]')
        scandesc = ds.get('SeriesDescription', '[SERIES]')
        scannum = ds.get('SeriesNumber', '[NUMBER]')
        subtitle_string = f'{project} • {session} • {scandesc} • {scannum}'
        num_vols = ds[(0x0020, 0x0105)].value
        if self._debug_display:
            pub.sendMessage('plot', instances=self._instances, subtitle_string=subtitle_string)
        elif num_vols == key:
            pub.sendMessage('plot', instances=self._instances, subtitle_string=subtitle_string)

        if key == num_vols:
            time.sleep(2)
            data_path = os.path.dirname(self._instances[key]['path'])
            logger.info(f'removing dicom dir: {data_path}')
            path_obj = Path(data_path)
            files = [f for f in os.listdir(path_obj.parent.absolute()) if os.path.isfile(f)]
            logger.info(f'dangling files: {files}')
            logger.info(f'removing {len(os.listdir(path_obj.parent.absolute())) - 1} dangling files')
            shutil.rmtree(data_path)
            self.make_arrays_zero()


    def check_volreg(self, key):
        tasks = list()
        current = self._instances[key]

        i = self._instances.bisect_left(key)

        try:
            left_index = max(0, i - 1)
            left = self._instances.values()[left_index]
            logger.debug(f'to the left of {current["path"]} is {left["path"]}')
            tasks.append((current, left))
        except IndexError:
            pass

        try:
            right_index = i + 1
            right = self._instances.values()[right_index]
            logger.debug(f'to the right of {current["path"]} is {right["path"]}')
            tasks.append((right, current))
        except IndexError:
            pass

        return tasks

    def get_new_key(self, instance_number):
        return ((instance_number - 2) // 4) + 1

    def check_echo(self, ds):
        '''
        This method will check for the string 'TE' in 
        the siemens private data tag. If 'TE' exists in that
        tag it means the scan is multi-echo. If it is multi-echo
        we are only interested in the second echo or 'TE2'
        Return False if 'TE2' is not found. Return True if 
        'TE2' is found or no reference to 'TE' is found
        '''
        sequence = ds[(0x5200, 0x9230)][0]
        siemens_private_tag = sequence[(0x0021, 0x11fe)][0]
        scan_string = str(siemens_private_tag[(0x0021, 0x1175)].value)
        if 'TE2' in scan_string:
            logger.info('multi-echo scan detected')
            logger.info(f'using 2nd echo time: {self.get_echo_time(ds)}')
            return True, True
        elif 'TE' not in scan_string:
            logger.info('single echo scan detected')
            return False, False
        else:
            logger.info('multi-echo scan found, wrong echo time, deleting file and moving on')
            return True, False

    def get_echo_time(self, ds):
        sequence = ds[(0x5200, 0x9230)][0]
        echo_sequence_item = sequence[(0x0018, 0x9114)][0]
        return echo_sequence_item[(0x0018, 0x9082)].value

