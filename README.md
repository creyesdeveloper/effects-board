# Effects Board

Utilidad gratuita para streamers y creadores: asigna archivos .wav/.mp3 a una cuadrícula de botones y reprodúcelos al instante.
UI oscura, control de volumen, multilenguaje EN/ES, guardado de perfiles (Save As), y soporte macOS/Windows/Linux.

## ✨ Características

- UI Dark con cuadrícula 3×4 (fácil de ampliar).

- Asignar sonido por botón (clic derecho) con preview corto.

- Guardar configuración como… (configs/*.json) y Cargar configuración.

- Resetear a valores por defecto.

- Idioma EN/ES conmutado desde la barra superior (los nombres de los botones cambian).

- Volumen maestro 0–100%.

- Atajos básicos: dígitos 1..0 disparan la primera fila.

## 📦 Requisitos

Python 3.12 (recomendado) – funciona 3.11–3.13.

## Dependencias

    customtkinter>=5.2

    pygame>=2.6

    Pillow>=10 (para íconos futuros)

Instálalas con:

    pip install -r requirements.txt

Nota macOS: si ves avisos de Cocoa tipo
The class 'NSOpenPanel'/'NSSavePanel' overrides the method identifier…
son inofensivos y no afectan la app.

## 🔧 Instalación del entorno (.venv)

### macOS / Linux

    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

#### Windows (PowerShell)

    py -3 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt

## ▶️ Ejecución

    python mp3boardver09.py

- Clic derecho sobre un botón → Asignar sonido… (admite .wav y .mp3).

- El volumen está en la barra superior.

- El idioma EN/ES se cambia con el conmutador de la derecha.

## 💾 Perfiles (Guardar/Cargar)

Guardar config Botónes → abre Guardar como… y te permite nombrar tu perfil.

- Ubicación sugerida: configs/ (se creará si no existe).

- Cargar configuración → abre el selector y aplica ese perfil.

- Resetear configuración → vuelve a la grilla vacía (3×4) y volumen 80%.

## Formato del JSON

    {
    "grid": { "rows": 3, "cols": 4 },
    "buttons": [
        {
        "row": 0,
        "col": 0,
        "labels": { "en": "Intro", "es": "Intro" },
        "file": "SOUND EFFECTS/intro.wav"
        }
    ],
    "__meta__": { "volume": 80, "lang": "es" }
    }

- labels.en / labels.es: nombres por idioma del botón.

- file: ruta absoluta o relativa al audio.

- __meta__.lang: idioma preferido al abrir.

- __meta__.volume: volumen inicial (0–100).

Si cargas una config antigua con label, la app migra a labels.en/es automáticamente.

## 📁 Estructura de directorios (sugerida)

    effects-board/
    ├─ configs/                 # perfiles .json (versiona ejemplos, tus perfiles a elección)
    │  └─ example_es.json
    ├─ old_versions/            # historial de scripts
    │  ├─ mp3boardver07.py
    │  └─ mp3boardver08.py
    ├─ SOUND EFFECTS/           # (local) tus audios .wav/.mp3  ❗no se suben al repo
    │  └─ README.md
    ├─ mp3boardver09.py         # versión estable v0.9
    ├─ button_config.json       # perfil por defecto (se actualiza al usar la app)
    ├─ requirements.txt
    ├─ LICENSE
    └─ README.md

.gitignore relevante:

    .venv/
    __pycache__/
    *.pyc
    dist/
    build/
    *.spec
    SOUND EFFECTS/**/*.wav
    SOUND EFFECTS/**/*.mp3

## 🧰 Empaquetado (opcional)

### PyInstaller

macOS (app sin consola):

    pip install pyinstaller
    python -m PyInstaller --name "EffectsBoard" --windowed --noconfirm \
    --add-data "configs:configs" mp3boardver09.py

### Windows (EXE sin consola):

    pip install pyinstaller
    pyinstaller --noconfirm --noconsole --name "EffectsBoard" `
    --add-data "configs;configs" mp3boardver09.py

Los binarios quedan en dist/.

## 🧭 Consejos y atajos

- Asignar sonido: clic derecho → Asignar sonido… (abre en SOUND EFFECTS/ por comodidad).

- Preview: al asignar, suena ~0.45s para confirmar.

- Atajos: 1..0 disparan la primera fila (extenderemos pronto Q–P, A–L, Z–M).

- Tamaño de ventana: la grilla se adapta, y puedes subir BTN_RADIUS, GRID_SPACING o ctk.set_widget_scaling() en el código para estética.

## 🤝 Contribuir

- Issues / PRs bienvenidos.

- Estilo de commit sugerido: feat(scope): mensaje / fix(scope): … / docs: ….

## 📜 Licencia

GPL-3.0 (ver LICENSE).
