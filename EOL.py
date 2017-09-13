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
    display = ''
    device = 1
    restTime = 0.1
    timeout = 30
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

    def updateJSON(self, grillType):
        self.jsonFile = self.linuxPath + self.hwcfg + str(grillType) + ".json"


def report(display, enable, data):
    display.fb_clear()
    volt = data[0]
    display.fb_println(" < Test Results > ", 1)
    display.fb_println("Phase A (V):     %r" % (volt[4] / 10.0), 0)
    display.fb_println("Phase B (V):     %r" % (volt[5] / 10.0), 0)
    display.fb_println("Phase C (V):     %r" % (volt[6] / 10.0), 0)
    display.fb_println("24V supply (V):  %r" % (float(volt[0]) / 100), 0)
    display.fb_println("12V supply (V):  %r" % (float(volt[1]) / 100), 0)
    display.fb_println("5V supply (V):   %r" % (float(volt[2]) / 100), 0)
    display.fb_println("3.3V supply (V): %r" % (float(volt[3]) / 100), 0)

    if enable[0] == 1:
        switch = data[1]
        killsw_enc = data[2]
        switch_enc = data[4]
        grillplate = data[7]
        error = data[8]
        display.fb_println("Time elapse upwards (sec):    %r" % round(switch[2], 3), 0)
        display.fb_println("Time elapse downwards (sec):  %r" % round(switch[3], 3), 0)
        if error[0] != 1:
            display.fb_println("Grill plate location (inch):  %r" % grillplate, 0)
        else:
            display.fb_println("Grill plate location (inch):  %r >tolerance" % grillplate, 1)
        if error[1] != 1:
            display.fb_println("Lift switch location (inch):  %r" % switch_enc[0], 0)
        else:
            display.fb_println("Lift switch location (inch):  %r >tolerance" % switch_enc[0], 1)
        if error[2] != 1:
            display.fb_println("Home switch location (inch):  %r" % switch_enc[1], 0)
        else:
            display.fb_println("Home switch location (inch):  %r >tolerance" % switch_enc[1], 1)
        if error[3] != 1:
            display.fb_println("Upper killsw location(inch):  %r" % killsw_enc[0], 0)
        else:
            display.fb_println("Upper killsw location(inch):  %r >tolerance" % killsw_enc[0], 1)
        if error[4] != 1:
            display.fb_println("Lower killsw location(inch): %r" % killsw_enc[1], 0)
        else:
            display.fb_println("Lower killsw location(inch): %r >tolerance" % killsw_enc[1], 1)

    if enable[2] == 1:
        magnet = data[3]
        display.fb_println("Distance moving down (count): %r" % magnet[0], 0)
        display.fb_println("Distance moving up (count):   %r" % magnet[1], 0)
        display.fb_println("Drift count (count):          %r" % magnet[2], 0)
    if enable[4] == 1:
        sensor = data[5]
        display.fb_println("Rear sensors gap (mm)         %r" % round((10 - ((sensor[0] * 10.0) / 32767)), 3), 0)
        display.fb_println("Front sensors gap (mm)        %r" % round((10 - ((sensor[1] * 10.0) / 32767)), 3), 0)
    if enable[5] == 1:
        ZDBF = data[6]
        display.fb_println("ZDBF: %r" % ZDBF, 0)

    display.fb_println("< Equipment passed all test requirements >", 1)


def copyLog(config, display):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    # print "USB path: ", os.path.isdir(config.usbpath)
    if os.path.exists(config.usbPath + config.usb_logpath) == True:
        config.logger.info("Test logs copy to USB path")
        os.popen('mv ' + config.logfile + config.log + ' ' + config.linuxPath + config.logPath + timestr + config.log)
        os.popen('mv ' + config.logfile + '*.log' + ' ' + config.usbPath + config.usb_logpath)
        display.fb_println("Test logs copied to USB path", 0)
    else:
        config.logger.info("USB log path not found")
        display.fb_println("USB log path not found", 0)
        os.popen('mv ' + config.logfile + config.log + ' ' + config.linuxPath + config.logPath + timestr + config.log)
        # print config.logfile
        # print (config.linuxPath + config.logPath + timestr + config.log)


def updateSettings(config, display):
    if os.path.exists(config.linuxPath + config.sysPath + 'image') == True:
        os.popen('rm ' + config.linuxPath + config.sysPath + 'image')
    if os.path.exists(config.usbPath + 'settings.json') == True:
        os.popen('cp ' + ' ' + config.usbPath + 'settings.json' + ' ' + config.settingsFile)
        display.fb_clear()
        display.fb_long_print("EOL settings updated...", 0)
    if os.path.exists(config.usbPath + 'hwcfg/*.json') == True:
        os.popen('cp ' + ' ' + '-u' + ' ' + config.usbPath + 'hwcfg/*.json' + ' ' + config.linuxPath + 'hwcfg/')
        display.fb_clear()
        display.fb_long_print("json file updated...", 0)
    else:
        display.fb_clear()
        display.fb_long_print("No updated required...", 0)


def calEncoderRef(config, switch, enc, gap, switch_enc, killsw_enc):
    grill_plate = gap[0] * enc
    lift_sw = (gap[0] - switch_enc[0]) * enc
    home_sw = (gap[0] - switch_enc[1]) * enc
    killsw_high = (gap[0] - killsw_enc[0]) * enc
    killlsw_low = (gap[0] - killsw_enc[1]) * enc
    config.logger.info("grill plate to home sw (inch): %r" % grill_plate)
    config.logger.info("lift switch location (inch):   %r" % lift_sw)
    config.logger.info("home switch location (inch):   %r" % home_sw)
    config.logger.info("upper killsw location (inch):  %r" % killsw_high)
    config.logger.info("lower killsw location (inch):  %r" % killlsw_low)

    error = [0, 0, 0, 0, 0]

    if commonFX.rangeCheck(grill_plate, switch[1], switch[0]) != True:
        config.logger.info("grill plate to home distance not in range")
        error[0] = 1
    if commonFX.rangeCheck(lift_sw, switch[2], switch[0]) != True:
        config.logger.info("lift switch location not in range")
        error[1] = 1
    if commonFX.rangeCheck(home_sw, switch[3], switch[0]) != True:
        config.logger.info("home switch location not in range")
        error[2] = 1
    if commonFX.rangeCheck(killsw_high, switch[4], switch[0]) != True:
        config.logger.info("upper kill switch location not in range")
        error[3] = 1
    if commonFX.rangeCheck(killlsw_low, switch[5], switch[0]) != True:
        config.logger.info("lower kill switch location not in range")
        error[4] = 1

    return round(grill_plate, 3), [round(lift_sw, 3), round(home_sw, 3)], [round(killsw_high, 3), round(killlsw_low, 3)], error


def main():
    # main starts here
    config = myConfig()
    display = LCD.display()
    try:
        master = setup()
    except serial.serialutil.SerialException:
        display.fb_clear()
        display.fb_long_print("FTDI USB cable not found, please connect cable and restart", 1)
        os._exit(1)

    switch = [0, 0, 0, 0]
    killsw_enc = [0, 0]
    magnet = [0, 0, 0]
    switch_enc = [0, 0]
    sensor = [0, 0]
    ZDBF = 0
    grill_plate = 0
    error = [0, 0, 0, 0, 0]

    logger = setup_logger('event_log', config.logfile + config.log)
    config.logger = logger
    config.display = display
    updateSettings(config, display)

    display.fb_clear()
    logger.info("==================== Load Settings ====================")
    # print "==================== Load Settings ===================="
    display.fb_println("=============== Load Settings ===============", 1)

    com = modbus.communicate()
    com.setup(logger, master, config.device, config.restTime)

    myJSON = jsonToFile.loadJSON()

    info = myJSON.readJSON(config.linuxPath + config.sysPath + 'setting.json')
    myJSON.update(logger, com, config.loadReg_enable)
    vlt, plat, act, sw = myJSON.loadSettings(info)

    processID = 1
    config.grillType = myJSON.grillType(processID)
    config.updateJSON(config.grillType)
    logger.info(config.jsonFile)
    config.test_enable = testRequired(config)

    data = myJSON.readJSON(config.jsonFile)
    config.description, config.sync_role = myJSON.loadHardware(data)
    myJSON.setDevice(data)
    display.fb_long_print(str(config.description), 1)
    # print config.jsonFile

    power = voltage.measure()
    power.update(logger, com, vlt[0], vlt[1])

    motor = actuator.motion()
    motor.update(logger, com, act[0], act[1], act[2], act[3], act[4], act[5])

    pl = platen.sensors()
    pl.update(logger, com, plat[0], plat[1], plat[2], plat[3])

    processID = 1
    display.fb_long_print("Press green button to execute sensors test only", 0)
    time.sleep(5)
    button = com.readCoil(processID, 30, 1)
    if button[0] == 0:
        display.fb_long_print("Execute sensors test only", 1)
        com.setCoil(processID, 30, [1])
        config.test_enable = [0, 0, 0, 1, 1, 1, 0, 1]

    logger.info("==================== Test Begins ====================")
    # print "==================== Test Begins ===================="
    display.fb_println("================ Test Begins ================", 1)
    logger.info("< execute voltage reading >")
    display.fb_println("< execute voltage reading >", 1)
    processID = 2
    power.updateLCD(display.FB_Y)
    display.FB_Y, phase_status, supply_voltage = power.voltage(processID)
    power.updateLCD(display.FB_Y)
    display.FB_Y = power.validate(phase_status, supply_voltage)

    if config.test_enable[0]:
        logger.info("< execute switch test >")
        # print "< execute switch test >"
        display.fb_println("< # 1 execute switch test >", 1)
        motor.updateLCD(display.FB_Y)
        display.FB_Y, switch = motor.switchTest()
    if config.test_enable[1]:
        logger.info("< execute kill switch test >")
        # print "< execute kill switch test >"
        display.fb_println("< # 2 execute kill switch test >", 1)
        motor.updateLCD(display.FB_Y)
        display.FB_Y, killsw_enc = motor.killSwitchTest()
    if config.test_enable[2]:
        logger.info("< execute magnet drift test >")
        # print "< execute magnet drift test >"
        display.fb_println("< # 3 execute magnet drift test >", 1)
        motor.updateLCD(display.FB_Y)
        display.FB_Y, magnet = motor.magnetDrift()
    if config.test_enable[3]:
        logger.info("< execute homing test >")
        # print "< execute homing test >"
        display.fb_clear()
        display.fb_println("< # 4 execute homing test >", 1)
        motor.updateLCD(display.FB_Y)
        motor.homing()
    if config.test_enable[4]:
        logger.info("< execute sensors gap test >")
        # print "< execute sensors gap test >"
        display.fb_println("< # 5 execute sensors gap test >", 1)
        motor.setpoint(0)
        time.sleep(3)
        pl.updateLCD(display.FB_Y)
        display.FB_Y, sensor = pl.sensorGap()
    if config.test_enable[5]:
        logger.info("< execute ZDBF test >")
        # print "< execute ZDBF test >"
        display.fb_println("< # 6 execute ZDBF test >", 1)
        motor.setpoint(0)
        time.sleep(3)
        pl.updateLCD(display.FB_Y)
        display.FB_Y, ZDBF, gap = pl.calZDBF()
        motor.setpoint(0)
    if config.test_enable[6]:
        logger.info("< execute level motor test >")
        # print "< execute level motor test >"
        display.fb_println("< # 7 execute level motor test >", 1)
        motor.setpoint(0)
        time.sleep(3)
        pl.updateLCD(display.FB_Y)
        display.FB_Y = pl.levelMotorTest()
    if config.test_enable[7]:
        logger.info("< calculate encoder references >")
        display.fb_println("< # 8 calculate encoder references >", 1)
        grill_plate, switch_enc, killsw_enc, error = calEncoderRef(config, sw, motor.encoder_conv, gap, switch_enc, killsw_enc)

    data = [supply_voltage, switch, killsw_enc, magnet, switch_enc, sensor, ZDBF, grill_plate, error]
    logger.info("==================== Test Completed ====================")
    # print "==================== Test Completed ===================="
    display.fb_println("============== Test Completed ==============", 1)
    report(display, config.test_enable, data)
    copyLog(config, display)

    display.keepON()

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
