#!/usr/bin/env python3 -u

import time
import logging
from pubsub import pub
from pathlib import Path
from argparse import ArgumentParser
from rtbold.directory_watcher import Directory_Watcher
from rtbold.consumer import Consumer
from rtbold.processor import Processor
from rtbold.volreg import VolReg
from rtbold.plotter.dash import DashPlotter
from rtbold.plotter.matplotlib import MplPlotter

logger = logging.getLogger('main')
logging.basicConfig(level=logging.INFO)

def main():
    parser = ArgumentParser()
    parser.add_argument('-m', '--mock', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--folder', type=Path, default='/tmp/rtbold')
    args = parser.parse_args()

    #args.folder = Path.joinpath(args.folder, 'pucky')

    directory_watcher = Directory_Watcher(args.folder)
    processor = Processor()
    volreg = VolReg(mock=args.mock)
    ui = DashPlotter()

    if args.verbose:
        logging.getLogger('processor').setLevel(logging.DEBUG)
        logging.getLogger('volreg').setLevel(logging.DEBUG)
        logging.getLogger('ui').setLevel(logging.DEBUG)
   
    # logging from this module is useful, but noisy
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    # Start the directory watcher and wait for it to return a value
    directory_path = directory_watcher.start()

    consumer = Consumer(directory_path)
    consumer.start()
    ui.forever()

if __name__ == '__main__':
    main()