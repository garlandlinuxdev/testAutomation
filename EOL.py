#!/usr/bin/python
# Project: EOL
# Description:
__author__ = "Adrian Wong"

import modbus_tk.modbus_rtu as modbus_rtu
import serial, os, logging, modbus, time, csv
import jsonToFile, actuator, voltage, platen, commonFX, LCD
from sys import platform

FB_Y = 10  # global Y position of LCD, update using subfile module


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
    if config.grillType in mcDonald[0]:  # Gas
        status = 1
        customer = 1
        config.logger.info("McDonald Gas Test")
        return [1, 1, 1, 1, 1, 1, 1, 1], customer

    if config.grillType in mcDonald[1]:  # Electric
        status = 1
        customer = 1
        config.logger.info("McDonald Electric Test")
        return [1, 1, 1, 1, 1, 1, 1, 1], customer

    if config.grillType in GenMarket[0]:  # Gas
        status = 1
        customer = 2
        config.logger.info("General Market Gas Test")
        return [1, 1, 1, 1, 0, 0, 0, 0], customer

    if config.grillType in GenMarket[1]:  # Electric
        status = 1
        customer = 2
        config.logger.info("General Market Electric Test")
        return [1, 1, 1, 1, 0, 0, 0, 0], customer

    if config.grillType in CFA:  # CFA
        status = 1
        customer = 3
        config.logger.info("CFA Gen 2 Test")
        return [1, 1, 1, 1, 1, 1, 0, 1], customer

    if status == 0:
        config.logger.info("Grill Type %r not found" % config.grillType)
        config.display.fb_println("Grill Type %r not found" % config.grillType)
        os._exit(1)


def testCase(config, num):
    if num == 0:
        config.logger.info("< Execute custom test only >")
        config.display.fb_println("< Execute custom test only >", 0)
        return config.json_test_config
    if num == 1:
        config.logger.info("< Execute switch test only >")
        config.display.fb_println("< Execute switch test only >", 0)
        return [1, 0, 0, 0, 0, 0, 0, 1]
    if num == 2:
        config.logger.info("< Execute kill switch test only >")
        config.display.fb_println("< Execute kill switch test only >", 0)
        return [0, 1, 0, 0, 0, 0, 0, 1]
    if num == 3:
        config.logger.info("< Execute magnet drift test only >")
        config.display.fb_println("< Execute magnet drift test only >", 0)
        return [0, 0, 1, 0, 0, 0, 0, 1]
    if num == 4:
        config.logger.info("< Execute homing test only >")
        config.display.fb_println("< Execute homing test only >", 0)
        return [0, 0, 0, 1, 0, 0, 0, 1]
    if num == 5:
        config.logger.info("< Execute sensors test only >")
        config.display.fb_println("< Execute sensors test only >", 0)
        return [0, 0, 0, 0, 1, 0, 0, 1]
    if num == 6:
        config.logger.info("< Execute ZDBF test only >")
        config.display.fb_println("< Execute ZDBF test only >", 0)
        return [0, 0, 0, 0, 0, 1, 0, 1]
    if num == 7:
        config.logger.info("< Execute level motor test only >")
        config.display.fb_println("< Execute level motor test only >", 0)
        return [0, 0, 0, 0, 0, 1, 1, 1]


class myConfig(object):
    logger = ''
    display = LCD.display()
    device = 1
    restTime = 0.05
    timeout = 30
    encoder_conv = 0.00049126  # encoder to inch conversion, update from json
    linuxPath = os.path.dirname(__file__)
    myPlatform = False
    logPath = '/log/'  # log files storage path
    sysPath = '/system/'  # system files storage path
    hwcfg = '/hwcfg/'  # library of all json configurations
    usbPath = '/media/usb0/'
    usb_logpath = 'log/'  # usb file path
    excel = 'log.csv'
    logfile = linuxPath + logPath
    settingsFile = linuxPath + sysPath + "settings.json"
    log = "event.log"
    test_completed = -1
    grillType = 0  # load from SIB
    jsonFile = linuxPath + hwcfg + str(grillType) + ".json"
    loadReg_enable = [1, 1, 1, 1]  # load register function, 1 for enable [motionPID, heaterPID, level sensors, power sync]
    test_enable = [0, 0, 0, 0, 0, 0, 0]  # selection for test execution
    temp_Limit = [2400, 2820, 2400, 2820, 2400, 0, 0, 0]  # temperature limit
    heaterTemp = [1766, 2183, 1766, 2183, 1766, 0, 0, 0]  # temperature setpoint
    customer = 1  # 1
    description = "unknown"  # load from json file
    sync_role = 0

    # storage
    json_test_config = ''
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
    ZDBF = -0
    gap = [0, 0]
    grill_plate = 0
    error = [0, 0, 0, 0, 0, 0, 0, 0]
    motor_range = [0, 0, 0]
    motor_limit = [0, 0, 0, 0, 0]
    newZDBF = 0

    def updateJSON(self, grillType):
        self.jsonFile = self.linuxPath + self.hwcfg + str(grillType) + ".json"

    def updateSettings(self):
        timestr = time.strftime("%Y%m%d-%H%M%S")
        if platform == "linux" or platform == "linux2":
            # linux
            self.myPlatform = True
            self.logger.info("Script running on Linux platform, LCD enabled")
        elif platform == "darwin":
            # OS X
            self.myPlatform = False
            self.logger.info("Script running on OS X platform, LCD disabled")
        elif platform == "win32" or platform == "cygwin":
            # Windows...
            self.myPlatform = False
            self.logger.info("Script running on windows platform, LCD disabled")

        if self.myPlatform == False:
            return
        if os.path.exists(self.linuxPath + self.sysPath + 'image') == True:
            os.popen('rm ' + self.linuxPath + self.sysPath + 'image')
        if os.path.exists(self.usbPath + self.excel) == True:
            if os.path.exists(self.logfile + self.excel) == True:
                self.logger.info("Previous log.csv file copied to USB path...")
                self.display.fb_long_print("Previous log.csv file copied to USB path...", 0)
                os.popen('mv ' + self.logfile + self.excel + ' ' + self.usbPath + timestr + '-' + self.excel)
                os.popen('cp ' + self.usbPath + self.excel + ' ' + self.logfile + self.excel)
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
        if os.path.isfile(self.logfile + self.log) == True:
            os.popen('mv ' + self.logfile + self.log + ' ' + self.linuxPath + self.logPath + timestr + '-' + str(
                self.grillType) + '.log')

        if os.path.exists(self.usbPath + self.usb_logpath) == True:
            try:
                self.logger.info("Test logs copy to USB path")
            except AttributeError:
                pass
            os.popen('mv ' + self.logfile + '*.log' + ' ' + self.usbPath + self.usb_logpath)
            self.display.fb_println("Test logs copied to USB path", 0)
        else:
            try:
                self.logger.info("USB log path not found")
            except AttributeError:
                pass
            self.display.fb_println("USB log path not found", 0)
            os.popen('mv ' + self.logfile + self.log + ' ' + self.linuxPath + self.logPath + timestr + '-' + str(
                self.grillType) + '.log')

    def writeToCSV(self):
        datestr = time.strftime('%Y/%m/%d')
        timestr = time.strftime('%H:%M:%S')
        with open(self.logfile + self.excel, 'a') as test:
            fieldnames = (
                'date', 'time', 'grill_type', 'linel', 'line2', 'line3', '24supply', '12supply', '5supply', '3_3supply',
                'timeUpwards', 'timeDownwards', 'grill_plate', 'lift_sw', 'home_sw', 'up_killsw', 'down_killsw',
                'dist_up', 'dist_dwn', 'max_drift', 'rear_sensor', 'front_sensor', 'zdbf', 'lvl_motor_pos',
                'lvl_motor_upper_range', 'lvl_motor_lower_range', 'new_zdbf', 'test_completed')
            targetWriter = csv.DictWriter(test, delimiter=',', lineterminator='\n', fieldnames=fieldnames)
            headers = dict((n, n) for n in fieldnames)
            #targetWriter.writerow(headers)
            targetWriter.writerow(
                {'date': datestr, 'time': timestr, 'grill_type': self.grillType,
                 'linel': str(self.supply_voltage[4] / 10.0),
                 'line2': str(self.supply_voltage[5] / 10.0),
                 'line3': str(self.supply_voltage[6] / 10.0),
                 '24supply': str(float(self.supply_voltage[0]) / 100),
                 '12supply': str(float(self.supply_voltage[1]) / 100),
                 '5supply': str(float(self.supply_voltage[2]) / 100),
                 '3_3supply': str(float(self.supply_voltage[3]) / 100),
                 'timeUpwards': str(round(self.time_elapse[0], 3)), 'timeDownwards': str(round(self.time_elapse[1], 3)),
                 'grill_plate': str(self.grill_plate), 'lift_sw': str(self.switch[0]), 'home_sw': str(self.switch[1]),
                 'up_killsw': str(self.killsw_enc[0]), 'down_killsw': str(self.killsw_enc[1]),
                 'dist_up': str(self.magnet[0]), 'dist_dwn': str(self.magnet[1]), 'max_drift': str(self.magnet[2]),
                 'rear_sensor': str(round(commonFX.baumerToThou(self.sensor[0]), 3)),
                 'front_sensor': str(round(commonFX.baumerToThou(self.sensor[1]), 3)),
                 'zdbf': str(self.ZDBF),
                 'lvl_motor_pos': str(round(self.motor_limit[0], 3)),
                 'lvl_motor_upper_range': str(round(self.motor_limit[1], 3)),
                 'lvl_motor_lower_range': str(round(self.motor_limit[2], 3)),
                 'new_zdbf': str(self.newZDBF),
                 'test_completed': str(self.test_completed)
                 })
        test.close()

    def report(self):
        self.logger.info("< Test Results >")
        self.logger.info("Line 1 (V):     %r" % (self.supply_voltage[4] / 10.0))
        self.logger.info("Line 2 (V):     %r" % (self.supply_voltage[5] / 10.0))
        self.logger.info("Line 3 (V):     %r" % (self.supply_voltage[6] / 10.0))
        self.logger.info("24V supply (V):  %r" % (float(self.supply_voltage[0]) / 100))
        self.logger.info("12V supply (V):  %r" % (float(self.supply_voltage[1]) / 100))
        self.logger.info("5V supply (V):   %r" % (float(self.supply_voltage[2]) / 100))
        self.logger.info("3.3V supply (V): %r" % (float(self.supply_voltage[3]) / 100))
        self.display.fb_clear()
        self.display.fb_println("< Test Results > ", 1)
        self.display.fb_println("Line 1 (V):     %r" % (self.supply_voltage[4] / 10.0), 0)
        self.display.fb_println("Line 2 (V):     %r" % (self.supply_voltage[5] / 10.0), 0)
        self.display.fb_println("Line 3 (V):     %r" % (self.supply_voltage[6] / 10.0), 0)
        # self.display.fb_println("24V supply (V):  %r" % (float(self.supply_voltage[0]) / 100), 0)
        # self.display.fb_println("12V supply (V):  %r" % (float(self.supply_voltage[1]) / 100), 0)
        # self.display.fb_println("5V supply (V):   %r" % (float(self.supply_voltage[2]) / 100), 0)
        # self.display.fb_println("3.3V supply (V): %r" % (float(self.supply_voltage[3]) / 100), 0)

        if self.test_enable[0] == 1 or self.test_enable[1] == 1:
            self.logger.info("Time elapse upwards (sec):    %r" % round(self.time_elapse[0], 3))
            self.logger.info("Time elapse downwards (sec):  %r" % round(self.time_elapse[1], 3))
            self.display.fb_println("Time elapse upwards (sec):    %r" % round(self.time_elapse[0], 3), 0)
            self.display.fb_println("Time elapse downwards (sec):  %r" % round(self.time_elapse[1], 3), 0)
            if self.error[0] == 0:
                self.display.fb_println("Grill plate to Home (inch):  %r" % self.grill_plate, 0)
            else:
                self.display.fb_println("Grill plate to Home (inch):  %r >tolerance" % self.grill_plate, 0)
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
            self.logger.info("Distance moving down (count): %r" % self.magnet[0])
            self.logger.info("Distance moving up (count):   %r" % self.magnet[1])
            self.logger.info("Max Drift count (count):      %r" % self.magnet[2])
            self.display.fb_println("Distance moving down (count): %r" % self.magnet[0], 0)
            self.display.fb_println("Distance moving up (count):   %r" % self.magnet[1], 0)
            self.display.fb_println("Max Drift count (count):      %r" % self.magnet[2], 0)
        if self.test_enable[4] == 1:
            self.logger.info("Rear sensors gap (mil)        %r" % round(commonFX.baumerToThou(self.sensor[0]), 3))
            self.logger.info("Front sensors gap (mil)       %r" % round(commonFX.baumerToThou(self.sensor[1]), 3))
            self.display.fb_println(
                "Rear sensors gap (mil)        %r" % round(commonFX.baumerToThou(self.sensor[0]), 3), 0)
            self.display.fb_println(
                "Front sensors gap (mil)       %r" % round(commonFX.baumerToThou(self.sensor[1]), 3), 0)
        if self.test_enable[5] == 1:
            self.logger.info("ZDBF:                         %r" % self.ZDBF)
            self.display.fb_println("ZDBF:                         %r" % self.ZDBF, 0)

        if self.test_enable[6] == 1:
            up_limit = round(commonFX.baumerToThou(self.motor_range[0]) - self.platen_config[6][1], 3)
            low_limit = round(commonFX.baumerToThou(self.motor_range[0]) + self.platen_config[6][1], 3)
            self.logger.info("Level motor position (mil):   %r" % round(self.motor_limit[0], 3))
            self.display.fb_println("Level motor position (mil):   %r" % round(self.motor_limit[0], 3), 0)
            if self.error[5] == 1:
                self.logger.info("upper travel range (mil):     %r > %r" % (round(self.motor_limit[1], 3), up_limit))
                self.display.fb_println(
                    "upper travel range (mil):     %r > %r" % (round(self.motor_limit[1], 3), up_limit), 1)
            else:
                self.logger.info("upper travel range (mil):     %r" % round(self.motor_limit[1], 3))
                self.display.fb_println("upper travel range (mil):     %r" % round(self.motor_limit[1], 3), 0)

            if self.error[6] == 1:
                self.logger.info("lower travel range (mil):     %r < %r" % (round(self.motor_limit[2], 3), low_limit))
                self.display.fb_println(
                    "lower travel range (mil):     %r < %r" % (round(self.motor_limit[2], 3), low_limit), 1)
            else:
                self.logger.info("lower travel range (mil):     %r" % round(self.motor_limit[2], 3))
                self.display.fb_println("lower travel range (mil):     %r" % round(self.motor_limit[2], 3), 0)

            self.logger.info("New ZDBF:                     %r " % self.newZDBF)
            self.display.fb_println("New ZDBF:                     %r " % self.newZDBF, 0)

        if 1 in self.error:
            self.test_completed = 0
            self.logger.info("Tolerances not in range, adjustment required")
            self.display.fb_long_print("Tolerances not in range, adjustment required", 1)
        else:
            self.test_completed = 1

            self.logger.info("< Equipment passed all test requirements >")
            self.display.fb_println("< Equipment passed all test requirements >", 1)

        self.writeToCSV()

    def calculate(self):
        error = [0, 0, 0, 0, 0, 0, 0, 0]

        if self.test_enable[0] == 1 or self.test_enable[1] == 1:
            home_sw = commonFX.encToInch(self.switch[1], self.encoder_conv)
            grill_plate = home_sw - commonFX.encToInch(self.gap[0])
            lift_sw = home_sw - commonFX.encToInch(self.switch[0], self.encoder_conv)
            killsw_high = home_sw - commonFX.encToInch(self.killsw_enc[0], self.encoder_conv)
            killlsw_low = home_sw - commonFX.encToInch(self.killsw_enc[1], self.encoder_conv)
            self.logger.info("Raw output:{%r, %r, %r, %r, %r}" % (
                self.gap[0], self.switch[0], self.switch[1], self.killsw_enc[0], self.killsw_enc[1]))
            self.logger.info("grill plate to home sw (inch):  %r" % grill_plate)
            self.logger.info("lift switch location (inch):    %r" % lift_sw)
            self.logger.info("home switch location (inch):    %r" % home_sw)
            self.logger.info("upper killsw location (inch):   %r" % killsw_high)
            self.logger.info("lower killsw location (inch):   %r" % killlsw_low)

            if commonFX.rangeCheck(round(grill_plate, 3), self.switch_config[1], self.switch_config[0]) != True:
                self.logger.info("grill plate to home distance not in range, target: %r +/- %r%%" % (
                    self.switch_config[1], self.switch_config[0] * 100))
                error[0] = -1
            if commonFX.rangeCheck(round(lift_sw, 3), self.switch_config[2], self.switch_config[0]) != True:
                self.logger.info("lift switch location not in range, target: %r +/- %r%%" % (
                    self.switch_config[2], self.switch_config[0] * 100))
                error[1] = 1
            if commonFX.rangeCheck(round(home_sw, 1), self.switch_config[3], self.switch_config[0]) != True:
                self.logger.info("home switch location not in range, target: %r +/- %r%%" % (
                    self.switch_config[3], self.switch_config[0] * 100))
                error[2] = 1
            if commonFX.rangeCheck(round(killsw_high, 3), self.switch_config[4], self.switch_config[0]) != True:
                self.logger.info("upper kill switch location not in range, target: %r +/- %r%%" % (
                    self.switch_config[4], self.switch_config[0] * 100))
                error[3] = 1
            if commonFX.rangeCheck(round(killlsw_low, 3), self.switch_config[5], self.switch_config[0]) != True:
                self.logger.info("lower kill switch location not in range, target: %r +/- %r%%" % (
                    self.switch_config[5], self.switch_config[0] * 100))
                error[4] = 1

            self.grill_plate = round(grill_plate, 3)
            self.switch = [round(lift_sw, 3), round(home_sw, 3)]
            self.killsw_enc = [round(killsw_high, 3), round(killlsw_low, 3)]

        if self.test_enable[6] == 1:
            position = commonFX.baumerToThou(self.motor_range[0])
            upper_limit = position - self.platen_config[6][0]
            lower_limit = position + self.platen_config[6][1]
            if commonFX.baumerToThou(self.motor_range[1]) <= upper_limit and commonFX.baumerToThou(
                    self.motor_range[2]) >= lower_limit:
                self.logger.info("level motor position in range")
            if commonFX.baumerToThou(self.motor_range[1]) > upper_limit:
                self.logger.info("upper travel limit not in range of %r" % round(upper_limit, 3))
                error[5] = 1
            else:
                self.logger.info("upper travel limit within range of %r" % round(upper_limit, 3))
            if commonFX.baumerToThou(self.motor_range[2]) < lower_limit:
                self.logger.info("lower travel limit not in range of %r" % round(lower_limit, 3))
                error[6] = 1
            else:
                self.logger.info("lower travel limit within range of %r" % round(lower_limit, 3))

        self.error = error


def main():
    # main starts here
    FB_X = 280
    config = myConfig()
    if config.display.checkOS() == True:
        config.display.fb_clear()
        config.copyLog()
    logger = setup_logger('event_log', config.logfile + config.log)
    config.logger = logger
    try:
        master = setup()
    except serial.serialutil.SerialException:
        config.display.fb_clear()
        config.display.fb_long_print("FTDI USB cable not found, please connect cable and restart", 1)
        logger.info("FTDI USB cable not found, please connect cable and restart")
        os._exit(1)

    config.updateSettings()

    config.display.fb_clear()
    logger.info("==================== Load Settings ====================")
    config.display.fb_println("=============== Load Settings ===============", 1)

    com = modbus.communicate()
    com.setup(logger, master, config.device, config.restTime)

    processID = 0
    com.setCoil(processID, 30, [1])  # reset button status

    myJSON = jsonToFile.loadJSON()
    myJSON.temp_Limit = config.temp_Limit # overrides default class in loadJSON
    myJSON.heaterTemp = config.heaterTemp # overrides default class in loadJSON
    myJSON.update(logger, com, config.loadReg_enable)

    # info = myJSON.readJSON(config.linuxPath + config.sysPath + 'settings.json')
    try:
        info = myJSON.readJSON(config.linuxPath + config.sysPath + 'settings.json')
    except ValueError:
        logger.info("settings.json file corrupted, update settings required")
        config.display.fb_long_print("settings.json file corrupted, update settings required", 0)
        os._exit(1)

    processID = 1
    config.grillType = myJSON.grillType(processID)
    config.updateJSON(config.grillType)
    logger.info(config.jsonFile)
    config.test_enable, config.customer = testRequired(config)

    config.json_test_config, config.voltage_config, config.platen_config, config.actuator_config, config.switch_config = myJSON.loadSettings(
        info, config.customer)

    data = myJSON.readJSON(config.jsonFile)
    config.description, config.sync_role = myJSON.loadHardware(data)
    myJSON.setDevice(data)
    config.display.fb_long_print(str(config.description), 1)

    power = voltage.measure()
    power.update(logger, com, config)

    motor = actuator.motion()
    motor.update(logger, com, config)
    config.encoder_conv = motor.encoder_conv

    pl = platen.sensors()
    pl.update(logger, com, config)

    config.display.fb_long_print("Press green button to execute custom test", 0)
    config.display.fb_long_print("Test selection: ", 0)
    button = com.readCoil(processID, 30, 1)
    startTime = time.time()
    counter = -1
    config.display.reverseLine()
    while button != 0 and commonFX.timeCal(startTime) < 10:
        button = com.readCoil(processID, 30, 1)
        if button[0] == 0:
            counter += 1
            config.display.fb_printX("%r " % counter, FB_X, 1)
            FB_X += 40
            # config.display.fb_long_print("< execute customized test sequence >", 1)
            com.setCoil(processID, 30, [1])
    config.display.nextLine()
    if counter != -1 and counter <= 7:
        config.test_enable = testCase(config, counter)

    # seek upper switch
    processID = 1
    com.setReg(processID, 255, [3])

    logger.info("==================== Test Begins ====================")
    config.display.fb_println("================ Test Begins ================", 1)
    logger.info("< execute voltage reading >")
    config.display.fb_println("< execute voltage reading >", 1)
    processID = 2
    config.phase_status, config.supply_voltage = power.voltage(processID)
    power.validate(config)

    if config.test_enable[0]:
        logger.info("< execute switch test >")
        config.display.fb_println("< # 1 execute switch test >", 1)
        config.switch, config.time_elapse = motor.switchTest(config)
    if config.test_enable[1]:
        logger.info("< execute kill switch test >")
        config.display.fb_println("< # 2 execute kill switch test >", 1)
        config.killsw_enc = motor.killSwitchTest()
    if config.test_enable[2]:
        logger.info("< execute magnet drift test >")
        config.display.fb_println("< # 3 execute magnet drift test >", 1)
        config.magnet = motor.magnetDrift(config)
    if config.test_enable[3]:
        logger.info("< execute homing test >")
        config.display.fb_clear()
        config.display.fb_println("< # 4 execute homing test >", 1)
        motor.homing(processID)
    if config.test_enable[4]:
        logger.info("< execute sensors gap test >")
        config.display.fb_println("< # 5 execute sensors gap test >", 1)
        motor.homing(processID)
        motor.setpoint(0)
        time.sleep(2)
        config.sensor = pl.sensorGap()
    if config.test_enable[5]:
        logger.info("< execute ZDBF test >")
        config.display.fb_println("< # 6 execute ZDBF test >", 1)
        motor.homing(processID)
        motor.setpoint(0)
        time.sleep(2)
        config.ZDBF, config.gap = pl.calZDBF()
    if config.test_enable[6]:
        logger.info("< execute level motor test >")
        config.display.fb_println("< # 7 execute level motor test >", 1)
        motor.homing(processID)
        time.sleep(2)
        config.motor_range, config.motor_limit, config.newZDBF = pl.motorRangeTest(config)
    if config.test_enable[7]:
        logger.info("< calculate results >")
        config.display.fb_println("< # 8 calculate results >", 1)
        config.calculate()

    logger.info("==================== Test Completed ====================")
    config.display.fb_println("============== Test Completed ==============", 1)
    config.report()
    config.display.checkOS()
    if config.display.myPlatform == True:
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
