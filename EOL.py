#!/usr/bin/python
# Project: EOL
# Description:
__author__ = "Adrian Wong"

import modbus_tk.modbus_rtu as modbus_rtu
import serial, os, logging, modbus, time
import jsonToFile, actuator, voltage, platen, commonFX, LCD


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

    status = 0
    test_type = config.grillType in mcDonald[0]  # Gas
    if test_type:
        status = 1
        config.logger.info("McDonald Gas Test")
        # print "McDonald Gas Test"
        return [1, 1, 1, 1, 1, 1, 1, 1]
    test_type = config.grillType in mcDonald[1]  # Electric
    if test_type:
        status = 1
        config.logger.info("McDonald Electric Test")
        # print "McDonald Electric Test"
        return [1, 1, 1, 1, 1, 1, 1, 1]
    test_type = config.grillType in GenMarket[0]  # Gas
    if test_type:
        status = 1
        config.logger.info("General Market Gas Test")
        # print "General Market Gas Test"
        return [1, 1, 1, 1, 0, 0, 0, 0]
    test_type = config.grillType in GenMarket[1]  # Electric
    if test_type:
        status = 1
        config.logger.info("General Market Electric Test")
        # print "General Market Electric Test"
        return [1, 1, 1, 1, 0, 0, 0, 0]
    test_type = config.grillType in CFA
    if test_type:
        status = 1
        config.logger.info("CFA Gen 2 Test")
        # print "CFA Gen 2 Test"
        return [1, 1, 1, 1, 1, 1, 0, 1]
    if status == 0:
        config.logger.info("Grill Type %r not found" % config.grillType)
        config.display.fb_println("Grill Type %r not found" % config.grillType)
        os._exit(1)


class myConfig(object):
    logger = ''
    display = LCD.display()
    device = 1
    restTime = 0.1
    timeout = 30
    encoder_conv = 0.00049126  # encoder to inch conversion, update from json
    linuxPath = os.path.dirname(__file__)
    logPath = '/log/'  # log files storage path
    sysPath = '/system/'  # system files storage path
    hwcfg = '/hwcfg/'  # library of all json configurations
    usbPath = '/media/usb0/'
    usb_logpath = 'log/'  # usb file path
    logfile = linuxPath + logPath
    settingsFile = linuxPath + sysPath + "settings.json"
    log = "event.log"
    grillType = 0  # load from SIB
    jsonFile = linuxPath + hwcfg + str(grillType) + ".json"
    loadReg_enable = [1, 1, 1, 1]  # load register function, 1 for enable [motionPID, heaterPID, level sensors]
    test_enable = [0, 0, 0, 0, 0, 0, 0]  # selection for test execution

    description = "unknown"  # load from json file
    sync_role = 0

    # storage
    voltage_config = ''
    platen_config = ''
    actuator_config = ''
    switch_config = ''
    phase_status = ''
    supply_voltage = ''
    switch = [0, 0]
    time_elapse = [0, 0]
    killsw_enc = [0, 0]
    magnet = [0, 0, 0]
    sensor = [0, 0]
    ZDBF = 0
    gap = 0
    grill_plate = 0
    error = [0, 0, 0, 0, 0]

    def updateJSON(self, grillType):
        self.jsonFile = self.linuxPath + self.hwcfg + str(grillType) + ".json"

    def updateSettings(self):
        if os.path.exists(self.linuxPath + self.sysPath + 'image') == True:
            os.popen('rm ' + self.linuxPath + self.sysPath + 'image')
        if os.path.exists(self.usbPath + 'settings.json') == True:
            os.popen('cp ' + ' ' + self.usbPath + 'settings.json' + ' ' + self.settingsFile)
            self.logger.info("EOL settings updated...")
            self.display.fb_clear()
            self.display.fb_long_print("EOL settings updated...", 0)
        if os.path.exists(self.usbPath + 'hwcfg/*.json') == True:
            os.popen('cp ' + ' ' + '-u' + ' ' + self.usbPath + 'hwcfg/*.json' + ' ' + self.linuxPath + 'hwcfg/')
            self.logger.info("json files updated...")
            self.display.fb_clear()
            self.display.fb_long_print("json files updated...", 0)
        else:
            self.logger.info("No updated required...")
            self.display.fb_clear()
            self.display.fb_long_print("No updated required...", 0)

    def copyLog(self):
        timestr = time.strftime("%Y%m%d-%H%M%S")
        # print "USB path: ", os.path.isdir(config.usbpath)
        if os.path.exists(self.usbPath + self.usb_logpath) == True:
            self.logger.info("Test logs copy to USB path")
            os.popen(
                'mv ' + self.logfile + self.log + ' ' + self.linuxPath + self.logPath + timestr + self.log)
            os.popen('mv ' + self.logfile + '*.log' + ' ' + self.usbPath + self.usb_logpath)
            self.display.fb_println("Test logs copied to USB path", 0)
        else:
            self.logger.info("USB log path not found")
            self.display.fb_println("USB log path not found", 0)
            os.popen(
                'mv ' + self.logfile + self.log + ' ' + self.linuxPath + self.logPath + timestr + self.log)
            # print config.logfile
            # print (config.linuxPath + config.logPath + timestr + config.log)

    def report(self):
        self.display.fb_clear()
        self.display.fb_println("< Test Results > ", 1)
        self.display.fb_println("Phase A (V):     %r" % (self.supply_voltage[4] / 10.0), 0)
        self.display.fb_println("Phase B (V):     %r" % (self.supply_voltage[5] / 10.0), 0)
        self.display.fb_println("Phase C (V):     %r" % (self.supply_voltage[6] / 10.0), 0)
        self.display.fb_println("24V supply (V):  %r" % (float(self.supply_voltage[0]) / 100), 0)
        self.display.fb_println("12V supply (V):  %r" % (float(self.supply_voltage[1]) / 100), 0)
        self.display.fb_println("5V supply (V):   %r" % (float(self.supply_voltage[2]) / 100), 0)
        self.display.fb_println("3.3V supply (V): %r" % (float(self.supply_voltage[3]) / 100), 0)

        if self.test_enable[0] == 1:
            self.display.fb_println("Time elapse upwards (sec):    %r" % round(self.time_elapse[0], 3), 0)
            self.display.fb_println("Time elapse downwards (sec):  %r" % round(self.time_elapse[1], 3), 0)
            if self.error[0] != 1:
                self.display.fb_println("Grill plate to Home (inch):   %r" % self.grill_plate, 0)
            else:
                self.display.fb_println("Grill plate to Home (inch):  %r >tolerance" % self.grill_plate, 1)
            if self.error[1] != 1:
                self.display.fb_println("Lift switch location (inch):  %r" % self.switch[0], 0)
            else:
                self.display.fb_println("Lift switch location (inch):  %r >tolerance" % self.switch[0], 1)
            if self.error[2] != 1:
                self.display.fb_println("Home switch location (inch):  %r" % self.switch[1], 0)
            else:
                self.display.fb_println("Home switch location (inch):  %r >tolerance" % self.switch[1], 1)
            if self.error[3] != 1:
                self.display.fb_println("Upper killsw location(inch):  %r" % self.killsw_enc[0], 0)
            else:
                self.display.fb_println("Upper killsw location(inch):  %r >tolerance" % self.killsw_enc[0], 1)
            if self.error[4] != 1:
                self.display.fb_println("Lower killsw location(inch): %r" % self.killsw_enc[1], 0)
            else:
                self.display.fb_println("Lower killsw location(inch): %r >tolerance" % self.killsw_enc[1], 1)

        if self.test_enable[2] == 1:
            self.display.fb_println("Distance moving down (count): %r" % self.magnet[0], 0)
            self.display.fb_println("Distance moving up (count):   %r" % self.magnet[1], 0)
            self.display.fb_println("Drift count (count):          %r" % self.magnet[2], 0)
        if self.test_enable[4] == 1:
            self.display.fb_println(
                "Rear sensors gap (mm)         %r" % round((10 - ((self.sensor[0] * 10.0) / 32767)), 3), 0)
            self.display.fb_println(
                "Front sensors gap (mm)        %r" % round((10 - ((self.sensor[1] * 10.0) / 32767)), 3), 0)
        if self.test_enable[5] == 1:
            self.display.fb_println("ZDBF: %r" % self.ZDBF, 0)

        if 1 in self.error:
            self.display.fb_long_print("Switches position not in range, adjustment required", 1)
        else:
            self.display.fb_println("< Equipment passed all test requirements >", 1)

    def calEncoderRef(self):
        grill_plate = self.gap[0] * self.encoder_conv
        lift_sw = (self.gap[0] - self.switch[0]) * self.encoder_conv
        home_sw = (self.gap[0] - self.switch[1]) * self.encoder_conv
        killsw_high = (self.gap[0] - self.killsw_enc[0]) * self.encoder_conv
        killlsw_low = (self.gap[0] - self.killsw_enc[1]) * self.encoder_conv
        self.logger.info("grill plate to home sw (inch): %r" % grill_plate)
        self.logger.info("lift switch location (inch):   %r" % lift_sw)
        self.logger.info("home switch location (inch):   %r" % home_sw)
        self.logger.info("upper killsw location (inch):  %r" % killsw_high)
        self.logger.info("lower killsw location (inch):  %r" % killlsw_low)

        error = [0, 0, 0, 0, 0]

        if commonFX.rangeCheck(grill_plate, self.switch_config[1], self.switch_config[0]) != True:
            self.logger.info("grill plate to home distance not in range")
            error[0] = 1
        if commonFX.rangeCheck(lift_sw, self.switch_config[2], self.switch_config[0]) != True:
            self.logger.info("lift switch location not in range")
            error[1] = 1
        if commonFX.rangeCheck(home_sw, self.switch_config[3], self.switch_config[0]) != True:
            self.logger.info("home switch location not in range")
            error[2] = 1
        if commonFX.rangeCheck(killsw_high, self.switch_config[4], self.switch_config[0]) != True:
            self.logger.info("upper kill switch location not in range")
            error[3] = 1
        if commonFX.rangeCheck(killlsw_low, self.switch_config[5], self.switch_config[0]) != True:
            self.logger.info("lower kill switch location not in range")
            error[4] = 1

        self.grill_plate = round(grill_plate, 3)
        self.switch = [round(lift_sw, 3), round(home_sw, 3)]
        self.killsw_enc = [round(killsw_high, 3), round(killlsw_low, 3)]
        self.error = error


def main():
    # main starts here
    config = myConfig()

    try:
        master = setup()
    except serial.serialutil.SerialException:
        config.display.fb_clear()
        config.display.fb_long_print("FTDI USB cable not found, please connect cable and restart", 1)
        os._exit(1)

    logger = setup_logger('event_log', config.logfile + config.log)
    config.logger = logger
    config.updateSettings()

    config.display.fb_clear()
    logger.info("==================== Load Settings ====================")
    # print "==================== Load Settings ===================="
    config.display.fb_println("=============== Load Settings ===============", 1)

    com = modbus.communicate()
    com.setup(logger, master, config.device, config.restTime)

    myJSON = jsonToFile.loadJSON()

    try:
        info = myJSON.readJSON(config.linuxPath + config.sysPath + 'settings.json')
    except ValueError:
        logger.info("settings.json file corrupted, update settings required")
        config.display.fb_long_print("settings.json file corrupted, update settings required")
        os._exit(1)

    myJSON.update(logger, com, config.loadReg_enable)
    config.voltage_config, config.platen_config, config.actuator_config, config.switch_config = myJSON.loadSettings(
        info)

    processID = 1
    config.grillType = myJSON.grillType(processID)
    config.updateJSON(config.grillType)
    logger.info(config.jsonFile)
    config.test_enable = testRequired(config)

    data = myJSON.readJSON(config.jsonFile)
    config.description, config.sync_role = myJSON.loadHardware(data)
    myJSON.setDevice(data)
    config.display.fb_long_print(str(config.description), 1)
    # print config.jsonFile

    power = voltage.measure()
    power.update(logger, com, config)

    motor = actuator.motion()
    motor.update(logger, com, config)
    config.encoder_conv = motor.encoder_conv

    pl = platen.sensors()
    pl.update(logger, com, config)

    processID = 1
    config.display.fb_long_print("Press green button to execute sensors test only", 0)
    time.sleep(5)

    # seek upper switch
    com.setReg(processID, 255, [3])

    button = com.readCoil(processID, 30, 1)
    if button[0] == 0:
        config.display.fb_long_print("Execute sensors test only", 1)
        com.setCoil(processID, 30, [1])
        config.test_enable = [0, 0, 0, 1, 1, 1, 0, 1]

    logger.info("==================== Test Begins ====================")
    # print "==================== Test Begins ===================="
    config.display.fb_println("================ Test Begins ================", 1)
    logger.info("< execute voltage reading >")
    config.display.fb_println("< execute voltage reading >", 1)
    processID = 2
    power.updateLCD(config.display.FB_Y)
    config.display.FB_Y, config.phase_status, config.supply_voltage = power.voltage(processID)
    power.updateLCD(config.display.FB_Y)
    config.display.FB_Y = power.validate(config)

    if config.test_enable[0]:
        logger.info("< execute switch test >")
        # print "< execute switch test >"
        config.display.fb_println("< # 1 execute switch test >", 1)
        motor.updateLCD(config.display.FB_Y)
        config.display.FB_Y, config.switch, config.time_elapse = motor.switchTest(config)
    if config.test_enable[1]:
        logger.info("< execute kill switch test >")
        # print "< execute kill switch test >"
        config.display.fb_println("< # 2 execute kill switch test >", 1)
        motor.updateLCD(config.display.FB_Y)
        config.display.FB_Y, config.killsw_enc = motor.killSwitchTest()
    if config.test_enable[2]:
        logger.info("< execute magnet drift test >")
        # print "< execute magnet drift test >"
        config.display.fb_println("< # 3 execute magnet drift test >", 1)
        motor.updateLCD(config.display.FB_Y)
        config.display.FB_Y, config.magnet = motor.magnetDrift()
    if config.test_enable[3]:
        logger.info("< execute homing test >")
        # print "< execute homing test >"
        config.display.fb_clear()
        config.display.fb_println("< # 4 execute homing test >", 1)
        motor.updateLCD(config.display.FB_Y)
        motor.homing()
    if config.test_enable[4]:
        logger.info("< execute sensors gap test >")
        # print "< execute sensors gap test >"
        config.display.fb_println("< # 5 execute sensors gap test >", 1)
        motor.setpoint(0)
        time.sleep(3)
        pl.updateLCD(config.display.FB_Y)
        config.display.FB_Y, config.sensor = pl.sensorGap()
    if config.test_enable[5]:
        logger.info("< execute ZDBF test >")
        # print "< execute ZDBF test >"
        config.display.fb_println("< # 6 execute ZDBF test >", 1)
        motor.setpoint(0)
        time.sleep(3)
        pl.updateLCD(config.display.FB_Y)
        config.display.FB_Y, config.ZDBF, config.gap = pl.calZDBF()
        motor.setpoint(0)
    if config.test_enable[6]:
        logger.info("< execute level motor test >")
        # print "< execute level motor test >"
        config.display.fb_println("< # 7 execute level motor test >", 1)
        motor.setpoint(0)
        time.sleep(3)
        pl.updateLCD(config.display.FB_Y)
        config.display.FB_Y = pl.levelMotorTest()
    if config.test_enable[7]:
        logger.info("< calculate encoder references >")
        config.display.fb_println("< # 8 calculate encoder references >", 1)
        config.calEncoderRef()

    logger.info("==================== Test Completed ====================")
    # print "==================== Test Completed ===================="
    config.display.fb_println("============== Test Completed ==============", 1)
    config.report()
    config.copyLog()
    config.display.keepON()

    # processID = 3
    # com.setCoil(processID, 30, [1])

    # while True:
    #     button = com.readCoil(processID, 30, 1)
    #     if button[0] == 0:
    #         report(display, config.test_enable, data)
    #         com.setCoil(processID, 30, [1])
    #     time.sleep(2)


if __name__ == "__main__":
    main()
