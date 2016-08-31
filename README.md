# openocd_tools
Tools for flashing firmware with OpenOCD

This is a collection of scripts and config files to flash various LPC microcontrollers with OpenOCD,
in combination with the lock pick tiny programmer.

It is intended to be used as a dependency for a firmware CPM package. See the example_blinky_m4 repository for a simple
example project that uses this package for flashing its firmware.

## requirements
- OpenOCD
- Python >= 3.5 (lower versions probably work fine as well)

## how to use
Assuming a linux/unix os with udev, copy the the .rules file(s) from the install folder into /etc/udev/rules.d/
to make sure access to the JTAG programmer is allowed as non-root.

## manual flashing

- To flash the lpc11uxx family, execute "openocd -f lpc11uxx.cfg"
- To flash the lpc4337, execute "openocd -f lpc4337_swd.cfg" or "openocd -f lpc4337_jtag.cfg", using the M4 core to flash the data
- To debug lpc4337 M0 core, use "openocd -f lpc4337_m0.cfg"
- For a jtag scan, execute "openocd -f jtag-scan.cfg"

## flashing a firmware CPM package

Checkout a firmware package, for example example_blinky_m4. Create a build dir: `mkdir build && cd build`.
- execute `make flash` to flash the firmware
