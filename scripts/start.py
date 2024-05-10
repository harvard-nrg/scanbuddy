#!/usr/bin/env python3

import logging
import time
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
    
    processor = Processor()
    pub.subscribe(processor.listener, 'incoming')
    logging.getLogger('processor').setLevel(logging.DEBUG)    
    
    volreg = VolReg(mock=True)
    pub.subscribe(volreg.listener, 'volreg')
    logging.getLogger('volreg').setLevel(logging.DEBUG)    

    plotter = Plotter()
    pub.subscribe(plotter.listener, 'plot')
    logging.getLogger('plotter').setLevel(logging.DEBUG)

    #st.write('''Realtime fMRI Motion Plot Thinger''')
    #time.sleep(10)
    #st.write('''foobar''')

    consumer.start()
    consumer.join()

if __name__ == '__main__':
    main()
    
