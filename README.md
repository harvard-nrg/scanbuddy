# Scan Buddy

Scan Buddy watches a folder for creation of an interior incoming folder. 
When created, it watches *that* folder for DICOM images. Each time one
appears, it plots motion data on a web page (by default at `localhost:8080`)
suitable for showing full time in the MR control room.

Whenever a DICOM from a new series is seen, all data from the previous series
is discarded.

