#!/usr/bin/env python3
"""Read-only source/acquisition checks; no native prediction or O0 score."""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

DATA = Path('manual2/data/m1/external_transitions')
CATALOG_SHA256 = '30251fef71a7304b3b71830e6c5110398afe9d1604fde0f919cbf4bcfd489f1a'
IDS = ('D2-ground-hfs-WinelandRamsey1972',
       'T3-ground-hfs-Mathur1967-untranscribed',
       'T3-ground-hfs-Kramida2010-rescaled-Mathur1967')
ACQUISITION = {
    'wineland-ramsey1972': 'raw_public_abstract_downloaded',
    'mathur1967': 'web_abstract_read_raw_download_failed',
    'kramida2010-hdt': 'web_pdf_text_extraction_only_raw_pdf_download_failed',
    'hellwig1970-full': 'copied_verified_earlier_primary_download',
}
UNCERTAINTY_LOCATORS = [
    'PDF page index 5 / printed page 591, footnote 3',
    'PDF page index 22 / printed page 608, explanation of experimental uncertainties',
]
UNCERTAINTY_CAVEAT = ('Evaluator intention; the exact meaning of uncertainties quoted from older '
    'publications is sometimes difficult to recover. This does not establish a Gaussian '
    'distribution, coverage probability or complete shared-reference covariance.')

def need(condition, message):
    if not condition:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def number(value, *, positive=False):
    need(type(value) is str and re.fullmatch(r'\d+(?:\.\d+)?', value) is not None,
         'A reported decimal must retain its string digits')
    out=Fraction(value)
    need(out>0 if positive else out>=0, 'Invalid reported magnitude')
    return out

class Description(HTMLParser):
    def __init__(self):
        super().__init__(); self.values=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='meta' and attrs.get('name')=='description':
            self.values.append(attrs.get('content',''))

def validate_metadata(data):
    need(data['schema']=='matter1.external-transition-acquisition-supplement.v1', 'Wrong acquisition schema')
    rows=data['records']
    need([r['id'] for r in rows]==list(IDS), 'Missing, duplicate or unknown target record')
    sources={s['id']:s for s in data['source_rows']}
    need(len(sources)==len(data['source_rows']) and set(sources)==set(ACQUISITION), 'Wrong source inventory')
    for key, source in sources.items():
        need(source['acquisition_status']==ACQUISITION[key], 'Unsupported acquisition promotion')
        need(source['url'].startswith('https://'), 'Source URL required')
        if key=='mathur1967':
            need(source['path'] is None and source['sha256'] is None, 'Missing raw primary must remain explicit')
        if key=='kramida2010-hdt':
            need(source['path'].endswith('.json') and source['full_text_status']=='web_pdf_text_browsed_no_raw_pdf_obtained',
                 'A web extraction is not a downloaded original PDF')
    for i,row in enumerate(rows):
        need(type(row['z']) is int and row['z']==1 and type(row['a']) is int and row['a']==(2 if i==0 else 3), 'Atomic identity differs')
        need(row['record_form']=='Measured target record' and row['role']=='external_transition_target', 'Wrong record form')
        need(row['data_support_class'] is None and row['intended_comparison_class']=='O0', 'A target alone is not an O0 calculation or D0 fixture')
        need(row['scientific_claim_class'] is None and row['native_calculation_input'] is False, 'External target cannot become a native calculation input')
        need(row['display_scope']==('external' if i==1 else 'derived external'), 'Wrong measured-sector display scope')
        need(row['unit']=='Hz' and row['quantity']=='ground_state_hyperfine_frequency', 'Wrong quantity or unit')
        need(row['exposure']=='retrospective_acquisition_before_any_future_atomic_model_freeze', 'Target exposure cannot be erased')
        need(row['physical_comparison_status']=='not_scored_map_and_preparation_unresolved', 'Acquisition does not supply a score')
        for key in ('experimental_window','magnetic_sublevels','native_configuration_id','native_observation_map',
                    'physical_prediction','preparation','reported_dimensionless_ratio','joint_covariance',
                    'uncertainty_coverage','uncertainty_distribution'):
            need(row[key] is None, 'Unsupported supplied field: '+key)
        need(row['source_id'] in sources and row['direct_measurement_source_id'] in sources, 'Unbound source')
        need(row['calibration_anchor']['isotope']=='H-1' and row['not_independent_of'], 'Shared hydrogen reference must be retained')
        if i==1:
            need(row['value_hz'] is None and row['uncertainty_hz'] is None and row['uncertainty_notation'] is None,
                 'Untranscribed primary tritium value cannot be filled from a later evaluation')
        else:
            number(row['value_hz'],positive=True); number(row['uncertainty_hz'],positive=True)
            need(row['calibration_anchor']['value_hz']=='1420405751.768', 'Changed hydrogen anchor')
    d,original,t=rows
    need((d['value_hz'],d['uncertainty_hz'])==('327384352.5222','0.0017'), 'Deuterium transcription differs')
    need(d['calibration_anchor']['uncertainty_hz']=='0' and d['calibration_anchor']['role']=='assumed_exact_reference_in_original_paper'
         and 'not an assertion' in d['calibration_anchor']['zero_uncertainty_scope'], 'Conditional reference assumption is not physical zero uncertainty')
    need((t['value_hz'],t['uncertainty_hz'])==('1516701470.775','0.007'), 'Evaluated tritium transcription differs')
    need(t['calibration_anchor']['uncertainty_hz']=='0.001' and original['id'] in t['not_independent_of'], 'Rescaling dependence differs')
    need(t['standard_uncertainty_hz']=='0.007' and t['standard_uncertainty_hz']==t['uncertainty_hz'],
         'Evaluated T standard uncertainty differs')
    need(t['uncertainty_convention']=={
        'kind':'one_standard_deviation_in_evaluation', 'source_id':'kramida2010-hdt',
        'locators':UNCERTAINTY_LOCATORS, 'caveat':UNCERTAINTY_CAVEAT},
        'Evaluated T uncertainty convention, source or caveat differs')
    need(all(row.get('standard_uncertainty_hz') is None and row.get('uncertainty_convention') is None
             for row in (d,original)), 'Evaluator convention cannot promote the separate primary records')
    return rows,sources

def verify(root):
    root=Path(root).resolve(); folder=root/DATA
    path=folder/'catalog.json'; before=path.read_bytes(); data=json.loads(before)
    rows,sources=validate_metadata(data)
    need(hashlib.sha256(before).hexdigest()==CATALOG_SHA256, 'Acquisition catalog differs from reviewed binding')
    checked=[]
    for source in sources.values():
        for name,digest in (('path','sha256'),('text_path','text_sha256')):
            if source.get(name) is None:continue
            p=(folder/source[name]).resolve()
            need(p.is_relative_to(folder) and p.is_file(), 'Source path escaped or missing')
            need(sha(p)==source[digest], 'Source bytes differ: '+source[name]);checked.append(source[name])
    parser=Description();parser.feed((folder/sources['wineland-ramsey1972']['path']).read_text())
    text=''.join(parser.values);compact=re.sub(r'\s+','',text)
    need('327384352.5222(17)' in compact and '1420405751.768' in compact and 'assumedtobeexactly' in compact,
         'Primary deuterium abstract no longer supports value and conditional reference')
    extracted=json.loads((folder/sources['kramida2010-hdt']['path']).read_text())
    need(extracted['raw_pdf_path'] is None and extracted['raw_pdf_sha256'] is None, 'Extraction cannot claim original-file authentication')
    facts=extracted['facts']
    need(facts['tritium_rescaled_frequency_hz']==rows[2]['value_hz'] and facts['tritium_parenthesized_uncertainty_hz']==rows[2]['uncertainty_hz'], 'Evaluation extraction differs')
    need(facts['tritium_standard_uncertainty_hz']==rows[2]['standard_uncertainty_hz'] and
         facts['parenthesized_uncertainty_convention']==rows[2]['uncertainty_convention'],
         'Evaluation uncertainty convention differs from target')
    need(facts['uncertainty_coverage'] is None and facts['uncertainty_distribution'] is None and
         facts['joint_covariance'] is None, 'Standard uncertainty does not supply a distribution or covariance')
    legacy=json.loads((root/'manual2/data/m1/hyperfine/target_inventory.json').read_text())
    h=next(s for s in legacy['sources'] if s['source_id']=='hellwig1970')
    need(h['pdf_sha256']==sources['hellwig1970-full']['sha256'], 'Full hydrogen PDF differs from original source binding')
    need(path.read_bytes()==before, 'Verifier changed the catalog')
    return {'status':'PASS_EXTERNAL_TRANSITION_SOURCE_INVENTORY','target_records':3,
        'reported_frequency_records':2,'untranscribed_primary_records':1,'source_records':4,
        'checked_local_source_files':checked,'original_tritium_numeric_value_recovered':False,
        'raw_nist_evaluation_pdf_downloaded':False,'D0_executions_verified':0,'O0_scores_executed':0,
        'native_calculation_inputs_supplied':False,'physical_predictions_executed':0,
        'scope':'Source binding, transcription and record-class separation; not original protocol verification or native/empirical agreement.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    args=parser.parse_args()
    try: print(json.dumps(verify(args.root),sort_keys=True))
    except (OSError,ValueError,KeyError,TypeError,StopIteration) as exc:
        parser.exit(1,'FAIL_EXTERNAL_TRANSITION_SOURCE_INVENTORY: '+str(exc)+'\n')

if __name__=='__main__':main()
