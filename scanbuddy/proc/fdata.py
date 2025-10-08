import os
import sys
import pdb
import glob
import json
import time
import shutil
import random
import logging
import pydicom
import subprocess
import numpy as np
import nibabel as nib
from pubsub import pub
import collections as c
from pathlib import Path

logger = logging.getLogger(__name__)

class ExtractFdata:
    def __init__(self):
        pub.subscribe(self.listener, 'fdata')


    def do(self, nii_path, tasks):
        logger.info('received tasks for fdata extraction')
        self.snr_tasks = tasks
        self._nii_path = nii_path

        self.run()

    def listener(self, nii_path, tasks):
        logger.info('received tasks for fdata extraction')
        self.snr_tasks = tasks
        self._nii_path = nii_path

        self.run()

    def run(self):
        self.get_num_tasks()

        start = time.time()

        dcm = self.read_dicoms(self._num_tasks-1)

        instance_num = int(dcm.InstanceNumber)

        logger.info(f'extracting fdata for volume {instance_num}')
        data_array = self.get_nii_array()

        self.insert_snr(data_array, self.snr_tasks[0], None)

        self.clean_dir(instance_num)

        elapsed = time.time() - start

        logger.info(f'extracting fdata from volume {instance_num} took {elapsed} seconds')

    def get_nii_array(self):
        return nib.load(self._nii_path).get_fdata()


    def insert_snr(self, slice_means, task, mask):
        logger.debug(f'state of tasks when inserting {self.snr_tasks}')
        x, y, z = slice_means.shape
        data_array_4d = slice_means.reshape(x, y, z, 1)
        task['fdata_array'] = data_array_4d

    def read_dicoms(self, last_idx):
        logger.debug(f'state of tasks when reading dicom: {self.snr_tasks}')
        dcm1 = self.snr_tasks[0]['path']

        ds1 = pydicom.dcmread(dcm1, force=True, stop_before_pixels=True)

        return ds1

    def clean_dir(self, instance_num):
        if instance_num == 1:
            return
        for file in glob.glob(f'{os.path.dirname(self._nii_path)}/*{instance_num-2}.json'):
            os.remove(file)
        for file in glob.glob(f'{os.path.dirname(self._nii_path)}/*{instance_num-2}.nii'):
            os.remove(file)

    def get_num_tasks(self):
        self._num_tasks = len(self.snr_tasks)

