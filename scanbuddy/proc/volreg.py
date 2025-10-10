import os
import sys
import glob
import json
import time
import random
import pydicom
import logging
import subprocess
import numpy as np
import nibabel as nib
from pubsub import pub
from retry import retry
from pathlib import Path
from subprocess import CalledProcessError

logger = logging.getLogger(__name__)

class VolReg:
    def __init__(self, mock=False, debug=False):
        self._mock = mock
        self._debug = debug
        self._dcm1_instance_num = None
        self._dcm2_instance_num = None
        pub.subscribe(self.listener, 'volreg')

    def listener(self, tasks, modality):
        '''
        In the following example, there are two tasks (most of the time there will be only 1)
             - dicom.2.dcm should be registered to dicom.1.dcm and the 6 moco params should be put into the 'volreg' attribute for dicom.2.dcm
             - dicom.3.dcm should be registered to dicom.2.dcm and the 6 moco params should be put into the 'volreg' attribute for dicom.3.dcm
        '''
        logger.debug('received tasks for volume registration')
        logger.debug(f'VOLREG TASKS: {json.dumps(tasks, indent=2)}')
        self.tasks = tasks
        self.modality = modality
        if not self.tasks:
            return 

        if self._mock:
            for task in self.tasks:
                task[0]['volreg'] = self.mock()
            return

        self.run()

    def run(self):
        self.get_num_tasks()

        '''
        iterate through each task 
        run 3dvolreg
        insert array into task volreg key-value pair
        '''
        for task_idx in range(self.num_tasks):
            if self.check_dicoms(task_idx):
                continue

            start = time.time()

            nii1, nii2 = self.get_niis(task_idx)

            logger.debug(f'nii1: {nii1}, nii2: {nii2}')

            arr = self.run_volreg(nii1, nii2)

            logger.info(f'volreg array from registering volume {self._dcm2_instance_num} to volume {self._dcm1_instance_num}: {arr}')

            self.insert_array(arr, task_idx)

            elapsed = time.time() - start

            logger.info(f'processing took {elapsed} seconds')


    def get_num_tasks(self):
        self.num_tasks = len(self.tasks)

    def get_niis(self, task_idx):
        logger.debug(f'VOLREG TASKS: {self.tasks}')
        nii_1 = self.tasks[task_idx][1]['nii_path']
        nii_2 = self.tasks[task_idx][0]['nii_path']
        return nii_1, nii_2

    def insert_array(self, arr, task_idx):
        self.tasks[task_idx][0]['volreg'] = arr

    def run_volreg(self, nii_1, nii_2):
        outdir = str(Path(nii_1).parent)
        mocopar = os.path.join(outdir, f'moco.par')
        cmd = [
            '3dvolreg',
            '-base', nii_1,
            '-linear',
            '-1Dfile', mocopar,
            '-x_thresh', '10',
            '-rot_thresh', '10',
            '-nomaxdisp',
            '-prefix', 'NULL',
            nii_2
        ]

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logger.error(f"3dvolreg failed: {e.output.decode()}")

        arr = np.loadtxt(mocopar)

        arr = list(arr)

        return arr

    def check_dicoms(self, task_idx):
        if self.tasks[task_idx][1]['path'] == self.tasks[task_idx][0]['path']:
            logger.warning(f'the two input dicom files are the same. registering {os.path.basename(self.tasks[task_idx][1]["path"])} to itself will yield 0s')
            self.insert_array([0, 0, 0, 0, 0, 0], task_idx)
            return True
        else:
            self._dcm1_instance_num = int(pydicom.dcmread(self.tasks[task_idx][1]['path'], force=True, stop_before_pixels=True).InstanceNumber)
            self._dcm2_instance_num = int(pydicom.dcmread(self.tasks[task_idx][0]['path'], force=True, stop_before_pixels=True).InstanceNumber)
            return False

    def mock(self):
        return [
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0)
        ]



