User Documentation
==================


.. note::
    This documentation assumes a basic understanding of the command line, the Linux operating system and Siemens MRI scanner host PCs. Here's a quick (and free!) crash `course <https://www.codecademy.com/learn/learn-the-command-line>`_ on the command line if needed. Instructions on streaming data to the Scanbuddy machine from a scanner are shown on a Siemens XA-30 system.


Overview
^^^^^^^^
Let's start with what Scanbuddy is all about. fMRI is a powerful research and clinical tool that allows us to peer into the brain function of living humans. One of the biggest challenges facing fMRI data quality is subject movement during data acquisition. Even subtle actions, such as swallowing or yawning, can have large impacts on data quality. 

To combat subject motion and optimize data quality, motion-correcting software algorithms can be employed at the post-processing stage, as well as data deletion and imputation methods. However, there are instances of subject motion being severe enough to make the dataset unusable. This is where Scanbuddy comes in! Scanbuddy produces motion plots to be viewed by researchers at the time of data acquisition, appearing on screen at the conclusion of fMRI scans. Individual researchers will determine acceptable motion standards. Seeing motion plots at acquisition can help researchers decide if a scan should be re-acquired. You no longer have to wait until data processing to get an idea of how much your subject has or has not moved.

Scanbuddy also provides an estimate of the Signal-to-Noise Ratio (SNR) with the motion plots to give researchers an idea of overall data quality. Scanbuddy does not save motion plots by default and does not store data on its host machine. Scanbuddy will create a new motion plot and compute a new SNR metric for every fMRI scan acquired. Scanbuddy currently does not support Multi-Echo BOLD imaging, though work is being done to make this feature available soon. Scanbuddy is containerized with docker and is available on Github Container Repository.


What You Will Need
^^^^^^^^^^^^^^^^^^
Scanbuddy should be run on a standalone machine (separate from the scanner host PC) that runs Linux and you have sudo privileges. We've used several distributions of Linux in development (ubuntu, debian, asahi) and all have run Scanbuddy successfully. Scanbuddy may work on MacOS and/or Windows, though it has not been tested by the developers. The Scanbuddy machine should have 16 GB of RAM if possible. It may still work with less memory depending on the size of the data being acquired. The machine should be capable of running a web browser and Docker. You will also need a monitor to connect to the machine to display the motion plots.

.. note::
     Take a look at installing Docker on Linux `here <https://docs.docker.com/engine/install/>`_.

Samba Share
^^^^^^^^^^^
Data streaming from the scanner to the Scanbuddy machine should be set up via a Samba share mount. Samba enables the scanner to stream dicom data directly to the Scanbuddy machine so that Scanbuddy can build the motion plots and display them when the scan ends.

Let's get Samba up and running! First thing to do, install Samba:

.. code-block:: shell
    
     sudo apt install samba

Create the directory you want to share over Samba and set ownership to a system account:

.. code-block:: shell

     sudo mkdir -p /data/folder
     sudo chown username:group /data/folder

If you are using SE Linux, you will need to make sure this directory is accessible to Samba:

.. code-block:: shell
    
     sudo semanage fcontext -a -t samba_share_t "/data/folder"
     sudo restorecon -R -v /data/folder

Check ``/var/log/audit/audit.log`` for Samba denial messages. You may not see any messages until the scanner attempts to mount the drive.

You will also need to create a Samba password. Samba uses its own password database for authentication. The password you choose for Samba may be different from the user's system password. Adding a new Samba user should automatically enable the user, but it's still a good idea to make sure the user is enabled with ``smbpasswd -e username``

.. code-block:: shell

      sudo smbpasswd -a username

Configure Samba
"""""""""""""""
Add the following to the end of ``/etc/samba/smb.conf``

.. code-block:: yaml

  [sharedfolder]
      comment = My Shared Folder
      path = /data/folder
      read only = no
      writable = yes
      browsable = yes
      create mode = 0660
      directory mode = 0770

Save the above file and restart Samba:

.. code-block:: yaml

     sudo service smbd restart

Your Samba share should be up and running now!

Configuring the Plugin
^^^^^^^^^^^^^^^^^^^^^^
We have to tell the scanner which scans should be exported to the Scanbuddy machine and where the scanbuddy machine is.

Building the Container Image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Scanbuddy is packaged up in a Docker container to abstract away the hassle of installing the specific software it needs. Hurray for Docker! We've built and pushed the Docker image to Github Container Repository so you can run ``docker pull`` to build it on your local (Scanbuddy) machine. Take a look at this page to pull the latest version: `Scanbuddy image <https://github.com/harvard-nrg/scanbuddy/pkgs/container/scanbuddy>`_.

Build the container by running:

.. code-block:: shell

     docker pull ghcr.io/harvard-nrg/scanbuddy:latest

Then verify that it built correctly:

.. code-block:: shell

     docker image ls

You should see the Scanbuddy image listed there (check that it's the correct version).

Redis Container
"""""""""""""""
One feature of Scanbuddy is checking that the head coil is plugged in correctly and communicating correctly with the Scanner PC. We use Redis as a lightweight database to keep track of the head coil status. Run this command to build and run the redis container:

.. code-block:: shell

     docker run -d --name redis -p 8001:8001 redis/redis-stack:latest

Running Scanbuddy
^^^^^^^^^^^^^^^^^
With the plugin and Samba configured and the container built, we're ready to run Scanbuddy! 

The first thing to do is set a few environment variables inside of your shell for Scanbuddy: ``SCANBUDDY_SESSION_ID`` and ``SCANBUDDY_SESSION_KEY``

You can make this whatever you want (I would recommend a string) inside of your ``~/.bashrc`` file:

.. code-block:: shell

     export SCANBUDDY_SESSION_PASS='iLoveScanbuddy'
     export SCANBUDDY_SESSION_KEY='1234'

.. note::
     Remember to reload your shell environment!

Scanbuddy Command and Arguments
"""""""""""""""""""""""""""""""





