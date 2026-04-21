"""
BaseSegura · Generador de Documentos PDF

CLI interactiva para rellenar templates HTML y exportarlos como PDF.
Uso: python -m basesegura_pdf
"""
import os
import re
import sys
from datetime import date
from pathlib import Path

from .template_engine import (
    discover_templates,
    extract_checkboxes,
    extract_fields,
    fill_template,
)
from .pdf_generator import html_to_pdf

TEMPLATES_DIR = Path.home() / "Documents" / "BaseSegura" / "Templates"
SAFE_CHAR_RE = re.compile(r"[^\w\s-]", re.UNICODE)
MULTI_SPACE_RE = re.compile(r"\s+")

BANNER = """
╔══════════════════════════════════════════════╗
║    BaseSegura · Generador de Documentos      ║
║    Higiene y Seguridad Laboral               ║
╚══════════════════════════════════════════════╝
"""


# ──────────────────────────── helpers ────────────────────────────

def _print(msg: str = "") -> None:
    print(msg)


def _ask(prompt: str, default: str = "") -> str:
    hint = f"  [{default}]" if default else ""
    try:
        value = input(f"  {prompt}{hint}: ").strip()
    except (KeyboardInterrupt, EOFError):
        _print("\n\nSaliendo…")
        sys.exit(0)
    return value or default


def _ask_multiline(label: str, hint: str = "") -> str:
    """Solicita texto multilínea. Línea en blanco finaliza el ingreso."""
    hint_str = f"\n     ({hint})" if hint else ""
    _print(f"\n  {label}{hint_str}")
    _print("  [Ingresá el texto. Línea vacía para terminar]")
    lines = []
    while True:
        try:
            line = input("  > ")
        except (KeyboardInterrupt, EOFError):
            break
        if line == "" and lines:
            break
        lines.append(line)
    return "\n".join(lines)


def _ask_choice(prompt: str, options: list[str]) -> str:
    """Menú de selección única. Retorna el valor elegido."""
    _print(f"\n  {prompt}")
    for i, opt in enumerate(options, 1):
        _print(f"    {i}. {opt}")
    while True:
        raw = _ask("Opción")
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        _print("  ✗ Ingresá un número válido.")


def _ask_multi_choice(prompt: str, options: list[str]) -> list[str]:
    """Selección múltiple. Retorna lista de valores elegidos."""
    _print(f"\n  {prompt}")
    for i, opt in enumerate(options, 1):
        _print(f"    {i}. {opt}")
    _print("    (Ingresá números separados por coma, ej: 1,3  —  Enter para ninguna)")
    while True:
        raw = _ask("Selección").replace(" ", "")
        if raw == "":
            return []
        parts = raw.split(",")
        if all(p.isdigit() and 1 <= int(p) <= len(options) for p in parts):
            return [options[int(p) - 1] for p in parts]
        _print("  ✗ Ingresá números válidos separados por coma.")


def _sanitize(text: str) -> str:
    """Convierte texto a nombre de archivo seguro."""
    text = SAFE_CHAR_RE.sub("", text)
    text = MULTI_SPACE_RE.sub("_", text.strip())
    return text[:40] if text else "documento"


def _default_output_name(template_display: str, data: dict) -> str:
    """Genera nombre de archivo PDF por defecto."""
    prefix = _sanitize(template_display.replace(" ", "_"))
    client_key = next((k for k in data if "RAZ" in k.upper()), None)
    client = _sanitize(data[client_key]) if client_key and data.get(client_key) else ""
    today = date.today().strftime("%Y%m%d")
    parts = [p for p in [prefix, client, today] if p]
    return "_".join(parts) + ".pdf"


# ──────────────────────────── flujo principal ────────────────────────────

def run() -> None:
    _print(BANNER)

    # 1. Descubrir templates
    templates = discover_templates(str(TEMPLATES_DIR))
    if not templates:
        _print(f"No se encontraron templates en:\n  {TEMPLATES_DIR}")
        sys.exit(1)

    template = _ask_choice(
        "Seleccioná el template a completar:",
        [t["display_name"] for t in templates],
    )
    selected = next(t for t in templates if t["display_name"] == template)
    html_path = Path(selected["path"])
    html = html_path.read_text(encoding="utf-8")

    _print(f"\n  Template: {selected['display_name']}")
    _print("  " + "─" * 44)

    # 2. Extraer campos y checkboxes
    fields = extract_fields(html)
    checkboxes = extract_checkboxes(html)

    # 3. Recolectar valores de campos
    data: dict[str, str] = {}

    if fields:
        _print("\n  ── Datos del documento ──────────────────────")
        for field in fields:
            if field["multiline"]:
                value = _ask_multiline(field["label"], field["hint"])
            else:
                prompt = field["label"]
                if field["hint"]:
                    prompt += f" ({field['hint']})"
                value = _ask(prompt)
            data[field["key"]] = value

    # 4. Recolectar checkboxes
    checked_activities: list[str] = []

    if checkboxes:
        _print("\n  ── Actividades realizadas ───────────────────")
        checked_activities = _ask_multi_choice(
            "Seleccioná las actividades que aplican:",
            [cb["label"] for cb in checkboxes],
        )

        # Si hay alguna actividad con campo de texto (ej. "Otros"), pedirlo
        for cb in checkboxes:
            if cb["label"] in checked_activities and cb["has_text_field"] and cb["field_key"]:
                value = _ask(f'  Especificá "{cb["label"]}"')
                data[cb["field_key"]] = value

    # 5. Ruta de salida
    _print("\n  ── Archivo de salida ────────────────────────")
    default_name = _default_output_name(selected["display_name"], data)
    default_path = str(html_path.parent / default_name)
    output_path = _ask("Ruta del PDF", default_path)
    if not output_path.lower().endswith(".pdf"):
        output_path += ".pdf"

    # 6. Generar PDF
    _print("\n  Procesando…")
    filled_html = fill_template(html, data, checked_activities)
    base_url = html_path.parent.as_uri() + "/"

    try:
        html_to_pdf(filled_html, base_url=base_url, output_path=output_path)
    except Exception as exc:
        _print(f"\n  ✗ Error al generar el PDF:\n    {exc}")
        sys.exit(1)

    _print(f"\n  ✓ PDF generado exitosamente:")
    _print(f"    {output_path}\n")


if __name__ == "__main__":
    run()
