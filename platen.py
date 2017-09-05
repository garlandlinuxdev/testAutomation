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
    sensor_target = [13500, 13763] # [rear, front]
    lvlMotorTime = 4

    def update(self, logger, com, sensor_target):
        self.logger = logger
        self.com = com
        self.sensor_target = sensor_target

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
        if commonFX.rangeCheck(int(rear), self.sensor_target[0], 0.02):
            self.logger.info("Rear sensors within range (mm) " + str((rear*10.0)/32767))
        else:
            self.logger.info("Rear sensor out of range (mm) " + str((rear*10.0)/32767))
            os._exit(1)
        if commonFX.rangeCheck(int(front), self.sensor_target[1], 0.02):
            self.logger.info("Front sensors within range (mm) " + str((front*10.0)/32767))
        else:
            self.logger.info("Front sensor out of range (mm) " + str((front*10.0)/32767))
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
        elif read[0] <= sensorReading[0] - 300:
            self.logger.info("Level motor moving in reverse direction")
            os._exit(1)
        else:
            self.logger.info("No level motor movement detected")
            os._exit(1)

        # position reset
        read = self.readSensor(processID)
        while commonFX.rangeCheck(read[0], sensorReading[0], 0.001) != True:
            read = self.readSensor(processID)
            if read[0] > sensorReading[0]:
                self.moveLvlMotor(1, 1)
            elif read[0] < sensorReading[0]:
                self.moveLvlMotor(1, -1)
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



