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
    magnet_drift_target = 50 # maximum drift target
    magnet_setpoint = -1000 # lower position for magnet drift test (before hitting home switch)
    magnet_testrun = 3 # total amount of test run for magnet drift test
    killSP = [-8000, 5000]  # [high, low] setpoint for kill switch test
    oc_time = 2  # time in seconds required to flag over current error
    oc_runtime = 5  # runtime for over current test
    encoder_conv = 0.000492126  # conversion from encoder count to inches

    def update(self, logger, com, config):
        self.logger = logger
        self.com = com
        self.timeout = config.actuator_config[0]
        self.magnetTolerance = config.actuator_config[1]
        self.magnet_drift_target = config.actuator_config[2]
        self.magnet_setpoint = config.actuator_config[3]
        self.magnet_testrun = config.actuator_config[4]
        self.killSP = config.actuator_config[5]
        self.oc_time = config.actuator_config[6]
        self.oc_runtime = config.actuator_config[7]
        self.encoder_conv = config.actuator_config[8]

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

    def homing(self, processID):
        homeStatus = self.com.readReg(processID, 25, 1)
        if homeStatus[0] != 5:
            self.com.setReg(processID, 25, [0])
            self.com.setReg(processID, 255, [1])
        startTime = time.time()
        while homeStatus[0] != 5 and commonFX.timeCal(startTime) < self.timeout:
            homeStatus = self.com.readReg(processID, 25, 1)

        if homeStatus[0] != 5:
            self.logger.info("Homing sequence failed, @ processID %r" % processID)
            self.stopMotion(processID)
            os._exit(1)

        self.logger.info("Homing sequence successful, @ processID %r" % processID)

    def switchTest(self, config):
        processID = 203

        # seek lower switch for initial position
        self.com.setReg(processID, 255, [6])
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

        # seek upper switch
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
        endTimeUP = commonFX.timeCal(startTime)
        time.sleep(1)
        encUP = self.spFeedback()

        # seek lower switch
        self.com.setReg(processID, 255, [6])
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
        endTimeDN = commonFX.timeCal(startTime)
        time.sleep(1)
        encDown = self.spFeedback()

        # results
        distance = abs(encUP - encDown) * config.encoder_conv
        self.logger.info("Distance between Lift and Home switch (inch): " + str(distance))
        self.logger.info("Lift switch location (count): %r" % encUP)
        self.logger.info("Home switch location (count): %r" % encDown)
        self.logger.info("Moving upwards time elapse (sec): " + str(endTimeUP))
        self.logger.info("Moving downwards time elapse (sec): " + str(endTimeDN))
        self.logger.info("Actuator speed upwards (inch/sec): " + str(distance / endTimeUP))
        self.logger.info("Actuator speed downwards (inch/sec): " + str(distance / endTimeDN))
        self.display.fb_println("Lift switch location (count): %r" % encUP, 0)
        self.display.fb_println("Home switch location (count): %r" % encDown, 0)
        return [encUP, encDown], [endTimeUP, endTimeDN]

    def magnetDrift(self, config):
        processID = 204
        test = 1
        error = 0
        distanceUP = [0]
        distanceDOWN = [0]
        drift = [0]

        while test <= self.magnet_testrun:
            self.homing(processID)
            self.logger.info("Test run #%r" % test)
            self.display.fb_println("Test run #%r" % test, 0)
            # seek upper reference switch
            self.com.setReg(processID, 255, [3])
            read = self.com.readReg(processID, 255, 1)
            startTime = time.time()
            while read[0] != 5 and commonFX.timeCal(startTime) < self.timeout:
                read = self.com.readReg(processID, 255, 1)
            if read[0] != 5:
                self.logger.info("Seeking upper switch failed, @ processID %r" % processID)
                self.display.fb_println("Seeking upper switch failed, @ processID %r" % processID, 1)
                self.stopMotion(processID)
                os._exit(1)
            self.logger.info("Seeking upper switch successful, @ processID %r" % processID)
            encUPintial = self.spFeedback()

            # move to lower test setpoint
            self.setpoint(self.magnet_setpoint)
            self.resetMode(processID)
            read = self.com.readReg(processID, 0, 1)
            startTime = time.time()
            while commonFX.signedInt(read[0]) != -32768 and commonFX.timeCal(startTime) < self.timeout:
                read = self.com.readReg(processID, 0, 1)
                if commonFX.signedInt(read[0]) != -32768:
                    time.sleep(0.4)
                    self.com.setReg(processID, 255, [0])
                    time.sleep(0.4)
                    self.resetMode(processID)

            if commonFX.timeCal(startTime) > self.timeout:
                self.logger.info("Motor did not reach lower target > %r" %self.timeout)
                self.display.fb_println("Motor did not reach lower target > %r" %self.timeout, 1)
                self.stopMotion(processID)
                os._exit(1)

            read = self.com.readCoil(processID, 6, 1)
            if read[0] == 1:
                self.logger.info("Reduce lower setpoint required, home switch pressed")
                self.display.fb_println("Reduce lower setpoint required, home switch pressed")
                self.stopMotion(processID)
                os._exit(1)

            self.resetMode(processID)
            encDown = self.spFeedback()
            distanceDOWN.append(abs(encUPintial - encDown))

            # seek upper reference switch
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
            self.resetMode(processID)
            encUP = self.spFeedback()
            distanceUP.append(abs(encDown - encUP))
            drift.append(abs(distanceUP[test] - distanceDOWN[test]))

            if drift[test] <= self.magnet_drift_target:
                self.logger.info("Distance moving up: " + str(distanceUP[test]))
                self.logger.info("Distance moving down: " + str(distanceDOWN[test]))
                self.logger.info("Encoder magnet ok, no drift found (%r)" %drift[test])
                self.display.fb_println("Distance moving up: %r" % distanceUP[test], 0)
                self.display.fb_println("Distance moving down: %r" % distanceDOWN[test], 0)
                self.display.fb_println("Encoder magnet ok, no drift found (%r)" %drift[test], 0)
            else:
                self.logger.info("Distance moving up: " + str(distanceUP[test]))
                self.logger.info("Distance moving down: " + str(distanceDOWN[test]))
                self.logger.info("Check encoder magnet, %r count drift found" % drift[test])
                self.display.fb_println("Distance moving up: %r" % distanceUP[test], 1)
                self.display.fb_println("Distance moving down: %r" % distanceDOWN[test], 1)
                self.display.fb_println("Check encoder magnet, %r count drift found" % drift[test], 1)
                error += 1
                #os._exit(1)

            test += 1

        if error >= 2:
            self.logger.info("Check encoder magnet, max drift count (%r)" % max(drift))
            self.display.fb_println("Magnet test failed, max drift count (%r)" % max(drift), 1)
            os._exit(1)

        index = drift.index(max(drift))

        return [distanceDOWN[index], distanceUP[index], max(drift)]

    def killSwitchTest(self):
        processID = 205
        encoder = [0, 0]
        status = self.com.readReg(processID, 25, 1)
        if status[0] != 5:
            self.homing(processID)
        self.resetMode(processID)

        # seek upper switch
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
        self.resetMode(processID)

        # move to high setpoint
        self.com.setReg(processID, 0, [self.killSP[0]])
        time.sleep(4)
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
            self.logger.info("Platen did not reach upper position")
            self.display.fb_println("Platen did not reach upper position", 1)
            self.stopMotion(processID)
            os._exit(1)

        encRead = self.com.readReg(processID, 3, 1)
        encoder[0] = commonFX.signedInt(encRead[0])
        self.logger.info("Upper kill switch location: %r" % encoder[0])
        self.display.fb_println("Upper kill switch location: %r" % encoder[0], 0)

        # seek lower reference switch
        self.com.setReg(processID, 255, [6])
        read = self.com.readReg(processID, 255, 1)
        startTime = time.time()
        while read[0] != 8 and commonFX.timeCal(startTime) < self.timeout:
            read = self.com.readReg(processID, 255, 1)

        if read[0] != 8:
            self.logger.info("Seeking lower switch failed, @ processID %r" % processID)
            self.display.fb_println("Seeking lower switch failed, @ processID %r" % processID, 1)
            self.stopMotion(processID)
            os._exit(1)
        self.logger.info("Seeking lower switch successful, @ processID %r" % processID)
        self.resetMode(processID)

        # move to low setpoint
        self.com.setReg(processID, 0, [self.killSP[1]])
        time.sleep(5)
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
            self.logger.info("Platen did not reach lower position")
            self.display.fb_println("Platen did not reach lower position", 1)
            self.stopMotion(processID)
            os._exit(1)

        encRead = self.com.readReg(processID, 3, 1)
        encoder[1] = commonFX.signedInt(encRead[0])
        self.logger.info("Lower kill switch location: %r" % encoder[1])
        self.display.fb_println("Lower kill switch location: %r" % encoder[1], 0)
        self.logger.info("Kill switch test successful")
        self.resetMode(processID)
        self.stopMotion(processID)
        return encoder