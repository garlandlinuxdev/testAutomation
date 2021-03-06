#!/usr/bin/python
# Project: modbus communications
# Description: simplied modbus functions in modbus tk with retry function
__author__ = "Adrian Wong"
import os, time, LCD
import modbus_tk
import modbus_tk.defines as cst


class communicate():
    # Temporary variables, do not modify here
    logger = ''
    master = ''
    device = 0
    display = LCD.display()
    restTime = 0  # rest time for in between communication functions
    retry = 20

    def setup(self, logger, master, device, restTime):
        self.logger = logger
        self.master = master
        self.device = device
        self.restTime = restTime

    def setReg(self, processID, startReg, Data):
        # For passing condition, no errors should occur and maximum retry is set at 3
        error = 1
        retry = self.retry
        while error == 1 and retry != -1:
            try:
                time.sleep(self.restTime)
                self.master.execute(self.device, cst.WRITE_MULTIPLE_REGISTERS, startReg, output_value=Data)
                error = 0
            except modbus_tk.modbus.ModbusInvalidResponseError:
                #print "Write to register %r failed (retry remains %r), @ processID %r" % (startReg, retry, processID)
                self.logger.info(
                    "Write to register %r failed (retry remains %r), @ processID %r" % (startReg, retry, processID))
                self.display.fb_clear()
                self.display.fb_println("Write to register %r failed (retry remains %r)" % (startReg, retry), 1)
                error = 1
                retry -= 1
                pass

        if retry < 0:
            #print "Max retry reached @ %r, exiting script...please restart" % processID
            self.logger.info("Max retry reached @ %r, exiting script...please restart" % processID)
            self.display.fb_println("Max retry reached @ %r, please restart" % processID, 1)
            os._exit(1)
        else:
            pass

    def setCoil(self, processID, startReg, Data):
        # For passing condition, no errors should occur and maximum retry is set at 3
        error = 1
        retry = self.retry
        while error == 1 and retry != -1:
            try:
                time.sleep(self.restTime)
                self.master.execute(self.device, cst.WRITE_MULTIPLE_COILS, startReg, output_value=Data)
                error = 0
            except modbus_tk.modbus.ModbusInvalidResponseError:
                #print "Write to coil %r failed (retry remains %r), @ processID %r" % (startReg, retry, processID)
                self.logger.info(
                    "Write to coil %r failed (retry remains %r), @ processID %r" % (startReg, retry, processID))
                self.display.fb_clear()
                self.display.fb_println("Write to coil %r failed (retry remains %r)" % (startReg, retry), 1)
                error = 1
                retry -= 1
                pass

        if retry < 0:
            #print "Max retry reached @ %r, exiting script...please restart" % processID
            self.logger.info("Max retry reached @ %r, exiting script...please restart" % processID)
            self.display.fb_println("Max retry reached, please restart" % processID, 1)
            os._exit(1)
        else:
            pass

    def readReg(self, processID, startReg, totalReg):
        error = 1
        retry = self.retry
        while error == 1 and retry != -1:
            try:
                time.sleep(self.restTime)
                read = self.master.execute(self.device, cst.READ_HOLDING_REGISTERS, startReg, totalReg)
                error = 0
            except modbus_tk.modbus.ModbusInvalidResponseError:
                #print "Reading register %r failed (retry remains %r), @ processID %r" % (startReg, retry, processID)
                self.logger.info(
                    "Reading register %r failed (retry remains %r), @ processID %r" % (startReg, retry, processID))
                self.display.fb_clear()
                self.display.fb_println("Reading register %r failed (retry remains %r)" % (startReg, retry), 1)
                error = 1
                retry -= 1
                pass

        if retry < 0:
            #print "Max retry reached @ %r, exiting script...please restart" % processID
            self.logger.info("Max retry reached @ %r, exiting script...please restart" % processID)
            self.display.fb_println("Max retry reached @ %r, please restart" % processID, 1)
            os._exit(1)
        else:
            pass

        return read

    def readCoil(self, processID, startReg, totalReg):
        error = 1
        retry = self.retry
        while error == 1 and retry != -1:
            try:
                time.sleep(self.restTime)
                read = self.master.execute(self.device, cst.READ_COILS, startReg, totalReg)
                error = 0
            except modbus_tk.modbus.ModbusInvalidResponseError:
                #print "Write to coil %r failed (retry remains %r), @ processID %r" % (startReg, retry, processID)
                self.logger.info(
                    "Write to coil %r failed (retry remains %r), @ processID %r" % (startReg, retry, processID))
                self.display.fb_clear()
                self.display.fb_println("Write to coil %r failed (retry remains %r)" % (startReg, retry), 1)
                error = 1
                retry -= 1
            pass

        if retry < 0:
            #print "Max retry reached @ processID %r, exiting script...please restart" % processID
            self.logger.info("Max retry reached @ processID %r, exiting script...please restart" % processID)
            self.display.fb_println("Max retry reached @ %r, please restart" % processID, 1)
            os._exit(1)
        else:
            pass
        return read
