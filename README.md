# mcu_debug
Tools for debugging & flashing firmware

This is a collection of scripts and config files to flash & debug microcontrollers.

Supported platforms:

lpc43xx_m0
lpc43xx_m4
lpc11uxx

Supported debuggers:
* OpenOCD (tested in combination with the [JTAG-lock-pick Tiny 2](http://www.distortec.com/jtag-lock-pick-tiny-2/) programmer)
* [Black Magic Probe](https://github.com/blacksphere/blackmagic/wiki)

It is intended to be used as a dependency for a firmware CPM package. See the example_blinky_m4 repository for a simple
example project that uses this package for flashing its firmware.

## requirements
- gdb
- OpenOCD (optional)
- Python >= 3.5 (lower versions probably work fine as well)

## how to use
Assuming a linux/unix os with udev, copy the the .rules file(s) from the install folder into /etc/udev/rules.d/
to make sure access to the JTAG programmer is allowed as non-root.
Depending on the os / linux distro you may need to be member of the 'dialout' group for the Black Magic Probe to work.

## flashing a firmware CPM package

Checkout a firmware package, for example example_blinky_m4. Create a build dir: `mkdir build && cd build`.
- execute `make flash` to flash the firmware


## OpenOCD

### Debugging

For debugging via OpenOCD, you need to start the openocd server manually.
For example, to debug lpc4337 M0 core, use "openocd -f lpc4337_m0.cfg"

### Flashing firmware
Simply execute "make flash". If you have an existing openocd server running,
it will be re-used, otherwise it will auto-start in the background.
If flashing fails, make sure to close existing debug sessions.

### Misc

For a jtag scan, execute "openocd -f jtag-scan.cfg"

## Black Magic Probe

### Debugging

Simply execute "make debug"

### Flashing firmware

Simply execute "make flash"


