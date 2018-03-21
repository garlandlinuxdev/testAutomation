#!/usr/bin/python
# Project: EOL
# Description:
__author__ = "Adrian Wong"
import serial, os, modbus, time, csv
import jsonToFile, actuator, platen, commonFX
import EOL


def writeToCSV(config, filename, zdbf, enc, status):
    datestr = time.strftime('%Y/%m/%d')
    timestr = time.strftime('%H:%M:%S')
    if status == 1:
        with open(filename, 'a') as test:
            fieldnames = (
                'date', 'time', 'grill_type', 'rear_enc', 'front_enc', 'zdbf', 'rear_mils', 'front_mils', 'zdbf_mils')
            targetWriter = csv.DictWriter(test, delimiter=',', lineterminator='\n', fieldnames=fieldnames)
            headers = dict((n, n) for n in fieldnames)
            targetWriter.writerow(headers)
        test.close()
    else:
        with open(filename, 'a') as test:
            fieldnames = (
                'date', 'time', 'grill_type',  'rear_enc', 'front_enc', 'zdbf', 'rear_mils', 'front_mils', 'zdbf_mils')
            targetWriter = csv.DictWriter(test, delimiter=',', lineterminator='\n', fieldnames=fieldnames)
            # headers = dict((n, n) for n in fieldnames)
            # targetWriter.writerow(headers)
            targetWriter.writerow(
                {'date': datestr, 'time': timestr, 'grill_type': config.grillType, 'rear_enc': str(enc[0]),
                 'front_enc': str(enc[1]), 'zdbf': str(zdbf), 'rear_mils': str(commonFX.encToInch(enc[0])*1000),
                 'front_mils': str(commonFX.encToInch(enc[1])*1000), 'zdbf_mils': str(commonFX.encToInch(zdbf) * 1000)
                 })
        test.close()


def main():
    # setup
    config = EOL.myConfig()
    myJSON = jsonToFile.loadJSON()

    if config.display.checkOS() == True:
        config.display.fb_clear()
        config.copyLog()

    logger = EOL.setup_logger('event_log', config.logfile + config.log)
    config.logger = logger

    try:
        master = EOL.setup()
    except serial.serialutil.SerialException:
        config.display.fb_clear()
        config.display.fb_long_print("FTDI USB cable not found, please connect cable and restart", 1)
        logger.info("FTDI USB cable not found, please connect cable and restart")
        os._exit(1)

    processID = 0
    com = modbus.communicate()
    com.setup(logger, master, config.device, config.restTime)

    logger.info("==================== Load Settings ====================")
    config.display.fb_println("=============== Load Settings ===============", 1)

    # info = myJSON.readJSON(config.linuxPath + config.sysPath + 'settings.json')
    try:
        settings = myJSON.readJSON(config.linuxPath + config.sysPath + 'settings.json')
    except ValueError:
        logger.info("settings.json file corrupted, update settings required")
        config.display.fb_long_print("settings.json file corrupted, update settings required", 0)
        os._exit(1)

    # load test settings only
    a, b, c, d, e, test = myJSON.loadSettings(settings, 0)
    config.loadReg_enable = test[6]

    # define variables (load from settings.json)
    restTime = test[0]
    pauseTime = test[1]
    zdbf = 0
    gap = [0, 0]
    name = str(test[2])
    cycle = test[3]
    setpoint = test[4]
    preheat = test[5]  # 1 for enable
    config.loadReg_enable = test[6]  # load register function, 1 for enable [motionPID, heaterPID, level sensors, power sync]
    config.temp_Limit = test[7]  # overrides temperature limit in loadJSON
    config.heaterTemp = test[8]  # to turn off heaters -> disable heaterPID from loadReg_enable

    linuxPath = os.path.dirname(__file__)
    logPath = linuxPath + '/log/'
    epoch_time = int(time.time())

    # main starts here
    myJSON.update(logger, com, config.loadReg_enable)
    config.updateSettings()
    config.display.fb_clear()

    # grill type update
    config.grillType = myJSON.grillType(processID)
    config.updateJSON(config.grillType)
    logger.info(config.jsonFile)

    if config.grillType != 47:
        testlog = logPath + str(name) + '_' + str(config.grillType) + '_' + str(epoch_time) + '-' + config.excel
    else:
        testlog = config.logfile + str(name) + '_' + str(config.grillType) + '_' + str(epoch_time) + '-' + config.excel
    writeToCSV(config, testlog, zdbf, gap, 1)

    # load test configuration based on EOL (master) settings
    config.json_test_config, config.voltage_config, config.platen_config, config.actuator_config, config.switch_config, x = myJSON.loadSettings(
        settings, config.customer)

    # update and load grill type json
    data = myJSON.readJSON(config.jsonFile)
    myJSON.setDevice(data)

    # motion setup
    motor = actuator.motion()
    motor.update(logger, com, config)
    config.encoder_conv = motor.encoder_conv

    # platen setup
    pl = platen.sensors()
    pl.update(logger, com, config)

    counter = 1
    motor.homing(processID)
    motor.resetMode(processID)

    # preheat
    ready = [0, 0, 0, 0, 0]
    if preheat == 1:
        logger.info('Preheat enabled')
        motor.setpoint(setpoint[0])
    while preheat == 1:
        temp = pl.com.readReg(processID, 84, 5)
        for x in range(0, 5):
            print temp[x], myJSON.heaterTemp[x], ready[x]
            if temp[x] >= myJSON.heaterTemp[x] - 80:
                ready[x] = 1
            else:
                ready[x] = 0

        if 0 in ready:
            preheat = 1
        else:
            preheat = 0

    logger.info('Test cycle started')

    while counter <= cycle:
        config.display.fb_println('Cycle: %r' % counter, 1)
        logger.info('Cycle: %r' % counter)
        pl.resetMode(processID)
        motor.setpoint(setpoint[1])
        startTime = time.time()
        while commonFX.timeCal(startTime) <= restTime:
            pl.com.readReg(processID, 0, 1)
            time.sleep(0.5)
        motor.setpoint(setpoint[2])
        time.sleep(pauseTime)
        zdbf, gap = pl.calZDBF()
        config.display.fb_println("ZDBF: %r  |  Rear: %r  |  Front: %r" % (zdbf, gap[0], gap[1]), 0)
        writeToCSV(config, testlog, zdbf, gap, 0)
        counter += 1

    while True:
        pl.com.readReg(processID, 0, 1)


if __name__ == "__main__":
    main()
