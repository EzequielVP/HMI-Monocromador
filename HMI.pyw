import serial
import serial.tools.list_ports
import sys
import time

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox

from interfazui import Ui_MainWindow  # importing our generated file


class mywindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        #           BOTONES
        self.ui.goscan.clicked.connect(self.go_scan)
        #           Combobox
        self.ui.shutter.addItem("Closed")
        self.ui.shutter.addItem("Open")
        #   tratamiento desactivar EditLine
        self.ui.presentwave.setReadOnly(True)  # desavilita los editline
        self.ui.response.setReadOnly(True)
        self.ui.setwave.setMaxLength(4)
        #       tratamiento de centrado
        self.ui.setwave.setAlignment(Qt.AlignCenter)
        self.ui.presentwave.setAlignment(Qt.AlignCenter)
        self.ui.startwave.setAlignment(Qt.AlignCenter)
        self.ui.endwave.setAlignment(Qt.AlignCenter)
        self.ui.intervalwave.setAlignment(Qt.AlignCenter)
        self.ui.delaywave.setAlignment(Qt.AlignCenter)
        self.ui.response.setAlignment(Qt.AlignCenter)
        self.ui.response.setFrame(False)
        self.ui.presentwave.setFrame(False)
        #           Texto por defecto
        self.ui.startwave.setPlaceholderText("min 200 nm")
        self.ui.endwave.setPlaceholderText("max 1500 nm")
        #           solo admite numeros
        self.ui.setwave.setValidator(QtGui.QDoubleValidator())
        self.ui.startwave.setValidator(QtGui.QDoubleValidator())
        self.ui.endwave.setValidator(QtGui.QDoubleValidator())
        self.ui.intervalwave.setValidator(QtGui.QDoubleValidator())
        self.ui.delaywave.setValidator(QtGui.QDoubleValidator())
        #           conectar lineEdit con funsiones
        self.ui.send.clicked.connect(self.send_)
        self.ui.send.setAutoDefault(True)  # enviar comando con enter
        self.ui.command.returnPressed.connect(self.ui.send.click)
        self.ui.setwave.returnPressed.connect(self.set_wave)
        self.ui.conectar.clicked.connect(self.conectar_)
        self.ui.refresh.clicked.connect(self.refresh_)
        self.ui.shutter.activated.connect(self.shutter_)

    def conectar_(self):
        puerto = self.ui.port.currentText()
        try:
            self.ser = serial.Serial(puerto, 9600, timeout=1)
            if (self.ser.isOpen() == True):
                self.ui.state.setText("Connected")
                self.presentwave_()

        except:
            self.ui.state.setText("Disconnected")

    def refresh_(self):
        self.ui.port.clear()
        for comport in serial.tools.list_ports.comports():
            self.ui.port.addItem(comport.device)

    def lectura(self):
        res = bytearray()  # se crea un lista para almacenar bytes "res" de tamaño 0
        while True:
            a = self.ser.read(1)  # cada caracter es leido y almacenado a "a"
            if a:
                res += a  # se acumulan en "res"
                if res[-1] == ord('\r'):  # ord convierte de char a entero en este caso "\r" = 13 si el ultimo byte
                    # de la lista es 13 imprime "res"
                    print(res)  # DEBUG
                    break
            else:
                break
        return res.decode('ascii').strip("\r\\n")

    def shutter_(self):
        try:
            estado_shutter = self.ui.shutter.currentText()
            if estado_shutter == "Closed":
                estado = "SHUTTER C" + chr(10)

            else:
                estado = "SHUTTER O" + chr(10)

            self.ser.write(estado.encode('ascii'))
            print(estado_shutter)
        except:
            self.show_popup()

    def presentwave_(self):
        coma = 'WAVE?' + chr(10)
        self.ser.write(coma.encode('ascii'))
        n_n = self.lectura()
        separador = n_n.split()
        self.ui.presentwave.setText(str(separador[-1]))

    def go_scan(self):
        try:
            start_wave = int(self.ui.startwave.text())
            end_wave = int(self.ui.endwave.text())
            delay = int(self.ui.delaywave.text())
            intervalo = int(self.ui.intervalwave.text())
            if 199 < start_wave < 1501 and 199 < end_wave < 1501:
                if start_wave < end_wave:
                    while start_wave <= end_wave:
                        comando = 'GOWAVE ' + str(start_wave) + chr(10)
                        self.ser.write(comando.encode('ascii'))
                        print("wave?:  " + str(start_wave))
                        start_wave = start_wave + intervalo
                    if start_wave > end_wave:
                        comando = 'GOWAVE ' + str(end_wave) + chr(10)
                        self.ser.write(comando.encode('ascii'))
                        print(end_wave)
                else:
                    while start_wave >= end_wave:
                        time.sleep(delay)
                        comando = 'GOWAVE ' + str(start_wave) + chr(10)
                        self.ser.write(comando.encode('ascii'))
                        print("wave?:  " + str(start_wave))
                        start_wave = start_wave - intervalo
                    if start_wave < end_wave:
                        comando = 'GOWAVE ' + str(end_wave) + chr(10)
                        self.ser.write(comando.encode('ascii'))
                        print(end_wave)
            else:
                msg = QMessageBox()
                msg.setWindowTitle("Warning")
                msg.setText("the range is 200nm to 1500nm")
                msg.setIcon(QMessageBox.Warning)
                msg.exec_()
        except:
            msg = QMessageBox()
            msg.setWindowTitle("Warning")
            msg.setText("   complete the date   ")
            msg.setIcon(QMessageBox.Warning)
            msg.exec_()

    def set_wave(self):
        try:
            rango = int(self.ui.setwave.text())
            if 199 < rango < 1501:
                comando = 'GOWAVE ' + self.ui.setwave.text() + chr(10)
                self.ser.write(comando.encode('ascii'))
                time.sleep(1)
                self.presentwave_()
            else:
                msg = QMessageBox()
                msg.setWindowTitle("Warning")
                msg.setText("the range is 200nm to 1500nm")
                msg.setIcon(QMessageBox.Warning)
                msg.exec_()

        except:
            self.show_popup()

    def send_(self):
        try:
            comando = self.ui.command.text() + chr(10)
            self.ser.write(comando.encode('ascii'))
            datox = self.lectura()
            separador = datox.split()


            self.ui.response.setText(str(separador[-1]))
            self.preguntar_si_hay_error()

        except AttributeError:
            self.show_popup()
            print("El error es: ", sys.exc_info()[0])

        except:
            pass

    def show_popup(self):
        msg = QMessageBox()
        msg.setWindowTitle("Warning")
        elerror = str(sys.exc_info()[0])
        systemerror = elerror.strip(" '' '<>' 'class'")
        msg.setText("Warning: " + systemerror)
        msg.setIcon(QMessageBox.Warning)
        msg.exec_()

    def show_error(self, condicion):
        msg = QMessageBox()
        msg.setWindowTitle("Warning")
        msg.setText(condicion)
        msg.setIcon(QMessageBox.Warning)
        msg.exec_()

    def preguntar_si_hay_error(self):
        error = 'ERROR?' + chr(10)
        self.ser.write(error.encode('ascii'))
        tipo_error = str(self.lectura())
        lista_error = tipo_error.split()
        numero_error = lista_error[-1]
        if numero_error == '1':
            variable_error = 'command not understood'

        elif numero_error == '2':
            variable_error = 'bad parameter used in command'

        elif numero_error == '3':
            variable_error = 'destination position for wavelenght motion not allowed'

        elif numero_error == '6':
            variable_error = 'Accesory not present (usually filter wheel)'

        elif numero_error == '7':
            variable_error = 'Accesory already in specified position'

        elif numero_error == '8':
            variable_error = 'Could not home wavelenght drive'

        elif numero_error == '9':
            variable_error = 'Label too long'

        elif numero_error == '0':
            variable_error = 'System error(miscellaneous)'

        self.show_error(variable_error)

app = QtWidgets.QApplication([])
application = mywindow()
application.show()
sys.exit(app.exec())
