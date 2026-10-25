#!/usr/bin/env python3
"""Generate into a disposable directory; compare without replacing source outputs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


EXPECTED_OUTPUTS = {
    'data/m1/history/declaration_crosswalk.csv',
    'data/m1/history/observable_coverage.csv',
    'data/m1/history/value_map_status.csv',
    'data/m1/matter1_audit_report.json',
    'data/m1/matter1_coord0_enclosure_summary.csv',
    'data/m1/matter1_elements_1_118_ledger.csv',
    'data/matter1_audit_report.json',
    'data/matter1_coord0_enclosure_summary.csv',
    'data/matter1_elements_1_118_ledger.csv',
    'figures/aod_matter1_wheel_accessible.pdf',
    'figures/aod_matter1_wheel_accessible.svg',
    'figures/matter1_figure_manifest.json',
    'sections/generated_elements_longtable.tex',
    'visuals/matter1-layout.json',
    'visuals/matter1-reference.html',
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def snapshot(root):
    # Include the active generators/checkers and bound Main source, not installed
    # packages or temporary build logs. New/deleted files change the inventory.
    paths = set()
    for folder in ('manual2', 'scripts', '.github/workflows'):
        paths.update(p for p in (root/folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts
                     and p.suffix not in {'.aux','.log','.out','.toc','.fls','.xdv','.blg','.pyc'})
    for name in ('README.md','requirements-matter1.txt','package.json'):
        if (root/name).is_file(): paths.add(root/name)
    foundation = root/'manual2/evidence/foundation-source.json'
    if foundation.is_file():
        paths.update(root/name for name in json.loads(foundation.read_text())['files'] if (root/name).is_file())
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def pdf_projection(path):
    import pdfplumber

    def normalized(value):
        if isinstance(value, float): return round(value, 3)
        if isinstance(value, (tuple, list)): return [normalized(v) for v in value]
        return value

    text_keys=('text','x0','top','x1','bottom','size','fontname','upright',
               'stroking_color','non_stroking_color')
    vector_keys=('x0','top','x1','bottom','path','linewidth','stroke','fill',
                 'evenodd','stroking_color','non_stroking_color','dash')
    result=[]
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            need(not page.images, 'Unexpected raster image in the vector chart: '+str(path))
            result.append({'size':[round(page.width,3),round(page.height,3)],
                           'chars':[{k:normalized(c.get(k)) for k in text_keys} for c in page.chars],
                           'vectors':{kind:[{k:normalized(obj.get(k)) for k in vector_keys}
                                            for obj in page.objects.get(kind,[])]
                                      for kind in ('line','rect','curve')}})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--generator-python',default=sys.executable)
    args=parser.parse_args();root=args.root.resolve();before=snapshot(root)
    with tempfile.TemporaryDirectory(prefix='matter1-reproduction-') as directory:
        out=Path(directory)/'manual2'
        commands=[
          [args.generator_python,'-B',str(root/'manual2/scripts/generate_matter1_ledger.py'),'--root',str(root/'manual2'),'--output-root',str(out)],
          [args.generator_python,'-B',str(root/'manual2/scripts/generate_matter1_wheel.py'),'--ledger',str(out/'data/m1/matter1_elements_1_118_ledger.csv'),'--figure-dir',str(out/'figures'),'--visual-dir',str(out/'visuals'),'--template',str(root/'manual2/visuals/matter1-reference.template.html')]
        ]
        for command in commands:
            result=subprocess.run(command,capture_output=True,text=True)
            need(result.returncode==0,'Explicit generator failed: '+result.stdout+result.stderr)
        generated = {p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}
        need(generated == EXPECTED_OUTPUTS, 'Generated output inventory mismatch; missing='
             +repr(sorted(EXPECTED_OUTPUTS-generated))+'; extra='+repr(sorted(generated-EXPECTED_OUTPUTS)))
        checked=[]
        for p in sorted(out.rglob('*')):
            if not p.is_file():
                continue
            rel=p.relative_to(out);original=root/'manual2'/rel
            need(original.is_file(),'Missing persisted output: '+str(rel))
            if p.suffix=='.pdf':
                need(pdf_projection(p)==pdf_projection(original),'PDF text/geometry reproduction mismatch: '+str(rel))
                mode='PDF text, vector geometry, colors and size'
            elif p.name=='matter1_figure_manifest.json':
                left=json.loads(p.read_text());right=json.loads(original.read_text())
                for value in (left,right):
                    value['files'].pop('aod_matter1_wheel_accessible.pdf',None)
                need(left==right,'Figure manifest reproduction mismatch')
                mode='manifest excluding PDF binary hash'
            else:
                need(p.read_bytes()==original.read_bytes(),'Output reproduction mismatch: '+str(rel))
                mode='byte equality'
            checked.append({'path':str(rel),'comparison':mode})
    need(snapshot(root)==before,'Reproduction changed source bytes')
    print(json.dumps({'status':'PASS_REPRODUCTION','outputs':checked,'source_unchanged':True,'scope':'Data/table/chart/companion reproduction; no native execution claim.'},indent=2))

if __name__=='__main__':
    try: main()
    except (ValueError,OSError,KeyError) as exc:
        print('FAIL_REPRODUCTION: '+str(exc),file=sys.stderr);raise SystemExit(1)
