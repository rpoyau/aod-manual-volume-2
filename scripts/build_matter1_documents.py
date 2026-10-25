#!/usr/bin/env python3
"""Clean, paired XeLaTeX build; publishes bound Main and two path-correct Manuals."""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from publication_support import digest, foundation_files, manifest_digest, manual_files, verify_foundation, verify_main_binding, verify_publication, require


def run_latex(directory, filename, log_name):
    command = ['latexmk','-xelatex','-recorder','-interaction=nonstopmode','-halt-on-error',filename]
    with (directory/log_name).open('w') as log:
        result = subprocess.run(command,cwd=directory,stdout=log,stderr=subprocess.STDOUT)
    require(result.returncode == 0, f'LaTeX build failed; inspect {directory/log_name}')
    texlog=(directory/Path(filename).with_suffix('.log')).read_text(errors='replace')
    require('There were undefined references' not in texlog and 'undefined on input line' not in texlog, 'Unresolved reference or citation in '+filename)
    require('Missing character:' not in texlog, 'Missing glyph in '+filename)
    return command


def build(root, work):
    foundation=verify_foundation(root)
    require(not work.exists() or not any(work.iterdir()), 'Build directory must be new or empty')
    work.mkdir(parents=True,exist_ok=True)
    # Only the bound Main source tree and active Manual are build inputs.
    for name in foundation['files']:
        target=work/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/name,target)
    shutil.copytree(root/'manual2',work/'manual2',ignore=shutil.ignore_patterns('*.aux','*.log','*.out','*.toc','*.fls','*.fdb_latexmk','*.xdv','*.synctex.gz','*.bbl','*.blg','*.bcf','*.run.xml','__pycache__','*.pyc','main.pdf','main-root.pdf','main-root.tex'))
    commands=[run_latex(work,'main.tex','main-build-console.txt')]
    # Bind the exact Main run before any downstream release build.
    binding_tex='\\providecommand{\\MainSourceFingerprint}{'+foundation['source_digest']+'}\n'
    (work/'main-build-binding.tex').write_text(binding_tex)
    main_binding={'source_digest':foundation['source_digest'],
                  'artifacts':{n:digest(work/n) for n in ('main.pdf','main.aux','main.fls','main-build-binding.tex')}}
    (work/'main-build-binding.json').write_text(json.dumps(main_binding,indent=2)+'\n')
    verify_main_binding(work)
    manual=work/'manual2'
    commands.append(run_latex(manual,'main.tex','manual-nested-build-console.txt'))
    (manual/'main-root.tex').write_text('\\def\\MainPDFTarget{main.pdf}\n\\input{main.tex}\n')
    verify_main_binding(work)
    commands.append(run_latex(manual,'main-root.tex','manual-root-build-console.txt'))
    shutil.copy2(manual/'main-root.pdf',work/'manual2.pdf')
    require(foundation_files(root)==foundation['files'], 'Main inputs changed during build')
    require(manual_files(root)==manual_files(work), 'Manual inputs changed during build')
    from pypdf import PdfReader
    inputs=manual_files(root)
    published={n:digest(work/n) for n in ('main.pdf','manual2/main.pdf','manual2.pdf')}
    receipt={'profile':'static_reference_publication','foundation_source_digest':foundation['source_digest'],
             'manual_inputs':inputs,'published_artifacts':published,'main_pages':len(PdfReader(work/'main.pdf').pages),
             'commands':commands,'engine':'XeLaTeX via latexmk',
             'tool_versions':{tool:subprocess.run([tool,'--version'],capture_output=True,text=True).stdout.splitlines()[0] for tool in ('xelatex','latexmk')},
             'scope':'Source, publication and static-reference checks; no native execution or empirical scoring.'}
    (manual/'evidence/publication-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
    verification=verify_publication(work)
    # Publish only after the paired build and checks succeed.
    for name in ('main.pdf','main.aux','main.fls','main-build-binding.tex','main-build-binding.json','manual2/main.pdf','manual2.pdf','manual2/main.bbl','manual2/evidence/publication-build.json'):
        shutil.copy2(work/name,root/name)
    return {'status':'PASS_PAIRED_BUILD','build_directory':str(work),'publication':verification}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--build-dir',type=Path)
    args=parser.parse_args()
    root=args.root.resolve()
    work=args.build_dir.resolve() if args.build_dir else Path(tempfile.mkdtemp(prefix='matter-i-build-'))
    try: result=build(root,work)
    except (ValueError,OSError,KeyError) as exc:
        print(json.dumps({'status':'FAIL_PAIRED_BUILD','build_directory':str(work),'error':str(exc)},indent=2)); return 1
    print(json.dumps(result,indent=2)); return 0

if __name__=='__main__': raise SystemExit(main())
