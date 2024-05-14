#!/usr/bin/env python3 -u

import logging
import time
from pubsub import pub
from rtbold.consumer import Consumer
from rtbold.processor import Processor
from rtbold.volreg import VolReg
from rtbold.plotter.dash import DashPlotter
from rtbold.plotter.matplotlib import MplPlotter

logger = logging.getLogger('main')
logging.basicConfig(level=logging.INFO)

def main():
    consumer = Consumer('/tmp/rtbold')
    logger.info('starting consumer')
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    processor = Processor()
    pub.subscribe(processor.listener, 'incoming')
    logging.getLogger('processor').setLevel(logging.DEBUG)    
    
    volreg = VolReg(mock=True)
    pub.subscribe(volreg.listener, 'volreg')
    logging.getLogger('volreg').setLevel(logging.DEBUG)    

    ui = DashPlotter()
    pub.subscribe(ui.listener, 'plot')
    logging.getLogger('ui').setLevel(logging.DEBUG)
    
    consumer.start()
    ui.forever()

if __name__ == '__main__':
    main()
