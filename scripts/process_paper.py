#!/usr/bin/env python3
"""
corpXiv paper processing pipeline.
- Extracts metadata from PDF (title, authors, abstract)
- Validates against guardrails
- Stamps PDF with corpXiv ID
- Generates Scholar-indexed landing page
- Updates papers.yml
- Regenerates sitemap.xml
"""

import sys
import json
import re
import hashlib
import unicodedata
import yaml
from datetime import datetime
from pathlib import Path
from io import BytesIO
from typing import Optional

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# Paths
MANIFEST_PATH = Path('manifest.json')
PAPERS_YAML_PATH = Path('data/papers.yml')
SITEMAP_PATH = Path('sitemap.xml')
TEMPLATES_PATH = Path('_templates')

# Guardrails config
MIN_ABSTRACT_WORDS = 50
MIN_TITLE_LENGTH = 10
MAX_PAPERS_PER_AUTHOR_PER_WEEK = 2


class ExtractionResult:
    def __init__(self):
        self.title: str = ""
        self.authors: list[str] = []
        self.abstract: str = ""
        self.raw_text: str = ""
        self.confidence: dict = {}
    
    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'confidence': self.confidence
        }


class ValidationResult:
    def __init__(self, valid: bool, errors: list[str] = None, warnings: list[str] = None):
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    return {'next_number': 1, 'papers': {}}


def save_manifest(manifest: dict) -> None:
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)


def load_papers_yaml() -> list:
    if PAPERS_YAML_PATH.exists():
        with open(PAPERS_YAML_PATH, 'r') as f:
            return yaml.safe_load(f) or []
    return []


def save_papers_yaml(papers: list) -> None:
    PAPERS_YAML_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PAPERS_YAML_PATH, 'w') as f:
        yaml.dump(papers, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def get_pdf_hash(filepath: str) -> str:
    """Generate SHA256 hash of PDF content."""
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def extract_metadata(filepath: str) -> ExtractionResult:
    """Extract title, authors, and abstract from arXiv-style PDF."""
    result = ExtractionResult()
    
    try:
        reader = PdfReader(filepath)
        
        # Get first page text
        first_page = reader.pages[0]
        text = first_page.extract_text() or ""
        result.raw_text = text
        
        # Try PDF metadata first
        meta = reader.metadata
        if meta:
            if meta.title:
                result.title = meta.title.strip()
                result.confidence['title'] = 'metadata'
            if meta.author:
                # Authors might be comma or semicolon separated
                authors = re.split(r'[;,]', meta.author)
                result.authors = [a.strip() for a in authors if a.strip()]
                result.confidence['authors'] = 'metadata'
        
        # Parse text for title if not in metadata
        if not result.title:
            result.title = extract_title_from_text(text)
            result.confidence['title'] = 'parsed'
        
        # Parse authors from text if not in metadata
        if not result.authors:
            result.authors = extract_authors_from_text(text)
            result.confidence['authors'] = 'parsed'
        
        # Extract abstract
        result.abstract = extract_abstract_from_text(text)
        result.confidence['abstract'] = 'parsed' if result.abstract else 'not_found'
        
    except Exception as e:
        print(f"Error extracting metadata: {e}")
    
    return result


def extract_title_from_text(text: str) -> str:
    """Extract title from first lines of PDF text."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    if not lines:
        return ""
    
    # Title is usually the first substantial line(s) before authors
    # Look for lines that are likely title (before we hit author patterns or Abstract)
    title_lines = []
    for line in lines[:10]:  # Check first 10 lines
        # Stop if we hit abstract or author indicators
        if re.match(r'^abstract', line, re.I):
            break
        if '@' in line or re.match(r'.*\d{4}.*@', line):  # Email = authors
            break
        if re.match(r'^(university|department|school|institute)', line, re.I):
            break
        # Skip very short lines or lines that look like headers
        if len(line) < 5:
            continue
        title_lines.append(line)
        # Title is usually 1-3 lines max
        if len(title_lines) >= 3:
            break
    
    title = ' '.join(title_lines)
    # Clean up
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Truncate if too long
    if len(title) > 200:
        title = title[:200] + "..."
    
    return title


def extract_authors_from_text(text: str) -> list[str]:
    """Extract authors from PDF text."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    authors = []
    
    # Look for lines between title and abstract that contain names
    in_author_section = False
    for i, line in enumerate(lines[:20]):
        # Skip until we're past likely title
        if i < 1:
            continue
        
        # Stop at Abstract
        if re.match(r'^abstract', line, re.I):
            break
        
        # Look for author patterns:
        # - Lines with multiple capitalized names
        # - Lines with commas separating names
        # - Lines before institutional affiliations
        
        # Check if line looks like names
        if re.match(r'^[A-Z][a-z]+(\s+[A-Z]\.?\s*)*[A-Z][a-z]+', line):
            # Split by comma or 'and'
            parts = re.split(r',\s*|\s+and\s+', line)
            for part in parts:
                part = part.strip()
                # Clean up affiliations markers (superscripts, numbers)
                part = re.sub(r'[\d\*†‡§¶]+', '', part).strip()
                if part and len(part) > 3 and not '@' in part:
                    if re.match(r'^[A-Z][a-z]+', part):
                        authors.append(part)
    
    return authors[:10]  # Max 10 authors


def extract_abstract_from_text(text: str) -> str:
    """Extract abstract section from PDF text."""
    # Look for Abstract header
    abstract_match = re.search(
        r'(?:^|\n)\s*(?:ABSTRACT|Abstract)\s*[:\.\n]\s*(.*?)(?=\n\s*(?:1\.?\s*Introduction|INTRODUCTION|Keywords|KEYWORDS|I\.\s|1\s+[A-Z])|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        # Clean up
        abstract = re.sub(r'\s+', ' ', abstract)
        # Remove any trailing keywords section that might have slipped in
        abstract = re.split(r'\bkeywords?\b', abstract, flags=re.I)[0].strip()
        return abstract
    
    return ""


def validate_submission(
    extraction: ExtractionResult,
    filepath: str,
    papers: list,
    manifest: dict
) -> ValidationResult:
    """Run guardrails validation."""
    errors = []
    warnings = []
    
    # Check title
    if not extraction.title or len(extraction.title) < MIN_TITLE_LENGTH:
        errors.append(f"Title too short or missing (minimum {MIN_TITLE_LENGTH} characters)")
    
    # Check authors
    if not extraction.authors:
        warnings.append("Could not extract authors — please provide manually")
    
    # Check abstract
    abstract_words = len(extraction.abstract.split()) if extraction.abstract else 0
    if abstract_words < MIN_ABSTRACT_WORDS:
        errors.append(f"Abstract too short ({abstract_words} words, minimum {MIN_ABSTRACT_WORDS})")
    
    # Check for duplicates (by hash)
    pdf_hash = get_pdf_hash(filepath)
    for paper in papers:
        if paper.get('hash') == pdf_hash:
            errors.append("Duplicate paper — this PDF has already been submitted")
            break
    
    # Check PDF is valid
    try:
        reader = PdfReader(filepath)
        if len(reader.pages) == 0:
            errors.append("PDF has no pages")
    except Exception as e:
        errors.append(f"Invalid PDF file: {e}")
    
    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def generate_corpxiv_id(manifest: dict, category: str) -> tuple[str, str]:
    """Generate new corpXiv ID and return (id, date)."""
    now = datetime.now()
    yymm = now.strftime('%y%m')
    seq = manifest['next_number']
    corpxiv_id = f"{yymm}.{seq:05d}v1"
    date_str = now.strftime('%Y-%m-%d')
    
    manifest['next_number'] = seq + 1
    
    return corpxiv_id, date_str


def create_stamp(corpxiv_id: str, category: str, date_str: str, page_width: float, page_height: float) -> BytesIO:
    """Create arXiv-style vertical stamp."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%-d %b %Y')
    
    c.saveState()
    c.setFont("Times-Roman", 18)
    c.setFillColor(HexColor('#444444'))
    
    watermark_text = f"corpXiv:{corpxiv_id} [{category}] {formatted_date}"
    
    c.translate(18, page_height / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, watermark_text)
    c.restoreState()
    
    c.save()
    buffer.seek(0)
    return buffer


def stamp_pdf(filepath: str, corpxiv_id: str, category: str, date_str: str) -> None:
    """Apply corpXiv stamp to PDF."""
    reader = PdfReader(filepath)
    writer = PdfWriter()
    
    first_page = reader.pages[0]
    page_width = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)
    
    stamp_buffer = create_stamp(corpxiv_id, category, date_str, page_width, page_height)
    stamp_reader = PdfReader(stamp_buffer)
    stamp_page = stamp_reader.pages[0]
    
    first_page.merge_page(stamp_page)
    writer.add_page(first_page)
    
    for page in reader.pages[1:]:
        writer.add_page(page)
    
    with open(filepath, 'wb') as f:
        writer.write(f)


def generate_landing_page(
    corpxiv_id: str,
    title: str,
    authors: list[str],
    date_str: str,
    abstract: str,
    category: str,
    pdf_filename: str,
    slug: str,
    output_dir: Path
) -> None:
    """Generate Scholar-indexed HTML landing page."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Format date for display
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    display_date = date_obj.strftime('%B %d, %Y')
    scholar_date = date_obj.strftime('%Y/%m/%d')
    
    # Format authors
    authors_meta = '\n  '.join([f'<meta name="citation_author" content="{a}">' for a in authors])
    authors_display = ', '.join(authors) if authors else 'Unknown'
    
    # Escape for HTML
    title_escaped = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    abstract_escaped = abstract.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_escaped} | corpXiv</title>
  
  <!-- Google Scholar metadata -->
  <meta name="citation_title" content="{title_escaped}">
  {authors_meta}
  <meta name="citation_publication_date" content="{scholar_date}">
  <meta name="citation_online_date" content="{scholar_date}">
  <meta name="citation_pdf_url" content="https://corpxiv.github.io/corpXiv/papers/{category}/{slug}/{pdf_filename}">
  <meta name="citation_abstract" content="{abstract_escaped}">
  <meta name="citation_publisher" content="corpXiv">
  
  <!-- Dublin Core metadata -->
  <meta name="DC.title" content="{title_escaped}">
  <meta name="DC.creator" content="{authors_display}">
  <meta name="DC.date" content="{date_str}">
  <meta name="DC.type" content="Technical Report">
  <meta name="DC.format" content="application/pdf">
  <meta name="DC.publisher" content="corpXiv">
  
  <style>
    :root {{
      --primary: #1a1a2e;
      --accent: #4a6fa5;
      --bg: #fafafa;
      --text: #2d2d2d;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Palatino Linotype', Palatino, 'Book Antiqua', Georgia, serif;
      line-height: 1.6;
      color: var(--text);
      background: var(--bg);
      max-width: 800px;
      margin: 0 auto;
      padding: 2rem;
    }}
    header {{
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 2px solid var(--primary);
    }}
    header a {{
      color: var(--primary);
      text-decoration: none;
      font-size: 1.4rem;
      letter-spacing: 0.05em;
    }}
    .back-link {{
      display: inline-block;
      margin-bottom: 1.5rem;
      color: var(--accent);
      text-decoration: none;
      font-size: 0.9rem;
    }}
    .back-link:hover {{ text-decoration: underline; }}
    h1 {{
      font-size: 1.5rem;
      color: var(--primary);
      line-height: 1.3;
      margin-bottom: 0.75rem;
      font-weight: normal;
    }}
    .meta {{
      color: #666;
      font-size: 0.95rem;
      margin-bottom: 1.5rem;
    }}
    .meta .authors {{ font-style: italic; }}
    .abstract {{
      background: white;
      border-left: 3px solid var(--accent);
      padding: 1rem 1.5rem;
      margin: 1.5rem 0;
    }}
    .abstract h2 {{
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--accent);
      margin-bottom: 0.5rem;
      font-weight: normal;
    }}
    .abstract p {{ text-align: justify; }}
    .download-btn {{
      display: inline-block;
      background: var(--accent);
      color: white;
      padding: 0.75rem 1.5rem;
      text-decoration: none;
      border-radius: 4px;
      margin-top: 1rem;
    }}
    .download-btn:hover {{ background: #3a5f95; }}
    .identifier {{
      font-family: monospace;
      font-size: 0.85rem;
      color: #666;
      margin-top: 1.5rem;
    }}
    footer {{
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid #ddd;
      font-size: 0.85rem;
      color: #666;
    }}
  </style>
</head>
<body>
  <header>
    <a href="https://corpxiv.github.io/corpXiv/">corpXiv</a>
  </header>
  
  <main>
    <a href="https://corpxiv.github.io/corpXiv/" class="back-link">← All papers</a>
    
    <article>
      <h1>{title_escaped}</h1>
      
      <div class="meta">
        <span class="authors">{authors_display}</span>
        <span> · {display_date}</span>
      </div>
      
      <div class="abstract">
        <h2>Abstract</h2>
        <p>{abstract_escaped}</p>
      </div>
      
      <a href="{pdf_filename}" class="download-btn">Download PDF</a>
      
      <p class="identifier">corpXiv:{corpxiv_id} [{category}]</p>
    </article>
  </main>
  
  <footer>
    <p>Licensed under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a></p>
  </footer>
</body>
</html>'''
    
    output_file = output_dir / 'index.html'
    output_file.write_text(html)


def add_to_papers_yaml(
    corpxiv_id: str,
    title: str,
    authors: list[str],
    date_str: str,
    abstract: str,
    category: str,
    slug: str,
    pdf_filename: str,
    pdf_hash: str
) -> None:
    """Add paper entry to papers.yml."""
    papers = load_papers_yaml()
    
    entry = {
        'id': corpxiv_id,
        'title': title,
        'authors': authors,
        'date': date_str,
        'category': category,
        'slug': slug,
        'abstract': abstract,
        'pdf': pdf_filename,
        'hash': pdf_hash
    }
    
    papers.insert(0, entry)  # Newest first
    save_papers_yaml(papers)


def generate_sitemap() -> None:
    """Regenerate sitemap.xml from papers.yml."""
    papers = load_papers_yaml()
    today = datetime.now().strftime('%Y-%m-%d')
    
    sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://corpxiv.github.io/corpXiv/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
'''
    
    for paper in papers:
        category = paper.get('category', 'other')
        slug = paper.get('slug', '')
        date = paper.get('date', today)
        
        sitemap += f'''  <url>
    <loc>https://corpxiv.github.io/corpXiv/papers/{category}/{slug}/</loc>
    <lastmod>{date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
'''
    
    sitemap += '</urlset>\n'
    
    SITEMAP_PATH.write_text(sitemap)
    print("Sitemap regenerated", file=sys.stderr)


def title_to_slug(title: str) -> str:
    """Convert title to URL-friendly slug."""
    # Normalize unicode
    slug = unicodedata.normalize('NFKD', title)
    # Lowercase
    slug = slug.lower()
    # Replace spaces and special chars with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Limit length
    slug = slug[:60]
    return slug


def process_paper(
    filepath: str,
    category: str,
    title: Optional[str] = None,
    authors: Optional[list[str]] = None,
    abstract: Optional[str] = None
) -> dict:
    """
    Full pipeline: extract, validate, stamp, generate.
    
    Returns dict with status and details.
    """
    path = Path(filepath)
    
    # Extract metadata from PDF
    extraction = extract_metadata(filepath)
    
    # Override with provided values
    if title:
        extraction.title = title
    if authors:
        extraction.authors = authors
    if abstract:
        extraction.abstract = abstract
    
    # Load existing data
    papers = load_papers_yaml()
    manifest = load_manifest()
    
    # Validate
    validation = validate_submission(extraction, filepath, papers, manifest)
    
    if not validation.valid:
        return {
            'status': 'error',
            'errors': validation.errors,
            'warnings': validation.warnings,
            'extraction': extraction.to_dict()
        }
    
    # Generate ID and slug
    corpxiv_id, date_str = generate_corpxiv_id(manifest, category)
    slug = title_to_slug(extraction.title)
    
    # Stamp PDF
    stamp_pdf(filepath, corpxiv_id, category, date_str)
    
    # Generate landing page (nested: category/slug)
    output_dir = Path('papers') / category / slug
    pdf_filename = f"{slug}.pdf"
    
    generate_landing_page(
        corpxiv_id=corpxiv_id,
        title=extraction.title,
        authors=extraction.authors,
        date_str=date_str,
        abstract=extraction.abstract,
        category=category,
        pdf_filename=pdf_filename,
        slug=slug,
        output_dir=output_dir
    )
    
    # Add to papers.yml
    pdf_hash = get_pdf_hash(filepath)
    add_to_papers_yaml(
        corpxiv_id=corpxiv_id,
        title=extraction.title,
        authors=extraction.authors,
        date_str=date_str,
        abstract=extraction.abstract,
        category=category,
        slug=slug,
        pdf_filename=pdf_filename,
        pdf_hash=pdf_hash
    )
    
    # Update manifest
    save_manifest(manifest)
    
    # Regenerate sitemap
    generate_sitemap()
    
    return {
        'status': 'success',
        'corpxiv_id': corpxiv_id,
        'slug': slug,
        'title': extraction.title,
        'authors': extraction.authors,
        'abstract': extraction.abstract,
        'category': category,
        'date': date_str,
        'warnings': validation.warnings
    }


def extract_only(filepath: str) -> dict:
    """Extract metadata without processing. For confirmation step."""
    extraction = extract_metadata(filepath)
    return extraction.to_dict()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='corpXiv paper processor')
    parser.add_argument('command', choices=['extract', 'process', 'sitemap'])
    parser.add_argument('filepath', nargs='?', help='Path to PDF')
    parser.add_argument('--category', default='other', help='Paper category')
    parser.add_argument('--title', help='Override title')
    parser.add_argument('--authors', help='Override authors (comma-separated)')
    parser.add_argument('--abstract', help='Override abstract')
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        if not args.filepath:
            print("Error: filepath required for extract")
            sys.exit(1)
        result = extract_only(args.filepath)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'process':
        if not args.filepath:
            print("Error: filepath required for process")
            sys.exit(1)
        authors = args.authors.split(',') if args.authors else None
        result = process_paper(
            filepath=args.filepath,
            category=args.category,
            title=args.title,
            authors=authors,
            abstract=args.abstract
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == 'sitemap':
        generate_sitemap()
