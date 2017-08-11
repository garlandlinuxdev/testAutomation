#!/usr/bin/python
# Load SIB settings from json file
# Program designed by Adrian Wong
import os, json, time
import modbus_tk
import modbus_tk.defines as cst


class loadJSON():
    motorPIDreg = 300
    current_limit_Reg = 515
    heaterPIDconfig = 0  # ["Standard Grilled", "Water Based", "Future Use 1", "Future Use 2", "Preheat"]
    setpoint = -4500 # initial position setpoint
    enable = [1, 1, 1, 1] # load register function, 1 for enable [motionPID, heaterPID, level sensors]
    logger = ''

    def readJSON(self, filename):
        with open(filename) as data_file:
            data = json.load(data_file)
        data_file.close()
        return data

    def jumperToDec(self, arg):
        combine = ''.join(map(str, reversed(arg)))
        return int(combine, 2)

    def jumperArray(self, data):
        description = []
        jumper = []
        grilltype = []
        for i in range(0, 27):
            description.append(data["jumper"][i]["description"])
            jumper.append(data["jumper"][i]["Grounded"])
            grilltype.append(data["jumper"][i]["grill_type"])

        return description, jumper, grilltype

    def loadMotorPID(self, data):
        motorPID = []
        current_limit = []
        for i in range(0, 6):
            motorPID.extend(data["motor_parameters"]["pid_parameters"][i]["proportional"])
            motorPID.extend(data["motor_parameters"]["pid_parameters"][i]["integral"])
            motorPID.extend(data["motor_parameters"]["pid_parameters"][i]["derivative"])
            motorPID.append(data["motor_parameters"]["pid_parameters"][i]["setpoint_slew_limit"])
            motorPID.append(data["motor_parameters"]["pid_parameters"][i]["integral_accumulator_limit"])
            motorPID.append(data["motor_parameters"]["pid_parameters"][i]["derivative_magnitude_limit"])

            motorPID.append(data["motor_parameters"]["extra"][i]["motor_pwm_slew_rate_up"])
            motorPID.append(data["motor_parameters"]["extra"][i]["motor_pwm_slew_rate_down"])
            motorPID.append(data["motor_parameters"]["extra"][i]["motor_pwm_deadband"])
            motorPID.append(data["motor_parameters"]["extra"][i]["motor_pwm_maximum"])
            motorPID.append(data["motor_parameters"]["extra"][i]["motor_pwm_minimum"])
            motorPID.append(data["motor_parameters"]["extra"][i]["motor_position_deadband"])
            motorPID.append(data["motor_parameters"]["extra"][i]["motor_homing_pwm"])
            motorPID.append(data["motor_parameters"]["extra"][i]["motor_bangbang_seek_pwm"])
            motorPID.append(data["motor_parameters"]["extra"][i]["motor_kicker_rampup_rate"])
            motorPID.append(data["motor_parameters"]["extra"][i]["motor_kicker_maximum"])

            current_limit.append(data["motor_parameters"]["extra"][i]["motor_current_limit"])
        return motorPID, current_limit

    def loadSensor(self, data, setpoint):
        trigger = []
        sensorLimit = []
        sensorPID = []
        levelMotor = []
        encoder = []
        trigger.append(data["auto_calibration"]["lower_virtual_stop"])
        trigger.extend(data["auto_calibration"]["autogap"][0]["minimum_gap"])
        trigger.append(data["auto_calibration"]["autogap"][0]["limit_after_capture"])

        sensorLimit.append(data["auto_calibration"]["absolute_min"])
        sensorLimit.append(data["auto_calibration"]["absolute_min"])
        sensorLimit.append(data["auto_calibration"]["absolute_min"])
        sensorLimit.append(data["auto_calibration"]["absolute_max"])
        sensorLimit.append(data["auto_calibration"]["absolute_max"])
        sensorLimit.append(data["auto_calibration"]["absolute_max"])

        # sensorPID not used
        sensorPID.extend(data["auto_calibration"]["leveling_controller"]["pid_parameters"]["proportional"])
        sensorPID.extend(data["auto_calibration"]["leveling_controller"]["pid_parameters"]["integral"])
        sensorPID.extend(data["auto_calibration"]["leveling_controller"]["pid_parameters"]["derivative"])
        sensorPID.append(data["auto_calibration"]["leveling_controller"]["pid_parameters"]["setpoint_slew_limit"])
        sensorPID.append(
            data["auto_calibration"]["leveling_controller"]["pid_parameters"]["integral_accumulator_limit"])
        sensorPID.append(
            data["auto_calibration"]["leveling_controller"]["pid_parameters"]["derivative_magnitude_limit"])

        levelMotor.append(data["auto_calibration"]["leveling_controller"]["deadband_pwm"])
        levelMotor.append(data["auto_calibration"]["leveling_controller"]["min_pwm"])
        levelMotor.append(data["auto_calibration"]["leveling_controller"]["max_pwm"])
        levelMotor.append(data["auto_calibration"]["leveling_controller"]["kick_pwm"])
        levelMotor.append(data["auto_calibration"]["leveling_controller"]["kick_offset"])

        encoder.append(setpoint)
        encoder.append(data["motor_parameters"]["platen_define_region_1"])
        encoder.append(data["motor_parameters"]["platen_define_region_2"])
        return trigger, sensorLimit, levelMotor, encoder

    def loadHeater(self, data):
        # "cooking_methodologies_names": ["Standard Grilled", "Water Based", "Future Use 1", "Future Use 2", "Preheat"]

        heaterPID = [[], [], [], [], []]
        TCfilter = []
        tempLimit = [1794, 2400, 1794, 2400, 1794, 0, 0, 0]
        heaterProcess = [0, 0, 0, 0, 0, 0, 0, 0]  # temperature setpoint

        TCfilter.extend(data["filter_weight"]["cold_junction"])
        TCfilter.extend(data["filter_weight"]["thermocouple"])

        for i in range(0, 5):
            for j in range(0, 5):
                heaterPID[i].extend(data["cooking_methodologies"][i][j]["proportional"])
                heaterPID[i].extend(data["cooking_methodologies"][i][j]["integral"])
                heaterPID[i].extend(data["cooking_methodologies"][i][j]["derivative"])
                heaterPID[i].append(data["cooking_methodologies"][i][j]["setpoint_slew_limit"])
                heaterPID[i].append(data["cooking_methodologies"][i][j]["integral_accumulator_limit"])
                heaterPID[i].append(data["cooking_methodologies"][i][j]["derivative_magnitude_limit"])

        tempLimit.extend(data["heater_config"]["first_cycle"])
        tempLimit.extend(data["heater_config"]["last_cycle"])
        tempLimit.extend(data["heater_config"]["justify"])

        heaterProcess.extend(data["heater_process"]["type"])
        heaterProcess.extend(data["heater_process"]["sensor_mask"])
        heaterProcess.extend(data["heater_process"]["heater_mask"])

        return TCfilter, heaterPID, tempLimit, heaterProcess

    def loadHardware(self, data):
        description = data["hardware"]["description"]
        sync_role = data["hardware"]["power_sync_role"]

        return description, sync_role

    def setReg(self, master, device, processID, startReg, restTime, Data):
        # For passing condition, no errors should occur and maximum retry is set at 3
        error = 1
        retry = 3
        while error == 1 and retry != 0:
            try:
                time.sleep(restTime)
                master.execute(device, cst.WRITE_MULTIPLE_REGISTERS, startReg, output_value=Data)
                error = 0
            except modbus_tk.modbus.ModbusInvalidResponseError:
                print "error: ", processID
                self.logger.info("Write to register %r failed, @ processID %r" % (startReg, processID))
                error = 1
                retry -= 1
                pass

        return retry, processID

    def readJumperPins(self, master, device, processID, restTime):
        error = 1
        retry = 3
        while error == 1 and retry != 0:
            try:
                time.sleep(restTime)
                jumper = master.execute(device, cst.READ_COILS, 20, 6)
                error = 0
            except modbus_tk.modbus.ModbusInvalidResponseError:
                print "error: ", processID
                self.logger.INFO("Write to coil %r failed, @ processID %r" % (20, processID))
                error = 1
                retry -= 1
                pass

        return retry, processID, jumper

    def maxRetryCheck(self, retry, processID):
        if retry <= 0:
            os._exit(1)
            print "Max retry reached @ %r, exiting script...please restart" %processID
        else:
            pass

    def setDevice(self, master, device, restTime, data):
        # motionPID
        if self.enable[0] == 1:
            motorPID, current_limit = self.loadMotorPID(data)
            retry, processID = self.setReg(master, device, 101, self.motorPIDreg, restTime, motorPID)
            self.maxRetryCheck(retry, processID)
            retry, processID = self.setReg(master, device, 102, self.current_limit_Reg, restTime, current_limit)
            self.maxRetryCheck(retry, processID)
            self.logger.info("Writing motionPID successful")

        # heaterPID
        if self.enable[1] == 1:
            TCfilter, heaterPID, tempLimit, heaterProcess = self.loadHeater(data)
            retry, processID = self.setReg(master, device, 103, 124, restTime, heaterPID[self.heaterPIDconfig])
            self.maxRetryCheck(retry, processID)
            retry, processID = self.setReg(master, device, 104, 256, restTime, TCfilter)
            self.maxRetryCheck(retry, processID)
            retry, processID = self.setReg(master, device, 105, 52, restTime, tempLimit)
            self.maxRetryCheck(retry, processID)
            retry, processID = self.setReg(master, device, 106, 92, restTime, heaterProcess)
            self.maxRetryCheck(retry, processID)
            self.logger.info("Writing heaterPID successful")

        # level sensors
        if self.enable[2] == 1:
            trigger, sensorLimit, levelMotor, encoder = self.loadSensor(data, self.setpoint)
            retry, processID = self.setReg(master, device, 107, 0, restTime, encoder)
            self.maxRetryCheck(retry, processID)
            retry, processID = self.setReg(master, device, 108, 463, restTime, sensorLimit)
            self.maxRetryCheck(retry, processID)
            retry, processID = self.setReg(master, device, 109, 471, restTime, trigger)
            self.maxRetryCheck(retry, processID)
            retry, processID = self.setReg(master, device, 110, 496, restTime, levelMotor)
            self.maxRetryCheck(retry, processID)
            self.logger.info("Writing level sensors successful")

        # power sync role
        if self.enable[3] == 1:
            description, sync_role = self.loadHardware(data)
            temp = [sync_role]
            retry, processID = self.setReg(master, device, 111, 41, restTime, temp)
            self.maxRetryCheck(retry, processID)
            self.logger.info("Writing power sync successful")

def main():
    test = loadJSON()
    data = test.readJSON("29.json")

    #test.setDevice(master, logger, config.device, config.restTime, data)

if __name__ == "__main__":
    main()
