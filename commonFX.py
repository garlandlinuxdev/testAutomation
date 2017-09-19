#!/usr/bin/python
# Project: common functions
# Description: group of commonly used functions
__author__ = "Adrian Wong"
import time


def timeCal(arg):  # time calculation
    timeElapse = time.time() - long(arg)
    return timeElapse


def baumerToMM(arg):
    mm = 10 - ((arg * 10.0) / 32767)
    return mm

def mmToBaumer(arg):
    count = ((10 - arg) * 32767) / 10
    return count

def encToInch(arg, conv = None):
    if conv == None:
        enc = arg * 0.000492126
    else:
        enc = arg * conv
    return enc

def rangeCheck(reading, target, tolerance, lower_limit=None):
    if lower_limit is None:  # same tolerance for upper and lower
        if target < 0:
            low = 1 + tolerance
            high = 1 - tolerance
        else:
            high = 1 + tolerance
            low = 1 - tolerance

    else:
        if target < 0:
            low = 1 + tolerance  # upper limit
            high = 1 - lower_limit
        else:
            high = 1 + tolerance  # upper limit
            low = 1 - lower_limit

    if target * low <= reading <= target * high:  # check within +/- %
        return True
    else:
        return False


def below_threshold(a, b, threshold):
    result = abs(a - b)
    if result < threshold:
        return True
    else:
        return False


def signedInt(arg):
    # MOD(NUM+2^15,2^16)-2^15
    num = ((int(arg) + 2 ** 15) % (2 ** 16)) - 2 ** 15
    return num


def signedFloat(arg):
    # MOD(NUM+2^15,2^16)-2^15
    num = ((float(arg) + 2 ** 15) % (2 ** 16)) - 2 ** 15
    return num
