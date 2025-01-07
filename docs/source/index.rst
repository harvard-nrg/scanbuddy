.. AnatQC documentation master file, created by
   sphinx-quickstart on Tue Jun 20 12:46:20 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to DWIQC's documentation!
==================================
.. _Prequal: https://doi.org/10.1002/mrm.28678 
.. _QSIPREP: https://doi.org/10.1038/s41592-021-01185-5 
.. _XNAT: https://doi.org/10.1385/NI:5:1:11

DWIQC is a diffusion MRI preprocessing and quality control pipeline built on the `Prequal`_ and `QSIPREP`_ software packages. Working closely with neuroimaging experts, we designed an ergonomic user interface for the `XNAT`_ informatics and data management platform that allows users to quickly assess image quality and use those insights to get ahead of issues within the data acquisition workflow. Non-XNAT users can also benefit from DWIQC as a one-stop shop for running two state of the art diffusion pipelines simultaneously and receiving their associated outputs. See `Prequal`_ and `QSIPREP`_ documentation for further details.


.. image:: images/logo.png

.. toctree::
   :maxdepth: 3
   :caption: Contents:
   
   xnat
   developers
   xnattagger

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
