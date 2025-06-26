# -*- coding: utf-8 -*-
"""
Created on Thu Feb 26 15:10:12 2015

DAQViewer is for viewing the raw tile output exported by the DAQ.exe component

@author: Patrick
"""

import os
import time
os.startfile(r".\Debug\ConsoleLog.exe")
os.startfile(r".\Debug\ConsoleOptions.exe")
os.startfile(r".\Debug\DAQ.exe")
time.sleep(5)

from PySide6.QtCore import * # PySide can be installed from .whl downloadable from here: http://www.lfd.uci.edu/~gohlke/pythonlibs/
from PySide6.QtGui import *
import win32file
import numpy as np
import matplotlib
import time, datetime
import struct
import pywintypes

# Continuously receives data from the named pipe and stores it in a buffer
class DataReceiverThread(QThread): 
    dataReady = Signal(object);    

    def __init__(self, pipeName, bufIm, bufMetaData, parent=None):
        super(DataReceiverThread, self).__init__(parent)
        self.bRunLoop = False;
        self.bLoopStopped = True;
        self.bDisable = False;
        self.bufMD = bufMetaData; # contains the frameID and time stamp for each image
        self.bufIm = bufIm; # the image buffer able to contain many many images
        self.pipeName = pipeName; # the name of the pipe used to receive data 
        self.frameID = 0; # the buffer frame count since data began flowing
        self.pipe = win32file.CreateFile(r'\\.\\pipe\\'+ pipeName,
          win32file.GENERIC_READ | win32file.GENERIC_WRITE,
          0, None,
          win32file.OPEN_EXISTING,
          win32file.FILE_ATTRIBUTE_NORMAL, None)

    def readImageFromNamedPipe(self):
        
        data = win32file.ReadFile(self.pipe, 2000000)
        (nMagic, nLength, nType, nFrameID, nWidth, nHeight, nZipMethod, nZipVersion, TSwYear, TSwMonth, 
         TSwDayOfWeek, TSwDay, TSwHour, TSwMinute, TSwSecond, TSwMilliseconds, anReserved, nFlags, nLength) = struct.unpack('<HHHHHHHHHHHHHHHHQHH', data[1][0:44]);
        
        im = np.frombuffer(data[1][44:], dtype='uint16')
        timestamp = 1000*time.mktime(datetime.datetime(TSwYear,TSwMonth, TSwDay, TSwHour, TSwMinute, TSwSecond, TSwMilliseconds).timetuple())
        frameID = nFrameID;
        self.frameID += 1;
        imHeight = nHeight; imWidth = nWidth;

        return [timestamp/1000.0, frameID, im, imHeight, imWidth];

    def cleanUp(self):
        self.pipe.close()

    def runSetup(self):
        self.bufImSize = np.size(self.bufIm);
        self.fcount = 0;
        
    def runLoop(self):
        try:            
            [timestamp, frameID, im, height, width] = self.readImageFromNamedPipe();
        except pywintypes.error:
            print("Data receiver pipe closed.")
            self.bRunLoop = False;            
            return;                
        if frameID == -1:
            return;
            print("!1!")
        self.bufIm[slice((self.fcount*height*width),((self.fcount+1)*height*width),1)] = np.frombuffer(im, dtype='uint16')            
        self.bufMD[(self.fcount*5):(self.fcount+1)*5] = [-1, frameID, height, width, timestamp];            
        self.bufMD[(self.fcount*5)] = 1; # data has been written
        self.fcount += 1;
        if (self.fcount+1)*height*width > self.bufImSize:
            self.fcount = 0;
        self.dataReady.emit(im.reshape([height, width])); # draw image

    # calls the setup functionality and runs the main loop until finished.
    def run(self):
        if self.bDisable == True:
            return; # do nothing if this thread is disabled        
        self.bRunLoop = True;
        self.runSetup();        
        while self.bRunLoop == True:
            self.runLoop();
        self.bLoopStopped = True;
                                       
    # sends a signal to end the main loop gracefully and waits until this is complete    
    def finish(self):
        self.bRunLoop = False;
        while self.bLoopStopped == False:
            time.sleep(0.01); # wait until the loop has stopped
        self.cleanUp()
            
# Data from DAQ - make sure that DAQ is running and has already begun streaming data
bufImSize = 1000*1000*1000    
bufIm = np.zeros(bufImSize,dtype='uint16')
bufMetaData = np.zeros(int(bufImSize/1000000*5*100)) - 1;
dataReceiver = DataReceiverThread("PipeOutput", bufIm, bufMetaData); # receives data through the named pipe        

# pyqtgraph lib animation output (fast!)
import pyqtgraph as pg  # download at pyqtgraph at http://www.pyqtgraph.org/
from pyqtgraph.Qt import QtCore, QtGui
app = QtGui.QGuiApplication([])
win = pg.GraphicsLayoutWidget()
win.showMaximized()  ## show widget alone in its own window
view = win.addViewBox()
view.setAspectLocked(True)
view.invertY(True);
view.setBackgroundColor([220,220,220])        
img = pg.ImageItem(border='w')
jetmap = (matplotlib.pyplot.get_cmap('jet')(np.arange(0,1.0,1.0/256.0))*255.0).astype('uint8')
jetmap[jetmap > 255] = 255;        
img.setLookupTable(jetmap)        
view.addItem(img)
view.enableAutoRange();        
iterI = 0;
textItem = pg.TextItem('')
view.addItem(textItem)


def updateImage(image):
    global img, prevImage, collectData, datamap, countmap, textItem, times, weights, bStable
    img.setImage(image.transpose(), levels=[0.0,1])  
    #img.setImage(np.rot90(image.transpose()), levels=[0.0,400])  
    
dataReceiver.dataReady.connect(updateImage, Qt.QueuedConnection);
dataReceiver.start();

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':

    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec()
