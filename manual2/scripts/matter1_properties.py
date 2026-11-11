"""Source-bound property inventory; no native model or physical prediction.

Build is deterministic and offline. Generation is explicit; verification rebuilds
in memory and compares bytes. Element-generic atom data never become measured
isotope-specific properties by a label join.
"""
from __future__ import annotations
import csv
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
BASE = Path('manual2/data/m1/properties')
INPUTS = BASE / 'inputs.json'
INPUTS_SHA256 = 'acf8fb6ad5a6e1f33f61e0f647dc2545b705be2d89667f791b380172d03cd169'
OUTPUTS = ('definitions.json', 'states.json', 'catalog.json', 'coverage.json', 'source_manifest.json')
PILOTS = ((1,1,'H'),(1,2,'H'),(1,3,'H'),(2,3,'He'),(2,4,'He'),(55,133,'Cs'))
SCHEMA = 'matter1.element-properties.v1'
MISSING_FAMILIES = ('atomic_ground_states_ionization','electron_affinities','atomic_levels_lines','nuclear_moments_radii')
SYMBOLS='H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split()
UNCERTAINTY_KINDS=('not_supplied','source_reported_magnitude_convention_not_reconstructed','scaled_source_reported_magnitude','joint_covariance_not_supplied','exact_definition_only','reported_standard_uncertainty','reported_last_digit_magnitude','interval_not_standard_uncertainty')
PROPERTY_SPECS = {
 'standard_atomic_weight': ('element','1','CIAAW standard atomic weight for normal materials, with interval where specified; distinct from isotope mass and sample composition.'),
 'ground_configuration': ('atom','text','Ground-state electronic configuration, isotope unspecified unless explicitly assigned.'),
 'ground_term': ('atom','text','Ground-state term and angular momentum designation with source qualifiers.'),
 'ionization_energy': ('atom','eV','Minimum energy to remove an electron from the stated charge-state ground state; q0 and q1 give first and second ionization separately.'),
 'electron_affinity': ('atom','eV','Energy released on attachment to the stated neutral ground state; positive denotes bound anion under the declared source convention.'),
 'excitation_energy': ('atom','cm^-1','Selected electronic level energy relative to the specified spectrum ground state.'),
 'line_wavelength': ('atom','nm','Selected observed or Ritz wavelength, with medium and transition retained.'),
 'polarizability': ('atom','a0^3','State-, frequency- and tensor-component-specific atomic polarizability in the explicitly stated source convention.'),
 'zeeman_coefficient': ('atom','Hz/T','Specified transition frequency response to magnetic field; sublevels, field regime and order required.'),
 'stark_coefficient': ('atom','Hz/(V/m)^2','Specified transition quadratic electric-field response; sublevels, field regime and order required.'),
 'atomic_mass': ('isotope','u','Neutral-atom atomic mass from AME2020; not bare nuclear mass and not standard atomic weight.'),
 'mass_excess': ('isotope','keV','AME2020 neutral-atom mass excess relative to A atomic mass units.'),
 'binding_energy_per_nucleon': ('isotope','keV','AME2020 reported binding energy per nucleon, retaining evaluation/systematics markers.'),
 'binding_energy': ('isotope','keV','A times the AME2020 binding energy per nucleon; exact multiplication of the reported decimal.'),
 'neutron_separation_energy': ('isotope','keV','ME(Z,A-1)+ME(neutron)-ME(Z,A), neutral-atom mass-excess convention; joint input covariance not supplied.'),
 'proton_separation_energy': ('isotope','keV','ME(Z-1,A-1)+ME(H-1)-ME(Z,A), neutral-atom mass-excess convention; electron binding corrections not separately reconstructed.'),
 'alpha_decay_q': ('isotope','keV','ME(parent)-ME(daughter)-ME(He-4), neutral-atom mass-excess convention. A positive Q does not establish an observed decay branch.'),
 'beta_minus_q': ('isotope','keV','AME2020 reported beta-minus energy with its source uncertainty; sign is retained.'),
 'spin_parity': ('isotope','text','NUBASE nuclear spin/parity designation; tentative parentheses, direct-measurement * and systematics # remain visible.'),
 'decay_branching': ('isotope','text','NUBASE verbatim decay-mode/intensity record; not normalized into unsupported probabilities.'),
 'isotopic_abundance': ('isotope','text','NUBASE source-reported abundance qualification; not a universal sample composition.'),
 'magnetic_dipole_moment': ('isotope','nuclear_magneton','State-specific nuclear magnetic dipole moment; no spin-only inferred value.'),
 'electric_quadrupole_moment': ('isotope','b','State-specific nuclear electric quadrupole moment.'),
 'charge_radius': ('isotope','fm','State-specific root-mean-square nuclear charge radius.'),
 'isomer_excitation_energy': ('isotope','keV','Energy of the named isomer relative to its stated ground-state endpoint; candidate assignments remain tentative.'),
 'hyperfine_frequency': ('atomic_isotope','Hz','Ground-state hyperfine separation with explicit isotope, electronic state and reference dependence.'),
 'isotope_shift': ('atomic_isotope','Hz','Frequency difference for one stated electronic transition between two explicit isotope/state endpoints, retaining sign convention.'),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def read(path):
    def pairs(items):
        result = {}
        for k,v in items:
            require(k not in result, 'Duplicate JSON key: '+k)
            result[k] = v
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON '+x)))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(root, relative):
    require(isinstance(relative,str) and not Path(relative).is_absolute(), 'Source path must be relative')
    p=(Path(root)/relative).resolve()
    require(p.is_relative_to(Path(root).resolve()) and p.is_file(), 'Source escaped or missing: '+relative)
    return p


def number(value):
    require(type(value) is str and re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?', value), 'A numeric value must preserve finite decimal digits as a string')
    try: result=Decimal(value)
    except InvalidOperation as exc: raise ValueError('Invalid decimal') from exc
    require(result.is_finite(), 'Nonfinite decimal')
    return result


def dec(value):
    return format(value, 'f')


def uncertainty(value=None, kind='not_supplied', **extra):
    return dict(value=value,kind=kind,coverage=None,distribution=None,**extra)


def parse_ame(text):
    require('mass.mas20' in text and 'f14.6,f12.6' in text, 'Unsupported AME format')
    rows={}
    def field(s):
        s=s.strip()
        if not s or '*' in s: return None
        return dec(number(s.replace('#','.')))
    for lineno,line in enumerate(text.splitlines(),1):
        if len(line)<123: continue
        try: z,a=int(line[9:14]),int(line[14:19])
        except ValueError: continue
        require((z,a) not in rows, 'Duplicate AME identity')
        mass_fraction=field(line[110:123]); mass_integer=line[106:109].strip()
        row={'z':z,'a':a,'line':lineno,'raw':line,'estimated':{},'symbol':line[20:23].strip()}
        for key,(lo,hi,ulo,uhi) in {
            'mass_excess':(28,42,42,54), 'binding_energy_per_nucleon':(54,67,68,78), 'beta_minus_q':(81,94,94,105)}.items():
            row[key]=field(line[lo:hi]);row[key+'_uncertainty']=field(line[ulo:uhi]);row['estimated'][key]='#' in line[lo:uhi]
        row['atomic_mass']=dec(Decimal(mass_integer)+number(mass_fraction)/Decimal(1000000)) if mass_fraction is not None and mass_integer else None
        mass_unc=field(line[123:135]);row['atomic_mass_uncertainty']=dec(number(mass_unc)/Decimal(1000000)) if mass_unc else None
        row['estimated']['atomic_mass']='#' in line[106:135]
        rows[(z,a)]=row
    require((1,1) in rows and (2,4) in rows, 'Incomplete AME source')
    return rows


def parse_nubase(text):
    require('Nubase2020 citation' in text and 'ZZZi' in text, 'Unsupported NUBASE format')
    rows={}
    for lineno,line in enumerate(text.splitlines(),1):
        if line.startswith('#') or len(line)<102: continue
        try:a,z,state=int(line[0:3]),int(line[4:7]),int(line[7:8])
        except ValueError:continue
        require((z,a,state) not in rows, 'Duplicate NUBASE identity')
        rows[(z,a,state)]={'line':lineno,'raw':line,'z':z,'a':a,'state_index':state,
          'spin_parity':line[88:102].strip(),'half_life_raw':line[69:88].strip(),'branches_raw':line[119:209].strip()}
    require((1,1,0) in rows, 'Incomplete NUBASE source')
    return rows


def entity(id_, kind,z,a=None,charge=None,nuclear_state=None,label=None,pilot=False):
    return dict(id=id_,kind=kind,z=z,a=a,charge=charge,nuclear_state=nuclear_state,
      electronic_state='ground' if kind in ('atom','atomic_isotope') else None,
      isotope_scope='specified' if a is not None else 'unspecified',label=label or id_,pilot=pilot,
      selection_provenance=[],native_state_correspondence='not_established')


def record(id_,entity_id,prop,value=None,kind='unknown',source=None,locator=None,method='not_available',reason=None,unc=None,conditions=None,**extra):
    return dict(id=id_,entity_id=entity_id,property=prop,value=value,unit=PROPERTY_SPECS[prop][1],value_kind=kind,
      uncertainty=unc or uncertainty(),method=method,exposure='retrospective',source_id=source,locator=locator,
      qualification=reason,physical_prediction=False,selection_status='adopted',conditions=conditions or {},**extra)


def validate_catalog(catalog,states,definitions,sources=None):
    require(catalog.get('schema')==SCHEMA, 'Wrong property catalog schema')
    entities={e['id']:e for e in states['entities']};defs={d['id']:d for d in definitions['properties']}
    require(len(entities)==len(states['entities']), 'Duplicate entity')
    require(len(defs)==len(definitions['properties']), 'Duplicate property definition')
    source_ids=set(s['id'] for s in sources) if sources is not None else set(catalog['source_ids'])
    for ent in entities.values():
        z,a,q,kind=ent['z'],ent['a'],ent['charge'],ent['kind']
        require(type(z) is int and 1<=z<=118, 'Invalid atomic number')
        require(kind in ('element','atom','isotope','atomic_isotope'),'Invalid entity kind')
        require(a is None or (type(a) is int and a>=z),'Invalid mass number')
        if kind in ('element','atom'):
            require(a is None and ent['isotope_scope']=='unspecified','Generic entity assigned isotope')
            expected=f'element:Z{z:03d}' if kind=='element' else f'atom:Z{z:03d}:q{q}:ground'
            require(ent['id']==expected,'Entity ID contradicts charge/Z/kind')
        if kind in ('atom','atomic_isotope'):
            require(type(q) is int and 0<=q<=z and ent['electronic_state']=='ground','Invalid atomic charge/electronic state')
        else:require(q is None and ent['electronic_state'] is None,'Non-atomic entity has electronic state/charge')
        if kind in ('isotope','atomic_isotope'):
            require(type(a) is int and ent['isotope_scope']=='specified' and ent['nuclear_state'],'Missing nuclear identity')
            pattern=r'isotope:([A-Z][a-z]?)-(\d+):(.+)' if kind=='isotope' else r'atomic-isotope:([A-Z][a-z]?)-(\d+):q(\d+):ground'
            match=re.fullmatch(pattern,ent['id']);require(match is not None and int(match[2])==a,'Entity ID contradicts isotope')
            require(match[1]==SYMBOLS[z-1],'Entity symbol contradicts atomic number')
            if kind=='isotope':require(match[3]==ent['nuclear_state'],'Entity ID contradicts nuclear state')
            else:require(int(match[3])==q and ent['nuclear_state']=='ground','Entity ID contradicts atomic isotope state')
    seen=set(); selected=set()
    for row in catalog['properties']:
        require(row['id'] not in seen,'Duplicate property row');seen.add(row['id'])
        require(row['entity_id'] in entities and row['property'] in defs,'Unknown entity/property')
        ent=entities[row['entity_id']]; spec=defs[row['property']]
        require(ent['kind']==spec['entity_kind'],'Property at wrong entity level')
        require(row['unit']==spec['unit'],'Wrong property unit')
        require(row['exposure']=='retrospective' and row['physical_prediction'] is False,'Property acquisition cannot confer prediction/independence')
        require(row['selection_status'] in ('adopted','alternative'),'Unknown selection status')
        key=(row['entity_id'],row['property'],row.get('transition'),row.get('level_id'),row.get('condition_id'))
        if row['selection_status']=='adopted':
            require(key not in selected,'Duplicate adopted property');selected.add(key)
        kind=row['value_kind'];require(kind in ('numeric','text','unknown','lower_limit','upper_limit','interval','not_applicable'),'Unknown value kind')
        if kind in ('numeric','lower_limit','upper_limit'):
            number(row['value']);require(row['source_id'] and row['locator'],'Numeric property requires source/locator')
            if row['property'] in ('atomic_mass','ionization_energy','line_wavelength','hyperfine_frequency','standard_atomic_weight'):
                require(number(row['value'])>0,'Positive physical quantity required')
            if row['property'] in ('excitation_energy','isomer_excitation_energy','charge_radius'):
                require(number(row['value'])>=0,'Nonnegative physical quantity required')
        elif kind=='interval':
            bounds=row.get('interval',{});require(row['value'] is None and number(bounds['lower'])<=number(bounds['upper']) and row['source_id'] and row['locator'],'Invalid sourced interval')
            if row['property'] in ('atomic_mass','ionization_energy','line_wavelength','hyperfine_frequency','standard_atomic_weight'):
                require(number(bounds['lower'])>0,'Positive quantity requires positive interval endpoints')
        elif kind=='text':require(type(row['value']) is str and row['source_id'] and row['locator'],'Text property requires sourced text')
        else:require(row['value'] is None and row['qualification'],'Missing property needs explicit null and reason')
        u=row['uncertainty'];require(set(u)>= {'value','kind','coverage','distribution'},'Incomplete uncertainty record')
        require(u['kind'] in UNCERTAINTY_KINDS,'Unknown uncertainty convention')
        if u['kind']=='exact_definition_only':require(row['method']=='definition' and u['value']=='0','Exact definition uncertainty requires a convention value')
        if u['value'] is not None:require(number(u['value'])>=0,'Negative uncertainty')
        if kind in ('unknown','not_applicable'):require(u['value'] is None and row['method']=='not_available','Unknown quantity has invented uncertainty or method')
        if row['source_id'] is not None:require(row['source_id'] in source_ids,'Property source is not bound')
        require(u['coverage'] is None and u['distribution'] is None,'No acquired joint distribution/coverage may be fabricated')
        require(row['method'] in ('not_available','evaluated','estimated','derived','measured','definition','theoretical','semiempirical'),'Unknown method')
        if ent['kind']=='atom':require(ent['a'] is None and ent['isotope_scope']=='unspecified','Generic atom assigned isotope')
        if row['property']=='hyperfine_frequency' and kind=='numeric':
            require(row.get('transition')=='ground_state_hyperfine_separation' and ent['charge']==0,'Unbound hyperfine transition')
            require(row['conditions'].get('electronic_state')=='ground' and row['conditions'].get('magnetic_field')=='unperturbed_zero_field','Unbound hyperfine conditions')
            require({'experimental_window','magnetic_sublevels'}<=set(row['conditions']),'Missing hyperfine condition qualifications')
        if row['property']=='excitation_energy' and kind=='numeric':require(row.get('level_id') and row.get('reference_level_id'),'Missing level identities')
        if row['property']=='line_wavelength' and kind=='numeric':require(row.get('transition') and row.get('lower_level_id') and row.get('upper_level_id') and row['conditions'].get('medium') in ('air','vacuum'),'Missing spectral endpoints/medium')
        if row['property'] in ('isotope_shift','zeeman_coefficient','stark_coefficient','polarizability') and kind=='numeric':
            require(type(row.get('condition_id')) is str and row['condition_id'] and row['conditions'],'Response property lacks a condition identity')
            conditions=row['conditions']
            if row['property']=='isotope_shift':
                reference=entities.get(row.get('reference_entity_id'))
                require(reference and reference['kind']=='atomic_isotope' and reference['z']==ent['z'] and reference['charge']==ent['charge'] and reference['a']!=ent['a'],'Isotope shift lacks a compatible distinct isotope endpoint')
                require(row.get('transition') and row.get('sign_convention')=='entity_minus_reference','Isotope shift lacks transition/sign convention')
            elif row['property']=='polarizability':
                require(conditions.get('state_id') and conditions.get('tensor_component') in ('scalar','vector','tensor'),'Polarizability lacks state/tensor component')
                require(conditions.get('frequency_unit')=='Hz' and number(conditions['frequency'])>=0,'Polarizability lacks probe frequency')
            else:
                require(row.get('transition') and row.get('lower_level_id') and row.get('upper_level_id'),'Field response lacks transition endpoints')
                require(type(conditions.get('magnetic_sublevels')) is list and len(conditions['magnetic_sublevels'])==2,'Field response lacks endpoint sublevels')
                order=1 if row['property']=='zeeman_coefficient' else 2
                require(type(conditions.get('response_order')) is int and conditions['response_order']==order,'Response order does not match coefficient unit')
                regime='magnetic_field_regime' if order==1 else 'electric_field_regime'
                require(conditions.get(regime),'Field-response regime absent')
    require(catalog['scope']=='source_inventory_not_native_prediction','Property scope promoted')


def build(root=ROOT):
    root=Path(root);require(sha(root/INPUTS)==INPUTS_SHA256,'Property input manifest differs from reviewed binding');inputs=read(root/INPUTS)
    sources=[]
    for src in inputs['sources']:
        p=source_path(root,src['path']);require(sha(p)==src['sha256'],'Source bytes changed: '+src['id'])
        if src.get('pdf_path'):require(sha(source_path(root,src['pdf_path']))==src['pdf_sha256'],'Retained PDF source changed: '+src['id'])
        sources.append(src)
    source_byid={x['id']:x for x in sources}; require(len(source_byid)==len(sources),'Duplicate source ID')
    ame=parse_ame(source_path(root,source_byid['ame2020']['path']).read_text())
    nubase=parse_nubase(source_path(root,source_byid['nubase2020']['path']).read_text())
    refs=[r for r in csv.DictReader(source_path(root,source_byid['reference-inputs']['path']).read_text().splitlines()) if r['record_kind']=='element_reference']
    require(len(refs)==118 and {int(r['z']) for r in refs}==set(range(1,119)), 'Reference requires exactly elements 1–118')
    legacy=read(source_path(root,source_byid['isotope-catalog']['path']))
    definitions={'schema':'matter1.property-definitions.v1','properties':[dict(id=k,entity_kind=v[0],unit=v[1],definition=v[2]) for k,v in PROPERTY_SPECS.items()],
      'axes':{'entity':['element','atom','isotope','atomic_isotope'],'method':['measured','evaluated','estimated','derived','theoretical','semiempirical','definition','not_available'],
        'exposure':['retrospective'],'value_kind':['numeric','text','unknown','lower_limit','upper_limit','interval','not_applicable']},
      'policies':['Decimal strings preserve reported digits; they do not make physical measurements exact.',
        'Uncertainty magnitude, statistical convention, distribution and covariance are distinct.',
        'NUBASE systematics/tentative markers remain visible; an absent source does not imply absent physical data.',
        'Element-reference A selections remain inherited unresolved choices, not standard atomic weights.',
        'Bulk-material properties require material/phase/temperature/pressure identity and are outside this atom/isotope catalog.']}
    entities=[];props=[];symbols={int(r['z']):r['symbol'] for r in refs}
    for r in refs:
        z=int(r['z'])
        eid=f'element:Z{z:03d}';entities.append(entity(eid,'element',z,label=r['symbol']))
        props.append(record(f'standard_atomic_weight:{eid}',eid,'standard_atomic_weight',reason='CIAAW evaluated value or interval not acquired; reference-A is not standard atomic weight.'))
        for charge in (0,1):
            id_=f'atom:Z{z:03d}:q{charge}:ground';entities.append(entity(id_,'atom',z,charge=charge,label=r['symbol']+('+' if charge else '')))
            for p in ('ground_configuration','ground_term','ionization_energy','electron_affinity','excitation_energy','line_wavelength','polarizability','zeeman_coefficient','stark_coefficient'):
                applicable=not(p=='electron_affinity' and charge!=0) and not(z==1 and charge==1)
                reason='Official atomic source not acquired in this version; no assertion that physical data do not exist.' if applicable else 'Outside this defined property domain: cation attachment or a bare nucleus has no applicable neutral-atom/electronic record.'
                props.append(record(f'{p}:{id_}',id_,p,kind='unknown' if applicable else 'not_applicable',reason=reason))
    selections={(int(r['z']),int(r['mass_a']),'ground') for r in refs}
    selections|={(x['Z'],x['A'],x['state']) for x in legacy['isotopes']}
    selections|={(z,a,'ground') for z,a,s in PILOTS}
    pilotkeys={(z,a) for z,a,s in PILOTS}
    for z,a,state in sorted(selections):
        symbol=symbols[z];id_=f'isotope:{symbol}-{a}:{state}'
        entities.append(entity(id_,'isotope',z,a,nuclear_state=state,label=f'{symbol}-{a} {state}',pilot=(z,a) in pilotkeys and state=='ground'))
        entities[-1]['selection_provenance']=(['inherited_reference_A_selection_unresolved'] if any(int(r['z'])==z and int(r['mass_a'])==a and state=='ground' for r in refs) else [])+(['curated_isotope_catalog:'+x['id'] for x in legacy['isotopes'] if (x['Z'],x['A'],x['state'])==(z,a,state)])+(['explicit_six_isotope_pilot'] if (z,a) in pilotkeys and state=='ground' else [])
        massrow=ame.get((z,a)) if state=='ground' else None
        for p in ('atomic_mass','mass_excess','binding_energy_per_nucleon','beta_minus_q'):
            value=massrow[p] if massrow else None
            if value is not None:
                props.append(record(f'{p}:{id_}',id_,p,value,'numeric','ame2020',f'line {massrow["line"]}; fixed-width {p}',
                    'estimated' if massrow['estimated'][p] else 'evaluated',reason='AME # systematics marker retained' if massrow['estimated'][p] else 'AME evaluated decimal; not an AOD prediction',
                    unc=uncertainty(massrow[p+'_uncertainty'],'source_reported_magnitude_convention_not_reconstructed')))
            else:props.append(record(f'{p}:{id_}',id_,p,reason='No matching AME2020 ground-state value; isomer/unknown identities are not replaced by ground states.'))
        if massrow and massrow['binding_energy_per_nucleon'] is not None:
            val=dec(number(massrow['binding_energy_per_nucleon'])*a);u=massrow['binding_energy_per_nucleon_uncertainty']
            props.append(record(f'binding_energy:{id_}',id_,'binding_energy',val,'numeric','ame2020',f'line {massrow["line"]}; A times binding energy/A','derived',
                reason='Derived from rounded source value; shares all source dependence.',unc=uncertainty(dec(number(u)*a) if u else None,'scaled_source_reported_magnitude'),input_estimated=massrow['estimated']['binding_energy_per_nucleon']))
        else:props.append(record(f'binding_energy:{id_}',id_,'binding_energy',reason='Required AME binding-energy input not available for this identity.'))
        for p,terms in [('neutron_separation_energy',[((z,a-1),1),((0,1),1),((z,a),-1)]),
                        ('proton_separation_energy',[((z-1,a-1),1),((1,1),1),((z,a),-1)]),
                        ('alpha_decay_q',[((z,a),1),((z-2,a-4),-1),((2,4),-1)])]:
            ok=state=='ground' and all(k in ame and ame[k]['mass_excess'] is not None for k,c in terms)
            if ok:
                value=dec(sum((number(ame[k]['mass_excess'])*c for k,c in terms),Decimal(0)))
                loc='; '.join(f'line {ame[k]["line"]} coefficient {c}' for k,c in terms)
                props.append(record(f'{p}:{id_}',id_,p,value,'numeric','ame2020',loc,'derived',
                    reason='Neutral-atom mass-excess reduction; covariance unavailable. No decay occurrence inferred.',
                    unc=uncertainty(kind='joint_covariance_not_supplied'),input_estimated=any(ame[k]['estimated']['mass_excess'] for k,c in terms),
                    input_mass_identities=[dict(z=k[0],a=k[1],coefficient=c,state='ground') for k,c in terms]))
            else:props.append(record(f'{p}:{id_}',id_,p,reason='Required parent/daughter/source masses not available or entity is not a ground-state mass record.'))
        nrow=nubase.get((z,a,0)) if state=='ground' else None
        for p in ('spin_parity','decay_branching','isotopic_abundance'):
            val=None
            if nrow:
                if p=='spin_parity':val=nrow['spin_parity']
                elif p=='isotopic_abundance':val='; '.join(v.strip() for v in nrow['branches_raw'].split(';') if v.strip().startswith('IS='))
                else:val='; '.join(v.strip() for v in nrow['branches_raw'].split(';') if not v.strip().startswith('IS='))
            if val:props.append(record(f'{p}:{id_}',id_,p,val,'text','nubase2020',f'line {nrow["line"]}; source columns retained','estimated' if '#' in val else 'evaluated',reason='Verbatim source qualification; no normalization, isotope-state substitution or universal abundance inferred.'))
            else:props.append(record(f'{p}:{id_}',id_,p,reason='No matching ground-state NUBASE field acquired for this entity; blank is not zero.'))
        for p in ('magnetic_dipole_moment','electric_quadrupole_moment','charge_radius'):
            props.append(record(f'{p}:{id_}',id_,p,reason='A state-resolved evaluated source has not been acquired for this property.'))
        props.append(record(f'isomer_excitation_energy:{id_}',id_,'isomer_excitation_energy',
          kind='not_applicable' if state=='ground' else 'unknown',
          reason='This identity is the ground state, not an isomer.' if state=='ground' else 'No adopted isomer-to-ground excitation energy acquired; candidate isomer must not be assigned a ground-state energy.'))
    h=read(source_path(root,source_byid['hyperfine-inventory']['path']))
    dt=read(source_path(root,source_byid['dt-catalog']['path']))
    for z,a,symbol in PILOTS:
        name=f'{symbol}-{a}';id_=f'atomic-isotope:{name}:q0:ground'
        entities.append(entity(id_,'atomic_isotope',z,a,0,'ground',name+' neutral ground',True))
        props.append(record('isotope_shift:'+name,id_,'isotope_shift',reason='No source-bound isotope pair and common electronic transition acquired.'))
        conditions=dict(electronic_state='ground',magnetic_field='unperturbed_zero_field',experimental_window=None,magnetic_sublevels=None)
        if name in ('H-1','Cs-133'):
            t=next(t for t in h['transitions'] if t['isotope_id']==f'atom:Z{z:03d}:A{a:03d}:q0')
            conditions['magnetic_sublevels']=['0','0']
            conditions['experimental_window']=t.get('measurement_interval')
            val=t.get('frequency_hz',t.get('defining_frequency_hz'));uv=t.get('standard_uncertainty_hz')
            props.append(record('hyperfine:'+name,id_,'hyperfine_frequency',val,'numeric','hyperfine-inventory','transitions/'+str(h['transitions'].index(t)),
              'definition' if name=='Cs-133' else 'measured',reason='Cs defining anchor is not a realized-clock measurement.' if name=='Cs-133' else 'Historical reported hydrogen value; prior exposure retained.',
              unc=uncertainty(uv,'exact_definition_only' if name=='Cs-133' else 'reported_standard_uncertainty'),conditions=conditions,transition='ground_state_hyperfine_separation',reference_dependence=t.get('covariance_status','See retained inventory source and correction context')))
        elif name in ('H-2','H-3'):
            t=dt['records'][0 if name=='H-2' else 2]
            props.append(record('hyperfine:'+name,id_,'hyperfine_frequency',t['value_hz'],'numeric','dt-catalog',f'records/{0 if name=="H-2" else 2}',
              'evaluated' if name=='H-3' else 'measured',reason=t['uncertainty_semantics'],unc=uncertainty(t['uncertainty_hz'],'reported_standard_uncertainty' if name=='H-3' and 'uncertainty_convention' in t else 'reported_last_digit_magnitude'),
              conditions=conditions,transition='ground_state_hyperfine_separation',reference_dependence=t['calibration_anchor'],not_independent_of=t['not_independent_of']))
        else:props.append(record('hyperfine:'+name,id_,'hyperfine_frequency',reason='No matching ground-state hyperfine frequency source acquired; electronic-state applicability must be established before comparison.'))
    if inputs.get('adoptions'):
        if __package__:
            from .matter1_property_adoption import adopt
        else:
            from matter1_property_adoption import adopt
        for adoption in inputs['adoptions']:
            src=source_byid[adoption['source_id']]
            adopted=adopt(source_path(root,src['path']).read_text(),adoption)
            # Remove only unsupplied placeholders; existing sourced alternatives
            # require an explicit selection policy and remain distinct records.
            keys={(r['entity_id'],r['property']) for r in adopted}
            props=[r for r in props if not((r['entity_id'],r['property']) in keys and r['value_kind']=='unknown')]+adopted
    catalog={'schema':SCHEMA,'scope':'source_inventory_not_native_prediction','properties':props,'source_ids':sorted(source_byid),
      'exposure':'retrospective_acquisition_before_any_future_model_freeze','atomic_isotope_substitution':False}
    states={'schema':'matter1.property-entities.v1','entities':entities,'pilot_isotopes':[f'{s}-{a}' for z,a,s in PILOTS],
      'reference_a_policy':'Inherited reference A choices; unresolved selection provenance remains unchanged.'}
    validate_catalog(catalog,states,definitions,sources)
    coverage_rows=[dict(entity_id=r['entity_id'],property=r['property'],status=r['value_kind'],reason=r['qualification']) for r in props]
    summary={'entities':len(entities),'properties':len(props),'numeric':sum(r['value_kind']=='numeric' for r in props),
      'text':sum(r['value_kind']=='text' for r in props),'unknown':sum(r['value_kind']=='unknown' for r in props),
      'element_z_coverage':len({e['z'] for e in entities if e['kind']=='element'}),'pilot_isotopes':len(PILOTS),
      'per_property':{p:{k:sum(r['property']==p and r['value_kind']==k for r in props) for k in ('numeric','text','unknown','not_applicable')} for p in PROPERTY_SPECS}}
    family_properties={'atomic_ground_states_ionization':['ground_configuration','ground_term','ionization_energy'],
      'electron_affinities':['electron_affinity'],'atomic_levels_lines':['excitation_energy','line_wavelength'],
      'nuclear_moments_radii':['magnetic_dipole_moment','electric_quadrupole_moment','charge_radius'],
      'standard_atomic_weights':['standard_atomic_weight'],'field_response_and_isotope_shifts':['polarizability','zeeman_coefficient','stark_coefficient','isotope_shift']}
    missing=[family for family,names in family_properties.items() if any(r['property'] in names and r['value_kind']=='unknown' for r in props)]
    coverage={'schema':'matter1.property-coverage.v1','summary':summary,'rows':coverage_rows,
      'acquisition_complete':not missing,'missing_source_families':missing,
      'interpretation':'All-118 identity coverage is not numeric-source completeness or physical-prediction validation.'}
    manifest={'schema':'matter1.property-sources.v1','sources':sources,'acquisition_attempts':inputs.get('acquisition_attempts',[]),
      'input_sha256':sha(root/INPUTS),'offline_reproducible':True,'new_external_targets_are_retrospective':True}
    return dict(zip(OUTPUTS,(definitions,states,catalog,coverage,manifest)))


def verify(root=ROOT):
    root=Path(root);expected=build(root)
    for name,value in expected.items():
        require((root/BASE/name).read_bytes()==canonical(value),'Property output differs: '+name)
    coverage=expected['coverage.json']
    return {'status':'PASS_ELEMENT_PROPERTY_CATALOG','schema':'matter1.property-verification.v1',
      'counts':coverage['summary'],'acquisition_complete':coverage['acquisition_complete'],
      'missing_source_families':coverage['missing_source_families'],'physical_predictions_executed':0,
      'outputs_sha256':{name:sha(root/BASE/name) for name in OUTPUTS},
      'scope':'Byte-bound source parsing, exact decimal reductions and identity/uncertainty validation only.'}
