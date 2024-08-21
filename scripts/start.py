#!/usr/bin/env python3 -u

import time
import logging
from pubsub import pub
from pathlib import Path
from argparse import ArgumentParser
from rtbold.watcher.directory import DirectoryWatcher
from rtbold.processor import Processor
from rtbold.volreg import VolReg
from rtbold.params import Params
from rtbold.plotter.dash import DashPlotter
from rtbold.broker.redis import MessageBroker

logger = logging.getLogger('main')
logging.basicConfig(level=logging.INFO)

def main():
    parser = ArgumentParser()
    parser.add_argument('-m', '--mock', action='store_true')
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--folder', type=Path, default='/tmp/rtbold')
    args = parser.parse_args()

    broker = MessageBroker()

    watcher = DirectoryWatcher(args.folder)
    processor = Processor()
    params = Params(broker=broker)
    volreg = VolReg(mock=args.mock)
    ui = DashPlotter(host=args.host, port=args.port)

    if args.verbose:
        logging.getLogger('processor').setLevel(logging.DEBUG)
        logging.getLogger('volreg').setLevel(logging.DEBUG)
        logging.getLogger('ui').setLevel(logging.DEBUG)
        logging.getLogger('registration').setLevel(logging.DEBUG)
   
    # logging from this module is useful, but noisy
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    # start the watcher and ui
    watcher.start()
    ui.forever()

if __name__ == '__main__':
    main()
