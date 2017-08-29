#!/usr/bin/python
# Project: EOL
# Description:
__author__ = "Adrian Wong"
import os


class measure():
    # Temporary variables, do not modify here
    logger = ''
    com = ''
    ac_voltage = 208

    def update(self, logger, com):
        self.logger = logger
        self.com = com

    def voltage(self, processID):
        phase_status = self.com.readCoil(processID, 49, 4)
        supply_voltage = self.com.readReg(processID, 33, 9)
        return phase_status, supply_voltage

    def rangeCheck(self, reading, target):
        if target * 0.95 <= reading <= target * 1.05: #check within +/- 5%
            return True
        else:
            return False

    def validate(self, ph_status, voltage):
        print "phase_status: ", str(ph_status)[1:-1]
        print "Supply Voltage: ", str(voltage)[1:-1]
        status = [1, 1, 1, 1, 1, 1, 1, 1]
        if ph_status[0] == 0:
            status[0] = 0
            self.logger.info("Phase A not present, " + str(voltage[4]))
            print "Phase A not present, ", voltage[4]
        if ph_status[1] == 0:
            status[1] = 0
            self.logger.info("Phase B not present, " + str(voltage[5]))
            print "Phase B not present, ", voltage[5]
        if ph_status[2] == 0:
            status[2] = 0
            self.logger.info("Phase C not present, " + str(voltage[6]))
            print "Phase C not present, ", voltage[6]

        if 40 <= voltage[7] <= 70:
            self.logger.info("Frequency: " + str(voltage[7]))
            print "Frequency: ", voltage[7]
        else:
            status[3] = 0
            self.logger.info("Frequency not in range, " + str(voltage[7]))
            print "Frequency not in range, ", voltage[7]

        if self.rangeCheck(voltage[0], 2400) == False:
            status[4] = 0
            self.logger.info("24V supply not in range: " + str(float(voltage[0]) / 100))
            print "24V supply not in range: ", float(voltage[0]) / 100
        if self.rangeCheck(voltage[1], 1200) == False:
            status[5] = 0
            self.logger.info("12V supply not in range: " + str(float(voltage[1]) / 100))
            print "12V supply not in range: ", float(voltage[1]) / 100
        if self.rangeCheck(voltage[2], 500) == False:
            status[6] = 0
            self.logger.info("5V supply not in range: " + str(float(voltage[2]) / 100))
            print "5V supply not in range: ", float(voltage[2]) / 100
        if self.rangeCheck(voltage[3], 330) == False:
            status[7] = 0
            self.logger.info("3.3V supply not in range: " + str(float(voltage[3]) / 100))
            print "3.3V supply not in range: ", float(voltage[3]) / 100

        for element in status:
            if element == 0:
                self.logger.info("Voltage validation Failed, check logs for error")
                print "Voltage validation Failed, check logs for error"
                # os._exit(1) # uncomment this to stop test when failed
                break

        self.logger.info("24V supply: " + str(float(voltage[0]) / 100))
        self.logger.info("12V supply: " + str(float(voltage[1]) / 100))
        self.logger.info("5V supply: " + str(float(voltage[2]) / 100))
        self.logger.info("3.3V supply: " + str(float(voltage[3]) / 100))


def main():
    x = 1


# main starts here

if __name__ == "__main__":
    main()
