import os
import time
import numpy as np
import struct
import datetime
import win32file
import pywintypes
import psutil
import threading
from collections import deque


def is_process_running(exe_name):
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == exe_name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

if not is_process_running("ConsoleLog.exe"):
    os.startfile(r".\Debug\ConsoleLog.exe")
if not is_process_running("ConsoleOptions.exe"):
    os.startfile(r".\Debug\ConsoleOptions.exe")
if not is_process_running("DAQ.exe"):
    os.startfile(r".\Debug\DAQ.exe")
time.sleep(3)

class DataReceiverThread(threading.Thread):
    HEIGHT = 720
    WIDTH = 240
    def __init__(self, pipeName, bufIm, bufMetaData, parent=None):
        super().__init__(parent)
        self.bRunLoop = False
        self.bLoopStopped = True
        self.bDisable = False
        self.bufMD = bufMetaData
        self.bufIm = bufIm
        self.pipeName = pipeName
        self.frameID = 0
        self.image_buffer = deque(maxlen=5000)
        self.image = np.zeros((self.HEIGHT, self.WIDTH), dtype='uint16')
        for _ in range(500):
            self.image_buffer.append(self.image)
        self.pipe = win32file.CreateFile(
            r'\\.\pipe\\' + pipeName,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            win32file.FILE_ATTRIBUTE_NORMAL, None
        )

    def readImageFromNamedPipe(self):
        data = win32file.ReadFile(self.pipe, 2000000)
        header = struct.unpack('<HHHHHHHHHHHHHHHHQHH', data[1][:44])
        (_, _, _, frameID, width, height, _, _, year, month,
         _, day, hour, minute, second, ms, _, _, _) = header
        im = np.frombuffer(data[1][44:], dtype='uint16')
        timestamp = 1000 * time.mktime(datetime.datetime(
            year, month, day, hour, minute, second, ms).timetuple())
        return [timestamp / 1000.0, frameID, im, height, width]

    def cleanUp(self):
        self.pipe.close()

    def runSetup(self):
        self.bufImSize = np.size(self.bufIm)
        self.fcount = 0

    def runLoop(self):
        try:
            timestamp, frameID, im, height, width = self.readImageFromNamedPipe()
        except pywintypes.error:
            print("Data receiver pipe closed.")
            self.bRunLoop = False
            return
        if frameID == -1:
            return
        self.bufIm[self.fcount * height * width:(self.fcount + 1) * height * width] = im
        self.bufMD[self.fcount * 5:(self.fcount + 1) * 5] = [-1, frameID, height, width, timestamp]
        self.bufMD[self.fcount * 5] = 1  # mark written
        self.fcount += 1
        if (self.fcount + 1) * height * width > self.bufImSize:
            self.fcount = 0
        self.image = im.reshape((height, width))
        self.image_buffer.append(self.image)

    def run(self):
        if self.bDisable:
            return
        self.bRunLoop = True
        self.runSetup()
        while self.bRunLoop:
            self.runLoop()
        self.bLoopStopped = True

    def finish(self):
        self.bRunLoop = False
        while not self.bLoopStopped:
            time.sleep(0.01)
        self.cleanUp()

