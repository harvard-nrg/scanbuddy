import os
import logging
from pubsub import pub

logger = logging.getLogger(__name__)

class Params:
    def __init__(self, config, broker=None):
        self._config = config.find_one('$.params', dict())
        self._broker = broker
        self._coil_checked = False
        self._table_checked = False
        pub.subscribe(self.listener, 'params')
        pub.subscribe(self.reset, 'reset')

    def reset(self):
        self._checked = False

    def listener(self, ds):
        if self._coil_checked:
            logger.info(f'already checked coil from series {ds.SeriesNumber}')
            return
        if self._table_checked:
            logger.info(f'already checked table table position from {ds.SeriesNumber}')
            return
        for item in self._config:
            args = self._config[item]
            f = getattr(self, item)
            f(ds, args)

    def coil_elements(self, ds, args):
        self._coil_checked = True
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

    def table_position(self, ds, args):
        self._table_checked = True
        patient_name = ds.get('PatientName', 'UNKNOWN PATIENT')
        series_number = ds.get('SeriesNumber', 'UNKNOWN SERIES')
        table_position = self.find_table_position(ds)
        receive_coil = self.findcoil(ds)
        message = args['message'].format(
            SESSION=patient_name,
            SERIES=series_number,
            TABLE_POSITION=table_position,
        )
        for bad in args['bad']:
            a = ( receive_coil, table_position )
            b = ( bad['receive_coil'], bad['table_position'] )
            logger.info(f'checking if {a} == {b}')
            if a == b:
                logger.warning(message)
                logger.info('publishing message to message broker')
                self._broker.publish('scanbuddy_messages', message)
                break


    def find_table_position(self, ds):
        seq = ds[(0x5200, 0x9230)][0]
        seq = seq[(0x0021, 0x11fe)][0]
        return seq[(0x0021, 0x1145)].value[-1]


    def findcoil(self, ds):
        seq = ds[(0x5200, 0x9229)][0]
        seq = seq[(0x0018, 0x9042)][0]
        return seq[(0x0018, 0x1250)].value
   
    def findcoilelements(self, ds):
        seq = ds[(0x5200, 0x9230)][0]
        seq = seq[(0x0021, 0x11fe)][0]
        return seq[(0x0021, 0x114f)].value

