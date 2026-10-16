import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from export_accessible import inline, uncomment, render, artifacts, group
from verify_resume import validate_log, validate_pdf, words
import build

class ResumeTests(unittest.TestCase):
    def setUp(self): self.source=(ROOT/'Ashwin_Iyer_CV.tex').read_text(encoding='utf-8')
    def test_published_pdf_matches_all_source_tokens_and_links(self):
        result=validate_pdf(ROOT/'Ashwin_Iyer_CV.pdf',self.source)
        self.assertEqual(result['pages'],1); self.assertEqual(result['links'],5)
    def test_source_export_is_current_and_semantic(self):
        page,text=artifacts(self.source,(ROOT/'scripts/resume.css').read_text(encoding='utf-8'))
        self.assertEqual(page,(ROOT/'docs/index.html').read_text(encoding='utf-8'))
        self.assertEqual(text,(ROOT/'docs/resume.txt').read_text(encoding='utf-8'))
        self.assertEqual(page.count('<section '),5)
        self.assertEqual(page.count('<li>'),12)
        self.assertIn('Incoming Summer Analyst, Equity Trading',text)
        self.assertNotIn('Availability:',text)
    def test_escaped_percent_and_comments(self):
        self.assertEqual(uncomment('a 40\\% % private note\nb'),'a 40\\% \nb')
        self.assertEqual(inline(r'40\% \& 2--5\%'),'40% &amp; 2–5%')
    def test_nested_formatting_safe_links_and_html_escape(self):
        self.assertEqual(inline(r'\textbf{A \textit{B}}'),'<strong>A <em>B</em></strong>')
        self.assertEqual(inline('<script>'), '&lt;script&gt;')
        self.assertIn('a%20b',inline(r'\href{https://example.test/a\%20b}{Report}'))
        with self.assertRaises(ValueError): inline(r'\href{javascript:alert(1)}{Bad}')
    def test_unknown_markup_and_missing_sections_fail_closed(self):
        for value in [r'\unknown{credential}',r'\textbf{unclosed',r'text}',r'\textbf word']:
            with self.assertRaises(ValueError): inline(value)
        with self.assertRaises(ValueError): render(self.source.replace(r'\begin{cvsection}{INTERESTS}',r'\begin{other}{INTERESTS}'))
    def test_log_must_prove_one_page_and_no_missing_glyphs(self):
        validate_log('Output written on Ashwin_Iyer_CV.pdf (1 page, 999 bytes).')
        for log in ['', 'Output written on cv.pdf (2 pages, 99 bytes).', 'Output written on cv.pdf (1 page).\nOverfull \\hbox', 'Output written on cv.pdf (1 page).\nMissing character: x', '! Fatal error']:
            with self.assertRaises(ValueError): validate_log(log)
    def test_changed_credential_cannot_pass_parity(self):
        with self.assertRaisesRegex(ValueError,'mismatch'): validate_pdf(ROOT/'Ashwin_Iyer_CV.pdf',self.source.replace('GPA: 3.8','GPA: 4.0'))
    def test_altered_pdf_link_is_rejected(self):
        writer=PdfWriter(); writer.clone_document_from_reader(PdfReader(ROOT/'Ashwin_Iyer_CV.pdf'))
        annotations=writer.pages[0]['/Annots']
        annotations[0].get_object()['/A'][NameObject('/URI')]=TextStringObject('https://wrong.invalid')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'synthetic.pdf'
            with path.open('wb') as handle: writer.write(handle)
            with self.assertRaisesRegex(ValueError,'hyperlinks'): validate_pdf(path,self.source)
    def test_uninitialized_miktex_fails_before_compiling_or_publishing(self):
        before=(ROOT/'Ashwin_Iyer_CV.pdf').read_bytes()
        with patch.object(sys,'argv',['build.py','--publish']), patch.object(build.shutil,'which',side_effect=lambda name:name), patch.object(build,'run',return_value='MiKTeX'), patch.object(build.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='')):
            with self.assertRaisesRegex(RuntimeError,'Missing lualatex.fmt'): build.main()
        self.assertEqual(before,(ROOT/'Ashwin_Iyer_CV.pdf').read_bytes())

if __name__=='__main__': unittest.main()
