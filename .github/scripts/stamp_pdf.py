#!/usr/bin/env python3
"""
Stamps PDFs with corpXiv ID and auto-updates README.
"""

import sys
import json
import re
from datetime import datetime
from pathlib import Path
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

MANIFEST_PATH = Path('manifest.json')
README_PATH = Path('README.md')


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    return {'next_number': 1, 'papers': {}}


def save_manifest(manifest: dict) -> None:
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)


def extract_title(filepath: str) -> str:
    """Try to extract title from PDF, fall back to filename."""
    try:
        reader = PdfReader(filepath)
        # Try metadata first
        if reader.metadata and reader.metadata.title:
            return reader.metadata.title
        # Try first line of text
        first_page = reader.pages[0]
        text = first_page.extract_text()
        if text:
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if lines:
                # First non-empty line is often the title
                title = lines[0]
                # Clean it up - take first 100 chars max
                if len(title) > 100:
                    title = title[:100] + "..."
                return title
    except:
        pass
    # Fall back to filename
    return Path(filepath).stem.replace('_', ' ').replace('-', ' ')


def get_corpxiv_id(filepath: str, manifest: dict) -> tuple[str, str, str, str]:
    """Returns (id, category, date, title)"""
    path = Path(filepath)
    relative = str(path.relative_to('papers'))
    category = path.parent.name
    
    if relative in manifest['papers']:
        entry = manifest['papers'][relative]
        return entry['id'], category, entry['submitted'], entry.get('title', path.stem)
    
    now = datetime.now()
    yymm = now.strftime('%y%m')
    seq = manifest['next_number']
    corpxiv_id = f"{yymm}.{seq:05d}v1"
    date_str = now.strftime('%Y-%m-%d')
    title = extract_title(filepath)
    
    manifest['papers'][relative] = {
        'id': corpxiv_id,
        'category': category,
        'submitted': date_str,
        'filename': path.name,
        'title': title
    }
    manifest['next_number'] = seq + 1
    
    return corpxiv_id, category, date_str, title


def update_readme(filepath: str, corpxiv_id: str, category: str, title: str):
    """Add paper to README if not already there."""
    path = Path(filepath)
    relative_path = str(path)
    
    # Read current README
    if not README_PATH.exists():
        return
    
    readme = README_PATH.read_text()
    
    # Check if paper already listed
    if relative_path in readme or path.name in readme:
        return
    
    # Find or create Papers section
    papers_header = "## Papers"
    
    if papers_header not in readme:
        # Add Papers section before --- or at end
        if "\n---\n" in readme:
            readme = readme.replace("\n---\n", f"\n{papers_header}\n\n\n---\n", 1)
        else:
            readme += f"\n\n{papers_header}\n\n"
    
    # Add the paper entry
    paper_line = f"- [{title}]({relative_path}) — corpXiv:{corpxiv_id} [{category}]\n"
    
    # Insert after ## Papers header
    lines = readme.split('\n')
    new_lines = []
    inserted = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        if line.strip() == "## Papers" and not inserted:
            # Add blank line if needed, then the paper
            if i + 1 < len(lines) and lines[i + 1].strip() == "":
                pass  # blank line already there
            else:
                new_lines.append("")
            new_lines.append(paper_line.rstrip())
            inserted = True
    
    if inserted:
        README_PATH.write_text('\n'.join(new_lines))
        print(f"README updated: {title}")


def create_stamp(corpxiv_id: str, category: str, date_str: str, page_width: float, page_height: float) -> BytesIO:
    """Create arXiv-style vertical stamp."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    
    # Format date like arXiv: "7 Jan 2023"
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%-d %b %Y')
    
    # arXiv style: dark gray, Times (serif) 18pt
    c.saveState()
    c.setFont("Times-Roman", 18)
    c.setFillColor(HexColor('#444444'))
    
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
    
    corpxiv_id, category, date_str, title = get_corpxiv_id(filepath, manifest)
    
    stamp_buffer = create_stamp(corpxiv_id, category, date_str, page_width, page_height)
    stamp_reader = PdfReader(stamp_buffer)
    stamp_page = stamp_reader.pages[0]
    
    first_page.merge_page(stamp_page)
    writer.add_page(first_page)
    
    for page in reader.pages[1:]:
        writer.add_page(page)
    
    with open(filepath, 'wb') as f:
        writer.write(f)
    
    # Update README
    update_readme(filepath, corpxiv_id, category, title)
    
    print(f"Stamped: corpXiv:{corpxiv_id} [{category}] — {title}")


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
