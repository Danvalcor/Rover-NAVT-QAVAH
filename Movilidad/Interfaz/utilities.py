import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
from PIL import Image, ImageTk  # Asegúrate de importar PIL para el manejo de imágenes

class Switch(tk.Frame):
    def __init__(self, parent, color = True, initial_state=False, state = tk.DISABLED, command=None, bg=None, **kwargs):
        """
        Crea un switch gráfico con estado on/off.

        Args:
            parent: El widget padre donde se colocará el switch.
            initial_state (bool): Estado inicial del switch (True para "on", False para "off").
            command (function): Función que se ejecutará al cambiar el estado.
            bg (str): Color de fondo del botón (puede ser 'white' u otro color).
        """
        super().__init__(parent, **kwargs)  # Inicializa como un Frame
        self.parent = parent
        self.command = command
        self.activeState = initial_state
        self.state = state
        self.bg = bg
        self.color = color

        # Redimensionar imágenes
        try:
            if color:
                self.on_image = Image.open("Recursos/switch-on.png").resize((40, 40))
                self.off_image = Image.open("Recursos/switch-off.png").resize((40, 40))
            else:
                self.on_image = Image.open("Recursos/switch-on-black.png").resize((40, 40))
                self.off_image = self.on_image.rotate(180, expand=True)

        except FileNotFoundError:
            print("Error: Las imágenes no se encuentran en las rutas especificadas.")
            return

        # Convertir a formato compatible con Tkinter
        self.on_image = ImageTk.PhotoImage(self.on_image)
        self.off_image = ImageTk.PhotoImage(self.off_image)
        
        # Crear botón
        self.button = tk.Button(self, 
                                image=self.on_image if self.activeState else self.off_image, 
                                bd=0, 
                                bg=self.bg, 
                                activebackground=bg,
                                state=tk.DISABLED,
                                command=self.toggle)
        self.button.pack()

    def toggle(self):
        """Alterna el estado del switch entre on y off."""
        self.activeState = not self.activeState  # Cambia el estado
        # Actualizar imagen según el estado
        self.button.config(image=self.on_image if self.activeState else self.off_image)
        
        # Ejecutar el comando asociado si existe
        if self.command:
            self.command(self.activeState)
    
    def set_state(self, state = None):
        """Método público para cambiar el estado del switch"""
        if state is not None:
            self.state = state
            self.button.config(state=self.state)
        else:
            self.button.config(state=self.state)

class VerticalSwitch(tk.Frame):
    def __init__(self, parent, color = True, initial_state=False, state = tk.DISABLED, command=None, bg=None, **kwargs):
        """
        Crea un switch gráfico con estado on/off.

        Args:
            parent: El widget padre donde se colocará el switch.
            initial_state (bool): Estado inicial del switch (True para "on", False para "off").
            command (function): Función que se ejecutará al cambiar el estado.
            bg (str): Color de fondo del botón (puede ser 'white' u otro color).
        """
        super().__init__(parent, **kwargs)  # Inicializa como un Frame
        self.parent = parent
        self.command = command
        self.state = state
        self.activeState = initial_state
        self.bg = bg
        self.color = color
        

        # Redimensionar imágenes
        try:
            if color:
                self.on_image = Image.open("Recursos/switch-on.png").resize((40, 40)).rotate(90, expand=True)
                self.off_image = Image.open("Recursos/switch-off.png").resize((40, 40)).rotate(90, expand=True)
            else:
                self.on_image = Image.open("Recursos/switch-on-black.png").resize((40, 40)).rotate(90, expand=True)  
                self.off_image = self.on_image.rotate(180, expand=True)

        except FileNotFoundError:
            print("Error: Las imágenes no se encuentran en las rutas especificadas.")
            return

        # Convertir a formato compatible con Tkinter
        self.on_image = ImageTk.PhotoImage(self.on_image)
        self.off_image = ImageTk.PhotoImage(self.off_image)
        
        # Crear botón
        self.button = tk.Button(self, 
                                image=self.on_image if self.activeState else self.off_image, 
                                bd=0, 
                                bg=self.bg, 
                                activebackground=bg,
                                state=state,
                                command=self.toggle)
        self.button.pack()

    def toggle(self):
        """Alterna el estado del switch entre on y off."""
        self.activeState = not self.activeState  # Cambia el estado
        # Actualizar imagen según el estado
        self.button.config(image=self.on_image if self.activeState else self.off_image)
        
        # Ejecutar el comando asociado si existe
        if self.command:
            self.command(self.activeState)
            
    def set_state(self, state = None):
        """Método público para cambiar el estado del switch"""
        if state is not None:
            self.state = state
            self.button.config(state=self.state)
        else:
            self.button.config(state=self.state)

