import customtkinter as CTk
import tkinter as tk
from tkinter import ttk
import threading
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utilities import *
from controller import *


class MovilidadTab:
    """Class for managing the layout and functionality of the Mobility tab."""
    def __init__(self, parent):
        """Initialize the Mobility tab layout."""
        self.parent = parent            # Objeto al que pertenece
        self.running = False            # Estado del boton running
        self.cameraState = False        # Estado de la cámara
        self.plotState = False
        self.cap = None                 # Objeto de captura de OpenCV
        self.canvas = None
        self.viewOptions = ["General", "Motor 1", "Motor 2", "Motor 3", "Motor 4", "Motor 5", "Motor 6"]
        self.graphsFrame = None
        self.tolerance = 0.02
        self.speed = []
        self.sp = []
        self.plotData = {i: {
                            "velocidad": [],
                            "error": [],
                            "PID": [],
                            "proporcional": [],
                            "integral": [],
                            "derivativo": []
                        } for i in range(1, 7)}
        self.defaultValues = [0,0,0,0,0,0]
        self.maxPoints = 1000
        self.timeData = []
        self.currTime = 0
        self.prevTime = time.time()
        # Crear el objeto del controlador y cargar la configuración desde el archivo JSON
        self.movilidad = MotorControllerSystem()
        self.movilidad.jsonConfig("Custom Tkinter\\config.json")

        # Divide into left and right sections
        leftFrame = CTk.CTkFrame(parent)
        leftFrame.pack(side=CTk.LEFT, fill=CTk.BOTH, expand=False, padx=10, pady=5)

        rightFrame = CTk.CTkFrame(parent)
        rightFrame.pack(side=CTk.RIGHT, fill=CTk.BOTH, expand=True, padx=10, pady=5)

        # Create left and right layouts.
        self.createLeftPanel(leftFrame)
        self.createRightPanel(rightFrame)
        
        #time.sleep(5)
        self.updateData()
        

    def createLeftPanel(self, frame):
        """Create controls and indicators in the left panel with better layout."""
        # Configuración principal de `frame` con `grid`
        frame.columnconfigure(0, weight=0)  # Controles (columna izquierda)
        frame.columnconfigure(1, weight=0)  # Indicadores (columna derecha)
        frame.rowconfigure(1, weight=0)     # Cámara (fila inferior)
        
        # Frame de controles (simulando un LabelFrame de Tkinter)
        controlsFrame = CTk.CTkFrame(frame)
        controlsFrame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        # Configurar que las filas y columnas se expandan con la ventana
        controlsFrame.grid_columnconfigure(0, weight=0, uniform="equal")
        controlsFrame.grid_columnconfigure(1, weight=0, uniform="equal")
        controlsFrame.grid_rowconfigure(0, weight=0)
        controlsFrame.grid_rowconfigure(1, weight=0)
        controlsFrame.grid_rowconfigure(2, weight=0)

        # Contenedor para el botón de conexión e indicador
        connectFrame = CTk.CTkFrame(controlsFrame,  bg_color=controlsFrame.cget('fg_color'), fg_color=controlsFrame.cget('fg_color'))
        connectFrame.grid(row=0, column=0, sticky="w", pady=5)

        # Botón de conexión
        self.conectionButton = CTk.CTkButton(connectFrame, text="Conectar", width=12)
        self.conectionButton.grid(row=0, column=0, padx=10,pady=5)

        # Indicador de conexión (canvas rojo por defecto)
        self.connectionCanvas = CTk.CTkCanvas(connectFrame, width=25, height=25, highlightthickness=0, bg=connectFrame["bg"])
        self.connectionCanvas.grid(row=0, column=1, padx=10, pady=5)
        self.connection_indicator = self.connectionCanvas.create_oval(5, 5, 24, 24, fill="red", outline="")

        # Botón Start
        self.startButton = CTk.CTkButton(controlsFrame, text="Start", width=5, command=self.startToggle)
        self.startButton.grid(row=1, column=0, pady=5, padx=10, sticky="ew")

        # Botón Save
        self.saveButton = CTk.CTkButton(controlsFrame, text="Save", width=5)
        self.saveButton.grid(row=1, column=1, pady=5, padx=10, sticky="ew")

        # Botón de Ajustes
        self.settingsButton = CTk.CTkButton(controlsFrame, text="Ajustes", width=10, command=self.openSettings)
        self.settingsButton.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

        # Crear el frame que simula el LabelFrame para "Indicadores"
        indicatorsFrame = CTk.CTkFrame(frame)
        indicatorsFrame.grid(row=0, column=1, sticky="ne", padx=10, pady=5)

        # Título del frame de Indicadores
        title_label = CTk.CTkLabel(indicatorsFrame, text="Variables", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Indicadores en una fila y dos columnas
        CTk.CTkLabel(indicatorsFrame, text="RPM:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.rpmVar = CTk.DoubleVar(value=0.0)
        self.rpmEntry = CTk.CTkEntry(
            indicatorsFrame, 
            width=50, 
            textvariable=self.rpmVar,
        )

        self.rpmEntry.grid(row=1, column=1, padx=10, pady=5)

        CTk.CTkLabel(indicatorsFrame, text="Ángulo:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.angleEntry = CTk.CTkEntry(indicatorsFrame, width=50, state="readonly")  # Aumentar el tamaño del Entry
        self.angleEntry.grid(row=2, column=1, padx=10, pady=5)

        # Botón para "Send"
        CTk.CTkButton(indicatorsFrame, width=25, text="Send", command=self.rpmUpdate).grid(row=3, column=0, columnspan=2, pady=5)

        # Crear el frame para "Cámara"
        cameraFrame = CTk.CTkFrame(frame)
        cameraFrame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        
        # Configurar las filas y columnas de cameraFrame para que se expandan
        cameraFrame.grid_rowconfigure(1, weight=1)  # Hacer que la fila 1 se expanda
        cameraFrame.grid_columnconfigure(0, weight=1)  # Hacer que la columna 0 se expanda
        cameraFrame.grid_columnconfigure(1, weight=1)  # Hacer que la columna 1 se expanda


        # Agregar un título en la parte superior del frame (simula un LabelFrame)
        title_label = CTk.CTkLabel(cameraFrame, text="Cámara", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, padx=10, pady=10, sticky="sew")
        self.cameraToggle = Switch(cameraFrame, command=self.toggleCamera, bg=title_label["bg"])
        self.cameraToggle.grid(row=0, column=1, padx=10, pady=10, rowspan=1)
        
        # Canvas para la cámara (aún usando CTk)
        self.cameraCanvas = CTk.CTkCanvas(cameraFrame, background="black", highlightbackground = "black",  borderwidth = 0)
        self.cameraCanvas.grid(row=1, column=0, columnspan=2, padx=20, pady=20, sticky="nsew")  # Centrado y expandido
        
        # Indicadores adicionales (debajo de la cámara)        
        indicatorsFrame2 = CTk.CTkFrame(frame)
        indicatorsFrame2.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        # Configurar peso para las filas y columnas (centrado)
        for i in range(3):  # Número de filas en el frame
            indicatorsFrame2.grid_rowconfigure(i, weight=1)
        for j in range(6):  # Número de columnas en el frame
            indicatorsFrame2.grid_columnconfigure(j, weight=1)

        # Agregar un título en la parte superior del frame (simula un LabelFrame)
        title_label = CTk.CTkLabel(indicatorsFrame2, text="Indicadores", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=6, padx=5, pady=5, sticky="n")

        # Indicadores en dos filas y tres columnas
        CTk.CTkLabel(indicatorsFrame2, text="X:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.xEntry = CTk.CTkEntry(indicatorsFrame2, width=50, state="readonly") 
        self.xEntry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")  # Centrado horizontal

        CTk.CTkLabel(indicatorsFrame2, text="Theta:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.yEntry = CTk.CTkEntry(indicatorsFrame2, width=50, state="readonly")
        self.yEntry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        CTk.CTkLabel(indicatorsFrame2, text="Theta:").grid(row=1, column=4, padx=5, pady=5, sticky="e")
        self.velEntry = CTk.CTkEntry(indicatorsFrame2, width=50, state="readonly")  # Aumentar el tamaño del Entry
        self.velEntry.grid(row=1, column=5, padx=5, pady=5, sticky="ew")

        CTk.CTkLabel(indicatorsFrame2, text="Y:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.thetaEntry = CTk.CTkEntry(indicatorsFrame2, width=50, state="readonly")  # Aumentar el tamaño del Entry
        self.thetaEntry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        CTk.CTkLabel(indicatorsFrame2, text="Speed:").grid(row=2, column=2, padx=5, pady=5, sticky="e")
        self.tempEntry = CTk.CTkEntry(indicatorsFrame2, width=50, state="readonly")  # Aumentar el tamaño del Entry
        self.tempEntry.grid(row=2, column=3, padx=5, pady=5, sticky="ew")

        CTk.CTkLabel(indicatorsFrame2, text="Pila:").grid(row=2, column=4, padx=5, pady=5, sticky="e")
        self.batteryEntry = CTk.CTkEntry(indicatorsFrame2, width=50, state="readonly")  # Aumentar el tamaño del Entry
        self.batteryEntry.grid(row=2, column=5, padx=5, pady=5, sticky="ew")


    def createRightPanel(self, frame):
        """Create the graph section in the right panel."""
        # Top section: Toggle Switch and Dropdown
        topFrame = CTk.CTkFrame(frame)
        topFrame.pack(fill="x", pady=5)

        self.toggleLabel = CTk.CTkLabel(topFrame, text="Odometría", width=100)
        self.toggleLabel.pack(side=CTk.LEFT, padx=5)
        
        self.toggleButton = Switch(topFrame, color=False, command=self.toggleGraph,bg=self.toggleLabel["bg"])
        self.toggleButton.pack(side=CTk.LEFT, padx=5)

        # Crear un dropdown con una opción predeterminada
        self.viewDropdown = CTk.CTkOptionMenu(master=topFrame,
                                           values=self.viewOptions,
                                           command=self.checkboxToggle)
        # Add checkbox
        self.plot1 = CTk.BooleanVar(value=True)  # Initialize the variable for the checkbox
        self.checkbox1 = CTk.CTkCheckBox(
            topFrame,
            text="SP vs PV",  # Text for the checkbox
            variable=self.plot1,
            onvalue=True,
            offvalue=False,
            command=self.checkboxToggle   # Callback when toggled
        )
        
        # Add checkbox
        self.plot2 = CTk.BooleanVar(value=True)  # Initialize the variable for the checkbox
        self.checkbox2 = CTk.CTkCheckBox(
            topFrame,
            text="Error vs Man",  # Text for the checkbox
            variable=self.plot2,
            onvalue=True,
            offvalue=False,
            command=self.checkboxToggle   # Callback when toggled
        )
        
        # Add checkbox
        self.plot3 = CTk.BooleanVar(value=False)  # Initialize the variable for the checkbox
        self.checkbox3 = CTk.CTkCheckBox(
            topFrame,
            text="PID Actions",  # Text for the checkbox
            variable=self.plot3,
            onvalue=True,
            offvalue=False,
            command=self.checkboxToggle   # Callback when toggled
        )
                                           
        self.viewDropdown.pack_forget()
        self.checkbox1.pack_forget()
        self.checkbox2.pack_forget()
        self.checkbox3.pack_forget()
        
        # Graph section
        self.graphsFrame = CTk.CTkFrame(frame)
        self.graphsFrame.pack(fill="both", expand=True)

        # Plot initial odometry graph
        self.createPlots()
    
    def rpmUpdate(self):
        # Esta función se ejecutará cada vez que cambie el valor de rpmVar
        try:
            rpm = self.rpmVar.get()
            for control in self.movilidad.controllers:
                for m in control.motors:
                    m.updateParams(setPoint=rpm)
        except:
            print("Error al obtener la velocidad.")
    
    
    def createPlots(self):
        """
            Creates and embeds the appropriate plots into the Tkinter interface for the control application.
            
            This function checks the plot mode and displays the corresponding plots:
                - Odometry: Displays one plot for the estimated position of the rover.
                - Speed control: Displays two subplots for the setpoint vs the actual speed and the manipulation vs the error.

            The function also ensures that previous plots are cleared by destroying any existing canvas before creating new plots.

            Args:
                None

            Returns:
                None
        """
        # Destroy the previous canvas to clear the window for new plots
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            
        # Create the plots based on the control mode
        if self.toggleButton.activeState:
            self.controlPlot() 
        else:
            self.odometryPlot()

        # Embed the plots into the Tkinter window

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graphsFrame)
        self.canvas.get_tk_widget().pack(fill=CTk.BOTH, expand=True) 
    
    def controlPlot(self):
        """
            Creates the plots for closed-loop control in the control application.

            Displays subplots that monitor key aspects of closed-loop performance, depending on which checkboxes are selected:
                1. Speed vs Setpoint: Shows the target speed and actual speed.
                2. Manipulation vs Error: Plots the control signal (manipulation) and the error using a secondary axis.
                3. PID constants (Kp, Ki, Kd) over time.
        """
        if self.viewDropdown.get() == "General":
            self.fig, self.ax1 = plt.subplots(1, 1)
            self.ax = [self.ax1]
            # Crear las líneas de Speed vs Setpoint
            self.lineSpeed, = self.ax[0].plot([], [], label="Speed")  # Speed line
            self.lineSetPoint, = self.ax[0].plot([], [], label="Setpoint", linestyle='--')  # Setpoint line
            self.lineUpper, = self.ax[0].plot([], [], label="Upper Bound", linestyle=':', color="g")  # Upper Bound
            self.lineLower, = self.ax[0].plot([], [], label="Lower Bound", linestyle=':', color="g")  # Lower Bound
            self.ax[0].set_title("Speed vs Setpoint")
            self.ax[0].set_xlabel(r"Time $[s]$")
            self.ax[0].set_ylabel(r"Speed $[RPM]$")
            self.ax[0].legend(loc='upper left', bbox_to_anchor=(1, 1), fancybox=True, shadow=True)
            
        else:
            # Contar cuántas son True
            toggles = [self.plot1, self.plot2, self.plot3]
            count = sum(int(sv.get()) for sv in toggles)
            
            # Crear la cantidad adecuada de subgráficas
            if count == 1:
                self.fig, (self.ax1) = plt.subplots(1, 1)
                self.ax = [self.ax1]
            elif count == 2:
                self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1)
                self.ax = [self.ax1, self.ax2]
            else:
                self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1)
                self.ax = [self.ax1, self.ax2, self.ax3]
                    
            # Ajustar el diseño para mejor legibilidad
            self.fig.subplots_adjust(hspace=1, right=0.75)

            # Inicializar el índice para recorrer los ejes
            idx = 0

            # Graficar según el estado de los checkboxes
            if self.plot1.get() == 1:  # Si el primer checkbox está activado (Speed vs Setpoint)
                # Crear las líneas de Speed vs Setpoint
                self.lineSpeed, = self.ax[idx].plot([], [], label="Speed")  # Speed line
                self.lineSetPoint, = self.ax[idx].plot([], [], label="Setpoint", linestyle='--')  # Setpoint line
                self.lineUpper, = self.ax[idx].plot([], [], label="Upper Bound", linestyle=':', color="g")  # Upper Bound
                self.lineLower, = self.ax[idx].plot([], [], label="Lower Bound", linestyle=':', color="g")  # Lower Bound
                self.ax[idx].set_title("Speed vs Setpoint")
                self.ax[idx].set_xlabel(r"Time $[s]$")
                self.ax[idx].set_ylabel(r"Speed $[RPM]$")
                self.ax[idx].legend(loc='upper left', bbox_to_anchor=(1, 1), fancybox=True, shadow=True)
                idx += 1  # Avanzar al siguiente eje

            if self.plot2.get() == 1:  # Si el segundo checkbox está activado (Manipulation vs Error)
                # Crear las líneas de Manipulation vs Error
                self.axS = self.ax[idx].twinx()  # Secondary y-axis for Error
                self.lineManipulation, = self.ax[idx].plot([], [], label="Manipulation")  # Manipulation line
                self.lineError, = self.axS.plot([], [], label="Error", linestyle='--', color='r')  # Error line in red
                self.ax[idx].set_title("Manipulation vs Error")
                self.ax[idx].set_xlabel(r"Time $[s]$")
                self.ax[idx].set_ylabel(r"Manipulation $[bits]$")
                self.axS.set_ylabel("Error [%]")
                self.ax[idx].legend([self.lineManipulation, self.lineError],
                                    [self.lineManipulation.get_label(), self.lineError.get_label()],
                                    loc='lower left', bbox_to_anchor=(1, 1), fancybox=True, shadow=True)
                idx += 1  # Avanzar al siguiente eje

            if self.plot3.get() == 1:  # Si el tercer checkbox está activado (PID constants)
                # Crear las líneas de PID Actions
                self.lineKp, = self.ax[idx].plot([], [], label="Proportional", linestyle=':')  # Kp line
                self.lineKi, = self.ax[idx].plot([], [], label="Integral", linestyle=':')  # Ki line
                self.lineKd, = self.ax[idx].plot([], [], label="Derivative", linestyle=':')  # Kd line
                self.ax[idx].set_title("PID Actions")
                self.ax[idx].set_xlabel(r"Time $[s]$")
                self.ax[idx].set_ylabel("Value")
                self.ax[idx].legend(loc='upper left', bbox_to_anchor=(1, 1), fancybox=True, shadow=True)
                idx += 1  # Avanzar al siguiente eje

        
    def odometryPlot(self):
        """
            Creates the plots for open-loop control in the control application.

            Displays two subplots that monitor key aspects of open-loop performance:
                1. Speed vs Time: Shows the speed of the motor over time.
                2. Manipulation vs Time: Plots the control signal (manipulation) over time.

            Configures the layout, labels, and legends for the subplots, ensuring clear data visualization.

            Args:
                None

            Returns:
                None
        """
        """Plot odometry graph."""
        
        
        # Create the two subplots for open-loop control
        self.fig, self.ax4 = plt.subplots(1, 1)

        # Adjust the layout of the plots for better readability
        self.fig.subplots_adjust(hspace=1, right=0.75)

        # Plot 1: Speed vs Time
        self.odometryLine, = self.ax4.plot([], [], label="Position", linestyle=':')
        self.ax4.axhline(0, color="black", linewidth=1)  # Central horizontal axis
        self.ax4.axvline(0, color="black", linewidth=1)  # Central vertical axis
        self.ax4.set_xlim(-5,5)
        self.ax4.set_ylim(-5,5)
        self.ax4.set_title("Odometry")
        self.ax4.set_xlabel(r"X $[m]$")
        self.ax4.set_ylabel(r"Y $[m]$")
        self.ax4.grid("minor", linestyle = ':', linewidth = 0.5)    
        #self.ax1.legend(loc='upper left', bbox_to_anchor=(1, 1), fancybox=True, shadow=True)
        self.ax4.legend(loc='lower left', bbox_to_anchor=(1, 1), fancybox=True, shadow=True)        

        
    def toggleGraph(self, state):
        """Toggle between odometry and control graph modes based on the state of the switch."""
        self.plotState = not self.plotState
        if self.plotState:  # Si el estado es "ON"
            self.toggleLabel.configure(text="Control")    # Cambiar el texto a "Control"
            self.viewDropdown.pack(side="left", padx=10)
            self.checkboxToggle()
        else:  # Si el estado es "OFF"
            self.toggleLabel.configure(text="Odometría")  # Cambiar el texto a "Odometría"
            self.viewDropdown.pack_forget()
            self.checkbox1.pack_forget()
            self.checkbox2.pack_forget()
            self.checkbox3.pack_forget()
            self.createPlots()  # Llamar a la función de odometría
    
    def toggleCamera(self, state):
        if self.running:
            if state:
                self.startThreads()
            else:
                self.stopCamera()
            
    def openSettings(self):
        """Open the settings window."""
        self.settingsWindow = CTk.CTkToplevel(self.parent)
        self.settingsWindow.title("Ajustes")
        self.createWindow()
    
    def createWindow(self):
        # Configurar la ventana para usar un grid layout
        self.settingsWindow.columnconfigure(0, weight=1)
        self.settingsWindow.columnconfigure(1, weight=1)

        # Dropdown
        self.settingsVar = CTk.StringVar(value=" ")  # Valor inicial
        dropdown_label = CTk.CTkLabel(self.settingsWindow, text="Seleccionar opción:")
        dropdown_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="e")  # Alinear a la derecha
        dropdown_menu = CTk.CTkOptionMenu(
            self.settingsWindow,
            values=self.viewOptions[1:-1],
            variable=self.settingsVar,
            command=self.updateTextBox
        )
        dropdown_menu.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="w")  # Alinear a la izquierda

        # Entradas para kp, ki, kd
        self.kp_var = CTk.DoubleVar()
        self.ki_var = CTk.DoubleVar()
        self.kd_var = CTk.DoubleVar()

        # Primera columna: etiquetas y entradas
        CTk.CTkLabel(self.settingsWindow, text="kp:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.kp_entry = CTk.CTkEntry(self.settingsWindow, textvariable=self.kp_var)
        self.kp_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        CTk.CTkLabel(self.settingsWindow, text="ki:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.ki_entry = CTk.CTkEntry(self.settingsWindow, textvariable=self.ki_var)
        self.ki_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        CTk.CTkLabel(self.settingsWindow, text="kd:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.kd_entry = CTk.CTkEntry(self.settingsWindow, textvariable=self.kd_var)
        self.kd_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        # Segunda columna: entradas para tolerancia y COM
        self.tolerance_var = CTk.DoubleVar()
        CTk.CTkLabel(self.settingsWindow, text="Tolerancia:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.tolerance_entry = CTk.CTkEntry(self.settingsWindow, textvariable=self.tolerance_var)
        self.tolerance_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        self.com_var = CTk.StringVar()
        CTk.CTkLabel(self.settingsWindow, text="COM:").grid(row=5, column=0, padx=10, pady=5, sticky="e")
        self.com_entry = CTk.CTkEntry(self.settingsWindow, textvariable=self.com_var)
        self.com_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Botón para enviar datos
        self.send_button = CTk.CTkButton(
            self.settingsWindow,
            text="Enviar datos",
            command=self.sendsettings
        )
        self.send_button.grid(row=6, column=1, padx=10, pady=20, sticky="w")  # Alinear en la segunda columna

        # Deshabilitar entradas inicialmente
        self.kp_entry.configure(state=CTk.DISABLED)
        self.ki_entry.configure(state=CTk.DISABLED)
        self.kd_entry.configure(state=CTk.DISABLED)
        self.com_entry.configure(state=CTk.DISABLED)
        self.send_button.configure(state=CTk.DISABLED)


    def sendsettings(self, motorIdx = None):
        """Acción para el botón de enviar datos."""
        # Obtener el índice del motor
        self.tolerance = self.tolerance_var.get()
        motorIdx = int(self.settingsVar.get().split(' ')[1])  # Extrae el índice del texto
        motor = self.movilidad.getMotor(motorIdx)  # Obtener el motor correspondiente
        tiva =  self.movilidad.getMotorController(motorIdx)
        # Obtén el valor introducido en la entrada COM
        newCOM = self.com_var.get()

        # Verifica si es diferente al COM actual del controlador
        if tiva.COM != newCOM:
            # Verifica si el nuevo COM ya existe en alguno de los controladores actuales
            if any(controller.COM == newCOM for controller in self.movilidad.controllers):
                print("El nuevo COM ya está en uso por otro controlador.")
            else:
                self.movilidad.addController(newCOM)

        if motor is not None:
            kp = self.kp_var.get()
            ki = self.ki_var.get()
            kd = self.kd_var.get()
            self.movilidad.updateMotor(idx=motorIdx, setPoint=None, kp=kp, ki=ki, kd=kd)
        
        
    def updateTextBox(self, motorIdx):
        """Actualiza las entradas en función de la selección del dropdown."""
        self.tolerance_var.set(self.tolerance)
        if self.settingsVar.get() != '':
            self.com_entry.configure(state=CTk.NORMAL)
            self.send_button.configure(state=CTk.NORMAL)

        else:
            self.com_entry.configure(state=CTk.DISABLED)
            self.send_button.configure(state=CTk.DISABLED)
        try:
            # Obtener el índice del motor
            motorIdx = int(self.settingsVar.get().split(' ')[1])  # Extrae el índice del texto
            motor = self.movilidad.getMotor(motorIdx)  # Obtener el motor correspondiente
            tiva = self.movilidad.getMotorController(motorIdx)
            if motor is not None:
                # Obtener parámetros del motor
                params = motor.getParams()  # Asume que regresa una lista [motorIdx, kp, ki, kd]

                # Actualizar entradas
                self.kp_var.set(params[1])  # Actualizar kp
                self.ki_var.set(params[2])  # Actualizar ki
                self.kd_var.set(params[3])  # Actualizar kd
                self.com_var.set(tiva.COM)

                # Habilitar entradas y botón
                self.kp_entry.configure(state=CTk.NORMAL)
                self.ki_entry.configure(state=CTk.NORMAL)
                self.kd_entry.configure(state=CTk.NORMAL)
            else:
                # Si no hay motor, deshabilitar entradas y botón
                self.kp_entry.configure(state=CTk.DISABLED)
                self.ki_entry.configure(state=CTk.DISABLED)
                self.kd_entry.configure(state=CTk.DISABLED)
                self.com_var.set("")
                
        except Exception as e:
            print(f"Error en updateTextBox: {e}")
            # Manejar posibles errores
            self.kp_entry.configure(state=CTk.DISABLED)
            self.ki_entry.configure(state=CTk.DISABLED)
            self.kd_entry.configure(state=CTk.DISABLED)
            self.send_button.configure(state=CTk.DISABLED)
            self.com_entry.configure(state=CTk.DISABLED)

        
    def startThreads(self):
        """Inicia el hilo para actualizar los datos."""
        if self.running:
            self.thread = threading.Thread(target=self.updateData)
            self.thread.daemon = True  # Permite que el programa termine aunque el hilo siga activo
            self.thread.start()
            print("Hilo de actualización iniciado.")
            
    def stopThreads(self):
        """Detiene el hilo de actualización."""
        if not self.running:
            if self.thread:
                self.thread.join()  # Espera a que el hilo termine
                print("Hilo de actualización detenido.")

    def stopCamera(self):
        """Stop the camera feed."""
        if self.cap:
            self.cap.release()  # Libera la cámara
            self.cap = None
        self.cameraCanvas.delete("all")  # Limpia el CTkCanvas

    def updateData(self):
        self.start_time = time.time()  # Momento inicial de la ejecución

        while self.running:
            try:
                # Gets every current motor value
                data = self.movilidad.getAllValues()
                
                # Saves interface data
                try: 
                    self.sp.append(float(self.rpmVar.get()))
                except:
                    if self.sp:  # Verifica que el arreglo no esté vacío
                        self.sp.append(self.sp[-1])  # Usa el último valor si existe
                    else:
                        self.sp.append(0.0)  # Valor predeterminado si no hay elementos previos
                
                # Gets current time.
                #self.currTime = self.currTime+1
                #self.timeData.append(self.currTime)
                #self.prevTime = self.currTime
                
                current_time = time.time()  # Tiempo actual en segundos
                elapsed_time = current_time - self.start_time  # Tiempo transcurrido desde el inicio
                self.timeData.append(elapsed_time)
                
                tempSpeed = 0
                speedIdx = 0
                # Saves the data in an aray to plot it, and another to save every data.
                for idx in range(1, 7):  # Procesar todos los motores del 1 al 6
                    values = data.get(idx, self.defaultValues)  # Obtener valores del motor o usar los predeterminados
                    # Actualizar cada tipo de dato
                    self.plotData[idx]["velocidad"].append(values[0])
                    self.plotData[idx]["error"].append(values[1])
                    self.plotData[idx]["PID"].append(values[2])
                    self.plotData[idx]["proporcional"].append(values[3])
                    self.plotData[idx]["integral"].append(values[4])
                    self.plotData[idx]["derivativo"].append(values[5])
                    if values[0] > 0:
                        tempSpeed = tempSpeed+values[0]
                        speedIdx = speedIdx+1
                
                if speedIdx == 0:
                    self.speed.append(0)
                else:
                    self.speed.append(tempSpeed/speedIdx)
                    
                self.updateGraphs()
                time.sleep(0.1)
            except KeyboardInterrupt:
                self.movilidad.stopAll()
    
    def startToggle(self):
        """Toggle running button"""
        self.running = not self.running
        if self.running:  # Si el estado es "ON"
            self.startButton.configure(text="Stop")
            
            # Enables controls
            self.toggleButton.set_state(tk.NORMAL)
            self.cameraToggle.set_state(tk.NORMAL)
            self.startThreads()
            
        else:  # Si el estado es "OFF"
            self.startButton.configure(text="Start")
            # Disables the controls
            self.toggleButton.set_state(tk.DISABLED)
            self.cameraToggle.set_state(tk.DISABLED)
            self.stopThreads()
            
    def checkboxToggle(self, state=None):
        """Este es el nuevo callback para manejar la lógica de asegurar que al menos un checkbox esté activado."""
        if self.viewDropdown.get() == "General":
            self.checkbox1.pack_forget()
            self.checkbox2.pack_forget()
            self.checkbox3.pack_forget()
        else:
            self.checkbox1.pack(side="left", padx=10) 
            self.checkbox2.pack(side="left", padx=10) 
            self.checkbox3.pack(side="left", padx=10) 
            # Asegurarse de que los checkboxes mantengan su valor
            self.checkbox1.select() if self.plot1.get() == True else self.checkbox1.deselect()
            self.checkbox2.select() if self.plot2.get() == True else self.checkbox2.deselect()
            self.checkbox3.select() if self.plot3.get() == True else self.checkbox3.deselect()
        
        # Contar cuántos checkboxes están activados
        active_count = sum(int(var.get()) for var in [self.plot1, self.plot2, self.plot3])

        # Si todos los checkboxes están desmarcados, restaurar el estado del último marcado
        if active_count == 0:
            # Si plot1 está desmarcado, volver a activarlo
            if self.plot1.get() == False:
                self.plot1.set(True)
        # Si el checkbox ha sido marcado o desmarcado, actualizar los gráficos
        self.createPlots()
    
    def updateGraphs(self):
        """
            Updates the data in the plots with the latest values.
            Limits the data points to 100 for continuous scrolling.
            Handles both closed-loop (PID) and open-loop modes.
            
            Args:
                None

            Returns:
                None
        """
        
        if self.plotState:
            limMax = len(self.timeData) # The latest time data length
            limMin = limMax - 100 if limMax > 100 else 0  # Keep the lastest points index
            
            if self.viewDropdown.get() == "General":
                self.lineSpeed.set_data(self.timeData[limMin:], self.speed[limMin:])
                self.lineSetPoint.set_data(self.timeData[limMin:], self.sp[limMin:])
                self.canvas.draw_idle()  # Redibuja el gráfico en la interfaz Tkinter

            else:
                motorIdx = int(self.viewDropdown.get().split(' ')[1])
                if self.plot1.get():
                    self.lineSpeed.set_data(self.timeData[limMin:], self.plotData[motorIdx]["velocidad"][limMin:])
                    self.lineSetPoint.set_data(self.timeData[limMin:], self.sp[limMin:])
                    spData = np.array(self.sp)
                    self.lineUpper.set_data(self.timeData[limMin:], spData[limMin:]*(1+self.tolerance)) 
                    self.lineLower.set_data(self.timeData[limMin:], spData[limMin:]*(1-self.tolerance)) 
                    
                if self.plot2.get():
                    self.lineManipulation.set_data(self.timeData[limMin:], self.plotData[motorIdx]["PID"][limMin:])
                    self.lineError.set_data(self.timeData[limMin:], self.plotData[motorIdx]["error"][limMin:])
                    
                if self.plot3.get():
                    self.lineKp.set_data(self.timeData[limMin:], self.plotData[motorIdx]["proporcional"][limMin:])
                    self.lineKi.set_data(self.timeData[limMin:], self.plotData[motorIdx]["integral"][limMin:])
                    self.lineKd.set_data(self.timeData[limMin:], self.plotData[motorIdx]["derivativo"][limMin:])

            if limMax>1:
                for ax in self.ax:
                    ax.relim()
                    ax.set_xlim(self.timeData[limMin], self.timeData[-1])
                    ax.autoscale_view()
            #self.canvas.draw_idle()  # Redibuja el gráfico en la interfaz Tkinter
            self.canvas.draw()
            
            
                
            
    