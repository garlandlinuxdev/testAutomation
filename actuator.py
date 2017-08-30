#!/usr/bin/python
# Project: EOL
# Description: Motion control related to actuator
__author__ = "Adrian Wong"
import os, time, commonFX


class motion():
    # Temporary variables, do not modify here
    logger = ''
    com = ''
    timeout = 30  # max time limit for each task completion, flag error when exceeded

    # adjustable limits
    magnetTolerance = 0.02 # percentage of error allowed for magnet drift test

    def update(self, logger, com, timeout):
        self.logger = logger
        self.com = com
        self.timeout = timeout

    def setpoint(self, SP):
        processID = 200
        self.com.setReg(processID, 0, [SP])
        self.logger.info("Writing setpoint reg 0 to %r" % SP)

    def spFeedback(self):
        processID = 201
        fb = self.com.readReg(processID, 3, 1)
        return commonFX.signedInt(fb[0])

    def homing(self):
        processID = 202
        self.com.setReg(processID, 25, [0])
        self.com.setReg(processID, 255, [1])
        homeStatus = self.com.readReg(processID, 25, 1)
        startTime = time.time()
        while homeStatus[0] != 5 and commonFX.timeCal(startTime) < self.timeout:
            homeStatus = self.com.readReg(processID, 25, 1)

        if homeStatus[0] != 5:
            self.logger.info("Homing sequence failed, @ processID %r" % processID)
            os._exit(1)

        self.logger.info("Homing sequence successful, @ processID %r" % processID)

    def switchTest(self):
        processID = 203
        self.com.setReg(processID, 255, [3])
        read = self.com.readReg(processID, 255, 1)
        startTime = time.time()
        while read[0] != 5 and commonFX.timeCal(startTime) < self.timeout / 2:
            read = self.com.readReg(processID, 255, 1)
        if read[0] != 5:
            self.logger.info("Seeking upper switch failed, @ processID %r" % processID)
            os._exit(1)
        self.logger.info("Seeking upper switch successful, @ processID %r" % processID)
        encUP = self.spFeedback()

        self.com.setReg(processID, 255, [6])
        timer = time.time()
        read = self.com.readReg(processID, 255, 1)
        startTime = time.time()
        while read[0] != 8 and commonFX.timeCal(startTime) < self.timeout / 2:
            read = self.com.readReg(processID, 255, 1)
        if read[0] != 8:
            self.logger.info("Seeking lower switch failed, @ processID %r" % processID)
            os._exit(1)
        self.logger.info("Seeking lower switch successful, @ processID %r" % processID)
        endTime = commonFX.timeCal(timer)
        encDown = self.spFeedback()
        distance = abs(encUP - encDown)
        self.logger.info("Distance between Lift and Home switch (count): " + str(distance))
        self.logger.info("Time elapse (sec): " + str(endTime))
        self.logger.info("Actuator speed (count/sec): " + str(distance / endTime))

    def magnetDrift(self):
        processID = 204
        self.com.setReg(processID, 255, [3])
        read = self.com.readReg(processID, 255, 1)
        startTime = time.time()
        while read[0] != 5 and commonFX.timeCal(startTime) < self.timeout / 2:
            read = self.com.readReg(processID, 255, 1)
        if read[0] != 5:
            self.logger.info("Seeking upper switch failed, @ processID %r" % processID)
            os._exit(1)
        self.logger.info("Seeking upper switch successful, @ processID %r" % processID)
        encUP = self.spFeedback()

        self.com.setReg(processID, 255, [6])
        timer = time.time()
        read = self.com.readCoil(processID, 6, 1)
        startTime = time.time()
        while read[0] != 1 and commonFX.timeCal(startTime) < self.timeout / 2:
            read = self.com.readCoil(processID, 6, 1)
            time.sleep(0.5)
            self.com.setReg(processID, 255, [0])
            time.sleep(0.5)
            self.com.setReg(processID, 255, [6])
        if read[0] != 1:
            self.logger.info("Seeking lower switch failed, @ processID %r" % processID)
            os._exit(1)
        self.logger.info("Seeking lower switch successful, @ processID %r" % processID)
        encDown = self.spFeedback()
        distanceDOWN = abs(encUP - encDown)

        self.com.setReg(processID, 255, [3])
        read = self.com.readReg(processID, 255, 1)
        startTime = time.time()
        while read[0] != 5 and commonFX.timeCal(startTime) < self.timeout / 2:
            read = self.com.readReg(processID, 255, 1)
        if read[0] != 5:
            self.logger.info("Seeking upper switch failed, @ processID %r" % processID)
            os._exit(1)
        self.logger.info("Seeking upper switch successful, @ processID %r" % processID)
        encUP = self.spFeedback()
        distanceUP = abs(encDown - encUP)

        if commonFX.rangeCheck(distanceDOWN, distanceUP, self.magnetTolerance):
            self.logger.info("Distance moving down: " + str(distanceDOWN))
            self.logger.info("Distance moving up: " + str(distanceUP))
            self.logger.info("No drift found on encoder magnet")
        else:
            self.logger.info("Distance moving down: " + str(distanceDOWN))
            self.logger.info("Distance moving up: " + str(distanceUP))
            self.logger.info("drift found on encoder magnet, check encoder on actuator")
            os._exit(1)


def main():
    x = 1

    # main starts here


if __name__ == "__main__":
    main()