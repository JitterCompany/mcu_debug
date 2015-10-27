from telnetlib import Telnet
from threading import Thread
import time
import argparse
import os

os.chdir(os.path.dirname(os.path.realpath(__file__)))

parser = argparse.ArgumentParser(description="Connects to a running OpenOCD server via telnet to flash a target with a given binary file to a given memory address")
parser.add_argument("binary",  help="The binary hex file to flash to the device")
parser.add_argument("address",  help="The memory address to flash the binary hex file to")
parser.add_argument("-b2", "--binary2",  help="The binary hex file to flash to the device")
parser.add_argument("-a2", "--address2",  help="The memory address to flash the binary hex file to")
parser.add_argument("-ip","--ip", type=str, help="The OpenOCD ip address to connect to", default="localhost")
parser.add_argument("-p","--port", type=int, help="The OpenOCD port to connect to", default=4444)
args = parser.parse_args()

cmd_start = 'init; reset halt'
cmd_flash = [('flash write_image erase '+args.binary+' '+args.address+';','verify_image ' + args.binary +' '+args.address+';')]

cmd_done = 'reset run;'
cmd_shutdown = 'shutdown'

if not args.binary2 is None:
    cmd_flash.append(('flash write_image erase '+args.binary2+' '+args.address2+';',    'verify_image ' + args.binary2 +' '+args.address2+';'))

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
        if(int(args.address,16) != 0):
                cpu = 'lpc4337_swd'
        else:
                cpu = 'lpc11uxx'
        os.popen('openocd -f ' + cpu + '.cfg' )

    thread = Thread(target=run_openocd)
    thread.deamon = True
    thread.start()
    time.sleep(4)

tn = Telnet(args.ip, args.port)
tn.write(cmd_start + '\n')
for cmd in cmd_flash:
    done = False
    tries = 0
    while not done:
        tn.write(cmd[0] + '\n')
        tn.write(cmd[1] + '\n')
        r = tn.expect(['verified', 'error', 'checksum', 'mismatch'], 2.5)
        done = (r[0] == 0)
        tries+=1
        if tries > 4:
            print('Flashing failed\n')
            break
    print('Flashing done after %d tries\n' % tries)
tn.write(cmd_done + '\n')
if not openocdFound:
    print('shutdown openocd...')
    tn.write(cmd_shutdown + '\n')
    tn.write(cmd_shutdown + '\n')
time.sleep(0.5)
tn.sock.close()

print('done')
#else:
#	if(int(args.address,16) != 0):
#		cpu = 'lpc4337_swd'
#	else:
#		cpu = 'lpc11uxx'
#
	#cmdStr = ''.join(cmdList)	
	#print("Programming with openOCD:")
	#os.popen('openocd -f ' + cpu + '.cfg -c "'+cmdStr+'"')



