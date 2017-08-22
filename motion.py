#!/usr/bin/python
# Project: EOL
# Description: Motion control related to actuator
__author__ = "Adrian Wong"
import os, time
import modbus_tk
import modbus_tk.defines as cst


class actuator():
    # Temporary variables, do not modify here
    logger = ''
    master = ''
    device = 0
    restTime = 0
    timeout = 30  # max time limit for each task completion, flag error when exceeded

    def update(self, logger, master, device, restTime, timeout):
        self.logger = logger
        self.master = master
        self.device = device
        self.restTime = restTime
        self.timeout = timeout

    def timeCal(self, arg):  # time calculation
        timeElapse = time.time() - long(arg)
        return timeElapse

    def setReg(self, processID, startReg, Data):
        # For passing condition, no errors should occur and maximum retry is set at 3
        error = 1
        retry = 3
        while error == 1 and retry != 0:
            try:
                time.sleep(self.restTime)
                self.master.execute(self.device, cst.WRITE_MULTIPLE_REGISTERS, startReg, output_value=Data)
                error = 0
            except modbus_tk.modbus.ModbusInvalidResponseError:
                print "Write to register %r failed, @ processID %r" % (startReg, processID)
                self.logger.info("Write to register %r failed, @ processID %r" % (startReg, processID))
                error = 1
                retry -= 1
                pass

        if retry <= 0:
            os._exit(1)
            print "Max retry reached @ %r, exiting script...please restart" % processID
        else:
            pass

    def setCoil(self, processID, startReg, Data):
        # For passing condition, no errors should occur and maximum retry is set at 3
        error = 1
        retry = 3
        while error == 1 and retry != 0:
            try:
                time.sleep(self.restTime)
                self.master.execute(self.device, cst.WRITE_MULTIPLE_COILS, startReg, output_value=Data)
                error = 0
            except modbus_tk.modbus.ModbusInvalidResponseError:
                print "Write to coil %r failed, @ processID %r" % (startReg, processID)
                self.logger.info("Write to coil %r failed, @ processID %r" % (startReg, processID))
                error = 1
                retry -= 1
                pass

        if retry <= 0:
            os._exit(1)
            print "Max retry reached @ %r, exiting script...please restart" % processID
        else:
            pass

    def readReg(self, processID, startReg, totalReg):
        error = 1
        retry = 3
        while error == 1 and retry != 0:
            try:
                time.sleep(self.restTime)
                read = self.master.execute(self.device, cst.READ_HOLDING_REGISTERS, startReg, totalReg)
                error = 0
            except modbus_tk.modbus.ModbusInvalidResponseError:
                print "Reading register %r failed, @ processID %r" % (startReg, processID)
                self.logger.info("Reading register %r failed, @ processID %r" % (startReg, processID))
                error = 1
                retry -= 1
                pass

        if retry <= 0:
            os._exit(1)
            print "Max retry reached @ %r, exiting script...please restart" % processID
        else:
            pass

        return read

    def setpoint(self, SP):
        self.setReg(200, 0, [SP])
        self.logger.info("Writing setpoint reg 0 to %r" % SP)

    def spFeedback(self):
        fb = self.readReg(201, 3, 1)
        return fb[0]

    def homing(self):
        process = 202
        self.setReg(process, 25, [0])
        self.setReg(process, 255, [1])
        homeStatus = self.readReg(process, 25, 1)
        startTime = time.time()
        while homeStatus[0] != 5 and self.timeCal(startTime) < self.timeout:
            homeStatus = self.readReg(process, 25, 1)

        if homeStatus[0] != 5:
            self.logger.info("Homing sequence failed, @ processID %r" % process)
            os._exit(1)

        self.logger.info("Homing sequence successful, @ processID %r" % process)

    def switchTest(self):
        process = 203
        self.setReg(process, 255, [3])
        read = self.readReg(process, 255, 1)
        startTime = time.time()
        while read[0] != 5 and self.timeCal(startTime) < self.timeout / 2:
            read = self.readReg(process, 255, 1)
        if read[0] != 5:
            self.logger.info("Seeking upper switch failed, @ processID %r" % process)
            os._exit(1)

        self.logger.info("Seeking upper switch successful, @ processID %r" % process)

        self.setReg(process, 255, [6])
        read = self.readReg(process, 255, 1)
        startTime = time.time()
        while read[0] != 8 and self.timeCal(startTime) < self.timeout / 2:
            read = self.readReg(process, 255, 1)
        if read[0] != 8:
            self.logger.info("Seeking lower switch failed, @ processID %r" % process)
            os._exit(1)

        self.logger.info("Seeking lower switch successful, @ processID %r" % process)


def main():
    x = 1

    # main starts here


if __name__ == "__main__":
    main()
