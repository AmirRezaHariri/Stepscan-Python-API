import os
import time
import numpy as np
import struct
import datetime
import matplotlib.pyplot as plt
import pyqtgraph as pg
import win32file
import pywintypes
import psutil

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor

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
time.sleep(5)

class DataReceiverThread(QThread):
    dataReady = Signal(object)

    def __init__(self, pipeName, bufIm, bufMetaData, parent=None):
        super().__init__(parent)
        self.bRunLoop = False
        self.bLoopStopped = True
        self.bDisable = False
        self.bufMD = bufMetaData
        self.bufIm = bufIm
        self.pipeName = pipeName
        self.frameID = 0
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
        self.dataReady.emit(im.reshape((height, width)))

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

bufImSize = 1000 * 1000 * 1000
bufIm = np.zeros(bufImSize, dtype='uint16')
bufMetaData = np.full(int(bufImSize / 1_000_000 * 5 * 100), -1, dtype=float)

dataReceiver = DataReceiverThread("PipeOutput", bufIm, bufMetaData)

app = QApplication([])
win = pg.GraphicsLayoutWidget()
win.showMaximized()
view = win.addViewBox()
view.setAspectLocked(True)
view.invertY(True)
view.setBackgroundColor(QColor(220, 220, 220))

img = pg.ImageItem(border='w')
jetmap = (plt.get_cmap('jet')(np.linspace(0, 1, 256)) * 255).astype(np.uint8)
jetmap[jetmap > 255] = 255
img.setLookupTable(jetmap)
view.addItem(img)
view.enableAutoRange()
textItem = pg.TextItem('')
view.addItem(textItem)

def updateImage(image):
    img.setImage(image.T, levels=[0, 14000]) 

dataReceiver.dataReady.connect(updateImage, Qt.QueuedConnection)
dataReceiver.start()

if __name__ == '__main__':
    import sys
    app.exec()