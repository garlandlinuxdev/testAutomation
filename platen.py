#!/usr/bin/python
# Project: EOL
# Description:
__author__ = "Adrian Wong"
import os, time, commonFX, LCD


class sensors():
    # Temporary variables, do not modify here
    logger = ''
    com = ''
    display = LCD.display()

    # adjustable limits
    sensor_target = [13500, 13763]  # [rear, front]
    sensorGapTolerance = 0.02  # tolerance for sensor gap
    lvlMotorTime = 4  # time (sec) for level motor to offset
    lvlMotorTolerance = [0.05, 0.05, 0.05]  # tolerance for level motor range [motor, upper, lower]
    level_motor_range = [0, 0, 0]  # [motor_position limit, high limit, low limit]
    movement_trigger = [150, 300]  # [ upper trigger, lower trigger ] sensors reading differences for motor adjustment
    offset_required = [2, 2]  # [up, down] distance require for motor moving down (mm)
    conversion = [46.21, 60]  # [conversion_down, conversion_up]
    ZDBF_limit = 5  # differences required for adjustment, between target ZDBF to current ZDBF
    ZDBF_limit_offset = 5 # offset limits for reduced adjustment conversion
    ZDBF_conv_correction = 0.5 # multipler for adjustment conversion
    autolevel_retry = 3 # max number of auto level retry

    def update(self, logger, com, config):
        self.logger = logger
        self.com = com
        self.sensor_target = config.platen_config[0]
        self.sensorGapTolerance = config.platen_config[1]
        self.lvlMotorTime = config.platen_config[2]
        self.lvlMotorTolerance = config.platen_config[3]
        self.level_motor_range = config.platen_config[4]
        self.movement_trigger = config.platen_config[5]
        self.offset_required = config.platen_config[6]
        self.conversion = config.platen_config[7]
        self.ZDBF_limit = config.platen_config[8]
        self.ZDBF_limit_offset = config.platen_config[9]
        self.ZDBF_conv_correction = config.platen_config[10]
        self.autolevel_retry = config.platen_config[11]

    def readSensor(self, processID):
        # [rear, front]
        sensor = self.com.readReg(processID, 460, 2)
        if sensor[0] == 32767:
            self.logger.info("Rear sensor not detected")
            self.display.fb_println("Rear sensor not detected", 1)
            os._exit(1)
        elif sensor[0] == 0:
            self.logger.info("Rear sensor out of range")
            self.display.fb_println("Rear sensor out of range", 1)
            os._exit(1)
        if sensor[1] == 32767:
            self.logger.info("Front sensor not detected")
            self.display.fb_println("Rear sensor out of range", 1)
            os._exit(1)
        elif sensor[1] == 0:
            self.logger.info("Front sensor out of range")
            self.display.fb_println("Rear sensor out of range", 1)
            os._exit(1)
        return sensor

    def resetMode(self, processID):
        self.com.setReg(processID, 255, [2])

    def setpoint(self, processID, SP):
        self.com.setReg(processID, 0, [SP])
        self.logger.info("Writing setpoint reg 0 to %r" % SP)

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
            time.sleep(1)

    def sensorGap(self):
        processID = 303
        check = 0
        status = 1
        retry = 1
        self.resetMode(processID)
        pos = self.com.readReg(processID, 0, 1)
        if commonFX.signedInt(pos[0]) != -32768:
            time.sleep(7)
        while check != 2 and retry <= 3:

            read = self.readSensor(processID)
            rear = read[0]
            front = read[1]
            self.com.setCoil(processID, 30, [1])  # reset button coil

            if commonFX.rangeCheck(int(rear), self.sensor_target[0], self.sensorGapTolerance):
                self.logger.info("Rear sensors within range (mil) " + str(commonFX.baumerToThou(rear)))
                self.display.fb_println("Rear sensors within range (mil) %r" % round(commonFX.baumerToThou(rear), 3), 0)
                check += 1
            else:
                self.logger.info("Rear sensor out of range (mil) " + str(commonFX.baumerToThou(rear)))
                self.display.fb_println("Rear sensor out of range (mil) %r" % round(commonFX.baumerToThou(rear), 3), 1)
                status = 0
            if commonFX.rangeCheck(int(front), self.sensor_target[1], self.sensorGapTolerance):
                self.logger.info("Front sensors within range (mil) " + str(commonFX.baumerToThou(front)))
                self.display.fb_println("Front sensors within range (mil) %r" % round(commonFX.baumerToThou(front), 3), 0)
                check += 1
            else:
                self.logger.info("Front sensor out of range (mil) " + str(commonFX.baumerToThou(front)))
                self.display.fb_println("Front sensor out of range (mil) %r" % round(commonFX.baumerToThou(front), 3), 1)
                status = 0

            if status == 0:
                self.logger.info("Waiting for adjustment to complete")

            while status == 0:
                read = self.readSensor(processID)

                self.display.fb_clear()
                self.display.fb_println("Adjust sensor gap to ~ %r (mil)" %round(commonFX.baumerToThou(self.sensor_target[0]), 2) , 1)
                self.display.fb_println("Rear sensors range (mil) %r" % round(commonFX.baumerToThou(read[0]), 3), 0)
                self.display.fb_println("Front sensors range (mil) %r" % round(commonFX.baumerToThou(read[1]), 3), 0)
                self.display.fb_println("Press Green button to proceed after adjustment", 1)

                button = self.com.readCoil(processID, 30, 1)
                if button[0] == 0:
                    self.com.setCoil(processID, 30, [1])
                    check = 0
                    status = 1
                time.sleep(1)
            retry += 1

        if retry > 3:
            self.logger.info("Sensor gap check bypassed...continue with testing")
            self.display.fb_println("Sensor gap check bypassed...continue with testing", 0)

        return read

    def calZDBF(self):
        processID = 305
        self.resetMode(processID)
        self.com.setReg(processID, 255, [10])
        read = self.com.readReg(processID, 255, 1)
        startTime = time.time()
        while read[0] != 14 and commonFX.timeCal(startTime) < self.lvlMotorTime/2:
            time.sleep(0.5)
            read = self.com.readReg(processID, 255, 1)
        if commonFX.timeCal(startTime) > self.lvlMotorTime/2:
            self.logger.info("Unable to capture ZDBF")
            self.display.fb_println("Unable to capture ZDBF", 1)
            os._exit(1)

        gap = self.com.readReg(processID, 5, 2)
        ZDBF = gap[0] - gap[1]
        self.logger.info("ZDBF: " + str(ZDBF))
        self.display.fb_println("ZDBF: %r" % ZDBF, 0)
        self.resetMode(processID)
        return ZDBF, gap

    def resetGAP(self, config):
        processID = 306
        if config.ZDBF == -0:
            target, gap = self.calZDBF()
        else:
            target = config.ZDBF

        adjustment = 0
        self.com.setReg(processID, 255, [10])
        read = self.com.readReg(processID, 255, 1)
        while read[0] != 14:
            time.sleep(0.5)
            read = self.com.readReg(processID, 255, 1)
        gap = self.com.readReg(processID, 5, 2)
        ZDBF = gap[0] - gap[1]
        self.resetMode(processID)
        # self.setpoint(processID, 0)

        if abs(target - ZDBF) <= self.ZDBF_limit:  # ignore when deviation less than limit
            direction = 0

        elif ZDBF > target:  # Rear higher than front
            direction = 1  # move CCW down
            if abs(target - ZDBF) > self.ZDBF_limit + 15:
                adjustment = commonFX.encToSensor((target - ZDBF), config.encoder_conv) * self.ZDBF_conv_correction
            elif self.ZDBF_limit < abs(target - ZDBF) < self.ZDBF_limit + self.ZDBF_limit_offset:
                adjustment = commonFX.encToSensor((target - ZDBF), config.encoder_conv)
            else:
                adjustment = commonFX.encToSensor((target - ZDBF), config.encoder_conv) * self.ZDBF_conv_correction / 2

        elif ZDBF < target:  # Rear lower than front
            direction = -1  # move CW up
            if abs(target - ZDBF) > self.ZDBF_limit + 15:
                adjustment = commonFX.encToSensor((target - ZDBF), config.encoder_conv) * self.ZDBF_conv_correction
            elif self.ZDBF_limit < abs(target - ZDBF) < self.ZDBF_limit + self.ZDBF_limit_offset:
                adjustment = commonFX.encToSensor((target - ZDBF), config.encoder_conv)
            else:
                adjustment = commonFX.encToSensor((target - ZDBF), config.encoder_conv) * self.ZDBF_conv_correction / 2

        self.logger.info("ZDBF: %r, direction: %r, adjustment: %r" % (ZDBF, direction, adjustment))
        self.display.fb_println("ZDBF: %r, direction: %r, adjustment: %r" % (ZDBF, direction, adjustment), 0)
        return ZDBF, direction, int(adjustment)

    def autolevel(self, processID, direction, adjustment):
        initial = self.com.readReg(processID, 460, 1)
        self.com.setReg(processID, 255, [28])
        time.sleep(1)
        read = self.com.readReg(processID, 255, 1)
        if read[0] != 29:
            self.com.setReg(processID, 255, [29])
        if direction == -1:
            self.logger.info("adjusting level motor up")
            self.display.fb_println("adjusting level motor up", 0)
            target = initial[0] + abs(adjustment)
            read = self.com.readReg(processID, 460, 1)
            self.moveLvlMotor(1, direction)
            startTime = time.time()
            self.logger.info("inital: %r, target: %r" %(initial[0], target))
            #self.display.fb_println("inital: %r, target: %r" %(initial[0], target), 0)
            while read[0] <= target and commonFX.timeCal(startTime) < self.lvlMotorTime:
                read = self.com.readReg(processID, 460, 1)
            self.moveLvlMotor(0, 0)
            if commonFX.timeCal(startTime) > self.lvlMotorTime:
                self.logger.info("level motor did not reach target, timed out at %r (sec)" % self.lvlMotorTime)
                self.display.fb_println("level motor did not reach target >%r (sec)" % self.lvlMotorTime, 1)

        if direction == 1:
            self.logger.info("adjusting level motor down")
            self.display.fb_println("adjusting level motor down", 0)
            target = initial[0] - abs(adjustment)
            read = self.com.readReg(processID, 460, 1)
            self.moveLvlMotor(1, direction)
            startTime = time.time()
            self.logger.info("inital: %r, target: %r" % (initial[0], target))
            #self.display.fb_println("inital: %r, target: %r" % (initial[0], target), 0)
            while read[0] >= target and commonFX.timeCal(startTime) < self.lvlMotorTime:
                read = self.com.readReg(processID, 460, 1)
            self.moveLvlMotor(0, 0)
            if commonFX.timeCal(startTime) > self.lvlMotorTime:
                self.logger.info("level motor did not reach target, timed out at %r (sec)" % self.lvlMotorTime)
                self.display.fb_println("level motor did not reach target >%r (sec)" % self.lvlMotorTime, 1)

        self.logger.info("adjustment completed")
        self.display.fb_println("adjustment completed", 0)

    def motorRangeTest(self, config):
        processID = 307
        sample = []
        motor_range = [0, 0, 0]
        self.resetMode(processID)
        self.setpoint(processID, 0)
        pos = self.com.readReg(processID, 0, 1)
        if commonFX.signedInt(pos[0]) != -32768:
            time.sleep(7)
        sensorReading = self.readSensor(processID)
        motor_range[0] = sensorReading[0]  # current position
        sample.append(sensorReading[0])  # initial
        sample.append(sensorReading[0] * 2)  # ensure it's not the same as initial

        offset = commonFX.baumerToMM(motor_range[0]) - self.offset_required[0]
        target = int(commonFX.mmToBaumer(offset))

        # adjustment upwards
        self.logger.info("Adjusting level motor up, gap target (mil): %r" % round(commonFX.baumerToThou(offset), 3))
        self.display.fb_println("Adjusting level motor up", 0)
        self.moveLvlMotor(1, -1)

        startTime = time.time()
        while sensorReading[0] < target and commonFX.timeCal(startTime) < self.lvlMotorTime:
            sensorReading = self.readSensor(processID)
            sample.append(sensorReading[0])
            # print sensorReading[0]
            time.sleep(1)

        self.moveLvlMotor(0, 0)
        if commonFX.timeCal(startTime) > self.lvlMotorTime:
            self.logger.info("level motor did not reach target, timed out at %r (sec)" % self.lvlMotorTime)
            self.display.fb_println("level motor did not reach target >%r (sec)" % self.lvlMotorTime, 1)

        sensorReading = self.readSensor(processID)
        motor_range[1] = sensorReading[0]

        # determine motor direction
        try:
            if commonFX.rangeCheck(sample[-1], sample[0], 0.01):
                self.logger.info("No level motor movement detected")
                self.display.fb_println("No level motor movement detected", 1)
                os._exit(1)
            elif sample[0] > sample[-1] - self.movement_trigger[0]:
                self.logger.info("Level motor moving in reverse direction")
                self.display.fb_println("Level motor moving in reverse direction", 1)
                os._exit(1)
            elif sample[0] < sample[-1] + self.movement_trigger[0]:
                self.logger.info("Level motor installed correctly")
                self.display.fb_println("Level motor installed correctly", 0)

        except IndexError:
            self.logger.info("No sensor reading collected")
            self.display.fb_println("No sensor reading collected", 1)

        # reset motor to inital position
        self.logger.info("Reset level motor to inital position")
        self.display.fb_println("Reset level motor to inital position", 0)
        sensorReading = self.readSensor(processID)
        self.moveLvlMotor(1, 1)
        startTime = time.time()
        while sensorReading[0] > sample[0] and commonFX.timeCal(startTime) < self.lvlMotorTime:
            sensorReading = self.readSensor(processID)
            time.sleep(0.5)
        self.moveLvlMotor(0, 0)
        if commonFX.timeCal(startTime) > self.lvlMotorTime:
            self.logger.info("level motor did not reach target, timed out at %r (sec)" % self.lvlMotorTime)
            self.display.fb_println("level motor did not reach target >%r (sec)" % self.lvlMotorTime, 1)

        # adjustment downwards
        offset = commonFX.baumerToMM(motor_range[0]) + self.offset_required[1]
        target = int(commonFX.mmToBaumer(offset))
        sensorReading = self.readSensor(processID)
        self.logger.info("Adjusting level motor down, gap target (mm): %r" % round(offset, 3))
        self.display.fb_println("Adjusting level motor down", 0)
        self.moveLvlMotor(1, 1)
        startTime = time.time()
        while sensorReading[0] > target and commonFX.timeCal(startTime) < self.lvlMotorTime:
            sensorReading = self.readSensor(processID)
            # print sensorReading[0]
            time.sleep(1)

        self.moveLvlMotor(0, 0)
        if commonFX.timeCal(startTime) > self.lvlMotorTime:
            self.logger.info("level motor did not reach target, timed out at %r (sec)" % self.lvlMotorTime)
            self.display.fb_println("level motor did not reach target >%r (sec)" % self.lvlMotorTime, 1)

        sensorReading = self.readSensor(processID)
        motor_range[2] = sensorReading[0]

        # log data
        position = commonFX.baumerToThou(motor_range[0])
        upperLimit = commonFX.baumerToThou(motor_range[1])
        lowerLimit = commonFX.baumerToThou(motor_range[2])

        self.logger.info("Sensor Reading {position: %r, upper range: %r, lower range: %r}" % (
            round(position, 3), round(upperLimit, 3), round(lowerLimit, 3)))

        # reset motor to inital position
        self.logger.info("Reset level motor to inital position")
        self.display.fb_println("Reset level motor to inital position", 0)
        sensorReading = self.readSensor(processID)
        self.moveLvlMotor(1, -1)
        startTime = time.time()
        while sensorReading[0] < sample[0] and commonFX.timeCal(startTime) < self.lvlMotorTime:
            sensorReading = self.readSensor(processID)
            time.sleep(0.5)
        self.moveLvlMotor(0, 0)
        if commonFX.timeCal(startTime) > self.lvlMotorTime:
            self.logger.info("level motor did not reach target, timed out at %r (sec)" % self.lvlMotorTime)
            self.display.fb_println("level motor did not reach target >%r (sec)" % self.lvlMotorTime, 1)

        # reset
        self.resetMode(processID)
        self.logger.info("Check ZDBF range")
        self.display.fb_println("Check ZDBF range", 0)
        newZDBF, direction, adjustment = self.resetGAP(config)

        retry = 1
        while direction != 0 and retry <= self.autolevel_retry:
            self.resetMode(processID)
            time.sleep(2)
            self.autolevel(processID, direction, adjustment)
            newZDBF, direction, adjustment = self.resetGAP(config)
            if retry > self.autolevel_retry:
                self.logger.info("Max auto level retry reached, > %r" % retry)
                self.display.fb_println("Max auto level retry reached, > %r" % retry, 1)
            retry += 1

        self.resetMode(processID)
        self.logger.info("New ZDBF: %r" % newZDBF)

        return motor_range, [position, upperLimit, lowerLimit], newZDBF
