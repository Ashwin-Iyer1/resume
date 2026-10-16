"""Validate PDF integrity, text-layer parity, page geometry and optional build log."""
import argparse
from collections import Counter
from pathlib import Path
import re
from pypdf import PdfReader
from export_accessible import ROOT, render
from html.parser import HTMLParser

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        if tag=='a': self.links.append(dict(attrs)['href'])

def validate_log(log):
    matches = re.findall(r'Output written on .*?\((\d+) page', log)
    if not matches: raise ValueError('Missing successful output/page-count marker')
    if matches[-1] != '1': raise ValueError('Resume must have exactly one page')
    if 'Overfull' in log: raise ValueError('Overfull box: inspect layout before publishing')
    if re.search(r'^!|LaTeX Error|Missing character:', log, re.M): raise ValueError('TeX error or missing glyph in log')

def words(text):
    return Counter(re.findall(r'[A-Za-z0-9]+', text.lower()))

def validate_pdf(path, source):
    reader = PdfReader(path, strict=True)
    if len(reader.pages) != 1: raise ValueError('PDF must contain exactly one page')
    page = reader.pages[0]
    if abs(float(page.mediabox.width)-612)>1 or abs(float(page.mediabox.height)-792)>1: raise ValueError('Expected US Letter page')
    text = page.extract_text() or ''
    expected = render(source)[2]
    missing, extra = words(expected)-words(text), words(text)-words(expected)
    if missing or extra: raise ValueError(f'Text-layer/source mismatch: missing={dict(missing)}, extra={dict(extra)}')
    if not text.lstrip().startswith('Ashwin Iyer'): raise ValueError('Name must come first in PDF reading order')
    if reader.metadata.title != 'Ashwin Iyer Resume' or reader.metadata.author != 'Ashwin Iyer': raise ValueError('Missing resume metadata')
    annotations = page.get('/Annots', [])
    if hasattr(annotations, 'get_object'): annotations = annotations.get_object()
    links = [a.get_object().get('/A', {}).get('/URI', '') for a in annotations]
    expected_links=Links(); expected_links.feed(render(source)[0])
    if Counter(map(str,links)) != Counter(expected_links.links): raise ValueError('PDF hyperlinks differ from source')
    return {'pages':1, 'words':sum(words(expected).values()), 'links':len(links)}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--pdf', type=Path, default=ROOT/'Ashwin_Iyer_CV.pdf'); parser.add_argument('--log', type=Path); args=parser.parse_args()
    if args.log: validate_log(args.log.read_text(encoding='utf-8',errors='replace'))
    print(validate_pdf(args.pdf, (ROOT/'Ashwin_Iyer_CV.tex').read_text(encoding='utf-8')))
if __name__ == '__main__': main()
