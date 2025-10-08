import os
import sys
import time
import shutil
import psutil
import logging
import pydicom
import threading
import subprocess
import numpy as np
import nibabel as nib
from pubsub import pub
import collections as c
from pathlib import Path
from sortedcontainers import SortedDict

logger = logging.getLogger(__name__)

class SNR:
    def __init__(self):
        pub.subscribe(self.listener, 'snr')
        self._debug_display = True

    def listener(self, key, snr_instances, ds):
        logger.info('received tasks for snr calculation')
        self._snr_instances = snr_instances
        self.run(key, ds)

    def do(self, key, snr_instances, ds):
        logger.info('received tasks for snr calculation')
        self._snr_instances = snr_instances
        self.run(key, ds)

    def run(self, key, ds):

        start = time.time()

        if key < 5:
            self._num_vols = ds[(0x0020, 0x0105)].value
            self._mask_threshold, self._decrement = self.get_mask_threshold(ds)
            x, y, self._z, _ = self._snr_instances[key]['fdata_array'].shape
            self._fdata_array = np.zeros((x, y, self._z, self._num_vols), dtype=np.float64)
            self._slice_intensity_means = np.zeros((self._z, self._num_vols), dtype=np.float64)

            logger.info(f'shape of zeros: {self._fdata_array.shape}')
            logger.info(f"shape of fdata array: {self._snr_instances[key]['fdata_array'].shape}")
        
        if key >= 5:
            # double check that necessary objects exist before calculating SNR
            if self._fdata_array is None:
                self._num_vols = ds[(0x0020, 0x0105)].value
                self._mask_threshold, self._decrement = self.get_mask_threshold(ds)
                x, y, self._z, _ = self._snr_instances[key]['fdata_array'].shape
                self._fdata_array = np.zeros((x, y, self._z, self._num_vols), dtype=np.float64)
                self._slice_intensity_means = np.zeros((self._z, self._num_vols), dtype=np.float64)

            insert_position = key - 5
            self._fdata_array[:, :, :, insert_position] = self._snr_instances[key]['fdata_array'].squeeze()
            self._snr_instances[key]['fdata_array'] = np.array([])
            logger.info(f'Current RAM usage: {round(psutil.virtual_memory().used / (1024 ** 3), 3)} GB')

        
        if key > 53 and (key % 4 == 0) and key < self._num_vols:
            logger.info('launching calculate and publish snr thread')

            #snr_thread = threading.Thread(target=self.calculate_and_publish_snr, args=(key,))
            #snr_thread.start()
            self.calculate_and_publish_snr(key)

        if key == self._num_vols:
            time.sleep(2)
            data_path = os.path.dirname(self._snr_instances[key]['path'])
            logger.info(f'removing dicom dir: {data_path}')
            path_obj = Path(data_path)
            files = [f for f in os.listdir(path_obj.parent.absolute()) if os.path.isfile(f)]
            logger.info(f'dangling files: {files}')
            logger.info(f'removing {len(os.listdir(path_obj.parent.absolute())) - 1} dangling files')
            shutil.rmtree(data_path)
            self.make_arrays_zero()

        elapsed = time.time() - start


    def read_dicoms(self, last_idx):
        logger.debug(f'state of tasks when reading dicom: {self.snr_tasks}')
        dcm1 = self.snr_tasks[0]['path']

        ds1 = pydicom.dcmread(dcm1, force=True, stop_before_pixels=True)

        return ds1

    def calculate_and_publish_snr(self, key):
        start = time.time()
        snr_metric = round(self.calc_snr(key), 2)
        elapsed = time.time() - start
        logger.info(f'snr calculation took {elapsed} seconds')
        logger.info(f'running snr metric: {snr_metric}')
        if np.isnan(snr_metric):
            logger.info(f'snr is a nan, decrementing mask threshold by {self._decrement}')
            self._mask_threshold = self._mask_threshold - self._decrement
            logger.info(f'new threshold: {self._mask_threshold}')
            self._slice_intensity_means = np.zeros( (self._z, self._num_vols) )
        else:
            if self._debug_display:
                pub.sendMessage('plot_snr', snr_metric=snr_metric) 
            elif key >= (self._num_vols - 6):
                pub.sendMessage('plot_snr', snr_metric=snr_metric) 

    def calc_snr(self, key):
        slice_intensity_means, slice_voxel_counts, data = self.get_mean_slice_intensities(key)

        non_zero_columns = ~np.all(slice_intensity_means == 0, axis=0)

        slice_intensity_means_2 = slice_intensity_means[:, non_zero_columns]

        slice_count = slice_intensity_means_2.shape[0]
        volume_count = slice_intensity_means_2.shape[1]

        
        slice_weighted_mean_mean = 0
        slice_weighted_stdev_mean = 0
        slice_weighted_snr_mean = 0
        slice_weighted_max_mean = 0
        slice_weighted_min_mean = 0
        outlier_count = 0
        total_voxel_count = 0

        for slice_idx in range(slice_count):
            slice_data         = slice_intensity_means_2[slice_idx]
            slice_voxel_count  = slice_voxel_counts[slice_idx]
            slice_mean         = slice_data.mean()
            slice_stdev        = slice_data.std(ddof=1)
            slice_snr          = slice_mean / slice_stdev

            slice_weighted_mean_mean   += (slice_mean * slice_voxel_count)
            slice_weighted_stdev_mean  += (slice_stdev * slice_voxel_count)
            slice_weighted_snr_mean    += (slice_snr * slice_voxel_count)

            total_voxel_count += slice_voxel_count

            logger.debug(f"Slice {slice_idx}: Mean={slice_mean}, StdDev={slice_stdev}, SNR={slice_snr}")
        
        return slice_weighted_snr_mean / total_voxel_count

    def get_mean_slice_intensities(self, key):
        
        data = self.generate_mask(key)

        mask = np.ma.getmask(data)
        dim_x, dim_y, dim_z, _ = data.shape

        dim_t = key - 4

        slice_voxel_counts = np.zeros( (dim_z), dtype='uint32' )
        slice_size = dim_x * dim_y

        for slice_idx in range(dim_z):
            slice_voxel_counts[slice_idx] = slice_size - mask[:,:,slice_idx,0].sum()

        zero_columns = np.where(np.all(self._slice_intensity_means[:,:dim_t] == 0, axis=0))[0].tolist()

        logger.info(f'volumes being calculated: {zero_columns}')


        if len(zero_columns) > 20:
            for volume_idx in range(dim_t):
                for slice_idx in range(dim_z):
                    slice_data = data[:,:,slice_idx,volume_idx]
                    self._slice_intensity_means[slice_idx,volume_idx] = slice_data.mean()

        else:

            for volume_idx in zero_columns:
                for slice_idx in range(dim_z):
                    slice_data = data[:,:,slice_idx,volume_idx]
                    slice_vol_mean = slice_data.mean()
                    self._slice_intensity_means[slice_idx,volume_idx] = slice_vol_mean

            if key == self._num_vols:
                start = time.time()
                differing_slices = self.find_mask_differences(key)
                logger.info(f'finding mask differences took {time.time() - start}')
                logger.info(f'recalculating slice means at the following slices: {differing_slices}')
                logger.info(f'total of {len(differing_slices)} new slices being computed')
                for volume_idx in range(dim_t):
                    for slice_idx in differing_slices:
                        slice_data = data[:,:,slice_idx,volume_idx]
                        slice_vol_mean = slice_data.mean()
                        self._slice_intensity_means[slice_idx,volume_idx] = slice_vol_mean

            elif key % 2 == 0: 
                #elif key % 6 == 0:
                logger.info(f'inside the even calculation')
                start = time.time()
                differing_slices = self.find_mask_differences(key)
                logger.info(f'finding mask differences took {time.time() - start}')
                logger.info(f'recalculating slice means at the following slices: {differing_slices}')
                logger.info(f'total of {len(differing_slices)} new slices being computed')
                for volume_idx in range(0, dim_t, 8):
                    for slice_idx in differing_slices:
                        slice_data = data[:,:,slice_idx,volume_idx]
                        slice_vol_mean = slice_data.mean()
                        self._slice_intensity_means[slice_idx,volume_idx] = slice_vol_mean

            else:
                #elif key % 5 == 0:
                logger.info(f'inside the odd calculation')
                start = time.time()
                differing_slices = self.find_mask_differences(key)
                logger.info(f'finding mask differences took {time.time() - start}')
                logger.info(f'recalculating slice means at the following slices: {differing_slices}')
                logger.info(f'total of {len(differing_slices)} new slices being computed')
                for volume_idx in range(5, dim_t, 8):
                    for slice_idx in differing_slices:
                        slice_data = data[:,:,slice_idx,volume_idx]
                        slice_vol_mean = slice_data.mean()
                        self._slice_intensity_means[slice_idx,volume_idx] = slice_vol_mean
        
        return self._slice_intensity_means[:, :dim_t], slice_voxel_counts, data

    def generate_mask(self, key):

        mean_data = np.mean(self._fdata_array[...,:key-4], axis=3)
        
        numpy_3d_mask = np.zeros(mean_data.shape, dtype=bool)
        
        to_mask = (mean_data <= self._mask_threshold)

        mask_lower_count = int(to_mask.sum())

        numpy_3d_mask = numpy_3d_mask | to_mask

        numpy_4d_mask = np.zeros(self._fdata_array[..., :key-4].shape, dtype=bool)

        numpy_4d_mask[numpy_3d_mask] = True

        masked_data = np.ma.masked_array(self._fdata_array[..., :key-4], mask=numpy_4d_mask)
    
        mask = np.ma.getmask(masked_data)

        self._snr_instances[key]['mask'] = mask

        mask = None
        
        return masked_data

    def find_mask_differences(self, key):
        num_old_vols = key - 8
        last_50 = num_old_vols - 50
        logger.info(f'looking for mask differences between {key} and {key - 4}')
        prev_mask = self._snr_instances[key - 4]['mask']
        current_mask = self._snr_instances[key]['mask']
        differences = prev_mask != current_mask[:,:,:,:num_old_vols]
        #differences = prev_mask[:,:,:,-50:] != current_mask[:,:,:,last_50:num_old_vols]
        diff_indices = np.where(differences)
        differing_slices = []
        for index in zip(*diff_indices):
            if int(index[2]) not in differing_slices:
                differing_slices.append(int(index[2]))
        logger.info(f'reclaim memory for instance {key - 4 } mask')
        self._snr_instances[key - 4]['mask'] = np.array([])
        return differing_slices


    def get_mask_threshold(self, ds):
        bits_stored = ds.get('BitsStored', None)
        receive_coil = self.find_coil(ds)

        if bits_stored == 12:
            logger.debug(f'scan has "{bits_stored}" bits and receive coil "{receive_coil}", setting mask threshold to 150.0')
            return 150.0, 10
        if bits_stored == 16:
            if receive_coil in ['Head_32']:
                logger.debug(f'scan has "{bits_stored}" bits and receive coil "{receive_coil}", setting mask threshold to 1500.0')
                return 1500.0, 100
            if receive_coil in ['Head_64', 'HeadNeck_64']:
                logger.debug(f'scan has "{bits_stored}" bits and receive coil "{receive_coil}", setting mask threshold to 3000.0')
                return 3000.0, 300
        raise MaskThresholdError(f'unexpected bits stored "{bits_stored}" + receive coil "{receive_coil}"')

    def find_coil(self, ds):
        seq = ds[(0x5200, 0x9229)][0]
        seq = seq[(0x0018, 0x9042)][0]
        return seq[(0x0018, 0x1250)].value

    def get_new_key(self, instance_number):
        return ((instance_number - 2) // 4) + 1

    def make_arrays_zero(self, moment='end'):
        if moment == 'end':
            logger.info('freeing up RAM from snr arrays')
        else:
            logger.debug('making sure snr arrays are deallocated')
        self._fdata_array = None
        self._slice_intensity_means = None
        self._snr_instances = SortedDict()
        logger.info(f'Final RAM usage: {round(psutil.virtual_memory().used / (1024 ** 3), 3)} GB')



