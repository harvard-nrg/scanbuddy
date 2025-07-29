.. _dcm2niix: https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage
.. _3dvolreg: https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dvolreg.html

Technical Appendix
==================
Welcome! This appendix is meant to provide more details about the computations that Scanbuddy is doing under the hood. If you have a suggestion, please see guidelines for `contributing to Scanbuddy <https://github.com/harvard-nrg/scanbuddy?tab=readme-ov-file#contributing-to-scanbuddy>`_.

Motion Calculation
^^^^^^^^^^^^^^^^^^
Motion calculation relies on Chris Rorden's dicom converter, `dcm2niix`_. Each incoming dicom file gets converted to the NIfTI format and then fed as input into AFNI's `3dvolreg`_ program. 3dvolreg is generally used to register volumes to one another, with one volume serving as the "base" volume that the other is being registered to. Our use case is taking each volume and registering it to the volume that immediately preceded it. For example, volume two gets registered to volume one, volume three gets registered to volume two, and so on. Scanbuddy does not run 3dvolreg on volume one.

3dvolreg optionally spits out a 1D file that estimates how much motion correction had to be done to the input volume to register it to the base volume. In other words, it tells us how much the participant moved between the two volumes. Scanbuddy plots the 1D file in the "Translations" and "Rotations" graphs. Here's an example of a 3dvolreg command Scanbuddy runs:

.. code-block:: shell
    
    3dvolreg -base nii_1 -linear -1Dfile moco.par -x_thresh 10 -rot_thresh 10 -nomaxdisp -prefix NULL nii_2

Some of you may be wondering why we chose to calculate volume by volume motion rather than using one of the first 5 volumes as the base. The purpose of Scanbuddy is to call users' attention to spikes in motion that can happen during the course of a scan rather than the motion "drift" that tends to naturally happen during a scan. Scanbuddy is not a replacement for motion correction. This way, users can make informed decision about recapturing scans if necessary and coaching participants to minimize motion.

SNR Calculation
^^^^^^^^^^^^^^^
Scanbuddy's SNR calculation is slice based. It uses coil element information available in the dicom header to determine what the expected voxel intensity should be. Any voxels that are below that threshold get masked out across every slice in each volume. Then we take the average of each slice from each volume to create a 2D array. We calculate an SNR metric for each slice by dividing the slice mean by the slice standard deviation. Next, we calculate a weighted SNR mean by dividing the slice SNR by the number of voxels in that slice. Finally, we aggregate the weighted slice means across all the volumes and divide it by the total number of voxels.

And voilà! We have an SNR estimate. Scanbuddy starts calculating SNR volume around volume 60, though it may differ depending on the headcoil being used. Scanbuddy will calculate SNR every four volumes after it's initial calculation. We optimized the calculation by having Scanbuddy only recalculate weighted slice means in slices where the estimated mask has changed.

Please direct any additional questions to info@neuroinfo.org

