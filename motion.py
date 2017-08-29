#!/usr/bin/python
# Project: EOL
# Description: Motion control related to actuator
__author__ = "Adrian Wong"
import os, time

class actuator():
    # Temporary variables, do not modify here
    logger = ''
    com = ''
    timeout = 30  # max time limit for each task completion, flag error when exceeded

    def update(self, logger, com, timeout):
        self.logger = logger
        self.com = com
        self.timeout = timeout

    def timeCal(self, arg):  # time calculation
        timeElapse = time.time() - long(arg)
        return timeElapse

    def setpoint(self, SP):
        process = 200
        self.com.setReg(process, 0, [SP])
        self.logger.info("Writing setpoint reg 0 to %r" % SP)

    def spFeedback(self):
        process = 201
        fb = self.com.readReg(process, 3, 1)
        return fb[0]

    def homing(self):
        process = 202
        self.com.setReg(process, 25, [0])
        self.com.setReg(process, 255, [1])
        homeStatus = self.com.readReg(process, 25, 1)
        startTime = time.time()
        while homeStatus[0] != 5 and self.timeCal(startTime) < self.timeout:
            homeStatus = self.com.readReg(process, 25, 1)

        if homeStatus[0] != 5:
            self.logger.info("Homing sequence failed, @ processID %r" % process)
            os._exit(1)

        self.logger.info("Homing sequence successful, @ processID %r" % process)

    def switchTest(self):
        process = 203
        self.com.setReg(process, 255, [3])
        read = self.com.readReg(process, 255, 1)
        startTime = time.time()
        while read[0] != 5 and self.timeCal(startTime) < self.timeout / 2:
            read = self.com.readReg(process, 255, 1)
        if read[0] != 5:
            self.logger.info("Seeking upper switch failed, @ processID %r" % process)
            os._exit(1)

        self.logger.info("Seeking upper switch successful, @ processID %r" % process)

        self.com.setReg(process, 255, [6])
        read = self.com.readReg(process, 255, 1)
        startTime = time.time()
        while read[0] != 8 and self.timeCal(startTime) < self.timeout / 2:
            read = self.com.readReg(process, 255, 1)
        if read[0] != 8:
            self.logger.info("Seeking lower switch failed, @ processID %r" % process)
            os._exit(1)

        self.logger.info("Seeking lower switch successful, @ processID %r" % process)


def main():
    x = 1

    # main starts here


if __name__ == "__main__":
    main()
