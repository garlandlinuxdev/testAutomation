#!/usr/bin/python
# Project: LCD display
# Description: This module prints line to display screen
__author__ = "Adrian Wong"
import os, time, textwrap, subfile
from sys import platform

class display():
    delay = 1
    FB_Y = 10
    max_line = 468
    linuxPath = os.path.dirname(__file__)
    logPath = '/log/'  # log files storage path
    sysPath = '/system/'  # system required storage path
    usbDIR = '/media/usb0/'  # usb storage path on UI
    FBUTIL = linuxPath + sysPath + 'fbutil'
    myPlatform = False

    def checkOS(self):
        if platform == "linux" or platform == "linux2":
            # linux
            self.myPlatform = True
        elif platform == "darwin":
            # OS X
            self.myPlatform = False
        elif platform == "win32" or platform == "cygwin":
            # Windows...
            self.myPlatform = False

    def updateFB_Y(self):
        subfile.storage(self.FB_Y) # update global Y position

    def fb_println(self, msg, color):
        self.checkOS()
        if self.myPlatform == False:
            return
        # Print a line on framebuffer.
        # '-x' Default is 10, 18 pixels = 16 + 2 = Font_Height + Line_Spacing.
        # y = 26 lines x = 46 characters
        self.FB_Y = subfile.getStorage() # get global Y position

        if color == 1:
            os.popen(self.FBUTIL + ' -y ' + str(self.FB_Y) + ' -r ' + 'red ' + ' ' + r"""%r""" % msg)

        else:
            os.popen(self.FBUTIL + ' -y ' + str(self.FB_Y) + ' ' + r"""%r""" % msg)
        self.FB_Y = self.FB_Y + 18
        self.updateFB_Y()

        if self.FB_Y >= self.max_line:
            # max lines = 26 * 18 pixels = 468
            time.sleep(self.delay)
            self.fb_clear()

    def fb_long_print(self, msg, color):
        self.checkOS()
        if self.myPlatform == False:
            return
        list = textwrap.wrap(msg, 46)
        self.FB_Y = subfile.getStorage()
        if color == 1:
            for element in list:
                os.popen(self.FBUTIL + ' -y ' + str(self.FB_Y) + ' -r ' + 'red ' + ' ' + r"""%r""" % element)
                self.FB_Y = self.FB_Y + 18
                self.updateFB_Y()

        else:
            for element in list:
                os.popen(self.FBUTIL + ' -y ' + str(self.FB_Y) + ' ' + r"""%r""" % element)
                self.FB_Y = self.FB_Y + 18
                self.updateFB_Y()

        if self.FB_Y >= self.max_line:
            # max lines = 26 * 18 pixels = 468
            time.sleep(self.delay)
            self.fb_clear()

    def fb_clear(self):
        self.checkOS()
        if self.myPlatform == False:
            return
        self.FB_Y = 10
        self.updateFB_Y()
        os.popen(self.FBUTIL + ' -c')

    def keepON(self):
        self.checkOS()
        if self.myPlatform == False:
            return
        os.popen(self.FBUTIL + ' -C ' + self.linuxPath + self.sysPath + 'image')
        while True:
            time.sleep(self.delay * 5)
            os.popen(self.FBUTIL + ' -R ' + self.linuxPath + self.sysPath + 'image')


def main():
    lcd = display()
    lcd.fb_clear()
    for x in range(1, 100, 1):
        lcd.fb_println(x, 0)
        # print lcd.FB_Y
        # lcd.fb_println('testing1234')
        # print lcd.FB_Y
        # lcd.fb_println('1234567890123456789012345678901234567890123456')


# main starts here

if __name__ == "__main__":
    main()
