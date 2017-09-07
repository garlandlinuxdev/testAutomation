#!/usr/bin/python
#Project: LCD display
#Description: This module prints line to display screen
__author__ = "Adrian Wong"
import os, time, textwrap

class display():
    delay = 1
    FB_Y = 10
    max_line = 468
    linuxPath = os.path.dirname(__file__)
    logPath = '/log/'  # log files storage path
    sysPath = '/system/'  # system required storage path
    usbDIR = '/media/usb0/' # usb storage path on UI
    FBUTIL = linuxPath + sysPath + 'fbutil'

    def fb_println(self, msg, color):
        # Print a line on framebuffer.
        # '-x' Default is 10, 18 pixels = 16 + 2 = Font_Height + Line_Spacing.
        # y = 26 lines x = 46 characters

        if color == 1:
            os.popen(self.FBUTIL + ' -y ' + str(self.FB_Y) + ' -r ' + 'red ' + ' ' + r"""%r""" % msg)

        else:
            os.popen(self.FBUTIL + ' -y ' + str(self.FB_Y) + ' ' + r"""%r""" %msg)
        self.FB_Y = self.FB_Y + 18

        if self.FB_Y >= self.max_line:
            # max lines = 26 * 18 pixels = 468
            time.sleep(self.delay)
            self.fb_clear()

    def fb_long_print(self, msg, color):
        list = textwrap.wrap(msg, 46)
        if color == 1:
            for element in list:
                os.popen(self.FBUTIL + ' -y ' + str(self.FB_Y) + ' -r ' + 'red ' + ' ' + r"""%r""" %element)
                self.FB_Y = self.FB_Y + 18

        else:
            for element in list:
                os.popen(self.FBUTIL + ' -y ' + str(self.FB_Y) + ' ' + r"""%r""" %element)
                self.FB_Y = self.FB_Y + 18

        if self.FB_Y >= self.max_line:
            # max lines = 26 * 18 pixels = 468
            time.sleep(self.delay)
            self.fb_clear()

    def fb_clear(self):
        self.FB_Y = 10
        os.popen(self.FBUTIL + ' -c')

    def keepON(self):
        time.sleep(self.delay * 10)
        os.popen(self.FBUTIL + ' -y ' + str(self.FB_Y) + ' ' + " ")


def main():
    lcd = display()
    lcd.fb_clear()
    for x in range(1, 100, 1):
        lcd.fb_println(x, 0)
    # print lcd.FB_Y
    # lcd.fb_println('testing1234')
    # print lcd.FB_Y
    # lcd.fb_println('1234567890123456789012345678901234567890123456')


#main starts here

if __name__ == "__main__":
    main()