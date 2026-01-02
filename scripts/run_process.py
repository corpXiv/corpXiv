#!/usr/bin/env python3
"""Wrapper for process_paper that reads from environment variables."""
import sys
import os
import json

sys.path.insert(0, 'scripts')
from process_paper import process_paper

title = os.environ.get('INPUT_TITLE') or None
authors = os.environ.get('INPUT_AUTHORS')
authors = [a.strip() for a in authors.split(',')] if authors else None
abstract = os.environ.get('INPUT_ABSTRACT') or None
category = os.environ.get('INPUT_CATEGORY', 'other')

result = process_paper(
    filepath='temp/paper.pdf',
    category=category,
    title=title,
    authors=authors,
    abstract=abstract
)
print(json.dumps(result))
