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
import nilearn.image
import nibabel as nib
from pubsub import pub
import collections as c
from pathlib import Path

logger = logging.getLogger(__name__)

class SNR:
    def __init__(self):
        pub.subscribe(self.listener, 'snr')


    def listener(self, tasks):
        logger.info('received tasks for snr calculation')
        self.snr_tasks = tasks
        #self._prev_snr = prev_snr

        self.run()

    def run(self):
        self.get_num_tasks()

        start = time.time()

        dcm = self.read_dicoms(self._num_tasks-1)

        logger.info(f'calculating slice means for volume {int(dcm.InstanceNumber)}')

        snr_nii = self.run_dcm2niix(dcm)

        #slice_means, mask = self.calculate_snr(dcm, snr_nii)

        data_array, mask_threshold = self.calculate_snr(dcm, snr_nii)

        self.insert_snr(data_array, self.snr_tasks[0], mask_threshold)

        self.clean_dir()

        elapsed = time.time() - start

        logger.info(f'snr processing took {elapsed} seconds')


    def calculate_snr(self, first_dcm, snr_nii):
        '''
        dcm 1 has already had an snr calculation run for it,
        so that value will be used as part of the running average.
        Calculate the snr for dcm2 and then add that to dcm 1 and
        take the average
        '''

        mask_threshold = self.get_mask_threshold(first_dcm)

        mask, data_array = self.generate_mask(mask_threshold, snr_nii)

        #current_slice_means = self.slice_based_stats(data_array, mask)

        return data_array, mask_threshold

        '''
        if self._prev_snr == 0.0:
            running_snr = round(current_snr, 2)

        else:
            running_snr = float(round((current_snr + self._prev_snr) / 2, 2))
            logger.info(f'value of calculated snr: {current_snr}')
            logger.info(f'value of previously calculated snr: {self._prev_snr}')
            logger.info(f'value of running snr: {running_snr}')

        return running_snr
        '''

    def insert_snr(self, slice_means, task, mask):
        logger.debug(f'state of tasks when inserting {self.snr_tasks}')
        x, y, z = slice_means.shape
        data_array_4d = slice_means.reshape(x, y, z, 1)
        task['slice_means'] = data_array_4d
        task['mask_threshold'] = mask


    def run_dcm2niix(self, dicom):

        self._outdir = Path(os.path.dirname(self.snr_tasks[0]['path']), 'tmp_snr_dir')
        os.makedirs(self._outdir, exist_ok=True)

        for idx, dicom in enumerate(self.snr_tasks):
            shutil.copy(self.snr_tasks[idx]['path'], self._outdir)

        dcm2niix_cmd = [
           'dcm2niix',
           '-b', 'y',
           '-s', 'y'
           '-f', f'snr_calc',
           '-o', self._outdir,
           self._outdir
        ]

        output = subprocess.check_output(dcm2niix_cmd, stderr=subprocess.STDOUT)

        logger.debug(f'dcm2niix output: {output}')

        nii_file = self.find_nii(self._outdir)

        return nii_file


    def find_nii(self, directory):
        for file in os.listdir(directory):
            if f'tmp_snr_dir' in file and file.endswith('.nii'):
                return Path(directory, file)

    def generate_mask(self, mask_threshold, nii):
        nii_array = nib.load(nii).get_fdata()
        binary_mask = nii_array <= mask_threshold
        return binary_mask, nii_array
        '''
        keeping this code for posterity. maybe one day we will 
        want a pre-masked array

        thresholded_nii = nilearn.image.threshold_img(nii, mask_threshold)
        output_file_path = Path(os.path.dirname(nii), 'thresholded_img.nii')
        nib.save(thresholded_nii, output_file_path)
        masked_data_array = nib.load(output_file_path).get_fdata()
        return (masked_data_array)
        '''     

    def get_mask_threshold(self, ds):
        bits_stored = ds.get('BitsStored', None)
        receive_coil = self.find_coil(ds)

        if bits_stored == 12:
            logger.debug(f'scan has "{bits_stored}" bits and receive coil "{receive_coil}", setting mask threshold to 150.0')
            return 150.0
        if bits_stored == 16:
            if receive_coil in ['Head_32']:
                logger.debug(f'scan has "{bits_stored}" bits and receive coil "{receive_coil}", setting mask threshold to 1500.0')
                return 1500.0
            if receive_coil in ['Head_64', 'HeadNeck_64']:
                logger.debug(f'scan has "{bits_stored}" bits and receive coil "{receive_coil}", setting mask threshold to 3000.0')
                return 3000.0
        raise MaskThresholdError(f'unexpected bits stored "{bits_stored}" + receive coil "{receive_coil}"')

    def slice_based_stats(self, dat, mask):
        '''
        Compute slice-based statistics  

        :param dat: Data matrix
        :type dat: numpy.array
        :param mask: Binary mask
        :type mask: numpy.array
        :returns: Tuple of ['summary', 'mean', 'std', 'snr']
        :rtype: collections.namedtuple
        '''
        # get the length of each dimension into named variables
        _,_,z = dat.shape
        # create slice means for every volume independently
        slice_means =np.zeros(z)
        volume = np.ma.array(dat[:,:,:], mask=mask[:,:,:], fill_value=0.0)
        for j in range(z):
            # Get the j'th slice
            slice_ij = volume[:, :, j]
            # Compute the mean of the slice, automatically handling mask
            x = slice_ij.mean()
            # Store the mean; if x is masked, it will return the fill_value by default
            slice_means[j] = x if not np.ma.is_masked(x) else 0.0

        return slice_means

        # we are breaking this function into two parts for now. The rest of this
        # this function will be in the proc __init__.py file
        '''

        # compute the raw and weighted means, stds, and snrs
        slice_wmean_sum = 0
        slice_wstd_sum = 0
        slice_wsnr_sum = 0
        total_masked_voxels = 0
        slice_summary = []

        for i,volume_means in iter(slice_means.items()):
            # cast volume means to a numpy array to make life easier
            volume_means = np.array(volume_means)
            # compute the raw slice mean across time
            mean = volume_means.mean()
            # compute the raw slice std across time
            std = volume_means.std(ddof=1)
            if std == 0:
                snr = 0
            else:
                snr = mean / std

            # store raw statistics within the slice summary
            #slice_summary.append(SliceRow(i + 1, mean, std, snr))
            # count the number of un-masked voxels for the i'th slice
            num_masked_voxels = (mask[:,:,i] == False).sum()
            # keep a running sum of the number of un-masked voxels
            total_masked_voxels += num_masked_voxels
            # keep running sums of the weighted mean, std, and snr
            slice_wmean_sum += volume_means.mean() * num_masked_voxels
            slice_wstd_sum += volume_means.std(ddof=1) * num_masked_voxels
            slice_wsnr_sum += snr * num_masked_voxels
        # compute the weighted slice-based mean, standard deviation, and snr
        wm = slice_wmean_sum / total_masked_voxels
        ws = slice_wstd_sum / total_masked_voxels
        wsnr = slice_wsnr_sum / total_masked_voxels
        
        return wsnr

        '''

    def read_dicoms(self, last_idx):
        logger.debug(f'state of tasks when reading dicom: {self.snr_tasks}')
        dcm1 = self.snr_tasks[0]['path']
        #dcm2 = self.snr_tasks[last_idx]['path']

        ds1 = pydicom.dcmread(dcm1, force=True, stop_before_pixels=True)
        #ds2 = pydicom.dcmread(dcm2, force=True, stop_before_pixels=True)

        return ds1

    def find_coil(self, ds):
        seq = ds[(0x5200, 0x9229)][0]
        seq = seq[(0x0018, 0x9042)][0]
        return seq[(0x0018, 0x1250)].value

    def clean_dir(self):
        for file in glob.glob(f'{self._outdir}/*.json'):
            os.remove(file)
        for file in glob.glob(f'{self._outdir}/*.nii'):
            os.remove(file)
        for file in glob.glob(f'{self._outdir}/*.dcm'):
            os.remove(file)

    def get_num_tasks(self):
        self._num_tasks = len(self.snr_tasks)


class MaskThresholdError(Exception):
    pass

