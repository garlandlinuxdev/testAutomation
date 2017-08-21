#!/usr/bin/python
#Project: EOL
#Description: 
__author__ = "Adrian Wong"
import modbus_tk
import modbus_tk.defines as cst

class actuator():

    def setpoint(self, master, device, SP):
        sp = [SP]
        master.execute(device, cst.WRITE_MULTIPLE_REGISTERS, 0, output_value=sp)

    def spFeedback(self, master, device):
        read = master.execute(device, cst.READ_HOLDING_REGISTERS, 3, 1)
        return read[0]

    def homing(self, master, device):
        out = [1]
        master.execute(device, cst.WRITE_MULTIPLE_REGISTERS, 25, output_value=sp)

def main():


#main starts here

if __name__ == "__main__":
    main()