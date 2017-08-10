#!/usr/bin/python
#Project: EOL
#Description: 
__author__ = "Adrian Wong"

import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu
import jsonToFile, serial, os, logging, time

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
    restTime = 0.05
    linuxPath = os.path.dirname(__file__)
    logPath = '/log/'  # log files storage path
    sysPath = '/system/'  # system files storage path
    hwcfg = '/hwcfg/' # library of all json configurations
    logfile = linuxPath + logPath + "error.log"
    jumperFile = linuxPath + sysPath + "jumpers.json"
    grillType = 0 #load from jumper
    jsonFile = linuxPath + hwcfg + repr(grillType) + ".json"

    def updateJSON(self, grillType):
        self.jsonFile = self.linuxPath + self.logPath + str(grillType) + ".json"

def main():
    # main starts here
    config = myConfig()
    master = setup()
    logger = setup_logger('event_log', config.logfile)

    myJSON = jsonToFile.loadJSON()


    retry, processID, jumperPIN = myJSON.readJumperPins(master, logger, config.device, 1, config.restTime)
    if retry <= 0:
        print "Failed reading Jumper.....@ processID %r" %processID
        logger.error("Failed reading Jumper.....@ processID %r" %processID)
        os._exit(1)
    config.grillType = myJSON.jumperToDec(jumperPIN)
    config.updateJSON(config.grillType)
    print config.jsonFile



if __name__ == "__main__":
    main()