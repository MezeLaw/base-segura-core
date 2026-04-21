# BaseSegura · Generador de PDFs

Convierte los templates HTML de BaseSegura en PDFs, reemplazando campos interactivamente desde la terminal.

## Requisitos del sistema

- Python 3.9+
- Homebrew (macOS)

## Instalación

```bash
# 1. Dependencia del sistema (necesaria para WeasyPrint)
brew install pango

# 2. Dependencias Python (desde el directorio del proyecto)
pip install -r basesegura_pdf/requirements.txt
```

## Uso

```bash
cd /Users/meze/PyCharmMiscProject
python -m basesegura_pdf
```

La app guía el proceso paso a paso:

1. Seleccioná el template (Constancia de Visita, Ruido, etc.)
2. Completá cada campo cuando se solicita
3. Para campos largos (observaciones, descripciones): escribí el texto y presioná **Enter en línea vacía** para terminar
4. Seleccioná las actividades realizadas ingresando los números separados por coma (ej. `1,3`)
5. Confirmá la ruta de salida — por defecto se genera automáticamente en la misma carpeta del template

El PDF se guarda en la ruta indicada.

## Estructura

```
basesegura_pdf/
├── cli.py               # Flujo interactivo (entry point)
├── template_engine.py   # Extracción de campos y relleno de templates
├── pdf_generator.py     # Conversión HTML → PDF con WeasyPrint
└── requirements.txt
```

Los templates se leen desde `~/Documents/BaseSegura/Templates/`.
