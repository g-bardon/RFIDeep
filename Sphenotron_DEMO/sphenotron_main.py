from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtNetwork import *
from main import *
from _SingleApp import *
import sys

if __name__ == "__main__":
    appGuid = 'F3FF80BA-BA05-4277-8063-82A6DB9245A2'
    app = QtSingleApplication(appGuid, sys.argv)
    app.setApplicationName("Sphenotron")

    if app.isRunning():
        print(f"RFID is {sys.argv[1]}")
        app.sendMessage(sys.argv[1])
        sys.exit(0)

    spheno = sphenotron()
    spheno.show()
    if len(sys.argv) > 1:
        spheno.open_cycle_tab(sys.argv[1])

    app.setActivationWindow(spheno)
    sys.exit(app.exec_())
