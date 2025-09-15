# mp3boardver09.py
# Effects Board: EN/ES dinámico para botones de acción + "Guardar como…"
from __future__ import annotations
import os, json, time
import pygame
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog, Menu

DEFAULT_CONFIG_FILE = "button_config.json"

# ----- Textos UI (i18n) -----
TEXTS = {
    "es": {
        "save": "Guardar config Botónes",
        "load": "Cargar configuración",
        "reset": "Resetear configuración",
        "save_title": "Guardar configuración como…",
        "load_title": "Cargar configuración",
        "saved_as": "💾 Guardado en: ",
        "reset_ok": "🔄 Configuración reseteada",
        "rename_title": "Renombrar",
        "rename_prompt": "Nuevo nombre:",
        "no_file": "Sin archivo asignado",
        "not_found": "Archivo no encontrado",
        "select_audio": "Seleccionar audio",
    },
    "en": {
        "save": "Save config Buttons",
        "load": "Load buttons config",
        "reset": "Reset buttons config",
        "save_title": "Save configuration as…",
        "load_title": "Load configuration",
        "saved_as": "💾 Saved to: ",
        "reset_ok": "🔄 Configuration reset",
        "rename_title": "Rename",
        "rename_prompt": "New name:",
        "no_file": "No file assigned",
        "not_found": "File not found",
        "select_audio": "Select audio",
    },
}

# ----- Estilo UI -----
APP_TITLE = "Effects Board"
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")
ctk.set_widget_scaling(1.05)

BTN_WIDTH = 140
BTN_HEIGHT = 80
BTN_RADIUS = 12
BTN_FONT = ("Arial", 14, "bold")
BTN_FG_ASSIGNED = "#0EA5E9"
BTN_FG_EMPTY = "#334155"
BTN_HOVER = "#1F2937"

PANEL_PADX = 10
PANEL_PADY = 10
GRID_SPACING = 8


# --------- Utilidades de archivo/config ---------
def ensure_sounds_folder():
    base = "SOUND EFFECTS"
    os.makedirs(base, exist_ok=True)
    readme = os.path.join(base, "README.md")
    if not os.path.exists(readme):
        with open(readme, "w", encoding="utf-8") as f:
            f.write("# Carpeta de sonidos\n\nColoca aquí tus .wav/.mp3.\n")
    return os.path.abspath(base)

def ensure_configs_folder():
    base = "configs"
    os.makedirs(base, exist_ok=True)
    return os.path.abspath(base)

def load_button_config(path: str) -> dict:
    if not os.path.exists(path):
        data = {
            "grid": {"rows": 3, "cols": 4},
            "buttons": [],
            "__meta__": {"volume": 80, "lang": "es"},
        }
        save_button_config(data, path)
        return data
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # Migración: label -> labels{en,es}
    changed = False
    for b in raw.get("buttons", []):
        if "labels" not in b:
            label_val = b.get("label")
            if isinstance(label_val, str) and label_val.strip():
                b["labels"] = {"en": label_val, "es": label_val}
            else:
                b["labels"] = {
                    "en": f'{b.get("row",0)+1},{b.get("col",0)+1}',
                    "es": f'{b.get("row",0)+1},{b.get("col",0)+1}'
                }
            changed = True
        if "label" in b:
            del b["label"]; changed = True
    if "__meta__" not in raw:
        raw["__meta__"] = {"volume": 80, "lang": "es"}; changed = True
    elif "lang" not in raw["__meta__"]:
        raw["__meta__"]["lang"] = "es"; changed = True
    if changed:
        save_button_config(raw, path)
    return raw

def save_button_config(cfg: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# -------------------- App --------------------
class AudioButtonApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1000x660")
        self.root.minsize(880, 540)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.cfg_path = DEFAULT_CONFIG_FILE
        self.cfg = load_button_config(self.cfg_path)
        self.rows = int(self.cfg.get("grid", {}).get("rows", 3))
        self.cols = int(self.cfg.get("grid", {}).get("cols", 4))
        self.lang = (self.cfg.get("__meta__", {}).get("lang", "es") or "es").lower()

        self._init_mixer()

        # ---------- Topbar ----------
        self.topbar = ctk.CTkFrame(self.root, corner_radius=0)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_columnconfigure(0, weight=1)

        self.title_lbl = ctk.CTkLabel(self.topbar, text=APP_TITLE, font=("Arial", 18, "bold"))
        self.title_lbl.grid(row=0, column=0, padx=(PANEL_PADX, 0), pady=8, sticky="w")

        volume_initial = int(self.cfg.get("__meta__", {}).get("volume", 80))
        volume_initial = min(100, max(0, volume_initial))
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
        self.vol_slider.grid(row=0, column=3, padx=(0, 12), pady=8, sticky="e")

        # Selector EN/ES
        self.lang_var = ctk.StringVar(value=self.lang.upper())
        self.lang_toggle = ctk.CTkSegmentedButton(
            self.topbar, values=["EN", "ES"], variable=self.lang_var,
            command=self._on_lang_change, width=120
        )
        self.lang_toggle.grid(row=0, column=4, padx=(0, PANEL_PADX), pady=8, sticky="e")

        # ---------- Centro (grilla) ----------
        self.center = ctk.CTkFrame(self.root)
        self.center.grid(row=1, column=0, sticky="nsew", padx=PANEL_PADX, pady=(0, PANEL_PADY))
        for c in range(self.cols): self.center.grid_columnconfigure(c, weight=1)
        for r in range(self.rows): self.center.grid_rowconfigure(r, weight=1)

        self.buttons_widgets: list[list[ctk.CTkButton]] = []
        self.buttons_data: list[list[dict]] = []
        self._build_grid_from_config()

        # ---------- Action bar ----------
        self.actionbar = ctk.CTkFrame(self.root, corner_radius=0)
        self.actionbar.grid(row=2, column=0, sticky="ew")
        self.actionbar.grid_columnconfigure(0, weight=1)

        self.status = ctk.CTkLabel(self.actionbar, text="Listo", anchor="w")
        self.status.grid(row=0, column=0, padx=(PANEL_PADX, 8), pady=8, sticky="w")

        # Títulos según idioma actual
        ui = TEXTS.get(self.lang, TEXTS["es"])
        self.btn_save = ctk.CTkButton(self.actionbar, text=ui["save"], command=self._save_config)
        self.btn_load = ctk.CTkButton(self.actionbar, text=ui["load"], command=self._load_config_from_disk)
        self.btn_reset = ctk.CTkButton(self.actionbar, text=ui["reset"], command=self._reset_config)
        self.btn_save.grid(row=0, column=1, padx=4, pady=8, sticky="e")
        self.btn_load.grid(row=0, column=2, padx=4, pady=8, sticky="e")
        self.btn_reset.grid(row=0, column=3, padx=(4, PANEL_PADX), pady=8, sticky="e")
        self._apply_ui_texts()


        self._bind_simple_hotkeys()
        self._build_menubar()  # opcional

    # ---------- Helpers ----------
    def t(self, key: str) -> str:
        return TEXTS.get(self.lang, TEXTS["es"]).get(key, key)

    def set_status(self, msg: str): self.status.configure(text=msg)

    def _init_mixer(self):
        try: pygame.mixer.init()
        except Exception as e: messagebox.showwarning("Audio", f"No se pudo inicializar audio:\n{e}")

    def _on_lang_change(self, _val: str):
        self.lang = self.lang_var.get().lower()
        # refrescar textos UI + botones
        self._apply_language()
        # persistir preferencia
        self.cfg["__meta__"]["lang"] = self.lang
        save_button_config(self._collect_config(), self.cfg_path)

    def _bind_simple_hotkeys(self):
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
        file_menu.add_command(label="Abrir carpeta de sonidos", command=self._open_sounds_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.destroy)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        self.root.config(menu=menubar)

    # ---------- Grid / Config ----------
    def _build_grid_from_config(self):
        self.buttons_widgets.clear()
        base = [[{"labels": {"en": f"{r+1},{c+1}", "es": f"{r+1},{c+1}"}, "file": None}
                 for c in range(self.cols)] for r in range(self.rows)]
        for item in self.cfg.get("buttons", []):
            try:
                r = int(item.get("row")); c = int(item.get("col"))
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    base[r][c]["file"] = item.get("file")
                    labels = item.get("labels", {})
                    if "en" in labels: base[r][c]["labels"]["en"] = labels["en"]
                    if "es" in labels: base[r][c]["labels"]["es"] = labels["es"]
            except Exception:
                continue
        self.buttons_data = base

        for r in range(self.rows):
            row_widgets = []
            for c in range(self.cols):
                lbl = self.buttons_data[r][c]["labels"].get(self.lang, f"{r+1},{c+1}")
                has_file = bool(self.buttons_data[r][c]["file"])
                fg = BTN_FG_ASSIGNED if has_file else BTN_FG_EMPTY
                btn = ctk.CTkButton(
                    self.center, text=lbl, width=BTN_WIDTH, height=BTN_HEIGHT,
                    corner_radius=BTN_RADIUS, font=BTN_FONT,
                    fg_color=fg, hover_color=BTN_HOVER,
                    command=lambda rr=r, cc=c: self._on_button_click(rr, cc)
                )
                btn.grid(row=r, column=c, padx=GRID_SPACING, pady=GRID_SPACING, sticky="nsew")
                btn.bind("<Button-3>", lambda e, rr=r, cc=c: self.show_context_menu(e, rr, cc))
                btn.bind("<Button-2>", lambda e, rr=r, cc=c: self.show_context_menu(e, rr, cc))
                row_widgets.append(btn)
            self.buttons_widgets.append(row_widgets)

        try: pygame.mixer.music.set_volume(self.vol_var.get()/100.0)
        except Exception: pass

        # Aplica textos de botones de acción al idioma actual
        # self._apply_ui_texts()

    def _apply_ui_texts(self):
        ui = TEXTS.get(self.lang, TEXTS["es"])
        if hasattr(self, "btn_save"):
            self.btn_save.configure(text=ui["save"])
        if hasattr(self, "btn_load"):
            self.btn_load.configure(text=ui["load"])
        if hasattr(self, "btn_reset"):
            self.btn_reset.configure(text=ui["reset"])


    def _apply_language(self):
        # Labels de la grilla
        for r in range(self.rows):
            for c in range(self.cols):
                lbl = self.buttons_data[r][c]["labels"].get(self.lang, f"{r+1},{c+1}")
                self.buttons_widgets[r][c].configure(text=lbl)
        # Textos de los botones de acción
        self._apply_ui_texts()

    def _collect_config(self) -> dict:
        buttons_list = []
        for r in range(self.rows):
            for c in range(self.cols):
                buttons_list.append({
                    "row": r, "col": c,
                    "labels": self.buttons_data[r][c]["labels"],
                    "file": self.buttons_data[r][c]["file"],
                })
        return {
            "grid": {"rows": self.rows, "cols": self.cols},
            "buttons": buttons_list,
            "__meta__": {"volume": int(self.vol_var.get()), "lang": self.lang},
        }

    # ----- GUARDAR COMO… -----
    def _save_config(self):
        """Siempre 'Guardar como…': pregunta nombre/ruta y guarda."""
        cfg = self._collect_config()
        ensure_configs_folder()
        default_name = f"buttons_{self.lang}.json"
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title=self.t("save_title"),
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialdir=ensure_configs_folder(),
            initialfile=default_name,
        )
        if not path:
            return
        self.cfg_path = path
        save_button_config(cfg, path)
        self.set_status(self.t("saved_as") + os.path.basename(path))

    def _load_config_from_disk(self):
        path = filedialog.askopenfilename(
            parent=self.root, title=self.t("load_title"),
            filetypes=[("JSON", "*.json")],
            initialdir=ensure_configs_folder(),
        )
        if not path: return
        try:
            self.cfg_path = path
            self.cfg = load_button_config(self.cfg_path)
            self.rows = int(self.cfg.get("grid", {}).get("rows", 3))
            self.cols = int(self.cfg.get("grid", {}).get("cols", 4))
            self.lang = (self.cfg.get("__meta__", {}).get("lang", self.lang) or self.lang).lower()

            for w in self.center.winfo_children(): w.destroy()
            for c in range(max(1, self.cols)): self.center.grid_columnconfigure(c, weight=1)
            for r in range(max(1, self.rows)): self.center.grid_rowconfigure(r, weight=1)
            self._build_grid_from_config()

            vol_int = int(self.cfg.get("__meta__", {}).get("volume", 80))
            self.vol_var.set(vol_int); self.vol_slider.set(vol_int)
            self.vol_value_lbl.configure(text=f"{vol_int}%")
            pygame.mixer.music.set_volume(vol_int / 100.0)

            self.lang_var.set(self.lang.upper())
            self._apply_language()
            self.set_status("✅ Config loaded" if self.lang == "en" else "✅ Configuración cargada")
        except Exception as e:
            messagebox.showerror(self.t("load_title"), f"No se pudo cargar:\n{e}")

    def _reset_config(self):
        if not messagebox.askyesno("Reset", "Resetear a valores por defecto?" if self.lang=="es" else "Reset to defaults?"):
            return
        self.cfg = {
            "grid": {"rows": self.rows, "cols": self.cols},
            "buttons": [],
            "__meta__": {"volume": 80, "lang": self.lang},
        }
        save_button_config(self.cfg, self.cfg_path)
        for w in self.center.winfo_children(): w.destroy()
        self._build_grid_from_config()
        self.vol_var.set(80); self.vol_slider.set(80); self.vol_value_lbl.configure(text="80%")
        pygame.mixer.music.set_volume(0.8)
        self.set_status(self.t("reset_ok"))

    # ---------- Interacción botones ----------
    def _on_button_click(self, r: int, c: int):
        info = self.buttons_data[r][c]
        path = info.get("file")
        if not path:
            self.set_status(self.t("no_file")); return
        if not os.path.exists(path):
            self.set_status(self.t("not_found"))
            messagebox.showwarning("Audio", f"No existe:\n{path}")
            self.buttons_widgets[r][c].configure(fg_color=BTN_FG_EMPTY)
            return
        self._play_file(path)

    def show_context_menu(self, event, r: int, c: int):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="Asignar sonido…" if self.lang=="es" else "Assign sound…",
                         command=lambda: self.root.after(10, self.show_assign_dialog, r, c))
        menu.add_command(label="Renombrar…" if self.lang=="es" else "Rename…",
                         command=lambda: self._rename_button(r, c))
        menu.add_command(label="Vaciar botón" if self.lang=="es" else "Clear button",
                         command=lambda: self._clear_button(r, c))
        menu.add_separator()
        menu.add_command(label="Abrir carpeta de sonidos" if self.lang=="es" else "Open sounds folder",
                         command=self._open_sounds_folder)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def show_assign_dialog(self, r: int, c: int):
        ensure_sounds_folder()
        try:
            path = filedialog.askopenfilename(
                parent=self.root, title=self.t("select_audio"),
                filetypes=[("Audio", ("*.wav", "*.mp3")), ("WAV", "*.wav"), ("MP3", "*.mp3")],
                initialdir=os.path.abspath("SOUND EFFECTS"),
            )
        except Exception as e:
            messagebox.showerror("Archivo", f"No se pudo abrir el selector:\n{e}")
            return
        if not path: return

        base = os.path.splitext(os.path.basename(path))[0]
        self.buttons_data[r][c]["file"] = path
        labels = self.buttons_data[r][c].setdefault("labels", {"en": base, "es": base})
        labels[self.lang] = base
        self.buttons_widgets[r][c].configure(text=labels[self.lang], fg_color=BTN_FG_ASSIGNED)
        self._preview(path)
        save_button_config(self._collect_config(), self.cfg_path)

    def _rename_button(self, r: int, c: int):
        current = self.buttons_data[r][c]["labels"].get(self.lang, f"{r+1},{c+1}")
        new = simpledialog.askstring(self.t("rename_title"), self.t("rename_prompt"),
                                     initialvalue=current, parent=self.root)
        if not new: return
        self.buttons_data[r][c]["labels"][self.lang] = new
        self.buttons_widgets[r][c].configure(text=new)
        save_button_config(self._collect_config(), self.cfg_path)

    def _clear_button(self, r: int, c: int):
        self.buttons_data[r][c]["file"] = None
        self.buttons_data[r][c]["labels"][self.lang] = f"{r+1},{c+1}"
        self.buttons_widgets[r][c].configure(text=f"{r+1},{c+1}", fg_color=BTN_FG_EMPTY)
        save_button_config(self._collect_config(), self.cfg_path)

    def _open_sounds_folder(self):
        folder = ensure_sounds_folder()
        if os.name == "posix":
            os.system(f'open "{folder}"')
        elif os.name == "nt":
            os.system(f'start "" "{folder}"')
        else:
            messagebox.showinfo("Carpeta", folder)

    # ---------- Audio ----------
    def _play_file(self, path: str):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(60); time.sleep(0.06)
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.vol_var.get() / 100.0)
            pygame.mixer.music.play()
            self.set_status(f"▶ Reproduciendo: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Audio", f"No se pudo reproducir:\n{e}")
            self.set_status("⚠️ Error de reproducción")

    def stop(self):
        try:
            if pygame.mixer.music.get_busy(): pygame.mixer.music.fadeout(150)
            self.set_status("⏹ Detenido")
        except Exception: pass

    def _preview(self, path: str, ms: int = 450):
        try:
            if pygame.mixer.music.get_busy(): pygame.mixer.music.fadeout(60)
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.vol_var.get() / 100.0)
            pygame.mixer.music.play()
            self.root.after(ms, lambda: pygame.mixer.music.fadeout(120))
        except Exception as e:
            messagebox.showerror("Preview", f"No se pudo previsualizar:\n{e}")

    def _press_cell(self, r: int, c: int):
        try: self.buttons_widgets[r][c].invoke()
        except Exception: pass


if __name__ == "__main__":
    app_root = ctk.CTk()
    app = AudioButtonApp(app_root)
    app_root.mainloop()
