"""
Generador PDF usando Playwright (Chromium headless).

html_to_pdf() es una función pura (bytes in, bytes out):
apta para Lambda, CLI o cualquier otro contexto de I/O.

Playwright renderiza el HTML con el mismo motor que Chrome, respetando
@media print, CSS grid/flex y fuentes — fidelidad total al diseño.
"""
from __future__ import annotations

from pathlib import Path


def html_to_pdf(html: str, base_url: str, output_path: str | None = None) -> bytes:
    """
    Convierte HTML a PDF con Playwright (Chromium).

    Args:
        html:        Contenido HTML ya procesado (campos rellenos).
        base_url:    Reservado para compatibilidad futura (assets locales relativos).
                     Actualmente no se usa porque los templates cargan fuentes vía CDN.
        output_path: Si se especifica, guarda el PDF en disco además de retornarlo.

    Returns:
        Bytes del PDF generado.
    """
    from playwright.sync_api import sync_playwright

    # Limpiar surrogates que lxml/BS4 puede introducir al serializar el HTML
    clean_html = html.encode("utf-8", errors="surrogatepass").decode("utf-8", errors="replace")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.set_content(clean_html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                print_background=True,
                prefer_css_page_size=True,
            )
        finally:
            browser.close()

    if output_path:
        Path(output_path).write_bytes(pdf_bytes)

    return pdf_bytes
