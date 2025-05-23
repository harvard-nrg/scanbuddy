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
    subparsers = parser.add_subparsers(help='sub-command help')
    parser_simulate = subparsers.add_parser('simulate', help='simulate -h')
    parser_simulate.add_argument('--copy-to', type=Path, required=True)
    parser_simulate.add_argument('--stop-after', type=int) 
    parser_simulate.add_argument('--delay', type=float, default=0)
    parser_simulate.add_argument('input', type=Path)
    parser_simulate.set_defaults(func=simulate)

    parser_sort = subparsers.add_parser('sort', help='sort -h')
    parser_sort.add_argument('--parent', type=Path)
    parser_sort.add_argument('--absolute', action='store_true')
    parser_sort.add_argument('input', type=Path)
    parser_sort.set_defaults(func=sort)

    args = parser.parse_args()
    args.func(args)
    
def sort(args):
    instances = dict()
    for path in args.input.iterdir():
        ds = pydicom.dcmread(path, stop_before_pixels=True)
        if args.parent:
            path = Path(args.parent, path.name)
        if args.absolute:
            instances[ds.InstanceNumber] = path.absolute()
        else:
            instances[ds.InstanceNumber] = path
            
    for _,path in iter(sorted(instances.items())):
        print(path) 

def simulate(args):
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
