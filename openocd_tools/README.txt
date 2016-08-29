This folder contains config files to flash various LPC chips with the lock pick tiny programmer.

Install the .rules file(s) from the install folder into /etc/udev/rules.d/
to make sure the JTAG programmer is allowed as non-root

- To flash the lpc11uxx family, execute "openocd -f lpc11uxx.cfg"
- To flash the lpc4337, execute "openocd -f lpc4337_swd.cfg" or "openocd -f lpc4337_jtag.cfg", using the M4 core to flash the data
- To debug lpc4337 M0 core, use "openocd -f lpc4337_m0.cfg"
- For a jtag scan, execute "openocd -f jtag-scan.cfg"
