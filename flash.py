from telnetlib import Telnet
import argparse
import os

os.chdir(os.path.dirname(os.path.realpath(__file__)))

parser = argparse.ArgumentParser(description="Connects to a running OpenOCD server via telnet to flash a target with a given binary file to a given memory address")
parser.add_argument("binary",  help="The binary hex file to flash to the device")
parser.add_argument("address",  help="The memory address to flash the binary hex file to")
parser.add_argument("-ip","--ip", type=str, help="The OpenOCD ip address to connect to", default="localhost")
parser.add_argument("-p","--port", type=int, help="The OpenOCD port to connect to", default=4444)
args = parser.parse_args()

# detect running openocd server
openocdFound = False
for line in os.popen("ps xa"):
	fields = line.split()
	process = fields[4]
	if(process.find('openocd') >= 0):
		openocdFound = True
		break


cmdList = ['init;',
'reset halt;',
'flash write_image erase '+args.binary+' '+args.address+';',
'verify_image ' + args.binary +' '+args.address+';',
'reset run;',
'shutdown;']

if(openocdFound):
	tn = Telnet(args.ip, args.port)
	tn.write(cmdList[0] + '\n')
	tn.write(cmdList[1] + '\n')
	tn.write(cmdList[2] + '\n')
	r = tn.expect(['wrote', 'couldn'])
	if r[0] == 0:
		print('Flashing done\n')
	else:
		print('Flashing failed\n')
	tn.write(cmdList[3] + '\n')
	tn.write(cmdList[4] + '\n')
	tn.sock.close()

else:
	if(int(args.address,16) != 0):
		cpu = 'lpc4337'
	else:
		cpu = 'lpc11uxx'

	cmdStr = ''.join(cmdList)	
	print("Programming with openOCD:")
	os.popen('openocd -f ' + cpu + '.cfg -c "'+cmdStr+'"')



