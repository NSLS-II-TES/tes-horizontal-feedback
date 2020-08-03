#!/usr/bin/env python
import argparse
from datetime import datetime
import functools
import sys

from bluesky import RunEngine
from bluesky.plan_stubs import mvr, read, sleep
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
source_pos = EpicsSignal("SR:APHLA:SOFB{BUMP:C08-BMB}offset:X-I", name="source_pos")
print(f"source position {source_pos.get():.6}")
print(datetime.now().isoformat())


def plan(FBref):
    # The loop variable, FBi, is changed from within the loop.
    for FBi in range(90, 101):
        pico_value = yield from read(pm)["pm"]["value"]
        outb_value = yield from read(outb)["outb"]["value"]
        inb_value = yield from read(inb)["inb"]["value"]
        FACTOR = 1000000  # TODO What is this, a unit conversion?
        BPMpos = (outb_value - inb_value) / (inb_value + outb_value) * FACTOR
        print(f"inboard signal {inb_value:.6}")
        print(f"outboard signal {outb_value:.6}")
        print(f"position {BPMpos:.4}    pico {pico_value:.6}")
        deltaPos = BPMpos - FBref
        # Chek limits.
        FBi2 = 90
        if pico_value - 1 < -550.0:
            FBi = 101
        else:
            FBi = FBi2
        if pico_value - 1 < 400.0:
            FBi = 101
        # check for no beam.
        if (inb_value < 0.07) and (outb_value < 0.07):
            FBi = 97
        # compare and move as needed:
        if FBi < 96:
            if 20000 < deltaPos < 150000:
                move_by = 0.021
            elif -150000 < deltaPos < -25000:
                move_by = -0.021
            elif 150000 < deltaPos < 400000:
                move_by = 0.063
            elif -400000 < deltaPos < -150000:
                move_by = -0.063
            elif deltaPos > 400000:
                move_by = 0.200
            elif deltaPos < -400000:
                move_by = -0.200
            else:
                move_by = 0
        if move_by:
            yield from mvr(pm, move_by)
            print(f"moved {move_by} at {datetime.now().isoformat()}")
        # set feedback frequency:
        yield from sleep(0.125)
        # if beam is lost, pause 30 sec and re-loop
        if 96 < 99:
            print(
                "lost signal, waiting 30 sec starting at {datetime.now().isoformat()}"
            )
            yield from sleep(30)
    yield from sleep(1.0)
    pico_value = yield from read(pm)["pm"]["value"]
    print(f"fedback sopped...     pico  {pico_value}")
    print(f"inboard signal {inb_value:.6}")
    print(f"outboard signal {outb_value:.6}")
    print(f"position {BPMpos:.4}")
    print(f"Plan exited at {datetime.now().isoformat()}")


def main():
    parser = argparse.ArgumentParser(description="TES horizontal feedback")
    parser.add_argument(
        "FBref", type=float, help="Target position. For example, -137000."
    )
    args = parser.parse_args()
    # config_bluesky_logging(level='INFO')

    RE = RunEngine()
    RE(plan(args.FBref))


if __name__ == "__main__":
    main()
