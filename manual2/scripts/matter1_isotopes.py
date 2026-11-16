"""Source-bound isotope catalog, distinct from the frozen element reference.

Generation is explicit. Verification never writes, also under python -O.
The curated snapshot is a scientific input, not a native survival prediction.
"""
from __future__ import annotations
import copy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

CURATION_SHA256 = 'b25ca90dad87219f5582ad01ec1e55f48467db54621f241675b79392a6cd41e4'
SYMBOLS = {'H': 1, 'Fe': 26, 'Ni': 28, 'Cs': 55, 'Pb': 82, 'Hg': 80,
           'Ds': 110, 'Cn': 112, 'Nh': 113, 'Fl': 114, 'Lv': 116, 'Og': 118}
EMPIRICAL = {'evaluated_observed','reported_observed','tentative_assignment',
             'tentative_isomer','unobserved_rejected_candidate','unobserved_model_target'}
CHANNEL_STATUS = {'observed','upper_limit','tentative'}
BASE = Path('data/m1/isotopes')

class ValidationError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise ValidationError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True)+'\n').encode()

def manual_root(root):
    root = Path(root)
    return root/'manual2' if (root/'manual2/data/m1').is_dir() else root

def read(path):
    try:
        return Path(path).read_bytes()
    except OSError as exc:
        raise ValidationError(f'{path}: cannot read') from exc

def read_json(path):
    try:
        return json.loads(read(path))
    except (ValueError, UnicodeError) as exc:
        raise ValidationError(f'{path}: invalid JSON') from exc

def decimal(value, context):
    require(isinstance(value,str),f'{context}: decimal string required')
    try: number=Decimal(value)
    except InvalidOperation as exc: raise ValidationError(f'{context}: invalid decimal') from exc
    require(number.is_finite(),f'{context}: nonfinite value')
    return number

def support_coordinates(z,a):
    require(type(z) is int and type(a) is int and 1<=z<=a,'exact nuclear identity required')
    n=a-z; q=min(z//2,n//2)
    return {'q':q,'r_p':z-2*q,'r_n':n-2*q}

def validate_life(h, quantity='total_half_life'):
    require(set(h)=={'kind','quantity','value_seconds','uncertainty_minus_seconds',
                    'uncertainty_plus_seconds','original','original_unit','confidence','unit_conversion'},
            'half-life schema differs')
    require(h['quantity']==quantity,'half-life/partial/event quantity conflation')
    require(h['kind'] in {'measured','observationally_stable','unknown','lower_limit','upper_limit'},'unknown life status')
    require(h['original_unit'] in {'s','ms','us','y'},'unknown original life unit')
    require(all(isinstance(h[k],str) and h[k] for k in ('original','confidence','unit_conversion')),'missing original/uncertainty context')
    if h['kind'] in {'observationally_stable','unknown'}:
        require(all(h[k] is None for k in ('value_seconds','uncertainty_minus_seconds','uncertainty_plus_seconds')),'unknown/stable is not numeric infinity')
    else:
        v=decimal(h['value_seconds'],'half-life');require(v>0,'half-life must be positive')
        lo=h['uncertainty_minus_seconds'];hi=h['uncertainty_plus_seconds']
        require((lo is None)==(hi is None),'asymmetric interval must have both sides')
        if lo is not None:
            require(0<=decimal(lo,'lower uncertainty')<v and decimal(hi,'upper uncertainty')>=0,'invalid half-life interval')

def validate_channel(ch,parent,source_ids):
    require(set(ch)=={'mode','daughter','status','branching_original','source_id'},'decay channel schema differs')
    require(ch['source_id'] in source_ids and ch['status'] in CHANNEL_STATUS,'invalid channel source/status')
    require(isinstance(ch['branching_original'],str) and ch['branching_original'],'missing branch qualification')
    if ch['mode']=='spontaneous_fission':
        require(ch['daughter'] is None,'fission does not define one daughter')
    else:
        require(ch['mode'] in {'alpha','electron_capture_or_beta_plus'},'unknown decay mode')
        d=ch['daughter'];require(isinstance(d,dict) and set(d)=={'Z','A','symbol','id'},'daughter identity schema')
        require(type(d['Z']) is int and type(d['A']) is int,'daughter exact integer identity')
        dz,da=(2,4) if ch['mode']=='alpha' else (1,0)
        require((d['Z'],d['A'])==(parent['Z']-dz,parent['A']-da),'daughter violates decay conservation')
        require(SYMBOLS.get(d['symbol'])==d['Z'] and d['id']==f"{d['symbol']}-{d['A']}:ground",'daughter identity inconsistent')

def validate_records(data):
    require(type(data.get('schema_version')) is int and data['schema_version']==1,'isotope schema version')
    ids={s['id'] for s in data['sources']}
    require(len(ids)==len(data['sources']),'duplicate source')
    seen=set()
    for r in data['isotopes']:
        require(type(r['Z']) is int and type(r['A']) is int and type(r['N']) is int,'nuclear counts require exact integers')
        require(SYMBOLS.get(r['symbol'])==r['Z'] and r['N']==r['A']-r['Z']>=0,'nuclear identity mismatch')
        require(r['state'] in {'ground','m_candidate'} and r['id']==f"{r['symbol']}-{r['A']}:{r['state']}",'isotope/state mismatch')
        require(r['id'] not in seen,'duplicate isotope/state');seen.add(r['id'])
        require(r['empirical_status'] in EMPIRICAL,'unknown empirical status')
        require(r['native_admission']=='not_established' and r['model_execution']=='not_executed'
                and r['empirical_agreement']=='not_tested','catalog is not native admission or model agreement')
        require(r['selection_source'] in ids,'missing selected source');validate_life(r['half_life'])
        if r['empirical_status'].startswith('unobserved'):
            require(r['half_life']['kind']=='unknown','unobserved state promoted to measured lifetime')
        require(r['state_assignment'] in {'established_ground_state','assumed_ground_state','tentative_ground_state','not_established','tentative_isomer'},'unknown state-assignment status')
        require(r['spin_parity']['assignment'] in {'source_reported','not_established'},'unknown spin assignment')
        require(r['exposure'] in {'retrospective_source_seen_before_model_freeze','unscored_target_no_measured_value'},'unknown exposure status')
        for s in r['source_records']:require(s['source_id'] in ids and bool(s['locator']),'source locator missing')
        for ch in r['decay_channels']:validate_channel(ch,r,ids)
        for u in r['updates']:
            require(u['source_id'] in ids and u['role'] in {'newer_overlapping_reanalysis','newer_experimental_compilation'},'invalid update')
            validate_life(u['half_life'])
            require(bool(u['locator']) and bool(u['overlap']),'update missing overlap/locator')
            for ch in u.get('decay_channels',[]):validate_channel(ch,r,ids)
            for partial in u.get('channel_partial_half_lives',[]):
                require(partial['source_id'] in ids and partial['channel'] in {'alpha_main','alpha_rare','spontaneous_fission'},'invalid partial channel')
                require(partial['uncertainty_status']=='incomplete_branching_uncertainty','partial channel uncertainty promoted')
                validate_life(partial['measurement'],'channel_partial_half_life')
        for lim in r['limits']:
            require(lim['source_id'] in ids and lim['relation'] in {'>','<'},'invalid limit')
            validate_life(lim['measurement'],'channel_partial_half_life' if lim['channel']!='all_modes' else 'total_half_life')
        for event in r.get('event_times',[]):
            require(event['quantity']=='event_waiting_time' and event['source_id'] in ids,'event is not half-life')
            require(decimal(event['value_seconds'],'event time')>0,'event waiting time must be positive')
    require(len(seen)==27,'reviewed isotope coverage changed')
    for sym,id in data['default_isotopes'].items():
        r=next((r for r in data['isotopes'] if r['id']==id),None)
        require(r is not None and r['symbol']==sym and r['empirical_status'] in {'evaluated_observed','reported_observed'},'invalid default isotope')
    require(data['default_isotopes']['Fl']=='Fl-289:ground' and data['default_isotopes']['Lv']=='Lv-293:ground'
            and data['default_isotopes']['Og']=='Og-294:ground','reference isotope drift')

def load_inputs(root):
    root=manual_root(root);base=root/BASE
    raw=read(base/'curation.json');require(sha(raw)==CURATION_SHA256,'curated isotope snapshot SHA-256 mismatch')
    data=read_json(base/'curation.json');validate_records(data)
    for source in data['sources']:
        require(source['kind'] in {'evaluated','experiment','discovery_compilation','experiment_and_overlapping_reanalysis','evaluation_crosscheck','evaluated_mass','unevaluated_experiment','authored_model_target'},'unknown source type')
        require(source['url'] is None or source['url'].startswith('https://'),'source URL must be HTTPS')
        for key,hkey in [('path','sha256'),('text_path','text_sha256')]:
            if key not in source:continue
            p=Path(source[key]);require(not p.is_absolute() and '..' not in p.parts,'source path escapes catalog')
            require(sha(read(base/p))==source[hkey],f'{p}: source SHA-256 mismatch')
    raw_nubase=read(base/'sources/nubase2020.txt').decode().splitlines()
    for r in data['isotopes']:
        cross=r.get('nubase_crosscheck')
        if cross:
            require(raw_nubase[cross['line']-1]==cross['raw'],'NUBASE source row mismatch')
            require(cross['scope']=='crosscheck_only_no_promotion_or_averaging','NUBASE status promotion')
    return data

def build_catalog(data):
    result=copy.deepcopy(data)
    result['curation_sha256']=CURATION_SHA256
    result['status']='source_bound_reference_not_native_prediction'
    for r in result['isotopes']:
        r['support_coordinates']=support_coordinates(r['Z'],r['A'])
        r['support_coordinates']['interpretation']='formal_2p2n_groups_not_physical_alpha_clusters'
    result['decay_edges']=[dict(parent=r['id'],**ch) for r in result['isotopes'] for ch in r['decay_channels']]
    return result

def tex_escape(s):
    for a,b in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]:s=s.replace(a,b)
    return s.replace('−','-').replace('α',r'$\alpha$')

def life_tex(r):
    h=r['half_life']
    if h['kind']=='observationally_stable':return 'observationally stable'
    if h['kind']=='unknown':return 'unobserved target' if r['empirical_status']=='unobserved_model_target' else 'not supplied'
    factor={'s':Decimal(1),'ms':Decimal('.001'),'us':Decimal('.000001'),'y':Decimal(31557600)}[h['original_unit']]
    v=Decimal(h['value_seconds'])/factor
    if h['uncertainty_minus_seconds'] is None:return f'${v}$ '+h['original_unit']
    lo=Decimal(h['uncertainty_minus_seconds'])/factor;hi=Decimal(h['uncertainty_plus_seconds'])/factor
    return f'${v}^{{+{hi}}}_{{-{lo}}}$ '+h['original_unit']

def table_tex(catalog, ids, caption, label):
    by={r['id']:r for r in catalog['isotopes']}
    lines=[r'\begin{table}[htbp]',r'\centering\small',r'\begin{tabular}{lrrrl}',r'\toprule',r'Isotope & $Z,N$ & $q$ & $r_p,r_n$ & Adopted $T_{1/2}$ \\',r'\midrule']
    for id in ids:
        r=by[id];s=r['support_coordinates'];lines.append(f"$^{{{r['A']}}}\\mathrm{{{r['symbol']}}}$ & ${r['Z']},{r['N']}$ & ${s['q']}$ & ${s['r_p']},{s['r_n']}$ & {life_tex(r)} \\\\")
    lines += [r'\bottomrule',r'\end{tabular}',r'\caption{'+caption+'}',r'\label{'+label+'}',r'\end{table}']
    return ('\n'.join(lines)+'\n').encode()

def expected_artifacts(root):
    data=load_inputs(root);c=build_catalog(data)
    artifacts={str(BASE/'catalog.json'):json_bytes(c)}
    tables=[('anchors',['H-1:ground','Cs-133:ground'],'Recurrence anchors. Stability is an observational classification; no infinite half-life is assigned.','tab:isotope-anchors'),('benchmarks',['Fe-56:ground','Pb-208:ground'],'Binding and observational-stability controls. The digital reference retains Ni-62 and the channel-specific Pb-208 bound.','tab:isotope-benchmarks'),('superheavy',['Og-294:ground','Lv-290:ground','Fl-286:ground','Lv-293:ground','Fl-289:ground','Fl-298:ground'],'Selected superheavy records. Asymmetric uncertainties are expanded from the adopted last-digit notation. Fl-298 is an unobserved target. Newer experimental analyses remain separate in the companion.','tab:isotope-superheavy')]
    for name,ids,caption,label in tables:artifacts[f'sections/generated_isotope_{name}.tex']=table_tex(c,ids,caption,label)
    artifacts['sections/generated_isotope_chains.tex']=(r'''\begin{figure}[htbp]
\centering
\( {}^{294}\mathrm{Og}\xrightarrow{\alpha}{}^{290}\mathrm{Lv}
\xrightarrow{\alpha}{}^{286}\mathrm{Fl}\xrightarrow{\alpha}{}^{282}\mathrm{Cn}
\xrightarrow{\mathrm{SF}}\text{fragments} \)
\par\smallskip
\( {}^{293}\mathrm{Lv}\xrightarrow{\alpha}{}^{289}\mathrm{Fl}
\xrightarrow{\alpha}{}^{285}\mathrm{Cn} \)
\caption{Observed alpha relationships in the selected records. The first route is one branch: Fl-286 also fissions. Cn-285 has further alpha decay; it is a scope endpoint here, not an asserted terminal stable state.}
\label{fig:isotope-chains}
\end{figure}
''').encode()
    summary={'schema_version':1,'catalog_id':c['catalog_id'],'isotope_state_records':len(c['isotopes']),'source_records':len(c['sources']),'observed_finite_records':sum(r['half_life']['kind']=='measured' and r['empirical_status'] in {'evaluated_observed','reported_observed'} for r in c['isotopes']),'native_prediction_executed':False,'all_known_half_life_tests':'retrospective','formal_grouping':'q=min(Z//2,N//2); A=4q+r_p+r_n','selection_policy':c['selection_policy'],'generated_sha256':{p:sha(b) for p,b in artifacts.items()}}
    artifacts[str(BASE/'verification.json')]=json_bytes(summary)
    return artifacts

def verify(root):
    root=manual_root(root);artifacts=expected_artifacts(root)
    for p,b in artifacts.items():require(read(root/p)==b,f'{p}: stale or mutated generated isotope artifact')
    return json.loads(artifacts[str(BASE/'verification.json')])

def load_catalog(root):
    verify(root)
    return read_json(manual_root(root)/BASE/'catalog.json')
