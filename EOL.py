#!/usr/bin/python
# Project: EOL
# Description:
__author__ = "Adrian Wong"

import modbus_tk.modbus_rtu as modbus_rtu
import serial, os, logging, modbus, time
import jsonToFile, actuator, voltage, platen, LCD


def setup():
    # Configure Hardware Overwrite
    # com_port = 'COM30'  # For windows
    # com_port = '/dev/ttyO4' #For UART4
    # com_port = '/dev/ttyO1' #For UI using UART1
    com_port = '/dev/ttyUSB0'  # For USB port

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


def testRequired(config):
    mcDonald = [[12, 20, 28, 42, 44], [13, 21, 29, 38, 50]]
    GenMarket = [[10, 14, 18, 22, 26, 30, 43, 45], [11, 15, 19, 23, 27, 31, 39, 51]]
    CFA = [47]

    test_type = config.grillType in mcDonald[0] # Gas
    if test_type:
        config.logger.info("McDonald Gas Test")
        print "McDonald Gas Test"
        return [1, 1, 1, 1, 1, 1, 1]
    test_type = config.grillType in mcDonald[1] # Electric
    if test_type:
        config.logger.info("McDonald Electric Test")
        print "McDonald Electric Test"
        return [1, 1, 1, 1, 1, 1, 1]
    test_type = config.grillType in GenMarket[0] # Gas
    if test_type:
        config.logger.info("General Market Gas Test")
        print "General Market Gas Test"
        return [1, 1, 1, 1, 0, 0, 0]
    test_type = config.grillType in GenMarket[1] # Electric
    if test_type:
        config.logger.info("General Market Electric Test")
        print "General Market Electric Test"
        return [1, 1, 1, 1, 0, 0, 0]
    test_type = config.grillType in CFA
    if test_type:
        config.logger.info("CFA Gen 2 Test")
        print "CFA Gen 2 Test"
        return [1, 1, 1, 1, 1, 1, 0]

class myConfig(object):
    logger = ''
    device = 1
    restTime = 0.03
    timeout = 30
    linuxPath = os.path.dirname(__file__)
    logPath = '/log/'  # log files storage path
    sysPath = '/system/'  # system files storage path
    hwcfg = '/hwcfg/'  # library of all json configurations
    logfile = linuxPath + logPath + "event.log"
    jumperFile = linuxPath + sysPath + "jumpers.json"
    grillType = 0  # load from SIB
    jsonFile = linuxPath + hwcfg + str(grillType) + ".json"
    loadReg_enable = [1, 1, 1, 1]  # load register function, 1 for enable [motionPID, heaterPID, level sensors]
    test_enable = [0, 0, 0, 0, 0, 0, 0] # selection for test execution

    description = "unknown"  # load from json file
    sync_role = 0
    sensor_target = [13500, 13763] # sensor gap target

    def updateJSON(self, grillType):
        self.jsonFile = self.linuxPath + self.hwcfg + str(grillType) + ".json"

def report(display, enable, data):
    display.fb_clear()
    volt = data[0]
    print volt
    display.fb_println(" < Test Results > ", 1)
    #display.fb_println("Phase A: %r, Phase B: %r, Phase C: %r" %((volt[4] / 10.0), (volt[5] / 10.0), (volt[6] / 10.0)), 0)
    display.fb_println("Phase A: %r" % (volt[4] / 10.0), 0)
    display.fb_println("Phase B: %r" % (volt[5] / 10.0), 0)
    display.fb_println("Phase C: %r" % (volt[6] / 10.0), 0)

    if enable[0] == 1:
        switch = data[1]
        print switch
        display.fb_println("Distance between switches (count): %r" %switch[0], 0)
        display.fb_println("Time elapse (sec): %r" % switch[1], 0)
    if enable[2] == 1:
        magnet = data[2]
        print magnet
        display.fb_println("Distance moving down: %r" % magnet[0], 0)
        display.fb_println("Distance moving up: %r" % magnet[1], 0)
        display.fb_println("Drift count: %r" % magnet[3], 0)
    if enable[4] == 1:
        sensor = data[3]
        print sensor
        display.fb_println("Rear sensors gap (mm) %r" % ((sensor[0] * 10.0) / 32767), 0)
        display.fb_println("Front sensors gap (mm) %r" % ((sensor[1] * 10.0) / 32767), 0)
    if enable[5] == 1:
        ZDBF = data[4]
        print ZDBF
        display.fb_println("ZDBF: %r" % ZDBF, 0)

    display.fb_println("Equipment passed all required test", 1)

def main():
    # main starts here
    config = myConfig()
    master = setup()
    display = LCD.display()

    volt = 0
    switch = 0
    magnet = 0
    sensor = 0
    ZDBF = 0

    logger = setup_logger('event_log', config.logfile)
    config.logger = logger
    display.fb_clear()
    logger.info("==================== Load Settings ====================")
    print "==================== Load Settings ===================="
    display.fb_println("=============== Load Settings ===============", 1)

    com = modbus.communicate()
    com.setup(logger, master, config.device, config.restTime)

    myJSON = jsonToFile.loadJSON()
    myJSON.update(logger, com, config.loadReg_enable)

    processID = 1
    config.grillType = myJSON.grillType(processID)
    config.updateJSON(config.grillType)
    logger.info(config.jsonFile)
    config.test_enable = testRequired(config)

    data = myJSON.readJSON(config.jsonFile)
    config.description, config.sync_role = myJSON.loadHardware(data)
    myJSON.setDevice(data)
    display.fb_long_print(str(config.description), 0)
    print config.jsonFile

    power = voltage.measure()
    power.update(logger, com)

    motor = actuator.motion()
    motor.update(logger, com, config.timeout)

    pl = platen.sensors()
    pl.update(logger, com, config.sensor_target)

    logger.info("==================== Test Begins ====================")
    print "==================== Test Begins ===================="
    display.fb_println("================ Test Begins ================", 1)
    logger.info("< execute voltage reading >")
    display.fb_println("< execute voltage reading >", 1)
    processID = 2
    power.updateLCD(display.FB_Y)
    display.FB_Y, phase_status, supply_voltage = power.voltage(processID)
    power.updateLCD(display.FB_Y)
    display.FB_Y = power.validate(phase_status, supply_voltage)
    time.sleep(3)

    if config.test_enable[0]:
        logger.info("< execute switch test >")
        print "< execute switch test >"
        display.fb_println("< # 1 execute switch test >", 1)
        motor.updateLCD(display.FB_Y)
        display.FB_Y, switch = motor.switchTest()
    if config.test_enable[1]:
        logger.info("< execute kill switch test >")
        print "< execute kill switch test >"
        display.fb_println("< # 2 execute kill switch test >", 1)
        motor.updateLCD(display.FB_Y)
        display.FB_Y = motor.killSwitchTest()
    if config.test_enable[2]:
        logger.info("< execute magnet drift test >")
        print "< execute magnet drift test >"
        display.fb_println("< # 3 execute magnet drift test >", 1)
        motor.updateLCD(display.FB_Y)
        display.FB_Y, magnet = motor.magnetDrift()
    if config.test_enable[3]:
        logger.info("< execute homing test >")
        print "< execute homing test >"
        display.fb_clear()
        display.fb_println("< # 4 execute homing test >", 1)
        motor.homing()
    if config.test_enable[4]:
        logger.info("< execute sensors gap test >")
        print "< execute sensors gap test >"
        display.fb_println("< # 5 execute sensors gap test >", 1)
        motor.setpoint(0)
        time.sleep(3)
        pl.updateLCD(display.FB_Y)
        display.FB_Y, sensor = pl.sensorGap()
    if config.test_enable[5]:
        logger.info("< execute ZDBF test >")
        print "< execute ZDBF test >"
        display.fb_println("< # 6 execute ZDBF test >", 1)
        motor.setpoint(0)
        time.sleep(3)
        pl.updateLCD(display.FB_Y)
        display.FB_Y, ZDBF = pl.calZDBF()
        motor.setpoint(0)
    if config.test_enable[6]:
        logger.info("< execute level motor test >")
        print "< execute level motor test >"
        display.fb_println("< # 7 execute level motor test >", 1)
        motor.setpoint(0)
        time.sleep(3)
        pl.updateLCD(display.FB_Y)
        display.FB_Y = pl.levelMotorTest()

    data = [supply_voltage, switch, magnet, sensor, ZDBF]
    logger.info("==================== Test Completed ====================")
    print "==================== Test Completed ===================="
    display.fb_println("============== Test Completed ==============", 1)
    report(display, config.test_enable, data)

if __name__ == "__main__":
    main()
