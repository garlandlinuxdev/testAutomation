#!/usr/bin/python
# Project: EOL
# Description:
__author__ = "Adrian Wong"
import os, commonFX, LCD


class measure():
    # Temporary variables, do not modify here
    logger = ''
    com = ''
    display = LCD.display()

    # adjustable limits
    voltageTolerance = 0.05 # percentage of error allowed for voltage test

    def updateLCD(self, FB_Y):
        if FB_Y >= self.display.max_line:
            self.display.fb_clear()
        else:
            self.display.FB_Y = FB_Y

    def update(self, logger, com):
        self.logger = logger
        self.com = com

    def voltage(self, processID):
        phase_status = self.com.readCoil(processID, 49, 4)
        supply_voltage = self.com.readReg(processID, 33, 9)
        return self.display.FB_Y, phase_status, supply_voltage

    def validate(self, ph_status, voltage):
        print "phase_status: ", str(ph_status)[1:-1]
        print "Supply Voltage: ", str(voltage)[1:-1]
        status = [1, 1, 1, 1, 1, 1, 1, 1]
        if ph_status[0] == 0:
            status[0] = 0
            self.logger.info("Phase A not present, " + str(voltage[4]))
            self.display.fb_println("Phase A not present, %r" %voltage[4], 1)
            #print "Phase A not present, ", voltage[4]
        else:
            self.logger.info("Phase A: " + str(voltage[4]/10.0))
            self.display.fb_println("Phase A: %r" %(voltage[4]/10.0), 0)

        if ph_status[1] == 0:
            status[1] = 0
            self.logger.info("Phase B not present, " + str(voltage[5]))
            self.display.fb_println("Phase B not present, %r" %voltage[5], 1)
            #print "Phase B not present, ", voltage[5]
        else:
            self.logger.info("Phase B: " + str(voltage[5]/10.0))
            self.display.fb_println("Phase B: %r" %(voltage[5]/10.0), 0)

        if ph_status[2] == 0:
            status[2] = 0
            self.logger.info("Phase C not present, " + str(voltage[6]))
            self.display.fb_println("Phase C not present, %r" %voltage[6], 1)
            #print "Phase C not present, ", voltage[6]
        else:
            self.logger.info("Phase C: " + str(voltage[6]/10.0))
            self.display.fb_println("Phase C: %r" %(voltage[6]/10.0), 0)

        if 40 <= voltage[7] <= 70:
            self.logger.info("Frequency: " + str(voltage[7]))
            self.display.fb_println("Frequency: %r" %voltage[7], 0)
            #print "Frequency: ", voltage[7]
        else:
            status[3] = 0
            self.logger.info("Frequency not in range, " + str(voltage[7]))
            self.display.fb_println("Frequency not in range, %r" %voltage[7], 1)
            #print "Frequency not in range, ", voltage[7]

        if commonFX.rangeCheck(voltage[0], 2400, self.voltageTolerance) == False:
            status[4] = 0
            self.logger.info("24V supply not in range: " + str(float(voltage[0]) / 100))
            self.display.fb_println("24V supply not in range: %r" %(float(voltage[0]) / 100), 1)
            #print "24V supply not in range: ", float(voltage[0]) / 100
        if commonFX.rangeCheck(voltage[1], 1200, self.voltageTolerance) == False:
            status[5] = 0
            self.logger.info("12V supply not in range: " + str(float(voltage[1]) / 100))
            self.display.fb_println("12V supply not in range: %r" %(float(voltage[1]) / 100), 1)
            #print "12V supply not in range: ", float(voltage[1]) / 100
        if commonFX.rangeCheck(voltage[2], 500, self.voltageTolerance) == False:
            status[6] = 0
            self.logger.info("5V supply not in range: " + str(float(voltage[2]) / 100))
            self.display.fb_println("5V supply not in range: %r" %(float(voltage[2]) / 100), 1)
            #print "5V supply not in range: ", float(voltage[2]) / 100
        if commonFX.rangeCheck(voltage[3], 330, self.voltageTolerance) == False:
            status[7] = 0
            self.logger.info("3.3V supply not in range: " + str(float(voltage[3]) / 100))
            self.display.fb_println("3.3V supply not in range: %r" %(float(voltage[3]) / 100), 1)
            #print "3.3V supply not in range: ", float(voltage[3]) / 100

        for element in status:
            if element == 0:
                self.logger.info("Voltage validation Failed, check logs for errors")
                self.display.fb_println("Voltage validation Failed, check logs for errors", 1)
                #print "Voltage validation Failed, check logs for errors"
                os._exit(1) # uncomment this line to stop test when failed
                break

        self.logger.info("24V supply: " + str(float(voltage[0]) / 100))
        self.logger.info("12V supply: " + str(float(voltage[1]) / 100))
        self.logger.info("5V supply: " + str(float(voltage[2]) / 100))
        self.logger.info("3.3V supply: " + str(float(voltage[3]) / 100))

        self.display.fb_println("24V supply: %r" %(float(voltage[0]) / 100), 0)
        self.display.fb_println("12V supply: %r" %(float(voltage[1]) / 100), 0)
        self.display.fb_println("5V supply: %r" %(float(voltage[2]) / 100), 0)
        self.display.fb_println("3.3V supply: %r" %(float(voltage[3]) / 100), 0)

        return self.display.FB_Y

def main():
    x = 1


# main starts here

if __name__ == "__main__":
    main()
