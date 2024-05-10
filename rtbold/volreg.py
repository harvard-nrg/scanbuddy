import json
import logging

logger = logging.getLogger('registration')

class VolReg:
    def listener(self, tasks):
        '''
        In the following example, there are two tasks (most of the time there will be only 1)
             - dicom.2.dcm should be registered to dicom.1.dcm and the 6 moco params should be put into the 'volreg' attribute for dicom.2.dcm
             - dicom.3.dcm should be registered to dicom.2.dcm and the 6 moco params should be put into the 'volreg' attribute for dicom.3.dcm

        [
            [
                {
                    'path': '/path/to/dicom.2.dcm'
                    'volreg': None
                },
                {
                    'path': '/path/to/dicom.1.dcm',
                    'volreg': None
                }
            ],
            [
                {
                    'path': '/path/to/dicom.3.dcm',
                    'volreg': None
                },
                {
                    'path': '/path/to/dicom.2.dcm',
                    'volreg': None
                }
            ]
        ]
        '''
        logger.info('received tasks for volume registration')
        logger.info(json.dumps(tasks, indent=2))
