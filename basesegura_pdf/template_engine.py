"""
Motor de templates BaseSegura.

Funciones puras (sin I/O): aptas para uso en Lambda o CLI.
Restricción de diseño: fill_template() NUNCA modifica CSS, clases ni estructura
del template original. Solo reemplaza texto en .field y agrega estado "checked".
"""
from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

PLACEHOLDER_RE = re.compile(r'\[([^\]]+)\]')

_INJECTED_CSS = """
/* --- estado checked y pre-wrap para bloques (inyectado por generador PDF) --- */
.field.block { white-space: pre-wrap; }
.activity-item.checked,
.activity-otros.checked {
  background: #EEF7F3 !important;
  border-color: #26A76F !important;
}
.activity-item.checked .check-box,
.activity-otros.checked .check-box {
  background: #26A76F !important;
  border-color: #26A76F !important;
  color: white !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  line-height: 14px !important;
}
@media print {
  .field {
    background: transparent !important;
    border-bottom: none !important;
    border: none !important;
  }
}
@page {
  size: A4 portrait;
  margin: 0;
}
"""


def discover_templates(templates_dir: str) -> list[dict]:
    """Escanea templates_dir y retorna [{name, path, display_name}] ordenado por nombre."""
    path = Path(templates_dir)
    result = []
    for f in sorted(path.glob("BaseSegura_*.html")):
        display = (
            f.stem
            .replace("BaseSegura_", "")
            .replace("_Template", "")
            .replace("_", " ")
        )
        result.append({"name": f.stem, "path": str(f), "display_name": display})
    return result


def _placeholder_meta(key: str) -> tuple[str, str]:
    """Separa 'LABEL: hint descriptivo' en (label, hint). Sin hint retorna ('LABEL', '')."""
    if ":" in key:
        label, hint = key.split(":", 1)
        return label.strip(), hint.strip()
    return key.strip(), ""


def extract_fields(html: str) -> list[dict]:
    """
    Extrae campos editables del HTML.

    Retorna lista de dicts únicos (en orden de aparición) con:
      key       — texto completo del placeholder (usado como clave en data)
      label     — parte antes de ':' (para mostrar al usuario)
      hint      — parte después de ':' (guía de contenido)
      multiline — True si el elemento tiene clase 'block'

    Excluye campos dentro de .activity-item / .activity-otros (los maneja extract_checkboxes).
    """
    soup = BeautifulSoup(html, "lxml")
    seen: set[str] = set()
    fields: list[dict] = []

    for el in soup.find_all(class_="field"):
        if el.find_parent(class_=["activity-item", "activity-otros"]):
            continue
        text = el.get_text()
        for m in PLACEHOLDER_RE.finditer(text):
            key = m.group(1).strip()
            if key in seen:
                continue
            seen.add(key)
            classes = el.get("class", [])
            label, hint = _placeholder_meta(key)
            fields.append({
                "key": key,
                "label": label,
                "hint": hint,
                "multiline": "block" in classes,
            })
    return fields


def extract_checkboxes(html: str) -> list[dict]:
    """
    Extrae actividades con checkbox del HTML.

    Retorna [{label, has_text_field, field_key}].
    field_key es el placeholder del campo de texto asociado (ej. "ESPECIFICAR"),
    o None si no hay campo de texto.
    """
    soup = BeautifulSoup(html, "lxml")
    checkboxes: list[dict] = []
    seen_labels: set[str] = set()

    for item in soup.find_all(class_=["activity-item", "activity-otros"]):
        label_el = item.find(class_="label-text")
        if not label_el:
            continue
        label = label_el.get_text(strip=True).rstrip(":")
        if label in seen_labels:
            continue
        seen_labels.add(label)

        field_key = None
        field_el = item.find(class_="field")
        if field_el:
            m = PLACEHOLDER_RE.search(field_el.get_text())
            if m:
                field_key = m.group(1).strip()

        checkboxes.append({
            "label": label,
            "has_text_field": field_el is not None,
            "field_key": field_key,
        })
    return checkboxes


def fill_template(
    html: str,
    data: dict[str, str],
    checked_activities: list[str] | None = None,
) -> str:
    """
    Rellena el template con los valores dados y marca las actividades seleccionadas.

    - data: {placeholder_key: valor_ingresado}
    - checked_activities: lista de labels de actividades a marcar

    Restricción: NO modifica ningún CSS, clase ni estructura existente del template.
    Solo reemplaza texto en nodos .field, agrega clase 'checked' a actividades
    seleccionadas e inyecta CSS mínimo adicional.
    """
    if checked_activities is None:
        checked_activities = []

    soup = BeautifulSoup(html, "lxml")

    # 1. Reemplazar placeholders en .field (excluye los de activity-items — se tratan abajo)
    for el in soup.find_all(class_="field"):
        for text_node in list(el.strings):
            raw = str(text_node)
            if not PLACEHOLDER_RE.search(raw):
                continue
            new_text = PLACEHOLDER_RE.sub(
                lambda m, _d=data: _d.get(m.group(1).strip(), m.group(0)),
                raw,
            )
            if new_text != raw:
                text_node.replace_with(NavigableString(new_text))

    # 2. Marcar actividades seleccionadas
    checked_set = set(checked_activities)
    for item in soup.find_all(class_=["activity-item", "activity-otros"]):
        label_el = item.find(class_="label-text")
        if not label_el:
            continue
        label = label_el.get_text(strip=True).rstrip(":")
        if label not in checked_set:
            continue

        classes = item.get("class", [])
        if "checked" not in classes:
            item["class"] = classes + ["checked"]

        check_box = item.find(class_="check-box")
        if check_box:
            check_box.clear()
            check_box.append(NavigableString("✓"))

    # 2b. Limpiar [ESPECIFICAR] en activity-otros no seleccionados
    for item in soup.find_all(class_="activity-otros"):
        label_el = item.find(class_="label-text")
        if not label_el:
            continue
        label = label_el.get_text(strip=True).rstrip(":")
        if label in checked_set:
            continue
        field_el = item.find(class_="field")
        if field_el:
            field_el.clear()

    # 2c. Eliminar secciones opcionales cuyos campos están todos vacíos o sin rellenar
    for section in soup.find_all(attrs={"data-optional-section": True}):
        fields_in_section = section.find_all(class_="field")
        if not fields_in_section:
            continue
        all_empty = all(
            not el.get_text(strip=True) or PLACEHOLDER_RE.search(el.get_text())
            for el in fields_in_section
        )
        if all_empty:
            section.decompose()

    # 3. Inyectar CSS adicional (solo append al <style> existente, sin tocar nada más)
    style_tag = soup.find("style")
    if style_tag:
        style_tag.append(NavigableString(_INJECTED_CSS))

    # 4. Remover .legend-tip (elemento de workspace, no debe aparecer en el PDF)
    for el in soup.find_all(class_="legend-tip"):
        el.decompose()

    return str(soup)
