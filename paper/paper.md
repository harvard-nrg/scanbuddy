---
title: 'Scanbuddy: fMRI motion plotting and SNR estimation at scan acquisition'
tags:
  - Python
  - neuroimaging
  - fMRI
  - motion detection
  - data quality
  - afni
  - snr
authors:
  - name: Daniel J. Asay
    orcid: 0000-0002-6691-7706
    affiliation: 1
  - name: Randy L. Buckner
    affiliation: "1, 2, 3" 
  - name: Timothy M. O'Keefe
    affiliation: 1
affiliations:
 - name: Center for Brain Science, Harvard University, Cambridge, Massachusetts, United States
   index: 1
 - name: Athinoula A. Martinos Center for Biomedical Imaging, Massachusetts General Hospital, Charlestown, Massachusetts, United States
   index: 2
 - name: Department of Psychiatry, Massachusetts General Hospital, Charlestown, Massachusetts, United States
   index: 3
date: 18 February 2025
bibliography: citations.bib
---

# Summary

Functional magnetic resonance imaging (fMRI) is a powerful research and clinical tool for in vivo imaging of human brain function. `Scanbuddy` is containerized software that produces motion plots at the time of scan acquisition. Users should have a machine separate from the scanner host PC with its own display monitor that is capable of running Linux and Docker. Users can set up auto exporting from the scanner host PC via a Samba share mount for BOLD scans. With auto exporting, the scanner will automatically send reconstructed DICOMs to both the scanner host PC and the `Scanbuddy` machine. `Scanbuddy` uses the excellent dcm2niix [@li_first_2016] and AFNI [@cox_afni:_1996] packages for DICOM conversion and computing motion estimates. `Scanbuddy` was developed in a linux environment and can handle repetition times as fast as 0.6 seconds.

`Scanbuddy` also provides an estimate of the Signal-to-Noise Ratio (SNR) with the motion plots to estimate data quality. `Scanbuddy` does not save motion plots by default and does not persist data on its host machine. `Scanbuddy` will create a new motion plot and compute a new SNR metric for every fMRI scan acquired. `Scanbuddy` supports multi-echo BOLD scans with the assumption that the second echo time (TE2) is the TE of interest. `Scanbuddy` is containerized with Docker and is available on GitHub Container Registry. `Scanbuddy` also checks head-coil elements and notifies users if a head-coil is missing expected elements (e.g. the head-coil is not plugged in properly). In many ways, `Scanbuddy` is the real-time acquisition version of the Automated Functional MRI Quality Assessment [@gabriele_automated_2014] software package with several additional features.


# Statement of need

One of the biggest challenges facing fMRI data quality is subject movement during data acquisition. Even subtle actions, such as swallowing or yawning, can have large impacts on data quality. To combat subject motion and optimize data quality, motion-correcting software algorithms can be employed in the post-processing stage, as well as data deletion and imputation methods. However, there are instances of subject motion being severe enough to make the dataset unusable. `Scanbuddy` attempts to address subject motion by producing motion plots to be viewed by researchers at the time of data acquisition, appearing on screen at the conclusion of fMRI scans. By seeing motion plots at scan acquisition, researchers can determine if a scan should be re-acquired due to excessive motion rather than lose part or all of an expensive dataset. With `Scanbuddy`, researchers no longer have to wait until data processing to find out how much a participant moved and can avoid the steep cost of data loss.

`Scanbuddy` helps researchers avoid data loss or poor data acquisition with SNR estimation and by checking head-coil elements. SNR estimation helps researchers set data quality expectations at the piloting stage of an fMRI experiment, while also keeping researchers apprised to ongoing data quality and unexpected dips in data quality at later phases of an fMRI experiment. Additionally, by checking head-coil elements, `Scanbuddy` provides a safety net to researcher mistakes that could result in loss of data at a significant financial cost, such as a head-coil not being plugged in properly. 

Overall, `Scanbuddy` aims to help researchers be more aware of participant motion artifacts, data quality issues, or other system failures that can have harmful effects on experimental outcomes in real time.

# Acknowledgements

We thank the Center for Brain Science at Harvard and the Harvard Faculty of Arts and Sciences for the financial support of this project.

# References
