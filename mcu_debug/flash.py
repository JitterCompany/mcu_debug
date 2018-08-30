#!/usr/bin/env python

from telnetlib import Telnet
from threading import Thread
import time
import argparse
import os
import sys
import re
from subprocess import PIPE, Popen



def blackmagic_present(blackmagic_device):
    return os.path.exists(blackmagic_device)

def flash_blackmagic(targets, blackmagic_device):
    
    if not blackmagic_present(blackmagic_device):
        print("Warning: no blackmagic device found at '"
                + blackmagic_device + "'")
        return False

    for target in targets:
        
        # we assume that arg 'binary' is the elf file, or if it ends in '.bin',
        # the elf file will have the same path, but end in '.elf' or without extension
        elf_file = target['binary']
        split = os.path.splitext(elf_file)
        fw_ext = split[1]
        if fw_ext == '.bin':
            elf_file = split[0]
            if os.path.exists(elf_file + '.elf'):
                elf_file+= '.elf'
                
        if not os.path.exists(elf_file):
            print("Warning: elf file '" + elf_file + "' not found")
            return False


        cmd = "arm-none-eabi-gdb -nx --batch"
        cmd+= " -ex 'target extended-remote " + blackmagic_device + "'"
        cmd+= " -ex 'monitor swdp_scan'"
        cmd+= " -ex 'attach 1'"
        cmd+= " -ex 'load'"

        # On this mcu series, set SYSMEMREMAP register to 2.
        # This correctly remaps the first 512 bytes to flash instead of boot ROM.
        # Otherwise the verify will fail...
        if target['cpu'] == 'lpc11uxx':
            cmd+= " -ex 'set mem inaccessible-by-default off'"
            cmd+= " -ex 'set {int}0x40048000 = 2'"

        cmd+= " -ex 'compare-sections'"
        cmd+= " -ex 'kill' " + elf_file

        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()

        result = stderr + stdout
        result = result.decode('utf-8')
        ok = 0
        error = 0
        for line in result.split("\n"):
            if re.match(r'Section .*: matched.', line):
                ok+= 1
                print("OK " + str(ok) + ":", line)
            if re.match(r'Section .*: MIS-MATCHED', line):
                error+= 1
                print("ERROR " + str(error) + ":", line)

        if error or (not ok):
            return False

    return True


def flash_openocd(targets):
    success = False
    try:

        cmd_start = 'reset init; halt'
        cmd_done = 'core_reset;'    # should be implemented in the config file
        cmd_shutdown = 'shutdown'
        cmd_flash = []

        for target in targets:
            cmd_flash.append(('flash write_image erase '+target['binary'] + ' \
                    ' + target['address'] + ';', 'verify_image ' + target['binary'] + ' \
                    ' + target['address'] + ';'))

            # detect running openocd server
        openocdFound = False
        for line in os.popen("ps xa"):
            fields = line.split()
            process = fields[4]
            if(process.find('openocd') >= 0):
                openocdFound = True
                break

        if not openocdFound:
            def run_openocd():
                # NOTE: all targets are assumed to have the same cpu config
                cfg = targets[0]['cpu'] + '.cfg'

                orig_wd = os.getcwd()
                os.chdir(os.path.realpath(os.path.dirname(__file__)) + '/config/')
                os.popen('openocd -f ' + cfg)
                os.chdir(orig_wd)

            thread = Thread(target=run_openocd)
            thread.deamon = True
            thread.start()
            time.sleep(0.1)

        tn = Telnet(args.ip, args.port)
        r = tn.expect([b'Open On-Chip Debugger'], 5)
        if r[0] != 0:
            print ("ERROR starting OpenOCD:")
            print(r)

        tn.write(str.encode(cmd_start + '\n'))
        for cmd in cmd_flash:

            tn.write(str.encode(cmd[0] + '\n'))
            tn.write(str.encode(cmd[1] + '\n'))
            r = tn.expect([str.encode(s) for s in ['verified', 'error', 'checksum', 'mismatch']], 5)
            done = (r[0] == 0) # wait for 'verified'

            if done:
                success = True
                print('Flashing succesfull\n')
            else:
                print('Flashing failed\n')
        time.sleep(0.01)
        tn.write(str.encode(cmd_done + '\n'))
        time.sleep(0.01)
        if not openocdFound:
            print('shutdown openocd...')
            tn.write(str.encode(cmd_shutdown + '\n'))
        time.sleep(0.5)
        tn.sock.close()
    except Exception:
        print("Flashing failed\n")

    return success


default_blackmagic = "/dev/ttyBmpGdb"

parser = argparse.ArgumentParser(description="Connects to a running \
        OpenOCD server via telnet to flash a target with a given \
        binary file to a given memory address")
parser.add_argument("--config",  help="A config file specifying one \
        target per line, formatted as <binary> <address> <cpu>")
parser.add_argument("binary", nargs='?', help="The binary hex file to flash to \
        the device")
parser.add_argument("address", nargs='?', help="The memory address to flash the \
        binary hex file to")
parser.add_argument("cpu", nargs='?', help="The cpu to flash, corresponding to \
        the openocd config file [cpu].cfg")
parser.add_argument("-b2", "--binary2",  help="The binary hex file to \
        flash to the device")
parser.add_argument("-a2", "--address2",  help="The memory address to \
        flash the binary hex file to")
parser.add_argument("-ip","--ip", type=str, help="The OpenOCD ip \
        address to connect to", default="localhost")
parser.add_argument("-p","--port", type=int, help="The OpenOCD port to\
        connect to", default=4444)
parser.add_argument("--blackmagic", nargs='?', type=str, help="The Blackmagic device file",
        default=default_blackmagic)
args = parser.parse_args()
if not args.blackmagic:
    args.blackmagic = default_blackmagic

targets = []
if not args.config is None:
    try:
        with open(args.config, 'r') as cfg:
            for line in cfg.readlines():
                opts = line.split()
                targets.append({
                    'binary':   opts[0],
                    'address':  opts[1],
                    'cpu':      opts[2]
                    })
    except IOError:
        print("Error: failed to open config file '%s'"
                % args.config)
        sys.exit()
    
    if not len(targets):
        print("Error: no valid target(s) found in config file '%s'"
                % args.config)
        parser.print_usage()
        sys.exit()
        
else:
    if (args.binary is None
            or args.address is None
            or args.cpu is None):

        print("Error: specify at least --config or binary, cpu and address")
        parser.print_usage()
        sys.exit()
    else:
        targets.append({
            'binary':   args.binary,
            'address':  args.address,
            'cpu':      args.cpu
            })
        if not args.binary2 is None and not args.address2 is None:
            targets.append({
                'binary':   args.binary2,
                'address':  args.address2,
                'cpu':      args.cpu
                })
        


print("\n\n")
if blackmagic_present(args.blackmagic):
    print("== Flashing via BlackMagic... ==\n")
    if flash_blackmagic(targets, args.blackmagic):
        print("\n== OK! Flashing succesfull! ==\n\n")
        sys.exit()

else:
    print("\n== Flashing via OpenOCD... ==\n")
    if flash_openocd(targets):
        print("\n== OK! Flashing succesfull! ==\n\n")
        sys.exit()

print("\n== Error: flashing failed ==")
print("Please check if a BlackMagic probe \
        or OpenOCD-compatible debugger is connected...\n")

    
