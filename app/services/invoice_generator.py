from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pathlib import Path
from datetime import datetime
from uuid import uuid4


def generate_invoice_pdf(data: dict, save_dir: Path) -> str:
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = f"invoice_{uuid4().hex}.pdf"
    file_path = save_dir / filename

    c = canvas.Canvas(str(file_path), pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "INVOICE")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Client: {data['client_name']} <{data['client_email']}>")
    c.drawString(50, height - 120, f"Project: {data['title']}")
    c.drawString(50, height - 140, f"Description: {data['description']}")
    c.drawString(50, height - 160, f"Status: {data['status']}")
    c.drawString(50, height - 180, f"Budget: {data['amount']} {data['currency']}")
    c.drawString(50, height - 200, f"Deadline: {data['deadline']}")
    c.drawString(50, height - 220, f"Invoice #: {data['invoice_number']}")
    c.drawString(50, height - 240, f"Generated: {data['generated_on']}")

    c.save()
    return str(file_path)
