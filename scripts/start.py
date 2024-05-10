#!/usr/bin/env python3

import logging
from pubsub import pub
from rtbold.consumer import Consumer
from rtbold.processor import Processor
from rtbold.volreg import VolReg
from rtbold.plotter import Plotter

logger = logging.getLogger('main')
logging.basicConfig(level=logging.INFO)

def main():
    consumer = Consumer('/tmp/rtbold')
    logger.info('starting consumer')
    consumer.start()

    processor = Processor()
    pub.subscribe(processor.listener, 'incoming')
    logging.getLogger('processor').setLevel(logging.DEBUG)    
    
    volreg = VolReg()
    pub.subscribe(volreg.listener, 'volreg')

    plotter = Plotter()
    pub.subscribe(plotter.listener, 'plot')

    consumer.join()

if __name__ == '__main__':
    main()
    
