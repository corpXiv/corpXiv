#!/usr/bin/env python3
"""
Stamps PDFs with corpXiv ID - matching actual arXiv style.
- Dark gray (#444444)
- Times (serif) 18pt
- Left margin, vertical
- Format: corpXiv:2501.00001v1 [ai-systems] 1 Jan 2025
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
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    return {'next_number': 1, 'papers': {}}


def save_manifest(manifest: dict) -> None:
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)


def get_corpxiv_id(filepath: str, manifest: dict) -> tuple[str, str, str]:
    """Returns (id, category, date)"""
    path = Path(filepath)
    relative = str(path.relative_to('papers'))
    category = path.parent.name
    
    if relative in manifest['papers']:
        entry = manifest['papers'][relative]
        return entry['id'], category, entry['submitted']
    
    now = datetime.now()
    yymm = now.strftime('%y%m')
    seq = manifest['next_number']
    corpxiv_id = f"{yymm}.{seq:05d}v1"
    date_str = now.strftime('%Y-%m-%d')
    
    manifest['papers'][relative] = {
        'id': corpxiv_id,
        'category': category,
        'submitted': date_str,
        'filename': path.name
    }
    manifest['next_number'] = seq + 1
    
    return corpxiv_id, category, date_str


def create_stamp(corpxiv_id: str, category: str, date_str: str, page_width: float, page_height: float) -> BytesIO:
    """Create arXiv-style vertical stamp."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    
    # Format date like arXiv: "7 Jan 2023"
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%-d %b %Y')
    
    # arXiv actual style: dark gray, Times (serif) 18pt
    c.saveState()
    c.setFont("Times-Roman", 18)
    c.setFillColor(HexColor('#444444'))  # Dark gray
    
    # Format exactly like arXiv
    watermark_text = f"corpXiv:{corpxiv_id} [{category}] {formatted_date}"
    
    # Position: left edge, centered vertically, rotated 90 degrees
    c.translate(18, page_height / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, watermark_text)
    c.restoreState()
    
    c.save()
    buffer.seek(0)
    return buffer


def stamp_pdf(filepath: str, manifest: dict) -> None:
    print(f"Stamping: {filepath}")
    
    reader = PdfReader(filepath)
    writer = PdfWriter()
    
    first_page = reader.pages[0]
    page_width = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)
    
    corpxiv_id, category, date_str = get_corpxiv_id(filepath, manifest)
    
    stamp_buffer = create_stamp(corpxiv_id, category, date_str, page_width, page_height)
    stamp_reader = PdfReader(stamp_buffer)
    stamp_page = stamp_reader.pages[0]
    
    first_page.merge_page(stamp_page)
    writer.add_page(first_page)
    
    for page in reader.pages[1:]:
        writer.add_page(page)
    
    with open(filepath, 'wb') as f:
        writer.write(f)
    
    print(f"Stamped: corpXiv:{corpxiv_id} [{category}]")


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
