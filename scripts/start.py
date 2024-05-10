#!/usr/bin/env python3

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
    
    processor = Processor()
    pub.subscribe(processor.listener, 'incoming')
    logging.getLogger('processor').setLevel(logging.DEBUG)    
    
    volreg = VolReg(mock=True)
    pub.subscribe(volreg.listener, 'volreg')
    logging.getLogger('volreg').setLevel(logging.DEBUG)    

    dash = DashPlotter()
    pub.subscribe(dash.listener, 'plot')
    logging.getLogger('dash').setLevel(logging.DEBUG)

    mpl = MplPlotter()
    pub.subscribe(mpl.listener, 'plot')
    logging.getLogger('mpl').setLevel(logging.DEBUG)

    consumer.start()
    consumer.join()

if __name__ == '__main__':
    main()
