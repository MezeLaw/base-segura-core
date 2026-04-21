"""
Generador PDF usando Playwright (Chromium headless).

html_to_pdf() es una función pura (bytes in, bytes out):
apta para Lambda, CLI o cualquier otro contexto de I/O.

Playwright renderiza el HTML con el mismo motor que Chrome, respetando
@media print, CSS grid/flex y fuentes — fidelidad total al diseño.
"""
from __future__ import annotations

import tempfile
from pathlib import Path


def html_to_pdf(html: str, base_url: str, output_path: str | None = None) -> bytes:
    """
    Convierte HTML a PDF con Playwright (Chromium).

    Args:
        html:        Contenido HTML ya procesado (campos rellenos).
        base_url:    URL base como 'file:///ruta/al/dir/' — se usa para
                     escribir un archivo temporal que Chromium navega,
                     resolviendo fuentes y assets relativos correctamente.
        output_path: Si se especifica, guarda el PDF en disco además de retornarlo.

    Returns:
        Bytes del PDF generado.
    """
    from playwright.sync_api import sync_playwright

    # Resolvemos la ruta del directorio base desde la file:// URL
    base_dir = base_url.removeprefix("file://").rstrip("/")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Escribimos el HTML en un archivo temporal dentro del directorio del
        # template para que Chromium resuelva fuentes y assets relativos
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".html",
            dir=base_dir,
            encoding="utf-8",
            delete=False,
        ) as tmp:
            tmp.write(html)
            tmp_path = Path(tmp.name)

        try:
            page.goto(tmp_path.as_uri(), wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
            )
        finally:
            tmp_path.unlink(missing_ok=True)
            browser.close()

    if output_path:
        Path(output_path).write_bytes(pdf_bytes)

    return pdf_bytes
