# Siglent SDS 1104X-E Setup - Raspberry Pi

Here are notes I have taken in order to get the SDS 1104X-E working properly with PyVisa and USB to a Raspberry Pi 4

Install the following driver (may need to use sudo)

https://github.com/alexforencich/python-usbtmc

Make sure to use the filename specified when adding the configuration (/etc/udev/rules.d/usbtmc.rules)

https://community.element14.com/members-area/personalblogs/b/blog/posts/step-by-step-guide-how-to-use-gpib-with-raspberry-pi-linux

Need to fix permissions to get USB working:

https://techoverflow.net/2019/08/09/how-to-fix-pyvisa-found-a-device-whose-serial-number-cannot-be-read-the-partial-visa-resource-name-is-usb0-0instr/
