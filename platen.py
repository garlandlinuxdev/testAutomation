#!/usr/bin/python
#Project: EOL
#Description: 
__author__ = "Adrian Wong"
import os, commonFX

class sensors():
    # Temporary variables, do not modify here
    logger = ''
    com = ''

    # adjustable limits
    rear_target = 4273 # percentage of pwm, reading/32767 * 10000, 50% = 5000
    front_target = 4273

    def update(self, logger, com):
        self.logger = logger
        self.com = com

    def readSensor(self, processID):
        # [rear, front]
        read = self.com.readReg(processID, 460, 2)
        return read

    def resetMode(self, processID):
        self.com.setReg(processID, 255, [2])

    def moveLvlMotor(self, status, direction):
        # 1 -> CCW moving down, -1 -> CW moving up
        processID = 302
        if status == 1:
            self.com.setCoil(processID, 56, [status])
            self.com.setReg(processID, 255, [28])
            self.com.setReg(processID, 255, [29])
            self.com.setReg(processID, 483, [direction])

        else:
            self.com.setCoil(processID, 56, status)
            self.resetMode(processID)
            self.com.setReg(processID, 483, [direction])

    def sensorGap(self):
        processID = 303
        read = self.readSensor(processID)
        rear = (float(read[0])/32767) * 10000
        front = (float(read[1])/32767) * 10000
        print rear, front
        if commonFX.rangeCheck(int(rear), self.rear_target, 0.05):
            self.logger.info("Rear sensors within range " + str(rear/100))
        else:
            self.logger.info("Rear sensor out of range " + str(rear/100))
            os._exit(1)
        if commonFX.rangeCheck(int(front), self.front_target, 0.05):
            self.logger.info("Front sensors within range " + str(front/100))
        else:
            self.logger.info("Front sensor out of range" + str(front/100))
            os._exit(1)


