import sys
import os
import weakref
import importlib
from PyQt5.QtCore import *

import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import functions as fn
from pyqtgraph import Point
# from controllers.AnimalAddEvent import *
from tools.add_cycling_data import *
from datetime import datetime

class signal_refresh(QObject):
    signal_refresh_cycle = pyqtSignal()


class MyViewBox(pg.ViewBox):
    def __init__(self, rfid = None, mysignal = None, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.rfid = rfid
        self.mysignal = mysignal  ## Here we get the instance of the signal class

    def mouseDragEvent(self, ev, axis=None):
        ## if axis is specified, event will only affect that axis.
        ev.accept()  ## we accept all buttons

        pos = ev.pos()
        lastPos = ev.lastPos()
        dif = pos - lastPos
        dif = dif * -1

        ## Ignore axes if mouse is disabled
        mouseEnabled = np.array(self.state['mouseEnabled'], dtype=np.float64)
        mask = mouseEnabled.copy()
        if axis is not None:
            mask[1 - axis] = 0.0

        ## Scale or translate based on mouse button
        if ev.button() & (QtCore.Qt.LeftButton | QtCore.Qt.MiddleButton):
            if self.state['mouseMode'] == pg.ViewBox.RectMode and axis is None:
                if ev.isFinish():  ## This is the final move in the drag; change the view scale now
                    # print ("finish")
                    self.rbScaleBox.hide()
                    ax = QtCore.QRectF(Point(ev.buttonDownPos(ev.button())), Point(pos))
                    ax = self.childGroup.mapRectFromParent(ax)
                    self.showAxRect(ax)
                    self.axHistoryPointer += 1
                    self.axHistory = self.axHistory[:self.axHistoryPointer] + [ax]
                else:
                    ## update shape of scale box
                    self.updateScaleBox(ev.buttonDownPos(), ev.pos())
            else:
                tr = self.childGroup.transform()
                tr = fn.invertQTransform(tr)
                tr = tr.map(dif * mask) - tr.map(Point(0, 0))

                x = tr.x() if mask[0] == 1 else None
                y = tr.y() if mask[1] == 1 else None

                self._resetTarget()
                if x is not None or y is not None:
                    self.translateBy(x=x, y=y)
                self.sigRangeChangedManually.emit(self.state['mouseEnabled'])
        elif ev.button() & QtCore.Qt.RightButton:
            pos_debut = ev.buttonDownScenePos(ev.button())
            start_dtime = datetime.fromtimestamp(pg.ViewBox.mapSceneToView(self, pos_debut).x()).replace(microsecond=0)
            if ev.isFinish():
                self.rbScaleBox.hide()
                end_dtime = datetime.fromtimestamp(pg.ViewBox.mapSceneToView(self, ev.scenePos()).x()).replace(microsecond=0)
                start_dtime, end_dtime = min(start_dtime,end_dtime), max(start_dtime, end_dtime)
                new_cycle = add_cycle(rfid=self.rfid, start_dtime=start_dtime, end_dtime=end_dtime, type='breeding')
                if new_cycle:
                    self.mysignal.signal_refresh_cycle.emit()
            else:
                ## update shape of scale box
                self.updateScaleBox(ev.buttonDownPos(), ev.pos())

    def mouseDoubleClickEvent(self, ev):
        ev.accept()  ## we accept all buttons
        if ev.button() & QtCore.Qt.RightButton:
            pos_debut = ev.scenePos()
            start_dtime = datetime.fromtimestamp(pg.ViewBox.mapSceneToView(self, pos_debut).x()).replace(microsecond=0)
            end_dtime = 0
            new_cycle = add_cycle(rfid=self.rfid, start_dtime=start_dtime, end_dtime=end_dtime, type='phenology')
            if new_cycle:
                self.mysignal.signal_refresh_cycle.emit()

class MyPlotItem(pg.PlotItem):
    def __init__(self, parent=None, rfid=None, mysignal=None, *args, **kargs):
        self.rfid = rfid
        self.mysignal = mysignal
        super().__init__(parent, viewBox=MyViewBox(rfid = self.rfid, mysignal=self.mysignal), *args, **kargs)

