#!/usr/bin/env python3
"""
Stamps PDFs with corpXiv metadata footer on page 1.
Usage: python stamp_pdf.py paper1.pdf paper2.pdf ...
"""

import sys
from datetime import datetime
from pathlib import Path
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor


def create_stamp(corpxiv_id: str, date: str, page_width: float, page_height: float) -> BytesIO:
    """Create a PDF overlay with the corpXiv stamp."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    
    # Footer positioning
    margin = 40
    y_position = 30
    
    # Draw line
    c.setStrokeColor(HexColor('#666666'))
    c.setLineWidth(0.5)
    c.line(margin, y_position + 20, page_width - margin, y_position + 20)
    
    # Draw text
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))
    
    stamp_text = f"corpXiv:{corpxiv_id}"
    c.drawString(margin, y_position + 5, stamp_text)
    
    meta_text = f"Submitted: {date} | github.com/corpXiv/corpXiv"
    c.drawRightString(page_width - margin, y_position + 5, meta_text)
    
    c.save()
    buffer.seek(0)
    return buffer


def get_corpxiv_id(filepath: str) -> str:
    """Generate corpXiv ID from file path."""
    # papers/data-architecture/semantic-mvcc.pdf -> data-architecture/semantic-mvcc
    path = Path(filepath)
    relative = path.relative_to('papers')
    return str(relative.with_suffix(''))


def stamp_pdf(filepath: str) -> None:
    """Add corpXiv stamp to a PDF."""
    print(f"Stamping: {filepath}")
    
    # Read original PDF
    reader = PdfReader(filepath)
    writer = PdfWriter()
    
    # Get first page dimensions
    first_page = reader.pages[0]
    page_width = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)
    
    # Generate stamp
    corpxiv_id = get_corpxiv_id(filepath)
    date = datetime.now().strftime('%Y-%m-%d')
    stamp_buffer = create_stamp(corpxiv_id, date, page_width, page_height)
    stamp_pdf = PdfReader(stamp_buffer)
    stamp_page = stamp_pdf.pages[0]
    
    # Merge stamp onto first page
    first_page.merge_page(stamp_page)
    writer.add_page(first_page)
    
    # Add remaining pages unchanged
    for page in reader.pages[1:]:
        writer.add_page(page)
    
    # Write stamped PDF
    with open(filepath, 'wb') as f:
        writer.write(f)
    
    print(f"Stamped: {filepath} -> corpXiv:{corpxiv_id}")


def main():
    if len(sys.argv) < 2:
        print("No PDFs to stamp")
        return
    
    for filepath in sys.argv[1:]:
        filepath = filepath.strip()
        if filepath and filepath.endswith('.pdf') and Path(filepath).exists():
            try:
                stamp_pdf(filepath)
            except Exception as e:
                print(f"Error stamping {filepath}: {e}")


if __name__ == '__main__':
    main()
