# mp3boardver07.py
# Effects Board - UI mejorada (Dark), volumen 0..100 (int) y preview al asignar
from __future__ import annotations

import os
import json
import time
import pygame
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog, Menu

# -------------------- Config básica --------------------
DEFAULT_CONFIG_FILE = "button_config.json"

# Estilos UI
APP_TITLE = "Effects Board"
ctk.set_appearance_mode("Dark")        # Dark consistente
ctk.set_default_color_theme("dark-blue")
ctk.set_widget_scaling(1.05)           # 5% más grande

BTN_WIDTH = 140
BTN_HEIGHT = 80
BTN_RADIUS = 12
BTN_FONT = ("Arial", 14, "bold")       # Cambia si prefieres "Inter" o "SF Pro"
BTN_FG_ASSIGNED = "#0EA5E9"            # Azul (asignado)
BTN_FG_EMPTY = "#334155"               # Slate-700 (vacío)
BTN_HOVER = "#1F2937"                  # Slate-800

PANEL_PADX = 10
PANEL_PADY = 10
GRID_SPACING = 8

# -------------------- Utilidades de config --------------------
def load_button_config(path: str) -> dict:
    if not os.path.exists(path):
        # Config por defecto 3x4
        data = {
            "grid": {"rows": 3, "cols": 4},
            "buttons": [],  # lista de dicts con {row, col, label, file}
            "__meta__": {"volume": 80}
        }
        save_button_config(data, path)
        return data
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_button_config(cfg: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def ensure_sounds_folder():
    base = "SOUND EFFECTS"
    os.makedirs(base, exist_ok=True)
    readme = os.path.join(base, "README.md")
    if not os.path.exists(readme):
        with open(readme, "w", encoding="utf-8") as f:
            f.write("# Carpeta de sonidos\n\nColoca aquí tus .wav/.mp3.\n")
    return os.path.abspath(base)

# -------------------- App --------------------
class AudioButtonApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("980x620")
        self.root.minsize(860, 520)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)  # centro expansible

        # Estado
        self.cfg_path = DEFAULT_CONFIG_FILE
        self.cfg = load_button_config(self.cfg_path)
        self.rows = int(self.cfg.get("grid", {}).get("rows", 3))
        self.cols = int(self.cfg.get("grid", {}).get("cols", 4))

        # Inicializar pygame mixer
        self._init_mixer()

        # ---------- Top bar ----------
        self.topbar = ctk.CTkFrame(self.root, corner_radius=0)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_columnconfigure(0, weight=1)

        self.title_lbl = ctk.CTkLabel(self.topbar, text=APP_TITLE, font=("Arial", 18, "bold"))
        self.title_lbl.grid(row=0, column=0, padx=(PANEL_PADX, 0), pady=(8, 8), sticky="w")

        # Volumen 0..100 (int) → sin alerta de tipos
        volume_initial = int(self.cfg.get("__meta__", {}).get("volume", 80))
        if volume_initial < 0 or volume_initial > 100:
            volume_initial = 80
        self.vol_var = ctk.IntVar(value=volume_initial)



        def _on_volume_change(v):
            try:
                vol = float(v) / 100.0
            except Exception:
                vol = self.vol_var.get() / 100.0
            try:
                pygame.mixer.music.set_volume(vol)
            except Exception:
                pass
            self.vol_value_lbl.configure(text=f"{int(vol*100)}%")

        ctk.CTkLabel(self.topbar, text="Vol").grid(row=0, column=1, padx=6, pady=8, sticky="e")
        self.vol_value_lbl = ctk.CTkLabel(self.topbar, text=f"{self.vol_var.get()}%")
        self.vol_value_lbl.grid(row=0, column=2, padx=(0, 6), pady=8, sticky="e")

        self.vol_slider = ctk.CTkSlider(
            self.topbar, from_=0, to=100, number_of_steps=100,
            command=_on_volume_change, width=200
        )
        self.vol_slider.set(self.vol_var.get())
        self.vol_slider.grid(row=0, column=3, padx=(0, PANEL_PADX), pady=8, sticky="e")

        # ---------- Centro (grilla) ----------
        self.center = ctk.CTkFrame(self.root)
        self.center.grid(row=1, column=0, sticky="nsew", padx=PANEL_PADX, pady=(0, PANEL_PADY))

        for c in range(self.cols):
            self.center.grid_columnconfigure(c, weight=1)
        for r in range(self.rows):
            self.center.grid_rowconfigure(r, weight=1)

        # Matrices
        self.buttons_widgets: list[list[ctk.CTkButton]] = []
        self.buttons_data: list[list[dict]] = []  # {label, file}

        self._build_grid_from_config()

        # ---------- Status bar ----------
        self.status = ctk.CTkLabel(self.root, text="Listo", anchor="w")
        self.status.grid(row=2, column=0, sticky="ew", padx=PANEL_PADX, pady=(0, 8))

        # Atajos simples (1..0 para la primera fila si aplica)
        self._bind_simple_hotkeys()

        # Menú principal (Guardar/Cargar)
        self._build_menubar()

    # ------------- UI helpers -------------
    def set_status(self, msg: str):
        self.status.configure(text=msg)

    def _init_mixer(self):
        try:
            pygame.mixer.init()
        except Exception as e:
            messagebox.showwarning("Audio", f"No se pudo inicializar audio:\n{e}")

    def _bind_simple_hotkeys(self):
        # Mapea 1..min(cols,9) a la fila 0
        digits = "1234567890"
        usable = min(self.cols, len(digits))
        for i in range(usable):
            self.root.bind(digits[i], lambda e, r=0, c=i: self._press_cell(r, c))

    def _build_menubar(self):
        menubar = Menu(self.root)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Guardar configuración", command=self._save_config)
        file_menu.add_command(label="Cargar configuración", command=self._load_config_from_disk)
        file_menu.add_separator()
        file_menu.add_command(label="Abrir carpeta de sonidos", command=lambda: os.system(f'open "{ensure_sounds_folder()}"' if os.name == "posix" else f'start "" "{ensure_sounds_folder()}"'))
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.destroy)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        self.root.config(menu=menubar)

    def show_context_menu(self, event, r: int, c: int):
        """Muestra el menú contextual y difiere la apertura del file dialog (macOS-safe)."""
        menu = Menu(self.root, tearoff=0)
        # Usamos after para abrir el diálogo fuera del handler del menú (evita que no se muestre en macOS)
        menu.add_command(label="Asignar sonido…", command=lambda: self.root.after(10, self.show_assign_dialog, r, c))
        menu.add_command(label="Renombrar…", command=lambda: self._rename_button(r, c))
        menu.add_command(label="Vaciar botón", command=lambda: self._clear_button(r, c))
        menu.add_separator()
        menu.add_command(label="Abrir carpeta de sonidos", command=self._open_sounds_folder)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def show_assign_dialog(self, r: int, c: int):
        """Selector de archivo con filtros correctos (tupla), inicializando en SOUND EFFECTS."""
        ensure_sounds_folder()
        try:
            path = filedialog.askopenfilename(
                parent=self.root,
                title="Seleccionar audio",
                filetypes=[("Audio", ("*.wav", "*.mp3")), ("WAV", "*.wav"), ("MP3", "*.mp3")],
                initialdir=os.path.abspath("SOUND EFFECTS"),
            )
        except Exception as e:
            messagebox.showerror("Archivo", f"No se pudo abrir el selector:\n{e}")
            return

        if not path:
            return  # cancelado

        # Actualiza datos y botón
        base = os.path.splitext(os.path.basename(path))[0]
        self.buttons_data[r][c]["file"] = path
        self.buttons_data[r][c]["label"] = base
        self.buttons_widgets[r][c].configure(text=base, fg_color=BTN_FG_ASSIGNED)

        # Preview corto y guardado
        self._preview(path)
        self._save_config()

    # ------------- Grid / Config -------------
    def _build_grid_from_config(self):
        # Inicializa matrices vacías
        self.buttons_widgets.clear()
        self.buttons_data = [[{"label": f"{r+1},{c+1}", "file": None} for c in range(self.cols)]
                             for r in range(self.rows)]

        # Aplica datos desde config (si existen)
        for item in self.cfg.get("buttons", []):
            try:
                r = int(item.get("row"))
                c = int(item.get("col"))
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    self.buttons_data[r][c]["label"] = item.get("label") or self.buttons_data[r][c]["label"]
                    self.buttons_data[r][c]["file"] = item.get("file")
            except Exception:
                continue

        # Construye widgets
        for r in range(self.rows):
            row_widgets = []
            for c in range(self.cols):
                label = self.buttons_data[r][c]["label"]
                has_file = bool(self.buttons_data[r][c]["file"])
                fg = BTN_FG_ASSIGNED if has_file else BTN_FG_EMPTY
                btn = ctk.CTkButton(
                    self.center,
                    text=label,
                    width=BTN_WIDTH,
                    height=BTN_HEIGHT,
                    corner_radius=BTN_RADIUS,
                    font=BTN_FONT,
                    fg_color=fg,
                    hover_color=BTN_HOVER,
                    command=lambda rr=r, cc=c: self._on_button_click(rr, cc),
                )
                btn.grid(row=r, column=c, padx=GRID_SPACING, pady=GRID_SPACING, sticky="nsew")

                # Context menu
                btn.bind("<Button-3>", lambda e, rr=r, cc=c: self.show_context_menu(e, rr, cc))
                btn.bind("<Button-2>", lambda e, rr=r, cc=c: self.show_context_menu(e, rr, cc))  # trackpad/ratón medio

                row_widgets.append(btn)
            self.buttons_widgets.append(row_widgets)

        # Aplica volumen inicial
        vol = self.vol_var.get() / 100.0
        try:
            pygame.mixer.music.set_volume(vol)
        except Exception:
            pass

    def _collect_config(self) -> dict:
        buttons_list = []
        for r in range(self.rows):
            for c in range(self.cols):
                buttons_list.append({
                    "row": r,
                    "col": c,
                    "label": self.buttons_data[r][c]["label"],
                    "file": self.buttons_data[r][c]["file"],
                })
        return {
            "grid": {"rows": self.rows, "cols": self.cols},
            "buttons": buttons_list,
            "__meta__": {"volume": int(self.vol_var.get())},
        }

    def _save_config(self):
        self.cfg = self._collect_config()
        save_button_config(self.cfg, self.cfg_path)
        self.set_status("💾 Configuración guardada")

    def _load_config_from_disk(self):
        path = filedialog.askopenfilename(
            title="Cargar configuración",
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return
        try:
            self.cfg_path = path
            self.cfg = load_button_config(self.cfg_path)
            self.rows = int(self.cfg.get("grid", {}).get("rows", 3))
            self.cols = int(self.cfg.get("grid", {}).get("cols", 4))

            # Reconstruye grilla
            for w in self.center.winfo_children():
                w.destroy()
            for c in range(max(1, self.cols)):
                self.center.grid_columnconfigure(c, weight=1)
            for r in range(max(1, self.rows)):
                self.center.grid_rowconfigure(r, weight=1)
            self._build_grid_from_config()
            # Volumen desde meta
            vol_int = int(self.cfg.get("__meta__", {}).get("volume", 80))
            self.vol_var.set(vol_int)
            self.vol_slider.set(vol_int)
            self.vol_value_lbl.configure(text=f"{vol_int}%")
            pygame.mixer.music.set_volume(vol_int / 100.0)
            self.set_status("✅ Configuración cargada")
        except Exception as e:
            messagebox.showerror("Cargar configuración", f"No se pudo cargar:\n{e}")

    # ------------- Interacción botones -------------
    def _on_button_click(self, r: int, c: int):
        info = self.buttons_data[r][c]
        path = info.get("file")
        if not path:
            self.set_status("Sin archivo asignado")
            return
        if not os.path.exists(path):
            self.set_status("Archivo no encontrado")
            messagebox.showwarning("Audio", f"No existe:\n{path}")
            # marca como roto
            self.buttons_widgets[r][c].configure(fg_color=BTN_FG_EMPTY)
            return
        self._play_file(path)

        def _open_context_menu(self, event, r: int, c: int):
            menu = Menu(self.root, tearoff=0)
            # OJO: usamos after para abrir el diálogo fuera del handler del menú
            menu.add_command(label="Asignar sonido…", command=lambda: self.root.after(10, self._assign_file_dialog, r, c))
            menu.add_command(label="Renombrar…", command=lambda: self._rename_button(r, c))
            menu.add_command(label="Vaciar botón", command=lambda: self._clear_button(r, c))
            menu.add_separator()
            menu.add_command(label="Abrir carpeta de sonidos", command=lambda: self._open_sounds_folder())
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        def _assign_file_dialog(self, r: int, c: int):
            ensure_sounds_folder()
            try:
                path = filedialog.askopenfilename(
                    parent=self.root,
                    title="Seleccionar audio",
                    # Tk NO acepta "*.wav;*.mp3" -> usa tupla de patrones
                    filetypes=[("Audio", ("*.wav", "*.mp3")), ("WAV", "*.wav"), ("MP3", "*.mp3")],
                    initialdir=os.path.abspath("SOUND EFFECTS"),
                )
            except Exception as e:
                messagebox.showerror("Archivo", f"No se pudo abrir el selector:\n{e}")
                return

            if not path:
                # usuario canceló
                return

            self.buttons_data[r][c]["file"] = path
            base = os.path.splitext(os.path.basename(path))[0]
            self.buttons_data[r][c]["label"] = base
            self.buttons_widgets[r][c].configure(text=base, fg_color=BTN_FG_ASSIGNED)
            self._preview(path)
            self._save_config()



    def _assign_file(self, r: int, c: int):
        ensure_sounds_folder()
        path = filedialog.askopenfilename(
            title="Seleccionar audio",
            filetypes=[("Audio", "*.wav;*.mp3"), ("WAV", "*.wav"), ("MP3", "*.mp3")],
            initialdir=os.path.abspath("SOUND EFFECTS"),
        )
        if not path:
            return
        self.buttons_data[r][c]["file"] = path
        # etiqueta amigable
        base = os.path.splitext(os.path.basename(path))[0]
        self.buttons_data[r][c]["label"] = base
        self.buttons_widgets[r][c].configure(text=base, fg_color=BTN_FG_ASSIGNED)
        self._preview(path)
        self._save_config()

    def _rename_button(self, r: int, c: int):
        current = self.buttons_data[r][c]["label"]
        new = simpledialog.askstring("Renombrar", "Nuevo nombre:", initialvalue=current, parent=self.root)
        if not new:
            return
        self.buttons_data[r][c]["label"] = new
        self.buttons_widgets[r][c].configure(text=new)
        self._save_config()

    def _clear_button(self, r: int, c: int):
        self.buttons_data[r][c]["file"] = None
        self.buttons_data[r][c]["label"] = f"{r+1},{c+1}"
        self.buttons_widgets[r][c].configure(text=self.buttons_data[r][c]["label"], fg_color=BTN_FG_EMPTY)
        self._save_config()

    def _open_sounds_folder(self):
        folder = ensure_sounds_folder()
        if os.name == "posix":
            os.system(f'open "{folder}"')
        elif os.name == "nt":
            os.system(f'start "" "{folder}"')
        else:
            messagebox.showinfo("Carpeta", folder)

    # ------------- Audio helpers -------------
    def _play_file(self, path: str):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(60)
                time.sleep(0.06)
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.vol_var.get() / 100.0)
            pygame.mixer.music.play()
            self.set_status(f"▶ Reproduciendo: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Audio", f"No se pudo reproducir:\n{e}")
            self.set_status("⚠️ Error de reproducción")

    def stop(self):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(150)
            self.set_status("⏹ Detenido")
        except Exception:
            pass

    def _preview(self, path: str, ms: int = 450):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(60)
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.vol_var.get() / 100.0)
            pygame.mixer.music.play()
            # corta solo
            self.root.after(ms, lambda: pygame.mixer.music.fadeout(120))
        except Exception as e:
            messagebox.showerror("Preview", f"No se pudo previsualizar:\n{e}")

    def _press_cell(self, r: int, c: int):
        try:
            self.buttons_widgets[r][c].invoke()
        except Exception:
            pass

# -------------------- Main --------------------
if __name__ == "__main__":
    app_root = ctk.CTk()
    app = AudioButtonApp(app_root)
    app_root.mainloop()
