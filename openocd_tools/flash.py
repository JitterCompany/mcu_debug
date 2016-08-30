#!/usr/bin/env python

from telnetlib import Telnet
from threading import Thread
import time
import argparse
import os
import sys

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
args = parser.parse_args()

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
        
    
cmd_start = 'reset init; halt'
cmd_done = 'reset run;'
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
r = tn.expect(['Open On-Chip Debugger'], 5)
if r[0] != 0:
    print ("ERROR starting OpenOCD:")
    print(r)

tn.write(cmd_start + '\n')
for cmd in cmd_flash:

    tn.write(cmd[0] + '\n')
    tn.write(cmd[1] + '\n')
    r = tn.expect(['verified', 'error', 'checksum', 'mismatch'], 5)
    done = (r[0] == 0) # wait for 'verified'

    if done:
        print('Flashing succesfull\n')
    else:
        print('Flashing failed\n')
time.sleep(0.01)
tn.write(cmd_done + '\n')
time.sleep(0.01)
if not openocdFound:
    print('shutdown openocd...')
    tn.write(cmd_shutdown + '\n')
time.sleep(0.5)
tn.sock.close()
