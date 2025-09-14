import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pygame
import json

# Ruta para guardar la configuración de botones
CONFIG_FILE = "button_config.json"

class AudioButtonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Button Grid")

        # Inicializar pygame mixer
        pygame.mixer.init()

        # Diccionario para guardar las asociaciones de botones
        self.button_audio_map = {}

        # Cargar configuración si existe
        self.load_config()

        # Crear matriz 5x5 de botones
        self.create_buttons()

    def create_buttons(self):
        self.buttons = []
        for row in range(5):
            button_row = []
            for col in range(5):
                button = tk.Button(self.root, text=f"{row+1},{col+1}", width=10, height=3,
                                   command=lambda r=row, c=col: self.handle_button_press(r, c))
                button.grid(row=row, column=col, padx=5, pady=5)
                button_row.append(button)
            self.buttons.append(button_row)

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
                self.save_config()
        else:
            # Asociar un archivo .mp3 al botón
            audio_file = filedialog.askopenfilename(filetypes=[("Archivos MP3", "*.mp3")])
            if audio_file:
                self.button_audio_map[button_key] = audio_file
                self.buttons[row][col].config(bg="green")  # Cambiar color para indicar asociación
                self.save_config()

    def play_audio(self, audio_file):
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo reproducir el archivo: {e}")

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as config_file:
                json.dump(self.button_audio_map, config_file)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as config_file:
                    self.button_audio_map = json.load(config_file)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la configuración: {e}")

# Crear la ventana principal
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioButtonApp(root)
    root.mainloop()
