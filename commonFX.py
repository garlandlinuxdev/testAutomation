#!/usr/bin/python
# Project: common functions
# Description: group of commonly used functions
__author__ = "Adrian Wong"
import time


def timeCal(arg):  # time calculation
    timeElapse = time.time() - long(arg)
    return timeElapse


def rangeCheck(reading, target, tolerance):
    high = 1 + tolerance
    low = 1 - tolerance
    if target * low <= reading <= target * high:  # check within +/- %
        return True
    else:
        return False


def signedInt(arg):
    # MOD(NUM+2^15,2^16)-2^15
    num = ((int(arg) + 2 ** 15) % (2 ** 16)) - 2 ** 15
    return num
