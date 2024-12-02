import os
import sys
import pdb
import time
import math
import json
import shutil
import logging
import datetime
import threading
import numpy as np
from pubsub import pub
from sortedcontainers import SortedDict

logger = logging.getLogger(__name__)

class Processor:
    def __init__(self):
        self.reset()
        pub.subscribe(self.reset, 'reset')
        pub.subscribe(self.listener, 'incoming')

    def reset(self):
        self._instances = SortedDict()
        self._slice_means = SortedDict()
        pub.sendMessage('plot_snr', snr_metric=str(0.0))
        logger.debug('received message to reset')

    def listener(self, ds, path):
        key = int(ds.InstanceNumber)
        self._instances[key] = {
            'path': path,
            'volreg': None,
            'nii_path': None
        }
        self._slice_means[key] = {
            'path': path,
            'slice_means': None,
            'mask_threshold': None,
            'mask': None
        }
        logger.debug('current state of instances')
        logger.debug(json.dumps(self._instances, default=list, indent=2))



        tasks = self.check_volreg(key)
        snr_tasks = self.check_snr(key)
        logger.debug('publishing message to volreg topic with the following tasks')
        logger.debug(json.dumps(tasks, indent=2))
        pub.sendMessage('volreg', tasks=tasks)
        logger.debug(f'publishing message to params topic')
        pub.sendMessage('params', ds=ds)
        logger.debug(f'publishing message to snr_fdata topic')
        logger.debug(f'snr task sorted dict: {snr_tasks}')
        pub.sendMessage('snr', nii_path=self._instances[key]['nii_path'], tasks=snr_tasks)
        logger.debug('after snr calculation')

        logger.debug(json.dumps(self._instances, indent=2))


        logger.debug(f'after volreg')
        logger.debug(json.dumps(self._instances, indent=2))
        project = ds.get('StudyDescription', '[STUDY]')
        session = ds.get('PatientID', '[PATIENT]')
        scandesc = ds.get('SeriesDescription', '[SERIES]')
        scannum = ds.get('SeriesNumber', '[NUMBER]')
        subtitle_string = f'{project} • {session} • {scandesc} • {scannum}'
        pub.sendMessage('plot', instances=self._instances, subtitle_string=subtitle_string)

        if key < 5:
            self._num_vols = ds[(0x0020, 0x0105)].value
            self._mask_threshold, self._decrement = self.get_mask_threshold(ds)
            x, y, self._z, _ = self._slice_means[key]['slice_means'].shape

            self._fdata_array = np.empty((x, y, self._z, self._num_vols))
            self._slice_intensity_means = np.zeros( (self._z, self._num_vols) )



            logger.info(f'shape of zeros: {self._fdata_array.shape}')
            logger.info(f'shape of first slice means: {self._slice_means[key]['slice_means'].shape}')

        if key >= 5:
            insert_position = key - 5
            self._fdata_array[:, :, :, insert_position] = self._slice_means[key]['slice_means'].squeeze()

        if key > 53 and (key % 4 == 0) and key < self._num_vols:
            logger.info('launching calculate and publish snr thread')

            snr_thread = threading.Thread(target=self.calculate_and_publish_snr, args=(key,))
            snr_thread.start()

        if key == self._num_vols:
            time.sleep(2)
            data_path = os.path.dirname(self._instances[key]['path'])
            logger.info(f'removing dicom dir: {data_path}')
            shutil.rmtree(data_path)

        #if key == self._num_vols:
        #    logger.info('RUNNING FINAL SNR CALCULATION')
        #    snr_metric = round(self.calc_snr(key), 2)
        #    logger.info(f'final snr metric: {snr_metric}')
        #    pub.sendMessage('plot_snr', snr_metric=snr_metric) 
            


    def calculate_and_publish_snr(self, key):
        start = time.time()
        snr_metric = round(self.calc_snr(key), 2)
        elapsed = time.time() - start
        #self._plot_dict[self._key] = elapsed
        logger.info(f'snr calculation took {elapsed} seconds')
        logger.info(f'running snr metric: {snr_metric}')
        if np.isnan(snr_metric):
            logger.info(f'snr is a nan, decrementing mask threshold by {self._decrement}')
            self._mask_threshold = self._mask_threshold - self._decrement
            logger.info(f'new threshold: {self._mask_threshold}')
            self._slice_intensity_means = np.zeros( (self._z, self._num_vols) )
        else:
            pub.sendMessage('plot_snr', snr_metric=snr_metric) 

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

    def calc_snr(self, key):

        slice_intensity_means, slice_voxel_counts, data = self.get_mean_slice_intensitites(key)

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


    def get_mean_slice_intensitites(self, key):

        data = self.generate_mask(key)
        mask = np.ma.getmask(data)
        dim_x, dim_y, dim_z, _ = data.shape

        dim_t = key - 4

        '''
        if key > 55:
            start = time.time()
            differing_slices = self.find_mask_differences(key)
            logger.info(f'finding mask differences took {time.time() - start}')
        '''


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

            #logger.info(f'recalculating slice means at the following slices: {differing_slices}')
            #logger.info(f'total of {len(differing_slices)} new slices being computed')

            #if differing_slices:

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

            elif key % 6 == 0:
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

            elif key % 5 == 0:
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

        numpy_4d_mask[numpy_3d_mask] = 1

        masked_data = np.ma.masked_array(self._fdata_array[..., :key-4], mask=numpy_4d_mask)

        mask = np.ma.getmask(masked_data)

        self._slice_means[key]['mask'] = mask

        return masked_data

    def find_mask_differences(self, key):
        num_old_vols = key - 8
        last_50 = num_old_vols - 50
        prev_mask = self._slice_means[key-4]['mask']
        current_mask = self._slice_means[key]['mask']
        differences = prev_mask[:,:,:,-50:] != current_mask[:,:,:,last_50:num_old_vols]
        diff_indices = np.where(differences)
        differing_slices = []
        for index in zip(*diff_indices):
            if int(index[2]) not in differing_slices:
                differing_slices.append(int(index[2]))
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


    def check_snr(self, key):
        tasks = list()
        current = self._slice_means[key]

        current_idx = self._slice_means.bisect_left(key)

        try:
            value = self._slice_means.values()[current_idx]
            tasks.append(value)
        except IndexError:
            pass

        return tasks

