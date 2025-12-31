#!/usr/bin/env python3
"""
Stamps PDFs with corpXiv metadata - arXiv style.
- Sequential reference numbers (corpXiv:2501.00001v1)
- Red vertical watermark on left edge
- Footer on page 1
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

MANIFEST_PATH = Path('manifest.json')


def load_manifest() -> dict:
    """Load or create the manifest file."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    return {'next_number': 1, 'papers': {}}


def save_manifest(manifest: dict) -> None:
    """Save the manifest file."""
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)


def get_corpxiv_id(filepath: str, manifest: dict) -> tuple[str, str]:
    """
    Generate or retrieve corpXiv ID.
    Returns (full_id, category)
    Format: 2501.00001v1
    """
    path = Path(filepath)
    relative = str(path.relative_to('papers'))
    category = path.parent.name  # e.g., 'ai-systems'
    
    # Check if already assigned
    if relative in manifest['papers']:
        entry = manifest['papers'][relative]
        return entry['id'], category
    
    # Generate new ID
    now = datetime.now()
    yymm = now.strftime('%y%m')  # e.g., '2501' for Jan 2025
    seq = manifest['next_number']
    corpxiv_id = f"{yymm}.{seq:05d}v1"
    
    # Save to manifest
    manifest['papers'][relative] = {
        'id': corpxiv_id,
        'category': category,
        'submitted': now.strftime('%Y-%m-%d'),
        'filename': path.name
    }
    manifest['next_number'] = seq + 1
    
    return corpxiv_id, category


def create_stamp(corpxiv_id: str, category: str, date_str: str, page_width: float, page_height: float) -> BytesIO:
    """Create a PDF overlay with arXiv-style stamp."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    
    # Format date like arXiv: "1 Jan 2025"
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%-d %b %Y')
    
    # --- FOOTER (bottom of page 1) ---
    margin = 40
    y_position = 25
    
    # Draw line
    c.setStrokeColor(HexColor('#999999'))
    c.setLineWidth(0.5)
    c.line(margin, y_position + 15, page_width - margin, y_position + 15)
    
    # Draw footer text
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor('#666666'))
    
    footer_text = f"corpXiv:{corpxiv_id} [{category}] {formatted_date} | github.com/corpXiv/corpXiv"
    c.drawString(margin, y_position, footer_text)
    
    # --- VERTICAL WATERMARK (left edge, arXiv style) ---
    c.saveState()
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(HexColor('#CC0000'))  # arXiv red
    
    watermark_text = f"corpXiv:{corpxiv_id} [{category}] {formatted_date}"
    
    # Rotate and position on left edge
    c.translate(12, page_height / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, watermark_text)
    c.restoreState()
    
    c.save()
    buffer.seek(0)
    return buffer


def stamp_pdf(filepath: str, manifest: dict) -> None:
    """Add corpXiv stamp to a PDF."""
    print(f"Stamping: {filepath}")
    
    reader = PdfReader(filepath)
    writer = PdfWriter()
    
    first_page = reader.pages[0]
    page_width = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)
    
    corpxiv_id, category = get_corpxiv_id(filepath, manifest)
    date_str = manifest['papers'][str(Path(filepath).relative_to('papers'))]['submitted']
    
    stamp_buffer = create_stamp(corpxiv_id, category, date_str, page_width, page_height)
    stamp_reader = PdfReader(stamp_buffer)
    stamp_page = stamp_reader.pages[0]
    
    # Merge stamp onto first page
    first_page.merge_page(stamp_page)
    writer.add_page(first_page)
    
    # Add remaining pages unchanged
    for page in reader.pages[1:]:
        writer.add_page(page)
    
    with open(filepath, 'wb') as f:
        writer.write(f)
    
    print(f"Stamped: {filepath} -> corpXiv:{corpxiv_id} [{category}]")


def main():
    if len(sys.argv) < 2:
        print("No PDFs to stamp")
        return
    
    manifest = load_manifest()
    
    for filepath in sys.argv[1:]:
        filepath = filepath.strip()
        if filepath and filepath.endswith('.pdf') and Path(filepath).exists():
            try:
                stamp_pdf(filepath, manifest)
            except Exception as e:
                print(f"Error stamping {filepath}: {e}")
    
    save_manifest(manifest)


if __name__ == '__main__':
    main()
