import os
import customtkinter as CTk
from PIL import Image, ImageTk
from movilidadCTK import MovilidadTab



class roverNQApp:
    """GUI application for controlling the embedded systems of the Rover NAVT QAVAH."""
    def __init__(self, root, bg="dark slate gray"):
        """Initialize the roverNQApp instance."""
        self.root = root
        self.root.configure(bg=bg)
        self.root.title("Rover NAVT QAVAH")
        
        self.path = os.path.join("Recursos", "Logo Rover NAVT QAVAH.png")
        
        # Add an icon to the window
        self.icon = ImageTk.PhotoImage(file=self.path)
        self.root.wm_iconbitmap()
        self.root.iconphoto(False, self.icon)
        self.root.bind("<Escape>", lambda e: e.widget.quit())

        # Create Layout
        self.create_header()
        self.create_tabs()
        
    def create_header(self):
        """Creates a header with a title and an image."""
        header_frame = CTk.CTkFrame(self.root)
        header_frame.pack(fill="x", pady=5)

        # Add title
        title_label = CTk.CTkLabel(
            header_frame,
            text="Rover NAVT QAVAH",
            font=("Arial", 24, "bold"),
            text_color="white"
        )
        title_label.pack(pady=(10, 5))
        image = Image.open(self.path).resize((100, 100)) # Resize for consistency
        self.header_image = CTk.CTkImage(image, size=(80, 80))  # Adjust size here (width, height)
        image_label = CTk.CTkLabel(header_frame, image=self.header_image, text="")
        image_label.pack(padx=10)
        
    def create_tabs(self):
        """Creates the tab structure for the GUI."""
        # Notebook (tab view in customtkinter)
        self.notebook = CTk.CTkTabview(master=self.root, width=800, height=600)
        self.notebook.pack(fill="both", expand=True, side = CTk.LEFT)

        # Mobility tab
        self.notebook.add("Movilidad")
        mobility_tab = self.notebook.tab("Movilidad")  # Access the tab as a frame
        self.movilityObj = MovilidadTab(mobility_tab)  # Initialize mobility tab layout using MovilidadTab class

        # Arm tab
        self.notebook.add("Brazo")
        arm_tab = self.notebook.tab("Brazo")  # Access the tab as a frame
        arm_tab.configure(fg_color="gray")  # Example configuration

        # Vision tab
        self.notebook.add("Mástil")
        vision_tab = self.notebook.tab("Mástil")  # Access the tab as a frame
        vision_tab.configure(fg_color="gray")  # Example configuration

        # Bind the tab change event (optional)
        self.notebook.set("Movilidad")  # Default selected tab

    def on_tab_change(self, event=None):
        """Handle the tab change event."""
        selected_tab = self.notebook.get()  # Get current tab text
        if selected_tab == "Movilidad":
            self.movilityObj.startThreads()  # Inicia la cámara
        else:
            self.movilityObj.stopCamera()  # Detiene la cámara


if __name__ == "__main__":
    # Setup customtkinter appearance
    CTk.set_appearance_mode("Dark")  # Options: "System", "Light", "Dark"
    CTk.set_default_color_theme("dark-blue")  # Options: "blue", "green", "dark-blue"

    # Create the root window
    root = CTk.CTk()
    app = roverNQApp(root)


    # Start the main loop
    root.mainloop()
