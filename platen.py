#!/usr/bin/python
#Project: EOL
#Description: 
__author__ = "Adrian Wong"
import os, time, commonFX

class sensors():
    # Temporary variables, do not modify here
    logger = ''
    com = ''

    # adjustable limits
    rear_target = 13500
    front_target = 13763
    lvlMotorTime = 4

    def update(self, logger, com):
        self.logger = logger
        self.com = com

    def readSensor(self, processID):
        # [rear, front]
        sensor = self.com.readReg(processID, 460, 2)
        if sensor[0] == 32767:
            self.logger.info("Rear sensor not detected")
            os._exit(1)
        elif sensor[0] == 0:
            self.logger.info("Rear sensor out of range")
            os._exit(1)
        if sensor[1] == 32767:
            self.logger.info("Front sensor not detected")
            os._exit(1)
        elif sensor[1] == 0:
            self.logger.info("Front sensor out of range")
            os._exit(1)
        return sensor

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
            self.com.setCoil(processID, 56, [status])
            self.resetMode(processID)
            self.com.setReg(processID, 483, [direction])

    def sensorGap(self):
        processID = 303
        read = self.readSensor(processID)
        rear = read[0]
        front = read[1]
        #rear = (float(read[0])/32767) * 10000
        #front = (float(read[1])/32767) * 10000
        if commonFX.rangeCheck(int(rear), self.rear_target, 0.02):
            self.logger.info("Rear sensors within range " + str(rear/100))
        else:
            self.logger.info("Rear sensor out of range " + str(rear/100))
            os._exit(1)
        if commonFX.rangeCheck(int(front), self.front_target, 0.02):
            self.logger.info("Front sensors within range " + str(front/100))
        else:
            self.logger.info("Front sensor out of range" + str(front/100))
            os._exit(1)

    def levelMotorTest(self):
        processID = 304
        sensorReading = self.readSensor(processID)
        self.moveLvlMotor(1, -1)
        time.sleep(self.lvlMotorTime)
        self.moveLvlMotor(0, 0)
        read = self.readSensor(processID)
        if read[0] > sensorReading[0] + 300:
            self.logger.info("Level motor installed correctly")
        else:
            self.logger.info("Level motor installed incorrectly, reverse direction")
            os._exit(1)

        # position reset
        self.moveLvlMotor(1, 1)
        read = self.readSensor(processID)
        while read[0] >= sensorReading[0] + 100:
            read = self.readSensor(processID)
        self.moveLvlMotor(0, 0)
        self.logger.info("Level motor test successful")
        self.resetMode(processID)

    def calZDBF(self):
        processID = 305
        sensor = self.com.readReg(processID, 460, 2)

        self.com.setReg(processID, 255, [10])
        read = self.com.readReg(processID, 255, 1)
        while read[0] != 14:
            read = self.com.readReg(processID, 255, 1)
        gap = self.com.readReg(processID, 5, 2)
        ZDBF = gap[0] - gap[1]
        self.logger.info("ZDBF: " + str(ZDBF))
        self.resetMode(processID)



