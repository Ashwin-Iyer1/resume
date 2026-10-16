"""Compile in a fresh staging directory; publish only after all checks pass."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import uuid
from export_accessible import ROOT, artifacts
from verify_resume import validate_log, validate_pdf

def run(command, cwd, timeout=120):
    process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', start_new_session=os.name!='nt')
    try:
        output,_ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # Only terminate this build's process tree, never a user's other TeX session.
        if os.name=='nt': subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
        else: os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise RuntimeError('Compiler timed out. Initialize the TeX distribution and installed fonts before rebuilding.')
    if process.returncode: raise RuntimeError(output[-6000:] or 'Compiler failed without diagnostics')
    return output

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--portable',action='store_true',help='Use TeX Gyre Termes without changing authored source'); parser.add_argument('--publish',action='store_true',help='Replace tracked PDF only after validation'); args=parser.parse_args()
    engine=shutil.which('lualatex')
    if not engine: raise SystemExit('lualatex not found. Install TeX Live or configure MiKTeX; Perl/latexmk is not required.')
    version=run([engine,'--version'],ROOT,15)
    if 'MiKTeX' in version:
        finder=shutil.which('kpsewhich')
        if not finder: raise RuntimeError('MiKTeX kpsewhich is missing; finish configuring the TeX distribution first.')
        found=subprocess.run([finder,'lualatex.fmt'],capture_output=True,text=True,timeout=15)
        if found.returncode or not found.stdout.strip():
            raise RuntimeError('Missing lualatex.fmt. Initialize LuaLaTeX in MiKTeX Console before building; no installer was launched and the published PDF is unchanged.')
    source=(ROOT/'Ashwin_Iyer_CV.tex').read_text(encoding='utf-8')
    compile_source=source
    if args.portable:
        compile_source,count=re.subn(r'\\documentclass\[\]\{mcdowellcv\}',r'\\documentclass[portable]{mcdowellcv}',source)
        if count!=1: raise SystemExit('Portable build expects one explicit empty documentclass option list')
    stage=ROOT/'build'/('run-'+uuid.uuid4().hex)
    stage.mkdir(parents=True)
    (stage/'Ashwin_Iyer_CV.tex').write_text(compile_source,encoding='utf-8')
    shutil.copy2(ROOT/'mcdowellcv.cls',stage/'mcdowellcv.cls')
    flags=['--disable-installer'] if 'MiKTeX' in version else []
    command=[engine,*flags,'-interaction=nonstopmode','-halt-on-error','-file-line-error','-no-shell-escape','Ashwin_Iyer_CV.tex']
    for i in (1,2):
        output=run(command,stage)
        (stage/f'compiler-{i}.txt').write_text(output,encoding='utf-8')
    log=(stage/'Ashwin_Iyer_CV.log').read_text(encoding='utf-8',errors='replace')
    validate_log(log)
    report=validate_pdf(stage/'Ashwin_Iyer_CV.pdf',source)
    report.update(font='TeX Gyre Termes' if args.portable else 'Times New Roman',published=args.publish)
    target=ROOT/'build'/'verified'; target.mkdir(exist_ok=True)
    for name in ('Ashwin_Iyer_CV.pdf','Ashwin_Iyer_CV.log'): shutil.copy2(stage/name,target/name)
    (target/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if args.publish:
        pending=ROOT/'build'/'publish.pdf'; shutil.copy2(stage/'Ashwin_Iyer_CV.pdf',pending); os.replace(pending,ROOT/'Ashwin_Iyer_CV.pdf')
    page,plain=artifacts(source,(ROOT/'scripts/resume.css').read_text(encoding='utf-8'))
    (ROOT/'docs').mkdir(exist_ok=True)
    (ROOT/'docs/index.html').write_text(page,encoding='utf-8',newline='\n')
    (ROOT/'docs/resume.txt').write_text(plain,encoding='utf-8',newline='\n')
    print(json.dumps(report,indent=2)); print('Verified artifacts: '+str(target))
if __name__=='__main__':
    try: main()
    except (ValueError,RuntimeError) as error: raise SystemExit(str(error))
