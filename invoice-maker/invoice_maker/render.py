"""Generic PDF renderer: builds a document for any registered template."""

from __future__ import annotations

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from .templates import get_template


def render_invoice(template_name: str, config, invoice, output_path: str) -> str:
    """Build the invoice PDF for ``template_name`` at ``output_path``."""
    spec = get_template(template_name)
    if spec.prepare:
        spec.prepare(config, invoice)
    meta = spec.doc_meta(config, invoice)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=spec.margins["left"],
        rightMargin=spec.margins["right"],
        topMargin=spec.margins["top"],
        bottomMargin=spec.margins["bottom"],
        title=meta.get("title", ""),
        author=meta.get("author", ""),
    )
    doc.build(spec.build(config, invoice))
    return output_path


def invoice_filename(template_name: str, config, invoice) -> str:
    return get_template(template_name).filename(config, invoice)
