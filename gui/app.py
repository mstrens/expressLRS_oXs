import sys
#this is needed to let pyinstaller include the data files used in the project (ui and jpg )
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)

from PyQt6 import QtWidgets, uic

from PyQt6.QtWidgets import (QMainWindow, QTextEdit,
        QFileDialog, QApplication , QMessageBox)
from pathlib import Path
import configparser
#from PySide6.QtSerialPort import QSerialPort
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo


from serial.tools.list_ports import comports
#from PySide6.QtCore import QIODeviceBase
from PyQt6.QtCore import QIODeviceBase , QByteArray 
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot , QTimer

version = "   (version 0.0.4)"
# TO DO
#add more checks ()
#perform checks when command is generated and save is done
#manage the case where usb is taken out when serial was already open
#add layout for rc channels
#add page for locator, logger, vcc, gnd ,gyro , rcchannels used to drive some functions
#add serial commands (failsafe, ...)
#add gps type
#add the ability to upload the current config from oXs
#PIDN = 500 0 500 500 0 500 500 0 500
#PIDH = 500 500 500 500 500 500 500 500 500
#PIDS = 500 0 500 500 0 500 500 0 500

BLANK_STRING = "N/A"

#those table are used to convert text to code and vice versa
protocolsCode = ["S","F","B","C","H","M","2","J","E","L","I"]
protocolsName = ["Frsky (Sport)" , "Frsky (Fbus)" , "Frsky (Hub)" , "ELRS" ,"Hott" , "Multiplex" , "Futaba Sbus2", "Jeti (Bus)" , "Jeti (Exbus)", "Specktrum SRXL2", "Flysky Ibus"]
escCode = ["HW4",  "BLH",  "JETI", "KON", "ZTW1"]
escName = ["Hobbywing v4", "BlHeli", "Jeti" , "Kontronik" , "ZTW mantis"]
gpsCode = ["U", "E", "C"]
gpsName = ["Ublox configured by oXs", "Ublox configured Externally", "CADIS"]
cmdCode = ["", "?", "SAVE", "DUMP", "SETFAILSAFE", "MPUCAL=A", "MPUCLA=C", "MPUORI=H", "MPUORI=V" , "FV", "FVP", "FVN", "PWM"]
cmdName = ["Display current config (ENTER)", "Help (?)", "Save current oXs config (SAVE)", \
           "Dump current oXs config (DUMP)","Set failsafe with current PWM (SETFAILSAFE)", \
           "Calibrate Accelerometers (MPUCAL=A)" , "Calibrate Gyro offsets (MPUCAL=G)", \
           "Set horizontal MPU orientation (MPUORI=H)" , "Set vertical MPU orientation (MPUORI=V)" , \
           "Display current field values (FV)", "Set all dummy positieve field values (FVP)" , \
           "Set all dummy negatieve field values (FVN)", "Display current PWM values (PWM)" ]
failsafeCode = ["H", "X"]
failsafeName = ["Hold", "Set with handset (when FAILSAFE cmd is sent)"]
gyroStickGainCode = ["1", "2", "3"]
gyroStickGainName = ["Correction on full throw", "Correction on half throw","Correction on quater throw"]
gyroMaxRotateCode = ["1", "2" , "3" , "4"]
gyroMaxRotateName = ["Very low", "Low" , "Medium" , "High"]
gyroStickRotateEnableCode = ["1" , "2"]
gyroStickRotateEnableName = ["Disabled" , "Enabled"]
gyroStabModeCode = ["ON" , "OFF"]
gyroStabModeName = ["Stabilize mode ON (no Hold mode)" , "Hold mode ON (no Stabilize mode)"]

defaultConfig = """
[DEFAULT]
protocol = Frsky (Sport)
crsfbaud = 115200
cbprim = False
pri= 5
cbsec = False
sec = 1
cbtlm = False
tlm = 0
cbsbusout = False
sbus_out = 0
Failsafe = Hold
cbgps = False
gps_tx = 0
gps_rx = 0
gps = Ublox configured by oXs
cbi2c = False
scl = 3
sda = 2
cbVspeedSource = False
acc = 1
cbrpm = False
rpm = 0
RPM_MULT = 1.0
cbvolt1 = False
V1 = 26
Scale1 = 1.0
offset1 = 0.0
cbvolt2 = False
v2 = 26
Scale2 = 1.0
Offset2 = 0.0
cbvolt3 = False
V3 = 26
Scale3 = 1.0
Offset3 = 0.0
cbvolt4 = False
V4 = 26
Scale4 = 1.0
Offset4 = 0.0
cbtemp1 = False
cbtemp2 = False
cbesc = False
Esc_pin = 0
Esc_Type = Hobbywing V4
cbch1 = False
cbch2 = False
cbch3 = False
cbch4 = False
cbch5 = False
cbch6 = False
cbch7 = False
cbch8 = False
cbch9 = False
cbch10 = False
cbch11 = False
cbch12 = False
cbch13 = False
cbch14 = False
cbch15 = False
cbch16 = False
c1 = 0
c2 = 0
c3 = 0
c4 = 0
c5 = 0
c6 = 0
c7 = 0
c8 = 0
c9 = 0
c10 = 0
c11 = 0
c12 = 0
c13 = 0
c14 = 0
c15 = 0
c16 = 0
Pwmhz = 50
cbInvertedLed = False
rgb = 16
cbVcc = False
high = 0
cbGrnd = False
low = 0
cbLocator = False
Spi_Cs = 0
Spi_Sck = 10
Spi_Mosi = 11
Spi_Miso = 8
Spi_Busy = 0
cbLogger = False
Log = 0
logbaud = 115200

cbGyro = False
GMG = 1
GSA = 1
GSE = 1
GSR = 1
GGR = 127
GGP = 127
GGY = 127
GGT = Correction on full throw
GMR = Medium
GRE = Disabled
GST = Stabilize mode ON (no Hold mode)

"""


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('oXs.ui', self)

        self.pushButtonCheckConfig.clicked.connect(self.checkConfig)
        self.pushButtonLoadConfig.clicked.connect(self.loadConfig)
        self.pushButtonSaveAsConfig.clicked.connect(self.saveAsConfig)
        self.pushButtonSearchSerialPort.clicked.connect(self.fill_ports_info)
        self.pushButtonSerialConnect.clicked.connect(self.serialConnect)
        self.pushButtonSerialDisconnect.clicked.connect(self.serialDisconnect)
        self.pushButtonSerialSend.clicked.connect(self.serialSend)
        self.pushButtonClearSerialSend.clicked.connect(self.clearCmdToSend)
        self.comboBoxSerialPort.currentIndexChanged.connect(self.handleSerialPort)
        self.pushButtonClearSerialFromOxs.clicked.connect(self.clearSerialFromOxs)
        self.pushButtonCreateUsbCommand.clicked.connect(self.createUsbCommand)
        self.pushButtonLoadConfigFromOxs.clicked.connect(self.loadConfigFromOxs)
        self.pushButtonReset.clicked.connect(self.resetConfig)
        self.pushButtonSendSelectedCmdToOxs.clicked.connect(self.sendSelectedCmdToOxs)
        
        self.m_serial = QSerialPort(self)
        self.m_serial.errorOccurred.connect(self.handle_error)
        self.m_serial.readyRead.connect(self.read_data)   
        

        #self.plainTextEditSerialFromOxs.clear()
        #self.plainTextEditSerialFromOxs.appendPlainText("Enter here your usb commands")
        
        #self.plainTextEditSerialFromOxs.setLineWrapMode(QtWidgets.QTextEdit.WrapMode.NoWrap)
        self.plainTextEditSerialFromOxs.setLineWrapMode( QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        
        #fill combobox with values
        self.comboBoxProtocol.addItems(protocolsName)
        self.comboBoxFailsafe.addItems(failsafeName)
        self.comboBoxEscType.addItems(escName)
        self.comboBoxGpsType.addItems(gpsName)
        self.comboBoxSendSelectedCmdToOxs.addItems(cmdName)
        self.comboBoxGyroStickGain.addItems(gyroStickGainName)
        self.comboBoxGyroMaxRotate.addItems(gyroMaxRotateName)
        self.comboBoxGyroStickRotateEnable.addItems(gyroStickRotateEnableName)
        self.comboBoxGyroStabMode.addItems(gyroStabModeName)
 
        # set the title
        self.setWindowTitle("Graphical user interface for oXs on RP2040 " + version)
        self.show()
        
    def resetConfig(self):
        config = configparser.ConfigParser()
        config.sections()
        config.read_string(defaultConfig + "[oXs]")
        self.fillUi(config)        

    def sendSelectedCmdToOxs(self):
        if not self.m_serial.isOpen():
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error!")
            dlg.setText("No usb connection with oXs (click first connect on Usb commands tab)")
            button = dlg.exec()
            self.serialDisconnect()
            return
        self.m_serial.write((cmdCode[self.comboBoxSendSelectedCmdToOxs.currentIndex()] + "\r\n").encode('utf-8'))

    def loadConfigFromOxs(self):
        if not self.m_serial.isOpen():
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error!")
            dlg.setText("No usb connection with oXs (click first connect on Usb commands tab)")
            button = dlg.exec()
            self.serialDisconnect()
            return
        self.plainTextEditSerialFromOxs.clear()
        self.m_serial.write("DUMP \r\n".encode('utf-8'))
        #while self.m_serial.bytesAvailable() > 0 :
        #    print(".")
        #print("Dump has been sent")
        #print(len(self.plainTextEditSerialFromOxs.toPlainText()))
        QTimer.singleShot(1000,self.endOfTimer) #endOfTimer will be called after 1000 msec; q loop is not blocked
    
    def endOfTimer(self):
        #process the reply to the DUMP command
        self.strToParse = self.plainTextEditSerialFromOxs.toPlainText()
        self.strToParse = self.strToParse.replace("; SCALE2","; \r\nSCALE2")
        self.strToParse = self.strToParse.replace("; SCALE3","; \r\nSCALE3")
        self.strToParse = self.strToParse.replace("; SCALE4","; \r\nSCALE4")
        self.strToParse = self.strToParse.replace("; OFFSET2","; \r\nOFFSET2")
        self.strToParse = self.strToParse.replace("; OFFSET3","; \r\nOFFSET3")
        self.strToParse = self.strToParse.replace("; OFFSET4","; \r\nOFFSET4")
        self.strToParse = self.strToParse.replace("; OFFSET =","; \r\nOFFSET4 =")
        self.strToParse = self.strToParse.replace("processing cmd"," ")
        self.strToParse = self.strToParse.replace("Cmd to execute:   DUMP"," ")
        self.strToParse = self.strToParse.replace("Dump of the config; can be used to copy, edit, paste","[oXs]")
        #replace name with code
        for i in range(len(protocolsCode)):
            self.strToParse = self.strToParse.replace("PROTOCOL = " + protocolsCode[i] + ";" ,"PROTOCOL = " + protocolsName[i])
        for i in range(len(escCode)):
            self.strToParse = self.strToParse.replace("ESC_TYPE = " + escCode[i] + ";" ,"ESC_TYPE = " + escName[i])
        for i in range(len(gpsCode)):
            self.strToParse = self.strToParse.replace("GPS = " + gpsCode[i] + ";" ,"GPS = " + gpsName[i])
        for i in range(len(failsafeCode)):
            self.strToParse = self.strToParse.replace("FAILSAFE = " + failsafeCode[i] + ";" ,"FAILSAFE = " + failsafeName[i])
        for i in range(len(gyroStickGainCode)):
            self.strToParse = self.strToParse.replace("GGT = " + gyroStickGainCode[i] + ";" ,"GGT = " + gyroStickGainName[i])
        for i in range(len(gyroMaxRotateCode)):
            self.strToParse = self.strToParse.replace("GMR = " + gyroMaxRotateCode[i] + ";" ,"GMR = " + gyroMaxRotateName[i])
        for i in range(len(gyroStickRotateEnableCode)):
            self.strToParse = self.strToParse.replace("GRE = " + gyroStickRotateEnableCode[i] + ";" ,"GRE = " + gyroStickRotateEnableName[i])
        for i in range(len(gyroStabModeCode)):
            self.strToParse = self.strToParse.replace("GST = " + gyroStabModeCode[i] + ";" ,"GST = " + gyroStabModeName[i])

        self.strToParse = self.strToParse.replace(";","")

        self.plainTextEditSerialFromOxs.clear()
        self.plainTextEditSerialFromOxs.appendPlainText(self.strToParse)
        
        config = configparser.ConfigParser()
        config.sections()
        config.read_string(defaultConfig + self.strToParse)
        self.fillUi(config)        

        if "PRI =" in self.strToParse: self.cbPrim.setChecked(True)
        if "SEC =" in self.strToParse: self.cbSec.setChecked(True)
        if "TLM =" in self.strToParse: self.cbTlm.setChecked(True)
        if "SBUS_OUT =" in self.strToParse: self.cbSbusOut.setChecked(True)
        if "GPS_TX =" in self.strToParse or "GPS_RX =" in self.strToParse : self.cbGps.setChecked(True)
        if "SCL =" in self.strToParse or "SDA =" in self.strToParse : self.cbI2c.setChecked(True)
        if "RPM =" in self.strToParse: self.cbRpm.setChecked(True)
        if "V1 =" in self.strToParse: self.cbVolt1.setChecked(True)            
        if "V2 =" in self.strToParse: self.cbVolt2.setChecked(True)            
        if "V3 =" in self.strToParse: self.cbVolt3.setChecked(True)            
        if "V4 =" in self.strToParse: self.cbVolt4.setChecked(True)            
        if "TEMP = 1" in self.strToParse or "TEMP = 2" in self.strToParse : self.cbTemp1.setChecked(True)
        if "TEMP = 2" in self.strToParse : self.cbTemp2.setChecked(True)
        if "ESC_PIN =" in self.strToParse : self.cbEsc.setChecked(True)
        
        if "C1 =" in self.strToParse : self.cbCh1.setChecked(True)
        if "C2 =" in self.strToParse : self.cbCh2.setChecked(True)
        if "C3 =" in self.strToParse : self.cbCh3.setChecked(True)
        if "C4 =" in self.strToParse : self.cbCh4.setChecked(True)
        if "C5 =" in self.strToParse : self.cbCh5.setChecked(True)
        if "C6 =" in self.strToParse : self.cbCh6.setChecked(True)
        if "C7 =" in self.strToParse : self.cbCh7.setChecked(True)
        if "C8 =" in self.strToParse : self.cbCh8.setChecked(True)
        if "C9 =" in self.strToParse : self.cbCh9.setChecked(True)
        if "C10 =" in self.strToParse : self.cbCh10.setChecked(True)
        if "C11 =" in self.strToParse : self.cbCh11.setChecked(True)
        if "C12 =" in self.strToParse : self.cbCh12.setChecked(True)
        if "C13 =" in self.strToParse : self.cbCh13.setChecked(True)
        if "C14 =" in self.strToParse : self.cbCh14.setChecked(True)
        if "C15 =" in self.strToParse : self.cbCh15.setChecked(True)
        if "C16 =" in self.strToParse : self.cbCh16.setChecked(True)
        
        if "LED = I" in self.strToParse : self.cbInvertedLed.setChecked(True)
        if "ACC =" in self.strToParse : self.cbVspeedSource.setChecked(True)
        if "GMG =" in self.strToParse : self.cbGyro.setChecked(True)
        if "HIGH =" in self.strToParse : self.cbVcc.setChecked(True)
        if "LOW =" in self.strToParse : self.cbGrnd.setChecked(True)
        if "SPI_CS =" in self.strToParse : self.cbLocator.setChecked(True)
        if "LOG =" in self.strToParse : self.cbLogger.setChecked(True)


    @pyqtSlot()
    def read_data(self):     
        if self.m_serial.isOpen():
            data = self.m_serial.readAll()        
            self.plainTextEditSerialFromOxs.insertPlainText( data.data().decode('utf-8')) 

    @pyqtSlot(QSerialPort.SerialPortError)
    def handle_error(self, error):
        print("In handle_error")
        print(self.m_serial.errorString())
        if self.m_serial.errorString() != "No error":
            print("serial error occured")
         
            self.m_serial.close()
            self.labelSerialStatus.setText("Disconnected")
            self.pushButtonSerialDisconnect.setEnabled(False)
            self.pushButtonSerialSend.setEnabled(False)
            self.pushButtonSendSelectedCmdToOxs.setEnabled(False)
            self.pushButtonLoadConfigFromOxs.setEnabled(False)
            self.pushButtonSerialConnect.setEnabled(True)

    
        if self.m_serial.isOpen():
            print("In handle error : serial is open")
            self.labelSerialStatus.setText("Connected")
            self.pushButtonSerialDisconnect.setEnabled(True)
            self.pushButtonSerialSend.setEnabled(True)
            self.pushButtonSendSelectedCmdToOxs.setEnabled(True)
            self.pushButtonLoadConfigFromOxs.setEnabled(True)
            self.pushButtonSerialConnect.setEnabled(False)
        else:
            print("In handle error : serial is not open")
            self.labelSerialStatus.setText("Disconnected")
            self.pushButtonSerialDisconnect.setEnabled(False)
            self.pushButtonSerialSend.setEnabled(False)
            self.pushButtonSendSelectedCmdToOxs.setEnabled(False)
            self.pushButtonLoadConfigFromOxs.setEnabled(False)
            self.pushButtonSerialConnect.setEnabled(True)
    
    
    @pyqtSlot()
    # when there is a port, connect is enabled
    # still connect is disabled when we are connected
    # when we are connected, disconnect is enabled (otherwise it is disable)
    # when we are connected, send is enabled (otherwise it is disabled)
    # clear (2X) are always enabled
    def handleSerialPort(self):
        #if self.comboBoxSerialPort.currentIndex() == -1 and not(self.m_serial.isOpen()) :
        if self.comboBoxSerialPort.currentIndex() == -1  :
            self.pushButtonSerialConnect.setEnabled(False)
        else :   
           self.pushButtonSerialConnect.setEnabled(True)
    
    @pyqtSlot()
    def clearCmdToSend(self):
        self.plainTextEditSerialToOxs.clear()

    def clearSerialFromOxs(self):
        self.plainTextEditSerialFromOxs.clear()

    def fill_ports_info(self):
        self.comboBoxSerialPort.clear()
        for info in QSerialPortInfo.availablePorts():
            list = []
            description = info.description()
            manufacturer = info.manufacturer()
            serial_number = info.serialNumber()
            list.append(info.portName())
            list.append(description if description else BLANK_STRING)
            list.append(manufacturer if manufacturer else BLANK_STRING)
            list.append(serial_number if serial_number else BLANK_STRING)
            list.append(info.systemLocation())
            vid = info.vendorIdentifier()
            list.append(f"{vid:x}" if vid else BLANK_STRING)
            pid = info.productIdentifier()
            list.append(f"{pid:x}" if pid else BLANK_STRING)
            self.comboBoxSerialPort.addItem(list[0], list)

        #print(self.comboBoxSerialPort.count())
        
    def serialSend(self):
        if  not self.m_serial.isOpen():
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error!")
            dlg.setText("Usb connection with oXs is lost")
            button = dlg.exec()
            self.serialDisconnect()
            print("serial is closed while writing")
        
        textvalue = self.plainTextEditSerialToOxs.toPlainText() + "\r\n"
        self.m_serial.write(str(textvalue).encode('utf-8'))
        
    def serialConnect(self):
        self.m_serial.setPortName(str(self.comboBoxSerialPort.currentText()))
        self.m_serial.setBaudRate(115200)
        self.m_serial.setDataBits(QSerialPort.DataBits.Data8)
        self.m_serial.setParity(QSerialPort.Parity.NoParity)
        self.m_serial.setStopBits(QSerialPort.StopBits.OneStop)
        self.m_serial.setFlowControl(QSerialPort.FlowControl.NoFlowControl)
        if self.m_serial.isOpen():
            self.m_serial.close()
        if self.m_serial.open(QIODeviceBase.OpenModeFlag.ReadWrite):
            self.m_serial.setDataTerminalReady(True)
            print("Serial is open")
            self.labelSerialStatus.setText("Connected")
            self.pushButtonSerialConnect.setEnabled(False)
            self.pushButtonSerialDisconnect.setEnabled(True)
            self.pushButtonSerialSend.setEnabled(True)
            self.pushButtonSendSelectedCmdToOxs.setEnabled(True)
            self.pushButtonLoadConfigFromOxs.setEnabled(True)
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error!")
            dlg.setText("Can't connect with oXs")
            button = dlg.exec()
            print("Serial is not open")
            self.serialDisconnect()
            
    def serialDisconnect(self):
        if self.m_serial.isOpen():
            self.m_serial.close()
        self.labelSerialStatus.setText("Disconnected")
        self.pushButtonSerialConnect.setEnabled(True)
        self.pushButtonSerialDisconnect.setEnabled(False)
        self.pushButtonSerialSend.setEnabled(False)
        self.pushButtonSendSelectedCmdToOxs.setEnabled(False)
        self.pushButtonLoadConfigFromOxs.setEnabled(False)


    def createUsbCommand(self):
        cmd = "DEFAULT"
        cmd += "; PROTOCOL=" + protocolsCode[self.comboBoxProtocol.currentIndex()]
        if self.comboBoxProtocol.currentText() == "ELRS":
            cmd += "; CRSFBAUD=" + str(self.doubleSpinBoxElrsBds.value())
        if self.cbPrim.isChecked():
            cmd += "; PRI=" + self.comboBoxPrim.currentText() 
        if self.cbSec.isChecked():
            cmd += "; SEC=" + self.comboBoxSec.currentText() 
        if self.cbTlm.isChecked():
            cmd += "; TLM=" + self.comboBoxTlm.currentText()
        if self.cbSbusOut.isChecked():
            cmd += "; SBUS_OUT=" + self.comboBoxSbusOut.currentText()
        if self.comboBoxFailsafe.currentText() == "Hold":
            cmd += "; FAILSAFE=" + failsafeCode[self.comboBoxFailsafe.currentIndex()]
        if self.cbGps.isChecked():
            cmd += "; GPS_TX=" + self.comboBoxGps_Tx.currentText() 
            cmd += "; GPS_RX=" + self.comboBoxGps_Rx.currentText()
            cmd += "; GPS=" + gpsCode[self.comboBoxGpsType.currentIndex()] 
        if self.cbI2c.isChecked():
            cmd += "; SCL=" + self.comboBoxScl.currentText() 
            cmd += "; SDA=" + self.comboBoxSda.currentText()
        if self.cbVspeedSource.isChecked():
            cmd += "; ACC=" + self.comboBoxVspeedSource.currentText()       
        if self.cbRpm.isChecked():
            cmd += "; RPM=" + self.comboBoxRpm.currentText() 
            cmd += "; RPM_MULT=" + str(self.doubleSpinBoxRpmMultiplier.value())
        if self.cbVolt1.isChecked():
            cmd += "; V1=" + self.comboBoxVolt1.currentText() 
            cmd += "; SCALE1=" + str(self.dsScaleVolt1.value())
            cmd += "; OFFSET1=" + str(self.dsOffsetVolt1.value())
        if self.cbVolt2.isChecked():
            cmd += "; V2=" + self.comboBoxVolt2.currentText() 
            cmd += "; SCALE2=" + str(self.dsScaleVolt2.value())
            cmd += "; OFFSET2=" + str(self.dsOffsetVolt2.value())
        if self.cbVolt3.isChecked():
            cmd += "; V3=" + self.comboBoxVolt3.currentText() 
            cmd += "; SCALE3=" + str(self.dsScaleVolt3.value())
            cmd += "; OFFSET3=" + str(self.dsOffsetVolt4.value())
        if self.cbVolt4.isChecked():
            cmd += "; V4=" + self.comboBoxVolt4.currentText() 
            cmd += "; SCALE4=" + str(self.dsScaleVolt4.value())
            cmd += "; OFFSET4=" + str(self.dsOffsetVolt4.value())
        if self.cbTemp1.isChecked() and (not self.cbTemp2.isChecked()) and  self.cbVolt3.isChecked():
            cmd += "; TEMP=1" 
        if self.cbTemp1.isChecked() and (self.cbTemp2.isChecked()) and  self.cbVolt3.isChecked() and self.cbVolt4.isChecked():
            cmd += "; TEMP=2" 
        if self.cbEsc.isChecked():
            cmd += "; ESC_PIN=" + self.comboBoxVolt4.currentText() 
            cmd += "; ESC_TYPE=" + escCode[self.comboBoxEscType.currentIndex()]
        if self.cbCh1.isChecked():  cmd += "; C1=" + self.comboBoxCh1.currentText()
        if self.cbCh2.isChecked():  cmd += "; C2=" + self.comboBoxCh2.currentText() 
        if self.cbCh3.isChecked():  cmd += "; C3=" + self.comboBoxCh3.currentText() 
        if self.cbCh4.isChecked():  cmd += "; C4=" + self.comboBoxCh4.currentText() 
        if self.cbCh5.isChecked():  cmd += "; C5=" + self.comboBoxCh5.currentText() 
        if self.cbCh6.isChecked():  cmd += "; C6=" + self.comboBoxCh6.currentText() 
        if self.cbCh7.isChecked():  cmd += "; C7=" + self.comboBoxCh7.currentText() 
        if self.cbCh8.isChecked():  cmd += "; C8=" + self.comboBoxCh8.currentText() 
        if self.cbCh9.isChecked():  cmd += "; C9=" + self.comboBoxCh9.currentText() 
        if self.cbCh10.isChecked():  cmd += "; C10=" + self.comboBoxCh10.currentText() 
        if self.cbCh11.isChecked():  cmd += "; C11=" + self.comboBoxCh11.currentText() 
        if self.cbCh12.isChecked():  cmd += "; C12=" + self.comboBoxCh12.currentText() 
        if self.cbCh13.isChecked():  cmd += "; C13=" + self.comboBoxCh13.currentText() 
        if self.cbCh14.isChecked():  cmd += "; C14=" + self.comboBoxCh14.currentText() 
        if self.cbCh15.isChecked():  cmd += "; C15=" + self.comboBoxCh15.currentText() 
        if self.cbCh16.isChecked():  cmd += "; C16=" + self.comboBoxCh16.currentText()
        if str(self.sbPwmFrequency.value()) != "50":  cmd += "; PWM=" + str(self.sbPwmFrequency.value())
        if self.cbInvertedLed.isChecked():  cmd += "; LED=I" 
        if self.comboBoxLedGpio.currentText() != "16":  cmd += "; RGB=" + self.comboBoxLedGpio.currentText()
        if self.cbVcc.isChecked():  cmd += "; HIGH=" + self.comboBoxVcc.currentText()
        if self.cbGrnd.isChecked():  cmd += "; LOW=" + self.comboBoxGrnd.currentText()
        if self.cbLocator.isChecked():
            cmd += "; SPI_CS=" + self.comboBoxSpiCs.currentText()
            cmd += "; SPI_SCK=" + self.comboBoxSpiSck.currentText()
            cmd += "; SPI_MOSI=" + self.comboBoxSpiMosi.currentText()
            cmd += "; SPI_MISO=" + self.comboBoxSpiMiso.currentText()
            cmd += "; SPI_BUSY=" + self.comboBoxSpiBusy.currentText()
        if self.cbLogger.isChecked():
            cmd += "; LOG=" + self.comboBoxLogger.currentText()
            cmd += "; LOGBAUD=" + str(self.doubleSpinBoxLoggerBaudrate.value())
        if self.cbGyro.isChecked():
            cmd += "; GMG=" + self.comboBoxGyroMode.currentText()
            cmd += "; GSA=" + self.comboBoxGyroAilStick.currentText()
            cmd += "; GSE=" + self.comboBoxGyroElvStick.currentText()
            cmd += "; GSR=" + self.comboBoxGyroRudStick.currentText()
            cmd += "; GGR=" + str(self.sbGainRoll.value())
            cmd += "; GGP=" + str(self.sbGainPitch.value())
            cmd += "; GGY=" + str(self.sbGainYaw.value())
            cmd += "; GGT =" + gyroStickGainCode[self.comboBoxGyroStickGain.currentIndex()]
            cmd += "; GMR =" + gyroMaxRotateCode[self.comboBoxGyroMaxRotate.currentIndex()]
            cmd += "; GRE =" + gyroStickRotateEnableCode[self.comboBoxGyroStickRotateEnable.currentIndex()]
            cmd += "; GST =" + gyroStabModeCode[self.comboBoxGyroStabMode.currentIndex()]

        self.plainTextEditSerialToOxs.clear()
        self.plainTextEditSerialToOxs.appendPlainText(cmd)
        #print(cmd) 
        
    def loadConfig(self):   #load from a file
        fname = QFileDialog.getOpenFileName(self, 'Select a file', None, "ini(*.ini)")
        config = configparser.ConfigParser()
        config.sections()
        config.read(fname)
        self.fillUi(config)

    def fillUi(self, config):   
        #ms = config['oXs']
        #self.comboBoxProtocol.setCurrentText(ms['comboBoxProtocol'])
        self.comboBoxProtocol.setCurrentText(config['oXs']['PROTOCOL'])
        self.doubleSpinBoxElrsBds.setValue(config.getint('oXs','CRSFBAUD'))
        self.cbPrim.setChecked( config.getboolean('oXs', 'cbPrim'))
        self.comboBoxPrim.setCurrentText(config['oXs']['pri'])
        self.cbSec.setChecked( config.getboolean('oXs', 'cbSec'))
        self.comboBoxSec.setCurrentText(config['oXs']['Sec'])
        self.cbTlm.setChecked( config.getboolean('oXs', 'cbTlm'))
        self.comboBoxTlm.setCurrentText(config['oXs']['Tlm'])
        self.cbSbusOut.setChecked( config.getboolean('oXs', 'cbSbusOut'))
        self.comboBoxSbusOut.setCurrentText(config['oXs']['Sbus_Out'])
                
        self.cbGps.setChecked( config.getboolean('oXs', 'cbGps'))
        self.comboBoxGps_Tx.setCurrentText(config['oXs']['Gps_Tx'])
        self.comboBoxGps_Rx.setCurrentText(config['oXs']['Gps_Rx'])
        self.comboBoxGpsType.setCurrentText(config['oXs']['gps'])
        
        self.cbI2c.setChecked( config.getboolean('oXs', 'cbI2c'))
        self.comboBoxScl.setCurrentText(config['oXs']['Scl'])
        self.comboBoxSda.setCurrentText(config['oXs']['Sda'])
        self.cbVspeedSource.setChecked( config.getboolean('oXs', 'cbVspeedSource'))
        self.comboBoxVspeedSource.setCurrentText(config['oXs']['ACC'])

        self.cbRpm.setChecked( config.getboolean('oXs', 'cbRpm'))
        self.comboBoxRpm.setCurrentText(config['oXs']['Rpm'])
        self.doubleSpinBoxRpmMultiplier.setValue(config.getfloat('oXs','RPM_MULT'))

        self.cbVolt1.setChecked( config.getboolean('oXs', 'cbVolt1'))
        self.comboBoxVolt1.setCurrentText(config['oXs']['V1'])
        self.dsScaleVolt1.setValue(config.getfloat('oXs','Scale1'))
        self.dsOffsetVolt1.setValue(config.getfloat('oXs','Offset1'))

        self.cbVolt2.setChecked( config.getboolean('oXs', 'cbVolt2'))
        self.comboBoxVolt2.setCurrentText(config['oXs']['V2'])
        self.dsScaleVolt2.setValue(config.getfloat('oXs','Scale2'))
        self.dsOffsetVolt2.setValue(config.getfloat('oXs','Offset2'))
            
        self.cbVolt3.setChecked( config.getboolean('oXs', 'cbVolt3'))
        self.comboBoxVolt3.setCurrentText(config['oXs']['V3'])
        self.dsScaleVolt3.setValue(config.getfloat('oXs','Scale3'))
        self.dsOffsetVolt3.setValue(config.getfloat('oXs','Offset3'))

        self.cbVolt4.setChecked( config.getboolean('oXs', 'cbVolt4'))
        self.comboBoxVolt4.setCurrentText(config['oXs']['V4'])
        self.dsScaleVolt4.setValue(config.getfloat('oXs','Scale4'))
        self.dsOffsetVolt4.setValue(config.getfloat('oXs','Offset4'))

        self.cbTemp1.setChecked( config.getboolean('oXs', 'cbTemp1'))
        self.cbTemp2.setChecked( config.getboolean('oXs', 'cbTemp2'))

        self.cbEsc.setChecked( config.getboolean('oXs', 'cbEsc'))
        self.comboBoxEsc.setCurrentText(config['oXs']['Esc_pin'])
        self.comboBoxEscType.setCurrentText(config['oXs']['Esc_type'])
        

        self.cbCh1.setChecked( config.getboolean('oXs', 'cbCh1'))
        self.cbCh2.setChecked( config.getboolean('oXs', 'cbCh2'))
        self.cbCh3.setChecked( config.getboolean('oXs', 'cbCh3'))
        self.cbCh4.setChecked( config.getboolean('oXs', 'cbCh4'))
        self.cbCh5.setChecked( config.getboolean('oXs', 'cbCh5'))
        self.cbCh6.setChecked( config.getboolean('oXs', 'cbCh6'))
        self.cbCh7.setChecked( config.getboolean('oXs', 'cbCh7'))
        self.cbCh8.setChecked( config.getboolean('oXs', 'cbCh8'))
        self.cbCh9.setChecked( config.getboolean('oXs', 'cbCh9'))
        self.cbCh10.setChecked( config.getboolean('oXs', 'cbCh10'))
        self.cbCh11.setChecked( config.getboolean('oXs', 'cbCh11'))
        self.cbCh12.setChecked( config.getboolean('oXs', 'cbCh12'))
        self.cbCh13.setChecked( config.getboolean('oXs', 'cbCh13'))
        self.cbCh14.setChecked( config.getboolean('oXs', 'cbCh14'))
        self.cbCh15.setChecked( config.getboolean('oXs', 'cbCh15'))
        self.cbCh16.setChecked( config.getboolean('oXs', 'cbCh16'))
        
        self.comboBoxCh1.setCurrentText(config['oXs']['C1'])
        self.comboBoxCh2.setCurrentText(config['oXs']['C2'])
        self.comboBoxCh3.setCurrentText(config['oXs']['C3'])
        self.comboBoxCh4.setCurrentText(config['oXs']['C4'])
        self.comboBoxCh5.setCurrentText(config['oXs']['C5'])
        self.comboBoxCh6.setCurrentText(config['oXs']['C6'])
        self.comboBoxCh7.setCurrentText(config['oXs']['C7'])
        self.comboBoxCh8.setCurrentText(config['oXs']['C8'])
        self.comboBoxCh9.setCurrentText(config['oXs']['C9'])
        self.comboBoxCh10.setCurrentText(config['oXs']['C10'])
        self.comboBoxCh11.setCurrentText(config['oXs']['C11'])
        self.comboBoxCh12.setCurrentText(config['oXs']['C12'])
        self.comboBoxCh13.setCurrentText(config['oXs']['C13'])
        self.comboBoxCh14.setCurrentText(config['oXs']['C14'])
        self.comboBoxCh15.setCurrentText(config['oXs']['C15'])
        self.comboBoxCh16.setCurrentText(config['oXs']['C16'])

        self.sbPwmFrequency.setValue(config.getint('oXs','pwmhz'))
        
        self.cbInvertedLed.setChecked( config.getboolean('oXs','cbinvertedled'))
        self.comboBoxLedGpio.setCurrentText(config['oXs']['rgb'])
        self.cbVcc.setChecked( config.getboolean('oXs', 'cbvcc'))
        self.comboBoxVcc.setCurrentText(config['oXs']['High'])
        self.cbGrnd.setChecked( config.getboolean('oXs', 'cbgrnd'))
        self.comboBoxGrnd.setCurrentText(config['oXs']['low'])

        self.cbLocator.setChecked( config.getboolean('oXs', 'cblocator'))
        self.comboBoxSpiCs.setCurrentText(config['oXs']['spi_cs'])
        self.comboBoxSpiSck.setCurrentText(config['oXs']['spi_sck'])
        self.comboBoxSpiMosi.setCurrentText(config['oXs']['spi_mosi'])
        self.comboBoxSpiMiso.setCurrentText(config['oXs']['spi_miso'])
        self.comboBoxSpiBusy.setCurrentText(config['oXs']['spi_busy'])

        self.cbLogger.setChecked( config.getboolean('oXs', 'cblogger'))
        self.comboBoxLogger.setCurrentText(config['oXs']['log'])
        self.doubleSpinBoxLoggerBaudrate.setValue(config.getint('oXs','logbaud'))

        self.cbGyro.setChecked( config.getboolean('oXs', 'cbgyro'))
        self.comboBoxGyroMode.setCurrentText(config['oXs']['GMG'])
        self.comboBoxGyroAilStick.setCurrentText(config['oXs']['GSA'])
        self.comboBoxGyroElvStick.setCurrentText(config['oXs']['GSE'])
        self.comboBoxGyroRudStick.setCurrentText(config['oXs']['GSR'])
        self.sbGainRoll.setValue(config.getint('oXs','GGR'))
        self.sbGainPitch.setValue(config.getint('oXs','GGP'))
        self.sbGainYaw.setValue(config.getint('oXs','GGY'))
        self.comboBoxGyroStickGain.setCurrentText(config['oXs']['GGT'])
        self.comboBoxGyroMaxRotate.setCurrentText(config['oXs']['GMR'])
        self.comboBoxGyroStickRotateEnable.setCurrentText(config['oXs']['GRE'])
        self.comboBoxGyroStabMode.setCurrentText(config['oXs']['GST'])
        


    def saveAsConfig(self): #save the ui in a .ini file
        fcontent = "this is the file content"
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setNameFilter("Ini (*.ini)")
        dialog.setDefaultSuffix('ini')
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        #dialog.setViewMode(QFileDialog.Detail)
        if dialog.exec():
            fileName = dialog.selectedFiles()
            print(fileName[0])

        #options = QFileDialog.options()
        #options |= QFileDialog.DontUseNativeDialog
        #fileName, _ = QFileDialog.getSaveFileName(self, 
        #    "Save File", "", "Ini Files(*.ini);;ini Files(*.ini)", options = options)
        if fileName[0]:
            config = configparser.ConfigParser()
            config['oXs'] = {}
            ms = config['oXs']
            ms['Protocol'] = self.comboBoxProtocol.currentText()
            ms['CRSFBAUD'] = str(self.doubleSpinBoxElrsBds.value())
            ms['cbPrim'] = str(self.cbPrim.isChecked())
            ms["Pri"] = self.comboBoxPrim.currentText()
            ms['cbSec'] = str(self.cbSec.isChecked())
            ms["Sec"] = self.comboBoxSec.currentText()
            ms['cbTlm'] = str(self.cbTlm.isChecked())
            ms["Tlm"] = self.comboBoxTlm.currentText()
            ms['cbSbusOut'] = str(self.cbSbusOut.isChecked())
            ms["Sbus_Out"] = self.comboBoxSbusOut.currentText()
            ms['failsafe'] = self.comboBoxFailsafe.currentText()

            ms['cbGps'] = str(self.cbGps.isChecked())
            ms["Gps_Tx"] = self.comboBoxGps_Tx.currentText()
            ms["Gps_Rx"] = self.comboBoxGps_Rx.currentText()
            ms["Gps"] = self.comboBoxGpsType.currentText()
            
            ms['cbI2c'] = str(self.cbI2c.isChecked())
            ms['Scl'] =   self.comboBoxScl.currentText()
            ms['Sda'] =   self.comboBoxSda.currentText()
            ms['cbVspeedSource'] = str(self.cbVspeedSource.isChecked())
            ms['acc'] = self.comboBoxVspeedSource.currentText()

            ms['cbRpm'] = str(self.cbRpm.isChecked())
            ms['Rpm'] =   self.comboBoxRpm.currentText()
            ms['RPM_MULT'] = str(self.doubleSpinBoxRpmMultiplier.value())
            
            ms['cbVolt1'] = str(self.cbVolt1.isChecked())
            ms['V1'] =   self.comboBoxVolt1.currentText()
            ms['Scale1'] = str(self.dsScaleVolt1.value())
            ms['Offset1'] = str(self.dsOffsetVolt1.value())
            ms['cbVolt2'] = str(self.cbVolt2.isChecked())
            ms['V2'] =   self.comboBoxVolt2.currentText()
            ms['Scale2'] = str(self.dsScaleVolt2.value())
            ms['Offset2'] = str(self.dsOffsetVolt2.value())
            ms['cbVolt3'] = str(self.cbVolt3.isChecked())
            ms['V3'] =   self.comboBoxVolt3.currentText()
            ms['Scale3'] = str(self.dsScaleVolt3.value())
            ms['Offset3'] = str(self.dsOffsetVolt3.value())
            ms['cbVolt4'] = str(self.cbVolt4.isChecked())
            ms['V4'] =   self.comboBoxVolt4.currentText()
            ms['Scale4'] = str(self.dsScaleVolt4.value())
            ms['Offset4'] = str(self.dsOffsetVolt4.value())
            ms['cbTemp1'] =  str(self.cbTemp1.isChecked()) 
            ms['cbTemp2'] =  str(self.cbTemp2.isChecked())
            ms['cbEsc'] = str(self.cbEsc.isChecked())
            ms['Esc_pin'] =   self.comboBoxEsc.currentText()
            ms['Esc_type'] =   self.comboBoxEscType.currentText()
            ms['cbCh1'] = str(self.cbCh1.isChecked())
            ms['cbCh2'] = str(self.cbCh2.isChecked())
            ms['cbCh3'] = str(self.cbCh3.isChecked())
            ms['cbCh4'] = str(self.cbCh4.isChecked())
            ms['cbCh5'] = str(self.cbCh5.isChecked())
            ms['cbCh6'] = str(self.cbCh6.isChecked())
            ms['cbCh7'] = str(self.cbCh7.isChecked())
            ms['cbCh8'] = str(self.cbCh8.isChecked())
            ms['cbCh9'] = str(self.cbCh9.isChecked())
            ms['cbCh10'] = str(self.cbCh10.isChecked())
            ms['cbCh11'] = str(self.cbCh11.isChecked())
            ms['cbCh12'] = str(self.cbCh12.isChecked())
            ms['cbCh13'] = str(self.cbCh13.isChecked())
            ms['cbCh14'] = str(self.cbCh14.isChecked())
            ms['cbCh15'] = str(self.cbCh15.isChecked())
            ms['cbCh16'] = str(self.cbCh16.isChecked())
            ms["C1"] = self.comboBoxCh1.currentText()
            ms["C2"] = self.comboBoxCh2.currentText()
            ms["C3"] = self.comboBoxCh3.currentText()
            ms["C4"] = self.comboBoxCh4.currentText()
            ms["C5"] = self.comboBoxCh5.currentText()
            ms["C6"] = self.comboBoxCh6.currentText()
            ms["C7"] = self.comboBoxCh7.currentText()
            ms["C8"] = self.comboBoxCh8.currentText()
            ms["C9"] = self.comboBoxCh9.currentText()
            ms["C10"] = self.comboBoxCh10.currentText()
            ms["C11"] = self.comboBoxCh11.currentText()
            ms["C12"] = self.comboBoxCh12.currentText()
            ms["C13"] = self.comboBoxCh13.currentText()
            ms["C14"] = self.comboBoxCh14.currentText()
            ms["C15"] = self.comboBoxCh15.currentText()
            ms["C16"] = self.comboBoxCh16.currentText()
            
            ms['pwmhz'] = str(self.sbPwmFrequency.value())
            ms['cbInvertedLed'] = str(self.cbInvertedLed.isChecked())
            ms['rgb'] =  self.comboBoxLedGpio.currentText()
            ms['cbVcc'] = str(self.cbVcc.isChecked())
            ms['high'] = self.comboBoxVcc.currentText()
            ms['cbGrnd'] = str(self.cbGrnd.isChecked())
            ms['low'] = self.comboBoxGrnd.currentText()

            ms['cbLocator'] = str(self.cbLocator.isChecked())
            ms['spi_cs'] = self.comboBoxSpiCs.currentText()
            ms['spi_sck'] = self.comboBoxSpiSck.currentText()
            ms['spi_mosi'] = self.comboBoxSpiMosi.currentText()
            ms['spi_miso'] = self.comboBoxSpiMiso.currentText()
            ms['spi_busy'] = self.comboBoxSpiBusy.currentText()

            ms['cbLogger'] = str(self.cbLogger.isChecked())
            ms['log'] = self.comboBoxLogger.currentText()
            ms['logbaud'] = str(self.doubleSpinBoxLoggerBaudrate.value())

            ms['cbGyro'] = str(self.cbGyro.isChecked())
            ms['GMG'] = self.comboBoxGyroMode.currentText()
            ms['GSA'] = self.comboBoxGyroAilStick.currentText()
            ms['GSE'] = self.comboBoxGyroElvStick.currentText()
            ms['GSR'] = self.comboBoxGyroRudStick.currentText()
            ms['GGR'] = str(self.sbGainRoll.value())
            ms['GGP'] = str(self.sbGainPitch.value())
            ms['GGY'] = str(self.sbGainYaw.value())
            ms['GGT'] = self.comboBoxGyroStickGain.currentText()
            ms['GMR'] = self.comboBoxGyroMaxRotate.currentText()
            ms['GRE'] = self.comboBoxGyroStickRotateEnable.currentText()
            ms['GST'] = self.comboBoxGyroStabMode.currentText()
 
            with open(fileName[0], 'w') as configfile:
                config.write(configfile)
            
            print("file is saved")
    
    
    def checkConfig(self):
        # This is executed when the button is pressed
        # We check that each pin is used only once
        self.lbGpio0.setText("---")
        # 2 tables to count how many time a pin is used and the list of names
        gpiosCnt = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        gpiosLabel = ["0 =>","1 =>","2 =>","3 =>","4 =>","5 =>","6 =>","7 =>","8 =>","9 =>","10 =>",\
                      "11 =>","12 =>","13 =>","<= 14","<= 15","<= 16","<= 17","<= 18","<= 19","<= 20",\
                        "<= 21","<= 22","<= 23","<= 24","<= 25","<= 26","<= 27","<= 28","<= 29"]
        if self.cbPrim.isChecked():    
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxPrim.currentText()) ," Prim ")
        if self.cbSec.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxSec.currentText()) ," Sec ")
        if self.cbTlm.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxTlm.currentText()) ," Tlm ")      
        if self.cbGps.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxGps_Tx.currentText()) ," GPS_TX ")
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxGps_Rx.currentText()) ," GPS_RX ")
        if self.cbI2c.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxScl.currentText()) ," Scl ")
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxSda.currentText()) ," Sda ")
        if self.cbRpm.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxRpm.currentText()) ," Rpm ")
        if self.cbVolt1.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxVolt1.currentText()) ," Volt1 ")    
        if self.cbVolt2.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxVolt2.currentText()) ," Current ")      
        if self.cbVolt3.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxVolt3.currentText()) ," Volt3 ")          
        if self.cbVolt4.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxVolt4.currentText()) ," Volt4 ")         
        if self.cbEsc.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxEsc.currentText()) ," Esc ")
        if self.cbCh1.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh1.currentText()) ," Channel_1 ")
        if self.cbCh2.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh2.currentText()) ," Channel_2 ")
        if self.cbCh3.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh3.currentText()) ," Channel_3 ")    
        if self.cbCh4.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh4.currentText()) ," Channel_4 ")
        if self.cbCh5.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh5.currentText()) ," Channel_5 ")
        if self.cbCh6.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh6.currentText()) ," Channel_5 ")
        if self.cbCh7.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh7.currentText()) ," Channel_7 ")
        if self.cbCh8.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh8.currentText()) ," Channel_8 ")
        if self.cbCh9.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh9.currentText()) ," Channel_9 ")
        if self.cbCh10.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh10.currentText()) ," Channel_10 ")
        if self.cbCh11.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh11.currentText()) ," Channel_11 ")
        if self.cbCh12.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh12.currentText()) ," Channel_12 ")
        if self.cbCh13.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh13.currentText()) ," Channel_13 ")
        if self.cbCh14.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh14.currentText()) ," Channel_14 ")
        if self.cbCh15.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh15.currentText()) ," Channel_15 ")
        if self.cbCh16.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxCh16.currentText()) ," Channel_16 ")
        if self.cbVcc.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxVcc.currentText()) ," High_level ")
        if self.cbGrnd.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxGrnd.currentText()) ," Low_level ")
        if self.cbLocator.isChecked():
            
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxSpiCs.currentText()) ," Spi_Cs ")
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxSpiSck.currentText()) ," Spi_Sck ")
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxSpiMosi.currentText()) ," Spi_Mosi ")
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxSpiMiso.currentText()) ," Spi_Miso ")
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxSpiBusy.currentText()) ," Spi_Busy ")
        if self.cbLogger.isChecked():
            self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxLogger.currentText()) ," Logger ")
        self.fillGpioLabel(gpiosCnt , gpiosLabel, int(self.comboBoxLedGpio.currentText()) ," Led ")
        
        print(gpiosCnt)
        self.lbGpio0.setText(gpiosLabel[0])
        self.lbGpio1.setText(gpiosLabel[1])
        self.lbGpio2.setText(gpiosLabel[2])
        self.lbGpio3.setText(gpiosLabel[3])
        self.lbGpio4.setText(gpiosLabel[4])
        self.lbGpio5.setText(gpiosLabel[5])
        self.lbGpio6.setText(gpiosLabel[6])
        self.lbGpio7.setText(gpiosLabel[7])
        self.lbGpio8.setText(gpiosLabel[8])
        self.lbGpio9.setText(gpiosLabel[9])
        self.lbGpio10.setText(gpiosLabel[10])
        self.lbGpio11.setText(gpiosLabel[11])
        self.lbGpio12.setText(gpiosLabel[12])
        self.lbGpio13.setText(gpiosLabel[13])
        self.lbGpio14.setText(gpiosLabel[14])
        self.lbGpio15.setText(gpiosLabel[15])
        """
        self.lbGpio16.setText(gpiosLabel[16])
        self.lbGpio17.setText(gpiosLabel[17])
        self.lbGpio18.setText(gpiosLabel[18])
        self.lbGpio19.setText(gpiosLabel[19])
        self.lbGpio20.setText(gpiosLabel[20])
        self.lbGpio21.setText(gpiosLabel[21])
        self.lbGpio22.setText(gpiosLabel[22])
        self.lbGpio23.setText(gpiosLabel[23])
        self.lbGpio24.setText(gpiosLabel[24])
        self.lbGpio25.setText(gpiosLabel[25])
        """
        self.lbGpio26.setText(gpiosLabel[26])
        self.lbGpio27.setText(gpiosLabel[27])
        self.lbGpio28.setText(gpiosLabel[28])
        self.lbGpio29.setText(gpiosLabel[29])
        
        dubbelGpioS = False
        for i in range( len(gpiosCnt)):
            if gpiosCnt[i] > 1: dubbelGpioS = True
        if dubbelGpioS :
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error in the gpio's assignment!")
            dlg.setText("At least one gpio has more than one function")
            button = dlg.exec()
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Configuration checked!")
            dlg.setText("No error detected")
            button = dlg.exec()

    def fillGpioLabel(self, gpio , gpiosLb, ind , txt):
        gpio[ind] = gpio[ind] + 1
        if ind < 14:
            gpiosLb[ind] = gpiosLb[ind] + txt
        else :
            gpiosLb[ind] = txt + gpiosLb[ind]    

app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec()

