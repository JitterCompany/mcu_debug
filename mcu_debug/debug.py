#!/usr/bin/env python

from telnetlib import Telnet
from threading import Thread
import time
import argparse
import os
import sys
import re
from subprocess import STDOUT, PIPE, Popen


def blackmagic_present(blackmagic_device):
    return os.path.exists(blackmagic_device)

def debug_blackmagic(gdb, elf_file, blackmagic_device):
    
    if not blackmagic_present(blackmagic_device):
        print("Warning: no blackmagic device found at '"
                + blackmagic_device + "'")
        return False

    args = [
            gdb,
            "-ex", "target extended-remote " + blackmagic_device,
            "-ex", "monitor swdp_scan",
            "-ex", "attach 1",
            "-ex", "set mem inaccessible-by-default off",
            elf_file
            ]

    # this never returns
    os.execvp(gdb, args)

def debug_openocd(gdb, elf_file, breakpoint_lim=2,watchpoint_lim=2):
    
    print("A running OpenOCD server is required.")
    print("If it is not running yet, manually start it with 'openocd -f <cpu>.cfg'")
    print("Connecting to OpenOCD...\n")

    args = [gdb]
    if not gdb.endswith('py'):
        args.append('-tui')

    args.extend(["-ex", "target remote localhost:3333"])
    args.extend(["-ex", "set remote hardware-breakpoint-limit "+breakpoint_lim])
    args.extend(["-ex", "set remote hardware-watchpoint-limit "+watchpoint_lim])
    args.append(elf_file)

    # this never returns
    os.execvp(gdb, args)



default_blackmagic = "/dev/ttyBmpGdb"

parser = argparse.ArgumentParser(description="Debug via gdb, using \
        either the Black Magic Probe or a running OpenOCD server via telnet")
parser.add_argument("elf", nargs='?', help="The elf file corresponding to the code \
        on the device")
parser.add_argument("--gdb", type=str, help="The GDB executable to use")
parser.add_argument("--blackmagic", nargs='?', type=str, help="The Blackmagic device file",
        default=default_blackmagic)
parser.add_argument("--breakpoints", nargs='?', type=str, help="Maximum breakpoint count for OpenOCD",
        default=1)
parser.add_argument("--watchpoints", nargs='?', type=str, help="Maximum watchpoint count for OpenOCD",
        default=1)
args = parser.parse_args()
if not args.blackmagic:
    args.blackmagic = default_blackmagic

targets = []
if args.elf is None:

    print("Error: specify at least the elf file corresponding to the code on the device")
    parser.print_usage()
    sys.exit()


if not os.path.exists(args.elf):
    print("Warning: elf file '" + args.elf + "' not found")
    sys.exit()

if blackmagic_present(args.blackmagic):
    print("\n== Debugging via BlackMagic... ==\n")
    if debug_blackmagic(args.gdb, args.elf, args.blackmagic):
        print("\n== End of debug session ==\n\n")
        sys.exit()

else:
    print("No Black Magic Probe found, trying OpenOCD")
    print("\n== Debugging via OpenOCD... ==\n")
    if debug_openocd(args.gdb, args.elf, args.breakpoints, args.watchpoints):
        print("\n== End of debug session ==\n\n")
        sys.exit()

print("\n== Error: failed to start debugging ==")
print("Please check if a BlackMagic probe"
        + " or OpenOCD-compatible debugger is connected...\n")

