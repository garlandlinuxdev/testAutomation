#!/usr/bin/python
# Project: EOL
# Description: module for importing shared variables between module, used to track Y location of LCD
__author__ = "Adrian Wong"

# ../myproject/subfile.py

# Save "hey" into myList
def storage(FB_Y):
    # You have to make the module main available for the code here.
    # Placing the import inside the function body will usually avoid import cycles -
    # unless you happen to call this function from either main or subfile's body
    # (i.e. not from inside a function or method)
    import EOL
    EOL.FB_Y = FB_Y

def getStorage():
    import EOL
    return EOL.FB_Y
