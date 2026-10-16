# Ashwin Iyer · Resume

[Download the one-page PDF](Ashwin_Iyer_CV.pdf) · [Plain text](docs/resume.txt) · [Accessible HTML](docs/index.html) · [Portfolio](https://ashwiniyer.com)

The authored LaTeX is the source of truth. This repository includes a one-page PDF and a responsive HTML/text version generated from exactly that source. Education, employers, dates, metrics, and project descriptions are preserved as authored; the build checks are consistency checks, not independent verification of those claims.

To read the HTML locally, open `docs/index.html` in a browser or run `python -m http.server 8000` from this directory and visit http://localhost:8000/docs/. It has semantic headings and lists, section navigation, keyboard focus styles, flexible mobile layout, and PDF/plain-text downloads. It does not require JavaScript or external fonts. GitHub's file viewer displays HTML source; download or serve the file to see the rendered resume.

## Update once, export consistently

Edit [`Ashwin_Iyer_CV.tex`](Ashwin_Iyer_CV.tex), then regenerate the web and text versions:

```sh
python scripts/export_accessible.py
python scripts/export_accessible.py --check
```

This renderer supports the small LaTeX subset used by this document. It handles nested emphasis, HTTPS links, escaped percent signs, sections, subsections, and bullets. Unknown commands or document structure fail explicitly instead of silently dropping resume content. Add renderer support and tests when introducing new markup.

## Build and verify

Install Python 3.10+ and a configured LuaLaTeX distribution (TeX Live or MiKTeX), then:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/verify_resume.py
python scripts/build.py
```

PowerShell and shell wrappers remain available as `./build.ps1` and `sh build.sh`. The build invokes LuaLaTeX directly, so it does not need `latexmk` or Perl. It compiles twice in a fresh staging directory with shell escape disabled, applies strict checks, and writes verified output to `build/verified/`. A failed build leaves the tracked PDF untouched. Compiler processes have a bounded timeout; MiKTeX's automatic installer is disabled for this command so missing setup produces an actionable failure rather than an unattended install.

- Exactly one US Letter page.
- Successful output marker, no overfull boxes, no missing glyphs or TeX errors.
- Every alphanumeric source token appears in the PDF text layer, with multiplicities preserved; the name comes first.
- All source hyperlinks appear in PDF annotations with their exact targets.
- Correct title/author metadata; generated HTML/text match the current source.

These checks are not an ATS certification or PDF accessibility certification. The semantic HTML is the accessible alternative; the compact PDF is not claimed to be a tagged PDF/UA document. Render the PDF and inspect it after layout changes—text parity alone cannot detect overlap.

### Portable fonts

The authored PDF uses Times New Roman. For an openly distributed font available on Linux/CI, run:

```sh
python scripts/build.py --portable
```

This uses the explicit `portable` class option (TeX Gyre Termes) in the staging copy only. Kerning is disabled for that option because some PDF extractors otherwise split words such as TypeScript and AWS. It does not change the authored source or silently substitute fonts. CI installs LuaLaTeX, required LaTeX packages, and TeX Gyre fonts, then runs the full portable build. TeX versions/platform spacing can change PDF bytes, so reproducibility here means a documented, checked build—not byte-identical output across distributions.

After inspecting the verified result, `python scripts/build.py --publish` (optionally with `--portable`) replaces the tracked PDF only if all checks pass. Commit the source and generated exports together.

On Windows, initialize MiKTeX's LuaLaTeX format and required packages through its normal setup first. This machine's pre-existing MiKTeX format was missing during verification; the existing authored PDF and HTML were verified locally, while the portable compilation is checked in CI.

## Attribution

The layout is derived from Daniil Belyakov's MIT-licensed [McDowell CV class](https://github.com/dnl-blkv/mcdowell-cv), based on Gayle Laakmann McDowell's resume design. Original license headers and [`LICENSE`](LICENSE) are preserved. [`docs/TEMPLATE.md`](docs/TEMPLATE.md) retains the previous template documentation; this repository's build and validation instructions above supersede its old wrapper behavior.
