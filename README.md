# corpXiv

**An open preprint archive for enterprise practitioners.**

arXiv for industry—where practitioners formalize rigorous thinking into papers, not slide decks.

## Papers
- [ben_button](papers/ai-systems/ben_button.pdf) — corpXiv:2512.00001v1 [ai-systems]


---

## What is corpXiv?

corpXiv is a community-driven repository of technical papers from enterprise practitioners. No paywalls. No gatekeepers. Just rigorous ideas, properly documented.

We believe the best thinking in enterprise technology lives inside companies—trapped in internal wikis, lost in Slack threads, buried in vendor-speak. corpXiv is where that thinking escapes.

---

## Who is this for?

- **Practitioners** who've solved hard problems and want to document them properly
- **Architects** with frameworks worth sharing beyond their org
- **Leaders** who think in systems, not just slides
- **Anyone** tired of blog posts that sacrifice rigor for reach

---

## The Format

All papers follow the **corpXiv style**:

| Element | Specification |
|---------|---------------|
| Layout | 2-column |
| Typeface | Palatino |
| Abstract | Smaller type, italicized |
| Citations | BibTeX, numeric style |
| Format | PDF (LaTeX-compiled preferred) |

The format is the point. Papers demand structure that forces clarity.

---

## How to Contribute

### Option 1: Pull Request (preferred)

```bash
# Fork this repo, then:
git clone https://github.com/YOUR-USERNAME/corpXiv.git
cd corpXiv

# Add your paper to the appropriate category
cp ~/your-paper.pdf papers/data-engineering/

# Submit
git add .
git commit -m "Added: Your Paper Title"
git push origin main
```

Then open a Pull Request.

### Option 2: Submit via Issue

Don't want to deal with Git? Open an Issue with:
- Paper title
- Abstract (100 words max)
- Attach the PDF

A maintainer will add it for you.

---

## Paper Categories

```
papers/
├── data-engineering/
├── ml-ops/
├── enterprise-ai/
├── data-governance/
├── architecture/
└── other/
```

---

## Quality Standards

corpXiv is open, not unfiltered. Papers should:

1. **Solve a real problem** — No thought experiments without grounding
2. **Show the work** — Methodology matters
3. **Be honest about limitations** — We're practitioners, not salespeople
4. **Cite prior art** — Ideas build on ideas

We don't require peer review, but we do require intellectual honesty.

---

## What corpXiv is NOT

- ❌ A blog aggregator
- ❌ A place for vendor whitepapers
- ❌ Academic-only (no PhD required)
- ❌ Gated or monetized

---

## License

All contributions are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). 

Share freely. Cite appropriately.

---

## Maintainers

This project is maintained by the community. Want to help? Open an issue.

---

*"In a world of hot takes, papers endure."*
