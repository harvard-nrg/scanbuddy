import os
import glob
import json
import time
import logging
import random
import pydicom
import subprocess
import numpy as np
from pubsub import pub
from pathlib import Path

logger = logging.getLogger(__name__)

class VolReg:
    def __init__(self, mock=False):
        self._mock = mock
        self._dcm1_instance_num = None
        self._dcm2_instance_num = None
        pub.subscribe(self.listener, 'volreg')

    def listener(self, tasks):
        '''
        In the following example, there are two tasks (most of the time there will be only 1)
             - dicom.2.dcm should be registered to dicom.1.dcm and the 6 moco params should be put into the 'volreg' attribute for dicom.2.dcm
             - dicom.3.dcm should be registered to dicom.2.dcm and the 6 moco params should be put into the 'volreg' attribute for dicom.3.dcm
        '''
        logger.info('received tasks for volume registration')
        logger.info(json.dumps(tasks, indent=2))
        self.tasks = tasks
        if not self.tasks:
            return 

        if self._mock:
            for task in self.tasks:
                task[0]['volreg'] = self.mock()
            return

        self.run()

    def run(self):
        self.get_num_tasks()

        #### iterate through each task, create a nii file, run 3dvolreg and insert array into task volreg key-value pair
        for task_idx in range(self.num_tasks):
            self.check_dicoms(task_idx)

            start = time.time()

            nii1, nii2, dcm1, dcm2 = self.create_niis(task_idx)

            arr = self.run_volreg(nii1, nii2, self.out_dir)

            #self.clean_dir(nii1, nii2, self.out_dir)

            logger.info(f'volreg array from registering volume {self._dcm2_instance_num} to volume {self._dcm1_instance_num}: {arr}')

            self.insert_array(arr, task_idx)

            elapsed = time.time() - start

            logger.info(f'processing took {elapsed} seconds')


    def get_num_tasks(self):
        self.num_tasks = len(self.tasks)

    def create_niis(self, task_idx):
        
        dcm1 = self.tasks[task_idx][1]['path']
        #nii1 = self.run_dcm2niix(dcm1, 1)
        self._dcm1_instance_num = int(pydicom.dcmread(dcm1, force=True, stop_before_pixels=True).InstanceNumber)
        nii1 = self.run_dcm2niix(dcm1, self._dcm1_instance_num)
        if self.tasks[task_idx][1]['nii_path'] is None:
            self.tasks[task_idx][1]['nii_path'] = nii1

        dcm2 = self.tasks[task_idx][0]['path']
        #nii2 = self.run_dcm2niix(dcm2, 2)
        self._dcm2_instance_num = int(pydicom.dcmread(dcm2, force=True, stop_before_pixels=True).InstanceNumber)
        nii2 = self.run_dcm2niix(dcm2, self._dcm2_instance_num)
        if self.tasks[task_idx][0]['nii_path'] is None:
            self.tasks[task_idx][0]['nii_path'] = nii2

        return nii1, nii2, dcm1, dcm2

    def insert_array(self, arr, task_idx):
        self.tasks[task_idx][0]['volreg'] = arr


    def run_dcm2niix(self, dicom, num):

        self.out_dir = os.sep.join(dicom.split(os.sep)[:-1])

        dcm2niix_cmd = [
           'dcm2niix',
           '-b', 'y',
           #'-z', 'y',
           '-s', 'y',
           '-f', f'bold_{num}',
           '-o', self.out_dir,
           dicom
        ]
        cmdstr = json.dumps(dcm2niix_cmd, indent=2)
        #logger.info(f'running {cmdstr}')

        output = subprocess.check_output(dcm2niix_cmd, stderr=subprocess.STDOUT)

        logger.debug(f'dcm2niix output: {output}')

        nii_file = self.find_nii(self.out_dir, num)

        return nii_file

    def run_volreg(self, nii_1, nii_2, outdir):
        mocopar = os.path.join(outdir, f'moco.par')
        maxdisp = os.path.join(outdir, f'maxdisp')
        cmd = [
            '3dvolreg',
            '-base', nii_1,
            '-linear',
            '-1Dfile', mocopar,
            #'-maxdisp1D', maxdisp,
            '-x_thresh', '10',
            '-rot_thresh', '10',
            '-nomaxdisp',
            '-prefix', 'NULL',
            nii_2
        ]

        _ = subprocess.check_output(cmd, stderr=subprocess.STDOUT)

        arr = np.loadtxt(mocopar)

        arr = list(arr)

        return arr

    def check_dicoms(self, task_idx):
        if self.tasks[task_idx][1]['path'] == self.tasks[task_idx][0]['path']:
            logger.warning(f'the two input dicom files are the same. registering {os.path.basename(self.tasks[task_idx][1]["path"])} to itself will yield 0s')
            return True
        else:
            return False

    def clean_dir(self, nii_1, nii_2, outdir):
        #os.remove(nii_1)
        #os.remove(nii_2)
        #os.remove(f'{outdir}/maxdisp_delt')
        #os.remove(f'{outdir}/maxdisp')
        os.remove(f'{outdir}/moco.par')
        for file in glob.glob(f'{outdir}/*.json'):
            os.remove(file)
        #for file in glob.glob(f'{outdir}/*.nii.gz'):
        for file in glob.glob(f'{outdir}/*.nii'):
            os.remove(file)


    def find_nii(self, directory, num):
        for file in os.listdir(directory):
            if f'bold_{num}' in file and file.endswith('.nii'):#file.endswith('.gz'):
                return os.path.join(directory, file)

    def mock(self):
        return [
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0)
        ]
