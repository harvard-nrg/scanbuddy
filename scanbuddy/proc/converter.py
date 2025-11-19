import os
import re
import glob
import json
import time
import random
import pydicom
import logging
import subprocess
import numpy as np
from pubsub import pub
from retry import retry
from pathlib import Path
from subprocess import CalledProcessError

logger = logging.getLogger(__name__)

class Converter:
    def __init__(self, mock=False, debug=False):
        self._mock = mock
        self._debug = debug

    def run(self, instance, modality, instance_num):
        self.run_dcm2niix(instance['path'], instance_num, modality)
        self.insert_array(instance)


    @retry((CalledProcessError), delay=.1, max_delay=1.0, tries=5)
    def run_dcm2niix(self, dicom, num, modality):

        out_dir = os.sep.join(dicom.split(os.sep)[:-1])

        dcm2niix_cmd = [
           'dcm2niix',
           '-b', 'y',
           '-s', 'y',
           '-f', f'{modality}_{num}',
           '-o', out_dir,
           dicom
        ]
        cmdstr = json.dumps(dcm2niix_cmd, indent=2)
        logger.debug(f'running dcm2niix: {cmdstr}')

        output = subprocess.check_output(dcm2niix_cmd, stderr=subprocess.STDOUT, text=True)

        logger.debug(f'dcm2niix output: {output}')

        self._nii_file = self.get_nii_file(output)

        if not self._nii_file:
            logger.critical(f'could not find converted nifti file for {dicom}')

    def insert_array(self, instance):
        instance['nii_path'] = self._nii_file

    def get_nii_file(self, output):
        for line in output.splitlines():
            match = re.search(r'Convert 1 DICOM as (/\S+)', line)
            if match:
                if os.path.isfile(str(match.group(1)) + '.nii'):
                    return str(match.group(1)) + '.nii'
                elif os.path.isfile(str(match.group(1)) + '.nii.gz'):
                    str(match.group(1)) + '.nii.gz'

