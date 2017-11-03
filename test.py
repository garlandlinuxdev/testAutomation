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
                'date', 'time', 'grill_type', 'rear_enc', 'front_enc', 'zdbf', 'rear_inch', 'front_inch', 'zdbf_mils')
            targetWriter = csv.DictWriter(test, delimiter=',', lineterminator='\n', fieldnames=fieldnames)
            headers = dict((n, n) for n in fieldnames)
            targetWriter.writerow(headers)
        test.close()
    else:
        with open(filename, 'a') as test:
            fieldnames = (
                'date', 'time', 'grill_type',  'rear_enc', 'front_enc', 'zdbf', 'rear_inch', 'front_inch', 'zdbf_mils')
            targetWriter = csv.DictWriter(test, delimiter=',', lineterminator='\n', fieldnames=fieldnames)
            # headers = dict((n, n) for n in fieldnames)
            # targetWriter.writerow(headers)
            targetWriter.writerow(
                {'date': datestr, 'time': timestr, 'grill_type': config.grillType, 'rear_enc': str(enc[0]),
                 'front_enc': str(enc[1]), 'zdbf': str(zdbf), 'rear_inch': str(commonFX.encToInch(enc[0])),
                 'front_inch': str(commonFX.encToInch(enc[1])), 'zdbf_mils': str(commonFX.encToInch(zdbf) * 1000)
                 })
        test.close()


def main():
    # define variables
    waitTime = 120
    zdbf = 0
    gap = [0, 0]
    name = 'test'

    # main starts here
    config = EOL.myConfig()
    if config.display.checkOS() == True:
        config.display.fb_clear()
        config.copyLog()
    logger = EOL.setup_logger('event_log', config.logfile + config.log)
    config.logger = logger

    epoch_time = int(time.time())

    try:
        master = EOL.setup()
    except serial.serialutil.SerialException:
        config.display.fb_clear()
        config.display.fb_long_print("FTDI USB cable not found, please connect cable and restart", 1)
        logger.info("FTDI USB cable not found, please connect cable and restart")
        os._exit(1)

    config.updateSettings()

    config.display.fb_clear()
    logger.info("==================== Load Settings ====================")
    config.display.fb_println("=============== Load Settings ===============", 1)

    processID = 0
    com = modbus.communicate()
    com.setup(logger, master, config.device, config.restTime)

    myJSON = jsonToFile.loadJSON()
    myJSON.update(logger, com, config.loadReg_enable)

    # info = myJSON.readJSON(config.linuxPath + config.sysPath + 'settings.json')
    try:
        info = myJSON.readJSON(config.linuxPath + config.sysPath + 'settings.json')
    except ValueError:
        logger.info("settings.json file corrupted, update settings required")
        config.display.fb_long_print("settings.json file corrupted, update settings required", 0)
        os._exit(1)

    config.grillType = myJSON.grillType(processID)
    config.updateJSON(config.grillType)
    logger.info(config.jsonFile)

    testlog = config.logfile + str(name) + '_' + str(config.grillType) + '_' + str(epoch_time) + '-' + config.excel
    writeToCSV(config, testlog, zdbf, gap, 1)

    config.json_test_config, config.voltage_config, config.platen_config, config.actuator_config, config.switch_config = myJSON.loadSettings(
        info, config.customer)

    data = myJSON.readJSON(config.jsonFile)
    myJSON.setDevice(data)

    motor = actuator.motion()
    motor.update(logger, com, config)
    config.encoder_conv = motor.encoder_conv

    pl = platen.sensors()
    pl.update(logger, com, config)

    counter = 1
    motor.homing(processID)
    motor.resetMode(processID)

    while counter <= config.cycle:
        config.display.fb_println('Cycle: %r' % counter, 1)
        pl.resetMode(processID)
        motor.setpoint(-4000)
        startTime = time.time()
        while commonFX.timeCal(startTime) <= waitTime:
            pl.com.readReg(processID, 0, 1)
            time.sleep(0.5)
        motor.setpoint(-500)
        time.sleep(8)
        zdbf, gap = pl.calZDBF()
        config.display.fb_println("ZDBF: %r  |  Rear: %r  |  Front: %r" % (zdbf, gap[0], gap[1]), 0)
        writeToCSV(config, testlog, zdbf, gap, 0)
        counter += 1

    while True:
        pl.com.readReg(processID, 0, 1)


if __name__ == "__main__":
    main()
