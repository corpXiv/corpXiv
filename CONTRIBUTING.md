# Contributing to corpXiv

Thanks for contributing. Here's everything you need to know.

---

## Before You Start

Ask yourself:

1. **Is this a real problem?** — Not a hypothetical or thought experiment
2. **Did you actually do this?** — Theory is fine, but grounded in practice is better
3. **Would you stake your reputation on it?** — Your name goes on this

If yes to all three, keep reading.

---

## The corpXiv Format

All papers must follow the corpXiv style. This isn't arbitrary—the format forces rigor.

### Requirements

| Element | Specification |
|---------|---------------|
| Layout | 2-column |
| Typeface | Palatino (body), Helvetica (headings OK) |
| Paper size | US Letter (8.5" × 11") |
| Margins | 0.75" all sides |
| Abstract | Italicized, smaller type (10pt), max 150 words |
| Body text | 10-11pt |
| Citations | Numeric style, e.g., [1], [2] |
| References | BibTeX preferred |
| File format | PDF |

### Recommended Length

- **Short paper**: 2-4 pages (focused insight, single technique)
- **Full paper**: 5-10 pages (complete methodology, results)
- **No maximum**, but respect the reader's time

---

## LaTeX Template

Use this as your starting point:

```latex
\documentclass[10pt,twocolumn,letterpaper]{article}

% Fonts
\usepackage{palatino}
\usepackage[T1]{fontenc}

% Layout
\usepackage[margin=0.75in]{geometry}
\usepackage{titlesec}
\usepackage{parskip}

% Graphics and tables
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tabularx}

% Citations
\usepackage{cite}

% Hyperlinks (optional, but recommended)
\usepackage[hidelinks]{hyperref}

% Abstract formatting
\renewenvironment{abstract}{
  \small\itshape
  \begin{center}
    \textbf{\abstractname}\vspace{-0.5em}
  \end{center}
  \quotation
}{\endquotation}

% Title formatting
\titleformat{\section}{\normalfont\large\bfseries}{\thesection.}{0.5em}{}
\titleformat{\subsection}{\normalfont\normalsize\bfseries}{\thesubsection.}{0.5em}{}

\begin{document}

% ============================================
% TITLE BLOCK
% ============================================
\title{Your Paper Title Here}
\author{
  Your Name\\
  \textit{Your Affiliation (optional)}\\
  \texttt{your.email@example.com}
}
\date{\today}
\maketitle

% ============================================
% ABSTRACT
% ============================================
\begin{abstract}
Your abstract goes here. Maximum 150 words. State the problem, your approach, and the key insight or result. No citations in the abstract.
\end{abstract}

% ============================================
% BODY
% ============================================
\section{Introduction}

What problem are you solving? Why does it matter? What's your contribution?

\section{Background}

What does the reader need to know? Prior art, context, definitions.

\section{Approach}

What did you do? Be specific enough that someone could reproduce it.

\section{Results}

What happened? Data, observations, outcomes.

\section{Discussion}

What does it mean? Limitations? Surprises?

\section{Conclusion}

So what? What should the reader take away?

% ============================================
% REFERENCES
% ============================================
\bibliographystyle{plain}
\bibliography{references}  % or use \begin{thebibliography} for manual entries

\end{document}
```

Save this as `corpxiv-template.tex`.

---

## Paper Structure

A good corpXiv paper typically includes:

### Required Sections

1. **Title** — Clear, specific, no clickbait
2. **Author(s)** — Name and contact; affiliation optional
3. **Abstract** — 150 words max; problem, approach, result
4. **Introduction** — Why this matters
5. **Approach/Methodology** — What you did
6. **Conclusion** — The takeaway

### Optional Sections

- **Background** — If the reader needs context
- **Results** — If you have data or outcomes
- **Discussion** — If there's nuance to unpack
- **Acknowledgments** — Credit where due
- **References** — Cite your sources

---

## Submission Process

### Option 1: Pull Request (preferred)

```bash
# 1. Fork this repo on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/corpXiv.git
cd corpXiv

# 3. Add your paper to the right category
cp ~/my-paper.pdf papers/data-engineering/my-paper.pdf

# 4. Commit and push
git add .
git commit -m "Added: My Paper Title"
git push origin main

# 5. Open a Pull Request on GitHub
```

Your PR should include:
- The PDF in the correct category folder
- A one-line description of the paper

### Option 2: Submit via Issue

If Git isn't your thing:

1. Go to **Issues** → **New Issue**
2. Title: `Submission: Your Paper Title`
3. Body: Include your abstract (100 words max)
4. Attach the PDF
5. A maintainer will review and add it

---

## Review Process

corpXiv is **lightly moderated**, not peer-reviewed.

We check for:
- ✅ Follows the format
- ✅ Has a real problem and approach
- ✅ Isn't a vendor whitepaper or advertisement
- ✅ Isn't plagiarized

We don't check for:
- ❌ Whether we agree with your conclusions
- ❌ Academic credentials
- ❌ Perfect grammar

Turnaround: Usually within 1 week.

---

## Updating a Paper

Made improvements? Submit a new version:

1. Name it `my-paper-v2.pdf` (or increment the version)
2. Submit via PR or Issue
3. We'll keep both versions (like arXiv)

---

## Naming Conventions

```
papers/
├── data-engineering/
│   ├── semantic-mvcc-v1.pdf
│   └── semantic-mvcc-v2.pdf
├── ml-ops/
│   └── feature-store-patterns.pdf
└── enterprise-ai/
    └── llm-governance-framework.pdf
```

- Lowercase, hyphenated
- Version suffix if multiple versions: `-v1`, `-v2`
- Descriptive but concise

---

## License

By submitting, you agree to license your work under **CC BY 4.0**.

This means:
- ✅ Anyone can share and adapt your work
- ✅ They must give you credit
- ✅ You retain authorship
- ❌ They can't claim it as their own

---

## Questions?

Open an Issue or reach out to a maintainer.

---

*"The best thinking in enterprise tech shouldn't be locked in internal wikis."*
