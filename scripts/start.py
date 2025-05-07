#!/usr/bin/env -S python3 -u

import sys
import time
import logging
from pubsub import pub
from pathlib import Path
from scanbuddy.proc.snr import SNR
from argparse import ArgumentParser
from scanbuddy.config import Config
from scanbuddy.proc import Processor
from scanbuddy.view.dash import View
from scanbuddy.proc.volreg import VolReg
from scanbuddy.proc.params import Params
from scanbuddy.broker.redis import MessageBroker
from scanbuddy.common import print_platform_info
from scanbuddy.watcher.directory import DirectoryWatcher

logger = logging.getLogger('main')
logging.basicConfig(level=logging.INFO)

def main():
    parser = ArgumentParser()
    parser.add_argument('-m', '--mock', action='store_true')
    parser.add_argument('-c', '--config', required=True, type=Path)
    parser.add_argument('--debug-display', action='store_true')
    parser.add_argument('--host', type=str)
    parser.add_argument('--port', type=int)
    parser.add_argument('--broker-host', type=str)
    parser.add_argument('--broker-port', type=int)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--snr-interval', default=10, 
        help='Every N volumes snr should be calculated')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    print_platform_info()

    config = Config(args.config)
    if args.host:
        config.update_or_create('$.app.host', args.host)
    if args.port:
        config.update_or_create('$.app.port', args.port)
    if args.debug_display:
        config.update_or_create('$.app.debug_display', args.debug_display)
    if args.broker_host:
        config.update_or_create('$.broker.host', args.broker_host)
    if args.broker_port:
        config.update_or_create('$.broker.port', args.broker_port)

    broker = MessageBroker(
        config=config,
        debug=args.verbose
    )
    watcher = DirectoryWatcher(args.folder)
    processor = Processor(
        config=config
    )
    params = Params(
        broker=broker,
        config=config,
        debug=args.verbose
    )
    volreg = VolReg(mock=args.mock)
    view = View(
        broker=broker,
        config=config,
        debug=args.verbose
    )

    if args.verbose:
        logging.getLogger('scanbuddy.proc').setLevel(logging.DEBUG)
        logging.getLogger('scanbuddy.proc.params').setLevel(logging.DEBUG)
        logging.getLogger('scanbuddy.proc.volreg').setLevel(logging.DEBUG)
        logging.getLogger('scanbuddy.view.dash').setLevel(logging.DEBUG)
   
    # logging from this module is useful, but noisy
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    # start the watcher and view
    watcher.start()
    view.forever()

if __name__ == '__main__':
    main()
