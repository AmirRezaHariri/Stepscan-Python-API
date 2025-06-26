# -*- coding: utf-8 -*-
"""
Created on Mon Feb 23 14:51:06 2015

@author: Patrick
"""

from PySide2.QtCore import *
from PySide2.QtGui import *
import pyqtgraph as pg
import sys, os
import time
from numpy import *
import numpy as np


# pyqtgraph lib animation output (fast!)
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
app = QtGui.QApplication([])
win = pg.GraphicsLayoutWidget()
win.ci.setBorder([255,255,255], width=5)
win.showMaximized()  ## show widget alone in its own window
view = win.addViewBox()
view.setAspectLocked(True)
view.invertY(True);
view.setBackgroundColor([220,220,220])        
view.enableAutoRange()
view.setAutoVisible()

# setting up the tracked paths of clients and client labels
paths = pg.GraphItem()
view.addItem(paths)
alpha = 150; width = 1;
lineStyles = np.array([(0,0,255,alpha,width), (0,255,0,alpha,width), (255,0,0,alpha,width), (255,0,255,alpha,width), (0,255,255,alpha,width), (255,255,150,alpha,width), (0,0,0,alpha,width)], dtype=[('red',np.ubyte),('green',np.ubyte),('blue',np.ubyte),('alpha',np.ubyte),('width',float)])        
colours = np.array([(0,0,255), (0,255,0), (255,0,0), (255,0,255), (0,255,255), (255,100,50)]);#, dtype=[('red',np.ubyte),('green',np.ubyte),('blue',np.ubyte)])        
cover = []

     
clientLabels = []
for iterI in range(100):
    textItem = pg.TextItem(html='<span style="color: #FFF; font-size: 20pt;"></span>')
    view.addItem(textItem)
    clientLabels.append(textItem)


# Continuously receives data from the named pipe and stores it in a buffer
class DISReceiverThread(QThread): 
    dataReady = Signal(object);    

    def __init__(self, filePath, parent=None):
        super(DISReceiverThread, self).__init__(parent)
        self.bRunLoop = False;
        self.bLoopStopped = True;
        self.bDisable = False;
        self.filePath = filePath; # the name of the pipe used to receive data 
        self.frameID = 0; # the buffer frame count since data began flowing
        self.lastFrameNo = ["-1"]

    def readDataFromFile(self):        
        sigf = open(self.filePath+"sig.txt", "r"); sig = sigf.readline(); sigf.close()                
        if len(sig) > 0 and int(sig)==1: # check that a fresh frame has been output              
            dataf = open(self.filePath+"data.txt", "r"); 
            frameNo = dataf.readline(); 
            self.individuals = [];                        
            if len(frameNo) > 0 and (self.lastFrameNo[0] != frameNo or len(self.lastFrameNo) < 20):
                if len(self.lastFrameNo) < 20:                
                    self.lastFrameNo.append(frameNo)
                else:
                    self.lastFrameNo = self.lastFrameNo[1:] + [frameNo]
                track = dataf.readline().split(",")
                while (len(track) > 1):
                    #import pdb; pdb.set_trace()
                    track = np.array(track).astype('double')
                    trackint = track.astype('int')
                    self.individuals.append([trackint[0], track[1:3].tolist(), [track[3], 0], trackint[4]]) 
                    track = dataf.readline().split(",")

                sig = open("sig.txt", "w"); sig.write("2"); sig.close(); #signal to the data reader to close
            dataf.close()  
        else:
            sig = open("sig.txt", "w"); sig.write("2"); sig.close(); #signal to the data reader to close
            self.bUpdate = False

    def cleanUp(self):
        pass

    def runSetup(self):
        pass
        
    def runLoop(self):
        self.readDataFromFile();
        time.sleep(0.04)        
        self.dataReady.emit(self.individuals); # draw image

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
            

# minX, maxX, minY, maxY
def expandCover(cover, x, y):
    if len(cover) > 0:    
        if (cover[0] > x):
            cover[0] = x
        if (cover[1] < x):
            cover[1] = x
        if (cover[2] > y):
            cover[2] = y
        if (cover[3] < y):
            cover[3] = y
    else:
        cover = [x, x, y, y]
    return cover

def convertToSensors(refX, refY, coord):
    #import pdb; pdb.set_trace()    
#    sensors_per_deg_y = 200.0*(111132.954 - 559.822 * cos(2 * refY) + 1.175 * cos(4 * refY));
#    sensors_per_deg_x = 200.0*(111132.954 * cos(refY));
    sensors_per_deg_y = 1;
    sensors_per_deg_x = 1;
    return [(coord[0] - refX)*sensors_per_deg_x, (coord[1] - refY)*sensors_per_deg_y]

def updateField(individuals):
    global paths, clientLabels, lineStyles, cover    
    # show region major and minor axes        
    pos = []; adj = []; lineSty = [];   

    if len(cover) > 0:
        # draw a line indicating orientation for each individual
        esize = 0.05;        
        for iterI in range(len(individuals)):
            poslen = len(pos);        
            indi = individuals[iterI]            
            orient = indi[2][0]                   
            conpos = convertToSensors(cover[0], cover[2], indi[1]);
            pos.append([conpos[0] + cos((orient+90)*pi/180)*esize*0.2, conpos[1] + sin((orient+90)*pi/180)*esize*0.2])
            pos.append([conpos[0] + cos((orient-90)*pi/180)*esize*0.2, conpos[1] + sin((orient-90)*pi/180)*esize*0.2])
            pos.append([conpos[0] + cos(orient*pi/180)*esize*2, conpos[1] + sin(orient*pi/180)*esize*2])
            pos.append([conpos[0] + cos((orient+90)*pi/180)*esize*0.2, conpos[1] + sin((orient+90)*pi/180)*esize*0.2])
            cover = expandCover(cover, indi[1][0], indi[1][1])        
            adj.append([poslen+0, poslen+1])
            adj.append([poslen+1, poslen+2])
            adj.append([poslen+2, poslen+3])
            lineSty.append(lineStyles[6]);   
            lineSty.append(lineStyles[6]);   
            lineSty.append(lineStyles[6]);   
       
       
        # label each individual numerically       
        #import pdb; pdb.set_trace()        
        posture = ["-", "S", "S", "S", "K", "P", "P"]
        movement = ["-", "N", "W", "R", "N", "N", "C"]
        for iterI in range(len(individuals)):
            individuals[iterI][3] /= 65536        
            clientLabels[iterI].setHtml('<span style="color: #888; font-size: 20pt;">'+str(individuals[iterI][0])+movement[individuals[iterI][3]]+posture[individuals[iterI][3]]+'</span>')    
            sens = convertToSensors(cover[0], cover[2], individuals[iterI][1])        
            clientLabels[iterI].setPos(sens[0], sens[1])
    
        ## set cover min position on screen        
        sens = convertToSensors(cover[0], cover[2], [cover[1], cover[3]])                
        #clientLabels[len(individuals)].setHtml('<span style="color: #888; font-size: 20pt;"> ('+str(abs(cover[2]))+( "\xb0 N" if cover[2] >= 0 else "\xb0 S")+", "+str(abs(cover[0]))+("\xb0 E" if cover[0] >= 0 else "\xb0 W") +')</span>')    
        clientLabels[len(individuals)].setHtml('<span style="color: #888; font-size: 20pt;"> ('+str(cover[2])+", "+str(cover[0])+')</span>')    
        clientLabels[len(individuals)].setPos(sens[0]/3, 0)
        
        
        for iterI in range(len(individuals)+1,size(clientLabels)):
            clientLabels[iterI].setText(''); # reset text on unused labels
    
        # display the rectangular extent of all positions seen so far
        poslen = len(pos);        
        maxXY = convertToSensors(cover[0], cover[2], [cover[1], cover[3]])        
        #import pdb; pdb.set_trace()
        pos.append([0, 0])
        pos.append([maxXY[0], 0])
        adj.append([poslen+0, poslen+1])
        lineSty.append(lineStyles[6]);   
        pos.append([maxXY[0], maxXY[1]])
        adj.append([poslen+1, poslen+2])
        lineSty.append(lineStyles[6]);   
        pos.append([0, maxXY[1]])
        adj.append([poslen+2, poslen+3])
        lineSty.append(lineStyles[6]);   
        pos.append([0, 0])
        adj.append([poslen+3, poslen+4])
        lineSty.append(lineStyles[6]);   
        
        if size(pos) > 0:
            paths.setData(pos=array(pos), adj=array(adj).astype('int'), pen=array(lineSty), size=0.01, pxMode=False)
            paths.setVisible(True)
    else:
        if len(individuals) > 0:
            indi = individuals[0]            
            cover = expandCover(cover, indi[1][0], indi[1][1]) 


DISReceiver = DISReceiverThread("..\\Distributables\\"); # receives data through the named pipe        
DISReceiver.dataReady.connect(updateField, Qt.QueuedConnection);
DISReceiver.start();

    
## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()             

