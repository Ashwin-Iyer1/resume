"""Deterministic, deliberately narrow renderer for this resume's LaTeX subset.

Unknown commands fail closed so a new credential cannot silently disappear.
This is not a general TeX interpreter and never executes TeX or shell commands.
"""
from pathlib import Path
import argparse
import hashlib
import html
from html.parser import HTMLParser
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

def uncomment(source):
    return re.sub(r'(?<!\\)%[^\n]*', '', source)

def group(source, pos):
    while pos < len(source) and source[pos].isspace(): pos += 1
    if pos >= len(source) or source[pos] != '{': raise ValueError('Expected braced argument')
    start = pos + 1
    depth = 1
    pos += 1
    while pos < len(source):
        if source[pos] == '\\': pos += 2; continue
        if source[pos] == '{': depth += 1
        if source[pos] == '}': depth -= 1
        if not depth: return source[start:pos], pos + 1
        pos += 1
    raise ValueError('Unclosed braced argument')

def inline(source):
    result = []
    i = 0
    while i < len(source):
        if source[i] == '{':
            value, i = group(source, i); result.append(inline(value)); continue
        if source[i] == '}': raise ValueError('Unmatched closing brace')
        if source[i] != '\\':
            result.append(html.escape(source[i])); i += 1; continue
        i += 1
        if i >= len(source): raise ValueError('Trailing escape')
        if source[i] in '&%_#$': result.append(html.escape(source[i])); i += 1; continue
        match = re.match(r'[A-Za-z]+', source[i:])
        if not match: raise ValueError('Unsupported TeX escape')
        command = match.group(); i += len(command)
        if command in ('RaggedRight', 'makeheader'): continue
        if command == 'vspace':
            _, i = group(source, i); continue
        if command not in ('textbf', 'textit', 'underline', 'href', 'hfill'): raise ValueError('Unsupported command: ' + command)
        value, i = group(source, i)
        if command == 'href':
            label, i = group(source, i)
            url = value.replace(r'\%', '%').replace(r'\&', '&').replace(r'\_', '_')
            if urlsplit(url).scheme not in ('https', 'mailto', 'tel'): raise ValueError('Unsafe link scheme')
            result.append('<a href="' + html.escape(url, quote=True) + '">' + inline(label) + '</a>')
        else:
            tag = {'textbf':'strong','textit':'em','underline':'span','hfill':'span'}[command]
            attr = ' class="date"' if command == 'hfill' else ''
            result.append('<' + tag + attr + '>' + inline(value) + '</' + tag + '>')
    return ''.join(result).replace('---', '—').replace('--', '–')

def paragraphs(source, projects=False):
    source = re.sub(r'\\vspace\*?\{[^}]*\}', '\n\n', source)
    result = []
    for paragraph in re.split(r'\n\s*\n', source.strip()):
        if not paragraph.strip(): continue
        # Authored source lines are semantic lines, not hard-wrapped prose.
        for line in paragraph.strip().splitlines():
            line = line.strip()
            if not line: continue
            tag = 'h3' if projects and r'\hfill{' in line else 'p'
            result.append('<' + tag + '>' + inline(line) + '</' + tag + '>')
    return '\n'.join(result)

def blocks(source, projects=False):
    result = []
    parts = re.split(r'(\\begin\{itemize\}.*?\\end\{itemize\})', source, flags=re.S)
    for part in parts:
        if part.startswith(r'\begin{itemize}'):
            body = part[len(r'\begin{itemize}'):-len(r'\end{itemize}')]
            items = re.split(r'\\item\s+', body)
            if items[0].strip(): raise ValueError('Unexpected content before first list item')
            result.append('<ul>' + ''.join('<li>' + inline(' '.join(item.split())) + '</li>' for item in items[1:]) + '</ul>')
        else: result.append(paragraphs(part, projects))
    return '\n'.join(result)

class TextOnly(HTMLParser):
    def __init__(self): super().__init__(); self.parts = []
    def handle_data(self, data): self.parts.append(data)
    def handle_starttag(self, tag, attrs):
        if tag in ('p','li','h1','h2','h3','section','div','header'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('p','li','h1','h2','h3','section','div','header'): self.parts.append('\n')

def text_only(markup):
    parser = TextOnly(); parser.feed(markup)
    return re.sub(r'\n\s*\n+', '\n\n', ''.join(parser.parts)).strip() + '\n'

def render(source):
    source = uncomment(source)
    def metadata(name):
        match = re.search(r'\\' + name + r'\s*\{', source)
        if not match: raise ValueError('Missing ' + name)
        return group(source, match.end() - 1)[0]
    name = inline(metadata('name'))
    header = '<header><h1>' + name + '</h1><p>' + inline(metadata('address')) + ' | ' + inline(metadata('contacts')) + '</p></header>'
    document = source.split(r'\begin{document}', 1)[1].split(r'\end{document}', 1)[0]
    section_pattern = re.compile(r'\\begin\{cvsection\}\{([^}]+)\}(.*?)\\end\{cvsection\}', re.S)
    sections, navigation = [], []
    for section in section_pattern.finditer(document):
        title, body = section.groups(); slug = title.lower().replace(' ', '-')
        navigation.append('<a href="#' + slug + '">' + html.escape(title.title()) + '</a>')
        entries = []
        while body.strip():
            body = re.sub(r'^\s*\\vspace\*?\{[^}]*\}', '', body).strip()
            if not body: break
            prefix = r'\begin{cvsubsection}'
            if not body.startswith(prefix): raise ValueError('Unexpected section content: ' + body[:50])
            pos = len(prefix)
            if body[pos:pos+1] == '[': raise ValueError('Optional cvsubsection arguments need renderer support')
            left, pos = group(body, pos); center, pos = group(body, pos); right, pos = group(body, pos)
            end = body.find(r'\end{cvsubsection}', pos)
            if end < 0: raise ValueError('Unclosed subsection')
            heading = ('<div class="entry-heading"><h3>' + inline(left) + '</h3><p class="date">' + inline(right) + '</p></div>') if left else ''
            if center: heading += '<p>' + inline(center) + '</p>'
            entries.append('<article>' + heading + blocks(body[pos:end], title == 'PROJECTS') + '</article>')
            body = body[end+len(r'\end{cvsubsection}'):]
        sections.append('<section id="' + slug + '"><h2>' + html.escape(title.title()) + '</h2>' + '\n'.join(entries) + '</section>')
    # Fail if unknown document structure would otherwise be silently omitted.
    residue = section_pattern.sub('', document)
    if text_only(inline(residue)).strip(): raise ValueError('Unrendered document content')
    if len(sections) != 5: raise ValueError('Expected all five resume sections')
    content = header + '\n' + '\n'.join(sections)
    return content, ''.join(navigation), text_only(content)

def artifacts(source, stylesheet):
    content, nav, plain = render(source)
    source_hash = hashlib.sha256(source.encode()).hexdigest()
    page = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Ashwin Iyer resume: education, experience, skills, and projects."><title>Ashwin Iyer · Resume</title><style>' + stylesheet + '</style></head><body><a class="skip" href="#resume">Skip to resume</a><div class="toolbar"><a href="../Ashwin_Iyer_CV.pdf">Download PDF</a><a href="resume.txt" download>Plain text</a><a href="https://ashwiniyer.com">Portfolio ↗</a></div><nav aria-label="Resume sections">' + nav + '</nav><main id="resume">' + content + '</main><footer>Generated from the authored LaTeX source. <a href="../Ashwin_Iyer_CV.tex">View source</a> · <a href="../LICENSE">Template license</a></footer><!-- source-sha256: ' + source_hash + ' --></body></html>\n'
    return page, plain

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    source = (ROOT/'Ashwin_Iyer_CV.tex').read_text(encoding='utf-8')
    page, plain = artifacts(source, (ROOT/'scripts/resume.css').read_text(encoding='utf-8'))
    for name, value in [('index.html', page), ('resume.txt', plain)]:
        path = ROOT/'docs'/name
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != value: raise SystemExit('Stale generated file: ' + str(path))
        else: path.parent.mkdir(exist_ok=True); path.write_text(value, encoding='utf-8', newline='\n')
    print('Accessible HTML and text ' + ('match source.' if args.check else 'generated.'))
if __name__ == '__main__': main()
