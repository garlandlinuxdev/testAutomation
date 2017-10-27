#!/usr/bin/python
#Project: EOL
#Description: 
__author__ = "Adrian Wong"
import serial, os, modbus, time, csv
import jsonToFile, actuator, platen, commonFX
import EOL


def writeToCSV(config, zdbf, sensor):
    datestr = time.strftime('%Y/%m/%d')
    timestr = time.strftime('%H:%M:%S')
    epoch_time = int(time.time())
    with open(config.logfile + 'test' + epoch_time + config.excel, 'a') as test:
        fieldnames = (
            'date', 'time', 'grill_type', 'zdbf', 'rear_enc', 'front_enc')
        targetWriter = csv.DictWriter(test, delimiter=',', lineterminator='\n', fieldnames=fieldnames)
        headers = dict((n, n) for n in fieldnames)
        targetWriter.writerow(headers)
        targetWriter.writerow(
            {'date': datestr, 'time': timestr, 'grill_type': config.grillType,
             'zdbf': str(zdbf),
             'rear_enc': str(sensor[0]),
             'front_enc': str(sensor[1]),
             })
    test.close()

def main():
    #main starts here
    config = EOL.myConfig()
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

    config.json_test_config, config.voltage_config, config.platen_config, config.actuator_config, config.switch_config = myJSON.loadSettings(
        info, config.customer)

    motor = actuator.motion()
    motor.update(logger, com, config)
    config.encoder_conv = motor.encoder_conv

    pl = platen.sensors()
    pl.update(logger, com, config)

    counter = 0
    motor.homing(processID)
    motor.resetMode(processID)
    while counter <= config.cycle:
        config.display.fb_println(counter, 1)
        motor.setpoint(-500)
        time.sleep(8)
        zdbf, gap = pl.calZDBF()
        config.display.fb_println("ZDBF: %r  |  Rear: %r  |  Front: %r" %(zdbf, gap[0], gap[1]), 0)
        writeToCSV(config, zdbf, gap)
        counter += 1

if __name__ == "__main__":
    main()