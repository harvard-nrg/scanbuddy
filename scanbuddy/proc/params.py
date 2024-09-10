import os
import logging
from pubsub import pub

logger = logging.getLogger(__name__)

class Params:
    def __init__(self, config, broker=None):
        self._config = config.find_one('$.params', dict())
        self._broker = broker
        self._checked = False
        pub.subscribe(self.listener, 'params')
        pub.subscribe(self.reset, 'reset')

    def reset(self):
        self._checked = False

    def listener(self, ds):
        if self._checked:
            logger.info(f'already checked an instance from series {ds.SeriesNumber}')
            return
        for item in self._config:
            args = self._config[item]
            f = getattr(self, item)
            f(ds, args)

    def coil_elements(self, ds, args):
        self._checked = True
        patient_name = ds.get('PatientName', 'UNKNOWN PATIENT')
        series_number = ds.get('SeriesNumber', 'UNKNOWN SERIES')
        receive_coil = self.findcoil(ds)
        coil_elements = self.findcoilelements(ds)
        message = args['message'].format(
            SESSION=patient_name,
            SERIES=series_number,
            RECEIVE_COIL=receive_coil,
            COIL_ELEMENTS=coil_elements
        )
        for bad in args['bad']:
            a = ( receive_coil, coil_elements )
            b = ( bad['receive_coil'], bad['coil_elements'] )
            logger.info(f'checking if {a} == {b}')
            if a == b:
                logger.warning(message)
                logger.info(f'publishing message to message broker')
                self._broker.publish('scanbuddy_messages', message)
                break

    def findcoil(self, ds):
        seq = ds[(0x5200, 0x9229)][0]
        seq = seq[(0x0018, 0x9042)][0]
        return seq[(0x0018, 0x1250)].value
   
    def findcoilelements(self, ds):
        seq = ds[(0x5200, 0x9230)][0]
        seq = seq[(0x0021, 0x11fe)][0]
        return seq[(0x0021, 0x114f)].value

