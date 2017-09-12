#!/usr/bin/python
# Project: EOL
# Description: Motion control related to actuator
__author__ = "Adrian Wong"
import os, time, commonFX, LCD


class motion():
    # Temporary variables, do not modify here
    logger = ''
    com = ''
    display = LCD.display()

    # adjustable limits
    timeout = 30  # max time limit for each task completion, flag error when exceeded
    magnetTolerance = 0.02  # percentage of error allowed for magnet drift test
    killSP = [-8000, 5000]  # [high, low] setpoint for kill switch test
    oc_time = 2  # time in seconds required to flag over current error
    oc_runtime = 5  # runtime for over current test

    def updateLCD(self, FB_Y):
        if FB_Y >= self.display.max_line:
            self.display.fb_clear()
        else:
            self.display.FB_Y = FB_Y

    def update(self, logger, com, timeout, magnet, killsp, oc_time, oc_runtime):
        self.logger = logger
        self.com = com
        self.timeout = timeout
        self.magnetTolerance = magnet
        self.killSP = killsp
        self.oc_time = oc_time
        self.oc_runtime = oc_runtime

    def setpoint(self, SP):
        processID = 200
        self.com.setReg(processID, 0, [SP])
        self.logger.info("Writing setpoint reg 0 to %r" % SP)

    def spFeedback(self):
        processID = 201
        fb = self.com.readReg(processID, 3, 1)
        return commonFX.signedInt(fb[0])

    def resetMode(self, processID):
        self.com.setReg(processID, 255, [2])

    def stopMotion(self, processID):
        self.com.setReg(processID, 255, [0])

    def homing(self):
        processID = 202
        encoder = [0, 0]
        self.com.setReg(processID, 25, [0])
        self.com.setReg(processID, 255, [1])
        homeStatus = self.com.readReg(processID, 25, 1)
        startTime = time.time()
        while homeStatus[0] != 5 and commonFX.timeCal(startTime) < self.timeout:
            homeStatus = self.com.readReg(processID, 25, 1)

        if homeStatus[0] != 5:
            self.logger.info("Homing sequence failed, @ processID %r" % processID)
            self.stopMotion(processID)
            os._exit(1)

        self.logger.info("Homing sequence successful, @ processID %r" % processID)

        # Find switch location
        self.com.setReg(processID, 255, [3])
        read = self.com.readReg(processID, 255, 1)
        startTime = time.time()
        while read[0] != 5 and commonFX.timeCal(startTime) < self.timeout / 2:
            read = self.com.readReg(processID, 255, 1)
        time.sleep(1)
        encRead = self.com.readReg(processID, 3, 1)
        encoder[0] = commonFX.signedInt(encRead[0])
        self.logger.info("Lift switch location: %r" % encoder[0])

        self.com.setReg(processID, 255, [6])
        read = self.com.readReg(processID, 255, 1)
        while read[0] != 8 and commonFX.timeCal(startTime) < self.timeout / 2:
            read = self.com.readReg(processID, 255, 1)
        time.sleep(1)
        encRead = self.com.readReg(processID, 3, 1)
        encoder[1] = commonFX.signedInt(encRead[0])
        self.logger.info("Home switch location: %r" % encoder[1])

        self.display.fb_println("Lift switch location: %r" % encoder[0], 0)
        self.display.fb_println("Home switch location: %r" % encoder[1], 0)

        return self.display.FB_Y, encoder

    def switchTest(self):
        processID = 203
        self.com.setReg(processID, 255, [3])
        read = self.com.readReg(processID, 255, 1)
        startTime = time.time()
        while read[0] != 5 and commonFX.timeCal(startTime) < self.timeout / 2:
            read = self.com.readReg(processID, 255, 1)
        if read[0] != 5:
            self.logger.info("Seeking upper switch failed, @ processID %r" % processID)
            self.display.fb_println("Seeking upper switch failed, @ processID %r" % processID, 1)
            self.stopMotion(processID)
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
            self.display.fb_println("Seeking lower switch failed, @ processID %r" % processID, 0)
            self.stopMotion(processID)
            os._exit(1)

        self.logger.info("Seeking lower switch successful, @ processID %r" % processID)
        endTime = commonFX.timeCal(timer)
        encDown = self.spFeedback()
        distance = abs(encUP - encDown)
        self.logger.info("Distance between Lift and Home switch (count): " + str(distance))
        self.logger.info("Time elapse (sec): " + str(endTime))
        self.logger.info("Actuator speed (count/sec): " + str(distance / endTime))
        self.display.fb_println("Distance between switches (count): %r" % distance, 0)

        self.display.fb_println("Time elapse (sec): %r" % round(endTime, 3), 0)
        self.display.fb_println("Actuator speed (count/sec): %r" % round((distance / endTime), 3), 0)
        self.resetMode(processID)
        return self.display.FB_Y, [distance, endTime]

    def magnetDrift(self):
        processID = 204
        self.com.setReg(processID, 255, [3])
        read = self.com.readReg(processID, 255, 1)
        startTime = time.time()
        while read[0] != 5 and commonFX.timeCal(startTime) < self.timeout / 2:
            read = self.com.readReg(processID, 255, 1)
        if read[0] != 5:
            self.logger.info("Seeking upper switch failed, @ processID %r" % processID)
            self.display.fb_println("Seeking upper switch failed, @ processID %r" % processID, 1)
            self.stopMotion(processID)
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
            self.display.fb_println("Seeking lower switch failed, @ processID %r" % processID, 1)
            self.stopMotion(processID)
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
            self.display.fb_println("Seeking upper switch failed, @ processID %r" % processID, 1)
            self.stopMotion(processID)
            os._exit(1)
        self.logger.info("Seeking upper switch successful, @ processID %r" % processID)
        endTime = commonFX.timeCal(startTime)
        self.resetMode(processID)
        encUP = self.spFeedback()
        distanceUP = abs(encDown - encUP)
        drift = abs(distanceUP - distanceDOWN)

        self.logger.info("Time elapse: " + str(endTime))

        if commonFX.rangeCheck(distanceDOWN, distanceUP, self.magnetTolerance):
            self.logger.info("Distance moving down: " + str(distanceDOWN))
            self.logger.info("Distance moving up: " + str(distanceUP))
            self.logger.info("Encoder magnet ok, no drift found")
            self.display.fb_println("Distance moving down: %r" % distanceDOWN, 0)
            self.display.fb_println("Distance moving up: %r" % distanceUP, 0)
            self.display.fb_println("Encoder magnet ok, no drift found", 0)
        else:
            self.logger.info("Distance moving down: " + str(distanceDOWN))
            self.logger.info("Distance moving up: " + str(distanceUP))
            self.logger.info("Check encoder magnet, %r count drift found" % drift)
            self.display.fb_println("Distance moving down: %r" % distanceDOWN, 1)
            self.display.fb_println("Distance moving up: %r" % distanceUP, 1)
            self.display.fb_println("Check encoder magnet, %r count drift found" % drift, 1)
            os._exit(1)
        return self.display.FB_Y, [distanceDOWN, distanceUP, drift]

    def killSwitchTest(self):
        processID = 205
        encoder = [0, 0]
        status = self.com.readReg(processID, 25, 1)
        if status[0] != 5:
            self.homing()
        self.resetMode(processID)
        self.com.setReg(processID, 0, [self.killSP[0]])
        time.sleep(5)
        startTime = time.time()
        upperSW = self.com.readCoil(processID, 7, 1)
        if upperSW[0]:
            self.com.setCoil(processID, 55, [0])
            timer = time.time()
            while commonFX.timeCal(startTime) <= self.oc_runtime:
                oc = self.com.readCoil(processID, 55, 1)
                if oc[0] == 1:
                    self.com.setCoil(processID, 55, [0])
                else:
                    timer = time.time()
                if commonFX.timeCal(timer) >= self.oc_time:
                    self.logger.info("Over current detected, upper kill switch failed")
                    self.display.fb_println("Over current detected, upper kill switch failed", 1)
                    self.stopMotion(processID)
                    os._exit(1)
        else:
            self.logger.info("Platen did not reach upper switch")
            self.display.fb_println("Platen did not reach upper switch", 1)
            self.stopMotion(processID)
            os._exit(1)

        encRead = self.com.readReg(processID, 3, 1)
        encoder[0] = commonFX.signedInt(encRead[0])
        self.logger.info("Upper kill switch location: %r" % encoder[0])
        self.display.fb_println("Upper kill switch location: %r" % encoder[0], 0)

        self.com.setReg(processID, 0, [self.killSP[1]])
        time.sleep(8)
        startTime = time.time()
        lowerSW = self.com.readCoil(processID, 6, 1)
        if lowerSW[0]:
            self.com.setCoil(processID, 55, [0])
            timer = time.time()
            while commonFX.timeCal(startTime) <= self.oc_runtime:
                oc = self.com.readCoil(processID, 55, 1)
                if oc[0] == 1:
                    self.com.setCoil(processID, 55, [0])
                else:
                    timer = time.time()
                if commonFX.timeCal(timer) >= self.oc_time:
                    self.logger.info("Over current detected, lower kill switch failed")
                    self.display.fb_println("Over current detected, lower kill switch failed", 1)
                    self.stopMotion(processID)
                    os._exit(1)

            lowerSW = self.com.readCoil(processID, 6, 1)
            if lowerSW[0]:
                self.logger.info("Home switch remain engaged, switch bracket ok ")
            else:
                self.logger.info("Home switch disengaged, check switch bracket or crossbar")
                self.display.fb_println("Home switch disengaged, check switch bracket", 1)
                self.stopMotion(processID)
                os._exit(1)
        else:
            self.logger.info("Platen did not reach lower switch")
            self.display.fb_println("Platen did not reach lower switch", 1)
            self.stopMotion(processID)
            os._exit(1)

        encRead = self.com.readReg(processID, 3, 1)
        encoder[1] = commonFX.signedInt(encRead[0])
        self.logger.info("Lower kill switch location: %r" % encoder[1])
        self.display.fb_println("Lower kill switch location: %r" % encoder[1], 0)

        self.logger.info("Kill switch test successful")
        self.stopMotion(processID)
        return self.display.FB_Y, encoder


def main():
    x = 1

    # main starts here


if __name__ == "__main__":
    main()
