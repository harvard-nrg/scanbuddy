#!/usr/bin/env python3

import sys
import time
import shutil
import logging
import pydicom
from pathlib import Path
from argparse import ArgumentParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def main():
    parser = ArgumentParser()
    parser.add_argument('--copy-to', type=Path, required=True)
    parser.add_argument('--stop-after', type=int) 
    parser.add_argument('--delay', type=int, default=0)
    parser.add_argument('input')
    args = parser.parse_args()

    with open(args.input) as fo:
        cleared = False
        for i,line in enumerate(fo, start=1):
            dcmfile = Path(line.strip())
            ds = pydicom.dcmread(dcmfile)
            dest = Path(args.copy_to, ds.SeriesInstanceUID)
            if not dest.exists():
                cleared = True
            elif dest.exists() and not cleared:
                while True:
                    ans = input(f'delete {dest} [y/n]: ').strip().lower()
                    match ans:
                        case 'y':
                            break
                        case 'n':
                            sys.exit(0)
                        case _:
                            pass
                shutil.rmtree(dest)
                cleared = True
            dest.mkdir(parents=True, exist_ok=True)
            logger.info(f'copying {dcmfile} to {dest}')
            shutil.copy2(dcmfile, dest)
            if args.stop_after and i >= args.stop_after:
                break
            time.sleep(args.delay)

if __name__ == '__main__':
    main()
