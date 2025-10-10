import os
import sys
import time
import json
import shutil
import logging
import numpy as np
import nibabel as nib
from pubsub import pub
from pathlib import Path
from sortedcontainers import SortedDict
from scanbuddy.proc.converter import Converter

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

    def listener(self, ds, path, modality):
        logger.info('inside of the vnav-proc topic')
        key = int(ds.InstanceNumber)
        self._instances[key] = {
            'path': path,
            'volreg': None,
            'nii_path': None
        }
        logger.debug('current state of instances')
        logger.debug(json.dumps(self._instances, default=list, indent=2))

        logger.info('instantiating and running converter')
        converter = Converter()
        converter.run(self._instances[key], modality, key)

        tasks = self.check_volreg(key)

        self.unmosaic_vnav([self._instances[key]['nii_path'], self._instances[key]['nii_path']])

        logger.debug('publishing message to volreg topic with the following tasks')
        logger.debug(json.dumps(tasks, indent=2))
        pub.sendMessage('volreg', tasks=tasks, modality=modality)
        logger.debug(f'after volreg')
        logger.debug(f'publishing message to params topic')
        pub.sendMessage('params', ds=ds, modality=modality)

        logger.debug(json.dumps(self._instances, indent=2))
        project = ds.get('StudyDescription', '[STUDY]')
        session = ds.get('PatientID', '[PATIENT]')
        scandesc = ds.get('SeriesDescription', '[SERIES]')
        scannum = ds.get('SeriesNumber', '[NUMBER]')
        subtitle_string = f'{project} • {session} • {scandesc} • {scannum}'
        try:
            num_vols = ds[(0x0020, 0x0105)].value
        except KeyError:
            logger.info('Could not determine total number of volumes')
            num_vols = 5000
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

    def unmosaic_vnav(self, nii_list):
        for file in nii_list:
            nii = nib.load(file)
            img = nii.get_fdata()
            aff = nii.affine
            hdr = nii.header        
            if img.ndim == 3 and img.shape[2] == 1:
                img = img[:, :, 0]
            elif img.ndim == 2:
                pass
            else:
                logger.debug(f"Unexpected input shape: {img.shape}")
                continue
            out_shape = (32, 32, 32)
            unmosaic = np.zeros(out_shape, dtype=img.dtype)
            count = 0
            for row in range(6):
                for col in range(6):
                    if count >= 32:
                        break
                    x1 = col * 32
                    y1 = row * 32
                    tile = img[x1:x1+32, y1:y1+32]
                    # In Siemens mosaic, each tile is a different slice and needs to go in the 3rd (z) dimension
                    unmosaic[:, :, count] = tile.T  # need .T to go from x/y order to row/column order
                    count += 1          
            new_nii = nib.Nifti1Image(unmosaic, aff, hdr)
            nib.save(new_nii, file)

