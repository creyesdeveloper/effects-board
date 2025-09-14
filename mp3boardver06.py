import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog, Menu
import pygame
import json

# Ruta para guardar la configuración de botones
DEFAULT_CONFIG_FILE = "button_config.json"

class AudioButtonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Button Grid")

        # Configurar apariencia general
        ctk.set_appearance_mode("System")  # "Light", "Dark", "System"
        ctk.set_default_color_theme("blue")  # Opciones: "blue", "green", "dark-blue"

        # Inicializar pygame mixer
        pygame.mixer.init()

        # Diccionario para guardar las asociaciones de botones
        self.button_audio_map = {}
        self.button_labels = {}

        # Cargar configuración inicial si existe
        self.load_config(DEFAULT_CONFIG_FILE)

        # Crear matriz 5x5 de botones
        self.create_buttons()

        # Agregar botones para guardar/cargar configuración y resetear
        self.create_control_buttons()

    def create_buttons(self):
        self.buttons = []
        for row in range(5):
            button_row = []
            for col in range(5):
                button = ctk.CTkButton(
                    self.root,
                    text=f"{row+1},{col+1}",
                    width=150,  # Ancho del botón
                    height=100,  # Alto del botón
                    corner_radius=20,  # Bordes redondeados
                    fg_color="#20B2AA",  # Azul
                    hover_color="#3CB371",  # Azul oscuro al pasar el mouse
                    command=lambda r=row, c=col: self.handle_button_press(r, c)
                )
                button.grid(row=row, column=col, padx=10, pady=10)
                button.bind("<Button-3>", lambda event, r=row, c=col: self.show_context_menu(event, r, c))
                button_row.append(button)
            self.buttons.append(button_row)

    def create_control_buttons(self):
        control_frame = ctk.CTkFrame(self.root)
        control_frame.grid(row=5, column=0, columnspan=5, pady=10)

        save_button = ctk.CTkButton(control_frame, text="Guardar Configuración", command=self.save_config_dialog)
        save_button.pack(side="left", padx=5)

        load_button = ctk.CTkButton(control_frame, text="Cargar Configuración", command=self.load_config_dialog)
        load_button.pack(side="left", padx=5)

        reset_button = ctk.CTkButton(control_frame, text="Resetear Configuración", command=self.reset_config)
        reset_button.pack(side="left", padx=5)

    def handle_button_press(self, row, col):
        button_key = f"{row},{col}"

        # Si el botón ya tiene un archivo asociado, reproducir el audio
        if button_key in self.button_audio_map:
            audio_file = self.button_audio_map[button_key]
            if os.path.exists(audio_file):
                self.play_audio(audio_file)
            else:
                messagebox.showerror("Error", f"El archivo {audio_file} no existe.")
                del self.button_audio_map[button_key]  # Eliminar la asociación inválida
                self.save_config(DEFAULT_CONFIG_FILE)
        else:
            # Asociar un archivo .mp3 al botón
            audio_file = filedialog.askopenfilename(filetypes=[("Archivos MP3", "*.mp3")])
            if audio_file:
                self.button_audio_map[button_key] = audio_file
                self.save_config(DEFAULT_CONFIG_FILE)

    def show_context_menu(self, event, row, col):
        """Muestra un menú contextual al hacer clic derecho en un botón."""
        context_menu = Menu(self.root, tearoff=0)
        context_menu.add_command(label="Cambiar Nombre", command=lambda: self.rename_button(row, col))
        context_menu.add_command(label="Asignar Archivo de Sonido", command=lambda: self.assign_audio_file(row, col))
        context_menu.post(event.x_root, event.y_root)

    def rename_button(self, row, col):
        """Cambia el nombre del botón seleccionado."""
        button_key = f"{row},{col}"
        new_label = simpledialog.askstring("Cambiar nombre", "Ingrese el nuevo nombre del botón:")
        if new_label:
            self.buttons[row][col].configure(text=new_label)
            self.button_labels[button_key] = new_label
            self.save_config(DEFAULT_CONFIG_FILE)

    def assign_audio_file(self, row, col):
        """Asigna un archivo de sonido al botón seleccionado."""
        button_key = f"{row},{col}"
        audio_file = filedialog.askopenfilename(filetypes=[("Archivos MP3", "*.mp3")])
        if audio_file:
            self.button_audio_map[button_key] = audio_file
            self.save_config(DEFAULT_CONFIG_FILE)

    def play_audio(self, audio_file):
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo reproducir el archivo: {e}")

    def save_config(self, config_file):
        try:
            config_data = {
                "button_audio_map": self.button_audio_map,
                "button_labels": self.button_labels
            }
            with open(config_file, "w") as file:
                json.dump(config_data, file)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")

    def load_config(self, config_file):
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as file:
                    config_data = json.load(file)
                    self.button_audio_map = config_data.get("button_audio_map", {})
                    self.button_labels = config_data.get("button_labels", {})

                # Actualizar botones con nombres cargados
                for button_key, label in self.button_labels.items():
                    row, col = map(int, button_key.split(","))
                    self.buttons[row][col].configure(text=label)

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la configuración: {e}")

    def save_config_dialog(self):
        config_file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if config_file:
            self.save_config(config_file)

    def load_config_dialog(self):
        config_file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if config_file:
            self.load_config(config_file)

    def reset_config(self):
        """Resetear configuración a valores predeterminados."""
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea resetear toda la configuración?"):
            self.button_audio_map.clear()
            self.button_labels.clear()
            for row in range(5):
                for col in range(5):
                    self.buttons[row][col].configure(text=f"{row+1},{col+1}")
            self.save_config(DEFAULT_CONFIG_FILE)

# Crear la ventana principal
if __name__ == "__main__":
    root = ctk.CTk()
    app = AudioButtonApp(root)
    root.mainloop()
