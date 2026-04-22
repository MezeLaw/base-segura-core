# BaseSegura · Generador de PDFs

Convierte los templates HTML de BaseSegura en PDFs, reemplazando campos interactivamente desde la terminal.

## Requisitos del sistema

- Python 3.9+
- Templates en `~/Documents/BaseSegura/Templates/`

## Instalación

```bash
# Desde la raíz del repositorio (base-segura-core/)

# 1. Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias Python
pip install -r basesegura_pdf/requirements.txt

# 3. Instalar los browsers de Playwright (solo la primera vez)
playwright install chromium
```

## Uso

```bash
# Desde la raíz del repositorio, con el entorno activado
source .venv/bin/activate
python -m basesegura_pdf
```

La CLI guía el proceso paso a paso:

1. Seleccioná el template (Constancia de Visita, Ruido, etc.)
2. Completá cada campo cuando se solicita
3. Para campos largos (observaciones, descripciones): escribí el texto y presioná **Enter en línea vacía** para terminar
4. Seleccioná las actividades realizadas ingresando los números separados por coma (ej. `1,3`)
5. Confirmá la ruta de salida — por defecto se genera automáticamente en la misma carpeta del template

El PDF se guarda en la ruta indicada.

## Estructura

```
base-segura-core/
├── basesegura_pdf/
│   ├── __main__.py          # Entry point (python -m basesegura_pdf)
│   ├── cli.py               # Flujo interactivo
│   ├── template_engine.py   # Extracción de campos y relleno de templates
│   ├── pdf_generator.py     # Conversión HTML → PDF con Playwright (Chromium)
│   └── requirements.txt
└── verificaciones.txt       # Checklist de verificaciones pendientes
```

Los templates se leen desde `~/Documents/BaseSegura/Templates/`.

## Dependencias

| Paquete | Uso |
|---|---|
| `playwright` | Renderizado HTML → PDF con Chromium headless |
| `beautifulsoup4` | Parsing y manipulación del HTML de los templates |
| `lxml` | Parser HTML para BeautifulSoup |
