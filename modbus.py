#!/usr/bin/python
#Project: modbus communications
#Description: simplied modbus functions in modbus tk with retry function
__author__ = "Adrian Wong"
import os, time
import modbus_tk
import modbus_tk.defines as cst

class communicate():
    # Temporary variables, do not modify here
    logger = ''
    master = ''
    device = 0
    restTime = 0

    def setup(self, logger, master, device, restTime):
        self.logger = logger
        self.master = master
        self.device = device
        self.restTime = restTime

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
            print "Max retry reached @ %r, exiting script...please restart" % processID
            os._exit(1)
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
            print "Max retry reached @ %r, exiting script...please restart" % processID
            os._exit(1)
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
            print "Max retry reached @ %r, exiting script...please restart" % processID
            os._exit(1)
        else:
            pass

        return read

    def readCoil(self, processID, startReg, totalReg):
        error = 1
        retry = 3
        while error == 1 and retry != 0:
            try:
                time.sleep(self.restTime)
                read = self.master.execute(self.device, cst.READ_COILS, startReg, totalReg)
                error = 0
            except modbus_tk.modbus.ModbusInvalidResponseError:
                print "Write to coil %r failed, @ processID %r" % (20, processID)
                self.logger.info("Write to coil %r failed, @ processID %r" % (20, processID))
                error = 1
                retry -= 1
            pass

        if retry <= 0:
            print "Max retry reached @ %r, exiting script...please restart" % processID
            os._exit(1)
        else:
            pass
        return read
