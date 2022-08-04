#!/usr/bin/env python
# coding=utf-8

from datetime import datetime
from genericpath import isdir
import os
import platform
from LRFutils.color import Color
import re
import sys
import traceback
import logging

# Get current time as string
def now(human=False):
    time = str(datetime.now())
    if human:
        return f"{time[8:10]}/{time[5:7]}/{time[0:4]} at {time[11:13]}:{time[14:16]}:{time[17:19]}"
    else:
        return time.replace(" ", "_").replace(":", ".")

startTime = now()
filename = f"logs/{startTime}.log"
if not os.path.isdir("logs"): os.makedirs(f"logs/")

# Getting the current environment
with open(filename, "a") as logFile:
    logFile.write(f"ENVIRONMENT: {platform.uname()}\n\n")

# Print message in log file
def logSave(message):
    currentTime = now(human = True)
    with open(filename, "a", encoding="utf-8") as logFile:
        logFile.write(f"{currentTime} | {message}\n")

# Print message in terminal
def logPrint(message):
    currentTime = now(human = True)
    print(f'{currentTime} | {message}')

# Info-styled messages
def info(message):
    logSave(f"[INFO] {message}")
    message = Color.Green + "[INFO] " + Color.NC + message
    logPrint(message)
    
# Warning-styled messages
def warn(message):
    message = f"[WARNING] {message}"
    logSave(message)
    message = Color.Yellow + message + Color.NC
    logPrint(message)

# Error-styled messages
def error(message, etype = None, value = None, tb=None):
    message = f"[ERROR] {message}"
    logSave(message)
    message = Color.on_Red + message + Color.NC

    if etype is None or value is None or tb is None: tb = traceback.format_exc()
    else: tb = ''.join(traceback.format_exception(etype, value, tb))
    logSave(f"Full traceback below.\n\n{tb}")

    logPrint(message + "\n -> Look at the log file for more information.\n")

# Catch unexpected crashes
def myexcepthook(etype, value, tb):
    error(f"🤕 Uh, there is an unexpected error somewhere: {value} ({type})", etype=etype, value=value, tb=tb)

sys.excepthook = myexcepthook