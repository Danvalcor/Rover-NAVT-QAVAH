import serial
import serial.tools.list_ports
import time
import struct
import threading
import json

class MotorControllerSystem:
    def __init__(self):
        self.controllers = []  # Lista para almacenar controladores de Tiva
        self.running = True

    def addController(self, COM, baudRate=1000000):
        """Agrega un nuevo controlador de Tiva al sistema."""
        # Verificar si el puerto COM existe
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        
        if COM not in available_ports:
            print(f"Error: El puerto {COM} no está disponible. No se puede agregar el controlador.")
            return  # No agregar el controlador si el puerto no existe
        else:
            controller = Controller(COM, baudRate)
            self.controllers.append(controller)
            controller.startThread()
    
    def jsonConfig(self, path):
        with open(path, 'r') as f:
            config = json.load(f)
            # Iterar por cada COM y sus motores
            for com, motors in config.items():
                # Crear un controlador para cada COM
                self.addController(com)
                for idx, param in motors.items():
                    m=self.getMotor(int(idx))
                    if m is None:  # Validar si el motor existe
                        print(f"Error: Motor con índice {idx} no encontrado en COM {com}.")
                        continue
                    m.setParams(setPoint = param.get("SetPoint"))
                    m.setParams(kp = param.get("kp"))
                    m.setParams(ki = param.get("ki"))
                    m.setParams(kd = param.get("kd"))
    

    def stopAll(self):
        """Detiene todos los hilos en el sistema."""
        self.running = False
        for controller in self.controllers:
            controller.stopThread()

    def showAllMotors(self):
        """Muestra los valores de todos los motores."""
        for i, controller in enumerate(self.controllers):
            print(f"--- Tiva {i + 1} ---")
            controller.showMotors()
    
    def getAllParams(self):
        """
            Regresa un diccionario con los parámetros de todos los motores.
            Los índices de los motores están basados en su posición:
            - Motor 1 y 2 del controlador 1 → índices 1, 2
            - Motor 1 y 2 del controlador 2 → índices 3, 4
            - Motor 1 y 2 del controlador 3 → índices 5, 6
        """
        allParams = {}

        for mIdx in range(1,len(self.controllers)*2+1):
            motor = self.getMotor(mIdx)
            allParams[mIdx] = motor.getParams()

        return allParams

    def getAllValues(self):
        """
        Regresa un diccionario con los parámetros de todos los motores.
        Los índices de los motores están basados en su posición:
        - Motor 1 y 2 del controlador 1 → índices 1, 2
        - Motor 1 y 2 del controlador 2 → índices 3, 4
        - Motor 1 y 2 del controlador 3 → índices 5, 6
        """
        allValues = {}

        for mIdx in range(1,len(self.controllers)*2+1):
            motor = self.getMotor(mIdx)
            allValues[mIdx] = motor.getValues()

        return allValues
            
    def getMotor(self, idx=None):
        if len(self.controllers)>0:
            if idx<=len(self.controllers)*2:
                tivaNum = (idx - 1) // 2  # Determina la Tiva (1, 2, 3)
                motorNum = (idx - 1) % 2  # Determina el motor (1 o 2)
                return self.controllers[tivaNum].motors[motorNum]
        else:
            return None
        
    def getMotorController(self, idx=None):
        if len(self.controllers)>0:
            if idx<=len(self.controllers)*2:
                tivaNum = (idx - 1) // 2  # Determina la Tiva (1, 2, 3)
                return self.controllers[tivaNum]
        else:
            return None

    def updateMotor(self, idx=None, setPoint=None, kp=None, ki=None, kd=None):
        """Agrega un nuevo controlador de Tiva al sistema."""
        motor = self.getMotor(idx=idx)
        if motor is not None:
            motor.updateParams(setPoint=setPoint, kp=kp, ki=ki, kd=kd)
            print(f"Updated motor: {idx}")
        else:
            print(f"Can't find motor {idx}")
        
            
class Controller:
    def __init__(self, COM, baudRate=1000000):
        self.COM = COM
        self.baudRate = baudRate
        self.m1 = Motors()
        self.m2 = Motors()
        self.motors = [self.m1, self.m2]
        self.running = True
        self.thread = None

    def startThread(self):
        self.running = True
        self.thread = threading.Thread(target=self.requestLoop)
        self.thread.daemon = True
        self.thread.start()

    def stopThread(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def requestLoop(self):
        try:
            with serial.Serial(port=self.COM, baudrate=self.baudRate, timeout=1) as tiva:
                while self.running:
                    if self.m1.update or self.m2.update:
                        self.sendParams(tiva)
                    self.recieveParams(tiva)
        except serial.SerialException as e:
            print(f"Error en la conexión serial ({self.COM}): {e}")
            time.sleep(2)

    def recieveParams(self, tiva):
        tiva.write('$'.encode('utf-8'))
        data = tiva.read(48)
        if len(data) == 48:
            self.m1.updateValues(data[0:24])
            self.m2.updateValues(data[24:48])

    def sendParams(self, tiva):
        if self.m1.update:
            params = self.m1.getParams()
            self.m1.update = False
            idx = 1
        else:
            params = self.m2.getParams()
            self.m2.update = False
            idx = 2

        out = '&'.encode('utf-8')
        out += struct.pack('I', idx)
        out += struct.pack('f', params[0])
        out += struct.pack('f', params[1])
        out += struct.pack('f', params[2])
        out += struct.pack('d', params[3])
        tiva.write(out)

    def showMotors(self):
        print("----- Motor 1 -----")
        self.m1.showValues()
        print("----- Motor 2 -----")
        self.m2.showValues()

class Motors:
    def __init__(self, setPoint=0, kp=0, ki=0, kd=0):
        self.rpm = 0
        self.error = 0
        self.pid = 0
        self.proportional = 0
        self.derivative = 0
        self.integral = 0
        self.setPoint = setPoint
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.update = False

    def updateValues(self, data):
        self.rpm = getNumber(data[0:4], 'f')
        self.error = getNumber(data[4:8], 'f')
        self.pid = getNumber(data[8:12], 'f')
        self.proportional = getNumber(data[12:16], 'f')
        self.integral = getNumber(data[16:20], 'f')
        self.derivative = getNumber(data[20:24], 'f')

    def updateParams(self, setPoint=None, kp=None, ki=None, kd=None):
        self.update = True
        if setPoint is not None:
            self.setPoint = setPoint
        if kp is not None:
            self.kp = kp
        if ki is not None:
            self.ki = ki
        if kd is not None:
            self.kd = kd
    
    def setParams(self, setPoint=None, kp=None, ki=None, kd=None):
        if setPoint is not None:
            self.setPoint = setPoint
        if kp is not None:
            self.kp = kp
        if ki is not None:
            self.ki = ki
        if kd is not None:
            self.kd = kd

    def getParams(self):
        return [self.setPoint, self.kp, self.ki, self.kd]
    
    def getValues(self):
        return [self.rpm, self.error, self.pid, self.proportional, self.integral, self.derivative]

    def showValues(self):
        print(f"RPM: {self.rpm}")
        print(f"Error: {self.error}")
        print(f"PID: {self.pid}")
        print(f"Proportional: {self.proportional}")
        print(f"Derivative: {self.derivative}")
        print(f"Integral: {self.integral}")

def getNumber(value, format):
    try:
        return struct.unpack_from(format, value)[0]
    except:
        return None


    
