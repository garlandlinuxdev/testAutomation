#!/usr/bin/python
#Project: EOL
#Description: 
__author__ = "Adrian Wong"

class measure():
    # Temporary variables, do not modify here
    logger = ''
    com = ''

    def update(self, logger, com):
        self.logger = logger
        self.com = com

    def voltage(self, processID):
        phase_status = self.com.readCoil(processID, 49, 4)
        supply_voltage = self.com.readReg(processID, 33, 9)
        return phase_status, supply_voltage

def main():
    x = 1

#main starts here

if __name__ == "__main__":
    main()