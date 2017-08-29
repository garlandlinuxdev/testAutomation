#!/usr/bin/python
# Project: EOL
# Description:
__author__ = "Adrian Wong"

import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu
import serial, os, logging, modbus
import jsonToFile, motion, voltage


def setup():
    # Configure Hardware Overwrite
    com_port = 'COM30'  # For windows
    # com_port = '/dev/ttyO4' #For UART4
    # com_port = '/dev/ttyO2' #For UI using UART2
    # com_port = '/dev/ttyUSB0'  # For USB port

    baud = 115200
    byte = 8
    par = serial.PARITY_EVEN
    stop = 1
    timeout = 0.07

    # configure communication settings in serConfig
    master = modbus_rtu.RtuMaster(
        serial.Serial(port=com_port, baudrate=baud, bytesize=byte, parity=par, stopbits=stop, xonxoff=0))
    master.set_timeout(timeout)
    master.set_verbose(True)

    return master


def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    """Function setup as many loggers as you want"""

    handler = logging.FileHandler(log_file, mode='a')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


class myConfig(object):
    device = 1
    restTime = 0.01
    timeout = 30
    linuxPath = os.path.dirname(__file__)
    logPath = '/log/'  # log files storage path
    sysPath = '/system/'  # system files storage path
    hwcfg = '/hwcfg/'  # library of all json configurations
    logfile = linuxPath + logPath + "event.log"
    jumperFile = linuxPath + sysPath + "jumpers.json"
    grillType = 0  # load from SIB
    jsonFile = linuxPath + hwcfg + str(grillType) + ".json"
    enable = [1, 1, 1, 1]  # load register function, 1 for enable [motionPID, heaterPID, level sensors]

    description = "unknown"  # load from json file
    sync_role = 0

    def updateJSON(self, grillType):
        self.jsonFile = self.linuxPath + self.hwcfg + str(grillType) + ".json"


def main():
    # main starts here
    config = myConfig()
    master = setup()

    logger = setup_logger('event_log', config.logfile)
    logger.info("==================== Load Settings ====================")
    print "==================== Load Settings ===================="

    com = modbus.communicate()
    com.setup(logger, master, config.device, config.restTime)

    myJSON = jsonToFile.loadJSON()
    myJSON.update(logger, com, config.enable)

    processID = 1
    config.grillType = myJSON.grillType(processID)
    config.updateJSON(config.grillType)
    logger.info(config.jsonFile)
    print config.jsonFile

    data = myJSON.readJSON(config.jsonFile)
    config.description, config.sync_role = myJSON.loadHardware(data)
    myJSON.setDevice(data)

    power = voltage.measure()
    power.update(logger, com)

    motor = motion.actuator()
    motor.update(logger, com, config.timeout)


    logger.info("==================== Test Begins ====================")
    print "==================== Test Begins ===================="
    logger.info("< execute voltage reading >")
    processID = 2
    phase_status, supply_voltage = power.voltage(processID)
    power.validate(phase_status, supply_voltage)

    logger.info("< execute switch test >")
    motor.switchTest()
    logger.info("< execute homing test >")
    motor.homing()
    logger.info("< execute setpoint settings >")
    motor.setpoint(-4000)

    logger.info("==================== Test Completed ====================")
    print "==================== Test Completed ===================="

if __name__ == "__main__":
    main()
