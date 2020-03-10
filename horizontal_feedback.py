#!/usr/bin/env python
import argparse
from datetime import datetime
import functools
import sys

from bluesky import RunEngine
from ophyd import EpicsMotor, EpicsSignal
# from bluesky.log import config_bluesky_logging


print = functools.partial(print, file=sys.stderr)


# Create ophyd devices
pm = EpicsMotor("XF:08BMA-OP{Mono:1-Ax:Pico}Mtr", name="pm")
inb = EpicsSignal("XF:08BMES-BI{PSh:1-BPM:1}V-I", name="inb")
outb = EpicsSignal("XF:08BMES-BI{PSh:1-BPM:2}V-I", name="outb")
pm.wait_for_connection()
inb.wait_for_connection()
outb.wait_for_connection()
print(f"pico starting position {pm.position:.6}")
inb_initial = inb.get()
outb_initial = outb.get()
print(f"inboard signal {inb_initial:.6}")
print(f"outboard signal {outb_initial:.6}")
BPMpos = (outb_initial - inb_initial) / (outb_initial + inb_initial) * 1000000
print(f"position {BPMpos:.4}")
source_pos = EpicsSignal("SR:APHLA:SOFB{BUMP:C08-BMB}offset:X-I",
                         name="source_pos")
print(f"source position {source_pos.get():.6}")
print(datetime.now().isoformat())


def plan(FBref=-13700):
    yield from []


def main():
    parser = argparse.ArgumentParser(
        description='TES horizontal feedback')
    args = parser.parse_args()
    # config_bluesky_logging(level='INFO')

    RE = RunEngine()
    RE(plan())


if __name__ == '__main__':
    main()
