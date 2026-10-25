"""Read-only publication binding and PDF inspection for Matter I."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest_digest(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def foundation_files(root):
    root = Path(root)
    paths = [root / n for n in ('main.tex', 'preamble.tex', 'refs.bib')]
    for name in ('sections', 'appendices', 'figures', 'figures_jpg'):
        folder = root / name
        if folder.exists():
            paths.extend(p for p in folder.rglob('*') if p.is_file())
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(paths)}


def manual_files(root):
    root = Path(root)
    paths = []
    for p in (root / 'manual2').rglob('*'):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if p.suffix in ('.tex', '.bib') and p.name != 'main-root.tex':
            paths.append(p)
        elif rel.startswith('manual2/figures/') and p.suffix in ('.pdf', '.svg', '.json'):
            paths.append(p)
        elif rel.startswith('manual2/data/') and p.suffix in ('.csv', '.json'):
            paths.append(p)
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(paths)}


def verify_foundation(root):
    root = Path(root)
    binding = json.loads((root / 'manual2/evidence/foundation-source.json').read_text())
    actual = foundation_files(root)
    require(actual == binding['files'], 'Pinned Main source/input mismatch')
    require(manifest_digest(actual) == binding['source_digest'], 'Foundation manifest digest mismatch')
    return binding


def verify_main_binding(root):
    root = Path(root)
    foundation = verify_foundation(root)
    receipt = json.loads((root / 'main-build-binding.json').read_text())
    require(receipt['source_digest'] == foundation['source_digest'], 'Stale Main source binding')
    require(isinstance(receipt['artifacts'], dict) and set(receipt['artifacts']) == {'main.pdf', 'main.aux', 'main.fls', 'main-build-binding.tex'}, 'Incomplete Main build binding')
    for name, expected in receipt['artifacts'].items():
        require((root / name).is_file() and digest(root / name) == expected, 'Main artifact mismatch: ' + name)
    return receipt


def _tex_group(text, start):
    """Read one balanced AUX group, including nested title/notation braces."""
    while start < len(text) and text[start].isspace():
        start += 1
    require(start < len(text) and text[start] == '{', 'Malformed Main AUX label group')
    depth, pos = 1, start + 1
    while pos < len(text):
        if text[pos] == '\\':
            pos += 2
            continue
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
            if depth == 0:
                return text[start + 1:pos], pos + 1
        pos += 1
    raise ValueError('Unterminated Main AUX label group')


def semantic_main_destinations(root):
    """Bind each semantic Main reference used by the Manual to its AUX target."""
    root = Path(root)
    keys = set()
    for name in manual_files(root):
        if not name.endswith('.tex'):
            continue
        tex = re.sub(r'(?<!\\)%[^\n]*', '', (root/name).read_text())
        keys.update(re.findall(r'\\main(?:equation|section|appendix|table)\{([^}]+)\}', tex))
    require(bool(keys), 'No semantic Main references in Manual sources')
    aux = (root/'main.aux').read_text()
    labels = {}
    for match in re.finditer(r'\\newlabel\{', aux):
        key, end = _tex_group(aux, match.end() - 1)
        value, _ = _tex_group(aux, end)
        fields, pos = [], 0
        while pos < len(value):
            field, pos = _tex_group(value, pos)
            fields.append(field)
        if len(fields) >= 4:
            labels[key] = fields[3]
    require(keys <= set(labels), 'Missing semantic Main AUX labels: ' + ', '.join(sorted(keys-set(labels))))
    destinations = {labels[key] for key in keys}
    require('' not in destinations, 'Semantic Main reference lacks a PDF destination')
    return destinations


def inspect_pdf_links(path, expected_target, main_pdf, required_destinations=None):
    from pypdf import PdfReader
    from urllib.parse import unquote
    reader = PdfReader(path)
    destinations = set(PdfReader(main_pdf).named_destinations)
    links = []
    for page_index, page in enumerate(reader.pages):
        for indirect in page.get('/Annots', []):
            annotation = indirect.get_object()
            action = annotation.get('/A')
            if action is None:
                continue
            action = action.get_object()
            if action.get('/S') == '/GoToR':
                target = action.get('/F')
                if hasattr(target, 'get_object'):
                    target = target.get_object()
                if isinstance(target, dict):
                    target = target.get('/UF', target.get('/F'))
                target = str(target)
                destination = action.get('/D')
                if isinstance(destination, str):
                    require(destination in destinations, f'Unknown Main PDF destination: {destination}')
                else:
                    raise ValueError('Main link must use a named semantic destination')
                require(target == expected_target, f'Wrong Main PDF target: {target!r}, expected {expected_target!r}')
                links.append({'page': page_index + 1, 'target': target, 'destination': str(destination)})
            elif action.get('/S') == '/URI':
                uri = str(action.get('/URI', ''))
                if '.pdf' in uri and not re.match(r'^[a-zA-Z]+:', uri):
                    target, _, destination = uri.partition('#')
                    require(target == expected_target, 'Wrong local PDF URI: ' + uri)
                    require(unquote(destination) in destinations, 'Unknown local PDF URI destination: ' + uri)
                    links.append({'page':page_index+1,'target':target,'destination':unquote(destination)})
    require(bool(links), 'No semantic external Main links in ' + str(path))
    if required_destinations is not None:
        missing = set(required_destinations) - {link['destination'] for link in links}
        require(not missing, 'Missing semantic Main PDF links: ' + ', '.join(sorted(missing)))
    return {'pages': len(reader.pages), 'main_link_count': len(links), 'links': links}


def pdf_text(path):
    from pypdf import PdfReader
    return '\n'.join(page.extract_text() or '' for page in PdfReader(path).pages)


def inspect_chart_fonts(root):
    import pdfplumber
    root = Path(root)
    figure = root / 'manual2/figures/aod_matter1_wheel_accessible.pdf'
    with pdfplumber.open(figure) as pdf:
        require(len(pdf.pages) == 1, 'Reference figure must be one page')
        p = pdf.pages[0]
        width_mm, height_mm = p.width * 25.4 / 72, p.height * 25.4 / 72
        require(abs(width_mm - 180) < .05 and height_mm <= 210.05, 'Reference figure physical size mismatch')
        visible = [c for c in p.chars if c['text'].strip()]
        require(visible, 'Reference figure has no extractable text')
        min_size = min(c['size'] for c in visible)
        require(min_size >= 8.99, f'Figure text below 9 pt: {min_size}')
        font_keys = {re.sub(r'^[A-Z]{6}\+', '', c['fontname']) for c in visible}
    placements = []
    with pdfplumber.open(root / 'manual2.pdf') as pdf:
        for idx, page in enumerate(pdf.pages):
            chars = [c for c in page.chars if re.sub(r'^[A-Z]{6}\+', '', c['fontname']) in font_keys and c['text'].strip()]
            if not chars:
                continue
            size = min(c['size'] for c in chars)
            require(size >= 8.99, f'Placed figure text below 9 pt on page {idx+1}: {size}')
            require(abs(size / min_size - 1) < .002, 'Manuscript silently scales the figure')
            require(all(c['x0'] >= -.1 and c['x1'] <= page.width+.1 and c['top'] >= -.1 and c['bottom'] <= page.height+.1 for c in chars), 'Placed chart text clipped')
            placements.append({'page':idx+1,'chart_characters':len(chars),'minimum_font_pt':size,'scale':size/min_size})
    require(len(placements) == 1, 'Expected exactly one placed chart page')
    return {'width_mm':width_mm,'height_mm':height_mm,'minimum_font_pt':min_size,'placements':placements}


def verify_publication(root, inspect_fonts=True):
    root = Path(root)
    verify_main_binding(root)
    foundation = verify_foundation(root)
    actual_text = re.sub(r'\s+', '', pdf_text(root/'main.pdf'))
    require(hashlib.sha256(actual_text.encode()).hexdigest() == foundation['released_text_sha256'], 'Rebuilt Main text differs from the released authority')
    receipt = json.loads((root / 'manual2/evidence/publication-build.json').read_text())
    require(receipt['profile'] == 'static_reference_publication', 'Wrong publication profile')
    require(receipt['foundation_source_digest'] == foundation['source_digest'], 'Stale publication foundation binding')
    require(receipt['manual_inputs'] == manual_files(root), 'Stale Manual publication inputs')
    require(isinstance(receipt['published_artifacts'], dict) and set(receipt['published_artifacts']) == {'main.pdf', 'manual2/main.pdf', 'manual2.pdf'}, 'Incomplete publication artifact binding')
    for name, expected in receipt['published_artifacts'].items():
        require((root / name).is_file() and digest(root/name)==expected, 'Published artifact mismatch: '+name)
    from pypdf import PdfReader
    main_pages = len(PdfReader(root/'main.pdf').pages)
    require(receipt['main_pages'] == main_pages, 'Publication Main page count mismatch')
    expected_destinations = semantic_main_destinations(root)
    nested = inspect_pdf_links(root/'manual2/main.pdf','../main.pdf',root/'main.pdf',expected_destinations)
    top = inspect_pdf_links(root/'manual2.pdf','main.pdf',root/'main.pdf',expected_destinations)
    require({(v['page'],v['destination']) for v in nested['links']} == {(v['page'],v['destination']) for v in top['links']}, 'Manual variants have different semantic Main links')
    require(pdf_text(root/'manual2/main.pdf') == pdf_text(root/'manual2.pdf'), 'Manual variants have different scientific text')
    result = {'status':'PASS_PUBLICATION','foundation_source_digest':receipt['foundation_source_digest'],
              'main_pages':main_pages,'manual_pages':top['pages'],'semantic_main_destination_count':len(expected_destinations),
              'root_main_links':top['main_link_count'],'nested_main_links':nested['main_link_count'],
              'manual_text_equal':True,'main_text_matches_release':True,'main_links':top['links']}
    if inspect_fonts:
        result['chart'] = inspect_chart_fonts(root)
    return result
