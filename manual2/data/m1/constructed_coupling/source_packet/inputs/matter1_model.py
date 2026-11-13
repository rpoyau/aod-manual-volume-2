#!/usr/bin/env python3
"""Exact declared reference relations; no native admission or execution engine.

The evaluator has no I/O. Readers validate immutable input bindings; serializers
return bytes. Only generate_matter1_ledger.py writes generated repository data.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path

SCHEMA_VERSION = 2
BASELINE_SHA256 = '202ab421ab2359b6b9e0838e0d5f39b8a8144b0f5ae03704853655c98db51246'
INTEGER_FIELDS = (
    'z', 'mass_a', 'm_order', 'enclosure_l', 'gamma_prev', 'gamma_m',
    'seat_s', 'a_tritrio', 'b_tetratrio', 'c_dimon', 'baryon_tritrio',
    'baryon_tetratrio', 'shell_dimon', 'pi_minus', 'h_mu', 'pi_plus',
    'support_sum', 'assigned_pressure', 'c_close', 's_residual', 'x_shedding',
    'assigned_ttl', 'window_w', 'n_f_count', 'is_group_boundary', 'is_named_anchor',
)
FIELDS = (
    'declaration_id', 'record_kind', 'input_binding_id', 'z', 'symbol', 'mass_a',
    'm_order', 'enclosure_l', 'enclosure_name', 'gamma_prev', 'gamma_m', 'seat_s',
    'hemisphere', 'a_tritrio', 'b_tetratrio', 'c_dimon', 'coord0_decl',
    'baryon_tritrio', 'baryon_tetratrio', 'shell_dimon', 'support_declaration',
    'pi_minus', 'h_mu', 'pi_plus', 'support_sum', 'assigned_pressure', 'c_close',
    's_residual', 'x_shedding', 'assigned_ttl', 'window_w', 'assigned_sheddic_path',
    'assigned_yro_status', 'assigned_route_class', 'n_f_count',
    'is_group_boundary', 'is_named_anchor', 'admission_status', 'execution_status',
)
REFERENCE_FIELDS = ('z', 'symbol', 'mass_a', 'record_kind', 'source_id', 'selection_policy_id')
MIGRATION = {'rd_fuse': 'support_sum', 'p_d': 'assigned_pressure', 'ttl_c': 'assigned_ttl'}
NATIVE_LANES = ('scope_instance', 'q4_traversal', 'admissibility', 'exact_kernel',
                'sadar_pairing', 'retained_return', 'fusion_certification')


class ValidationError(ValueError):
    """A source-bound reference contract was violated."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    try:
        return Path(path).read_bytes()
    except OSError as exc:
        raise ValidationError(f'{path}: {exc.strerror}') from exc


def read_json(path):
    try:
        return json.loads(read_bytes(path))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValidationError(f'{path}: malformed JSON: {exc}') from exc


def csv_rows(path, fields=None):
    try:
        reader = csv.DictReader(io.StringIO(read_bytes(path).decode('utf-8-sig'), newline=''))
        require(reader.fieldnames is not None, f'{path}: missing CSV header')
        require(len(set(reader.fieldnames)) == len(reader.fieldnames), f'{path}: duplicate CSV columns')
        if fields is not None:
            require(reader.fieldnames == list(fields), f'{path}: schema/header differs; expected {list(fields)}')
        result = list(reader)
        for i, row in enumerate(result, 2):
            require(None not in row and None not in row.values(), f'{path}:{i}: missing/extra CSV cells')
        return result
    except (UnicodeError, csv.Error) as exc:
        raise ValidationError(f'{path}: malformed CSV: {exc}') from exc


def integer(value, context):
    if type(value) is int:
        return value
    require(isinstance(value, str) and re.fullmatch(r'-?(?:0|[1-9][0-9]*)', value) is not None,
            f'{context}: expected exact canonical integer, got {value!r}')
    return int(value)


def typed_rows(path):
    rows = csv_rows(path, FIELDS)
    for i, row in enumerate(rows, 2):
        for field in INTEGER_FIELDS:
            row[field] = integer(row[field], f'{path}:{i}:{field}')
    return rows


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def csv_bytes(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def placement(z):
    require(type(z) is int and 1 <= z <= 126, f'Z={z!r}: outside reference scope 1..126')
    for m in range(3, 12):
        previous, endpoint = (m-1)*m-6, m*(m+1)-6
        if previous < z <= endpoint:
            s, length = z-previous, 2*m
            role = ('Pi_alpha (+1)' if s < m else 'H_mu (turnaround)' if s == m
                    else 'Pi_Omega (-1)' if s < length else 'Spine (filled 2m)')
            return {'m_order': m, 'enclosure_l': length, 'enclosure_name': {6: 'hexon', 8: 'octon', 10: 'decon'}.get(length, f'C{length}'),
                    'gamma_prev': previous, 'gamma_m': endpoint, 'seat_s': s,
                    'hemisphere': role, 'a_tritrio': (s+1)//2, 'b_tetratrio': s//2, 'c_dimon': s % 2}
    raise ValidationError('unreachable reference group')


def evaluate_support(z, mass_a):
    require(type(mass_a) is int and mass_a >= z, f'Z={z}, A={mass_a!r}: require integer A >= Z')
    p = placement(z)
    minus, plus = 30*z + 68*(mass_a-z), 4*p['seat_s']
    return {**p, 'baryon_tritrio': z, 'baryon_tetratrio': mass_a-z,
            'shell_dimon': z, 'pi_minus': minus, 'h_mu': 1, 'pi_plus': plus,
            'support_sum': minus+1+plus}


def load_contract(root):
    """Read, hash-bind and validate the declared inputs. Never writes."""
    root = Path(root)
    manifest = read_json(root/'evidence/input_manifest.json')
    require(manifest.get('schema_version') == 2, 'input_manifest.json: schema_version must be 2')
    required = {'data/m1/reference_inputs.csv', 'data/m1/model_inputs.json', 'data/m1/schema.json',
                'data/m1/input_provenance.json', 'data/m1/field_migration.json',
                'evidence/pr1_baseline_ledger_v1.csv', 'evidence/historical_sources.json'}
    required.update('data/m1/history/'+name for name in (
        'v94_placements.csv', 'v94_observable_matrix.csv', 'v94_value_maps.csv',
        'r24_occurrence_cards.csv', 'r24_transition_packets.csv', 'r24_sadar_declarations.csv'))
    require(set(manifest.get('files', {})) == required, 'input_manifest.json: required input inventory differs')
    for name, expected in manifest['files'].items():
        require(sha(read_bytes(root/name)) == expected, f'{name}: input SHA-256 mismatch')
    history = read_json(root/'evidence/historical_sources.json')
    historical_paths = {name for name in required if name.startswith('data/m1/history/')}
    require(set(history.get('members', {})) == historical_paths, 'historical_sources.json: raw member inventory differs')
    for name, binding in history['members'].items():
        require(binding.get('sha256') == sha(read_bytes(root/name)), f'{name}: historical source member SHA-256 mismatch')
    baseline = root/'evidence/pr1_baseline_ledger_v1.csv'
    require(sha(read_bytes(baseline)) == BASELINE_SHA256, f'{baseline}: reviewed baseline identity mismatch')
    old = csv_rows(baseline)
    require(len(old) == 126 and [integer(r['z'], 'baseline Z') for r in old] == list(range(1,127)),
            'baseline: exact Z coverage required')
    schema = read_json(root/'data/m1/schema.json')
    require(schema.get('version') == 2 and schema.get('fields') == list(FIELDS)
            and schema.get('integer_fields') == list(INTEGER_FIELDS), 'schema.json: unsupported field contract')
    migration = read_json(root/'data/m1/field_migration.json')
    require(migration.get('from_schema') == 1 and migration.get('to_schema') == 2
            and migration.get('numeric_renames') == MIGRATION, 'field_migration.json: numeric migration differs')
    provenance = read_json(root/'data/m1/input_provenance.json')
    require(provenance.get('baseline_sha256') == BASELINE_SHA256
            and provenance.get('reference_a', {}).get('status') == 'selection_provenance_unresolved'
            and provenance.get('unfilled_a', {}).get('status') == 'model_fixture_only'
            and provenance.get('assigned_inputs', {}).get('status') == 'declared_model_inputs'
            and provenance.get('isotope_parameterization', {}).get('status') == 'conditional_arithmetic_only',
            'input_provenance.json: source or claim status differs')
    model = read_json(root/'data/m1/model_inputs.json')
    required_model = {'model_id', 'schema_version', 'scope', 'source', 'support_operands', 'capacity_multiplier',
                      'window_rule', 'pressure_rule', 'ttl_rule', 'shedding_z', 'acceptor_z', 'unfilled_start_z'}
    require(set(model) == required_model and model['schema_version'] == 2,
            'model_inputs.json: unsupported keys/schema')
    require(isinstance(model['support_operands'], dict) and all(type(v) is int for v in model['support_operands'].values()),
            'model_inputs.json: support operands require exact integers')
    require(model['support_operands'] == {'tritrio': 30, 'tetratrio': 68, 'seat_dimon': 4, 'hinge': 1},
            'model_inputs.json: support specialization differs from frozen baseline')
    for key in ('capacity_multiplier', 'unfilled_start_z'):
        require(type(model[key]) is int, f'model_inputs.json:{key}: exact integer required')
    require(model['capacity_multiplier'] == 3 and model['unfilled_start_z'] == 119,
            'model_inputs.json: legacy fixture scope/capacity changed')
    require(model['window_rule'] == 'L' and model['pressure_rule'] == 'legacy-z-class-offset-v1'
            and model['ttl_rule'] == 'legacy-class-window-offset-v1', 'model_inputs.json: unsupported assigned rule')
    for key in ('shedding_z', 'acceptor_z'):
        values = model[key]
        require(isinstance(values, list) and all(type(z) is int and 1 <= z <= 118 for z in values)
                and values == sorted(set(values)), f'model_inputs.json:{key}: unique sorted Z integers required')
    require(not set(model['shedding_z']) & set(model['acceptor_z']), 'assigned classes overlap unexpectedly')
    refs = csv_rows(root/'data/m1/reference_inputs.csv', REFERENCE_FIELDS)
    require(len(refs) == 126, 'reference_inputs.csv: expected 126 rows')
    for i, (r, previous) in enumerate(zip(refs, old), 1):
        for key in ('z', 'mass_a'):
            r[key] = integer(r[key], f'reference_inputs.csv:{i+1}:{key}')
        require(r['z'] == i and r['symbol'] == previous['symbol'] and r['mass_a'] == int(previous['mass_a']),
                f'reference_inputs.csv:Z={i}: baseline identity/reference-A changed')
        require(r['mass_a'] >= i, f'reference_inputs.csv:Z={i}: A must be >= Z')
        kind = 'element_reference' if i <= 118 else 'unfilled_reference_slot'
        require(r['record_kind'] == kind, f'reference_inputs.csv:Z={i}: record_kind mismatch')
        require(r['source_id'] == 'pr1-421e0cad-reference-fixture'
                and r['selection_policy_id'] == ('legacy-reference-a-unresolved' if i <= 118 else 'legacy-projected-a'),
                f'reference_inputs.csv:Z={i}: provenance binding mismatch')
    return refs, model, old


def build_rows(refs, model):
    """Evaluate typed declarations. No I/O or native certification."""
    rows = []
    for ref in refs:
        z, mass_a = ref['z'], ref['mass_a']
        p = evaluate_support(z, mass_a)
        m,L,s = p['m_order'],p['enclosure_l'],p['seat_s']
        capacity = model['capacity_multiplier']*L
        if z >= model['unfilled_start_z']:
            status, pressure, ttl = 'unfilled', capacity+3*(z-118), 0
            path, yro = 'C24 (open_loss)', f'Yro_{L+1}(open_cutoff)'
        elif z in model['shedding_z']:
            units = 1 if z in (43,61) else (z-84)//6+1
            status, pressure, ttl = 'surplus', capacity+3*units, L-1
            path, yro = f'C{L+2}', f"Yro_{L+1}({p['a_tritrio']}:{p['b_tetratrio']}:{p['c_dimon']};B_{z})"
        elif z in model['acceptor_z']:
            status, pressure, ttl = 'deficit', capacity-3, L
            path, yro = 'none (deficit/open E2^0)', 'none'
        else:
            status, pressure, ttl = 'neutral', capacity, L+2
            path, yro = 'none (retained)', 'none'
        a,b,c = p['a_tritrio'],p['b_tetratrio'],p['c_dimon']
        row = {'declaration_id': f'matter1:reference:Z{z:03}:A{mass_a:03}' if z<=118 else f'matter1:slot:Z{z:03}',
               'record_kind': ref['record_kind'], 'input_binding_id': f'reference-input:Z{z:03}',
               'z': z, 'symbol': ref['symbol'], 'mass_a': mass_a, **p,
               'coord0_decl': f'0|- :: {z}:{mass_a}:0:{L}<{a}:{b}:{c}::{L}>',
               'support_declaration': f'Tritrio^{a}::Tetratrio^{b}::Dimon^{c}::out({L})',
               'assigned_pressure': pressure, 'c_close': capacity, 's_residual': pressure-capacity,
               'x_shedding': max(0,pressure-capacity), 'assigned_ttl': ttl, 'window_w': L,
               'assigned_sheddic_path': path, 'assigned_yro_status': yro, 'assigned_route_class': status,
               'n_f_count': s, 'is_group_boundary': int(s==L), 'is_named_anchor': int(s==L and z<=118),
               'admission_status': 'pending', 'execution_status': 'not_executed'}
        rows.append({key: row[key] for key in FIELDS})
    return rows


def verify_rows(actual, expected, baseline):
    require(len(actual) == 126, f'ledger: expected 126 rows, got {len(actual)}')
    require([r['z'] for r in actual] == list(range(1,127)), 'ledger:z: expected unique ordered coverage 1..126')
    for row, target, old in zip(actual, expected, baseline):
        z = target['z']
        require(set(row) == set(FIELDS), f'ledger:Z={z}: unknown/missing fields')
        for field in INTEGER_FIELDS:
            require(type(row[field]) is int, f'ledger:Z={z}:{field}: exact int required')
        for field in FIELDS:
            require(row[field] == target[field], f'ledger:Z={z}:{field}: expected {target[field]!r}, got {row[field]!r}')
        # Independent baseline conservation for every numeric field in v1.
        for key, value in old.items():
            if re.fullmatch(r'-?(?:0|[1-9][0-9]*)', value):
                new_key = MIGRATION.get(key, key)
                require(new_key in row and row[new_key] == int(value), f'baseline conservation:Z={z}:{key}')
        require(row['symbol'] == old['symbol'], f'baseline conservation:Z={z}:symbol')


def history_artifacts(root, rows):
    base = Path(root)/'data/m1/history'
    placements = csv_rows(base/'v94_placements.csv')
    matrix = csv_rows(base/'v94_observable_matrix.csv')
    maps = csv_rows(base/'v94_value_maps.csv')
    occurrences = csv_rows(base/'r24_occurrence_cards.csv')
    transitions = csv_rows(base/'r24_transition_packets.csv')
    sadar = csv_rows(base/'r24_sadar_declarations.csv')
    def by_z(records, key, context):
        result = {}
        for r in records:
            z = integer(r[key], context)
            require(z not in result, f'{context}: duplicate Z={z}')
            result[z] = r
        require(set(result) == set(range(1,119)), f'{context}: expected Z=1..118')
        return result
    old = by_z(placements,'AtomicNumber','v94 placements')
    occ = by_z(occurrences,'element_Z','r24 occurrence')
    trans = by_z(transitions,'element_Z','r24 transition')
    flows = by_z(sadar,'element_Z','r24 SADAR')
    crosswalk=[]
    fields=(('coord0_group_m','m_order'),('range_position','seat_s'),('Gamma_prev','gamma_prev'),('Gamma_m','gamma_m'))
    for row in rows[:118]:
        z=row['z']; v,o,t,f=old[z],occ[z],trans[z],flows[z]
        require(v['Symbol']==row['symbol'] and v['closure_lane'].replace('_','')==f"C{row['enclosure_l']}", f'v94 placement:Z={z}: symbol/enclosure changed')
        for before,after in fields:
            require(integer(v[before],f'v94:{z}:{before}')==row[after], f'v94 placement:Z={z}:{after} changed')
        require(o['symbol']==t['symbol']==f['symbol']==row['symbol'], f'history:Z={z}: symbol mismatch')
        require(t['occurrence_id']==o['occurrence_id'] and f['transition_packet_id']==t['transition_packet_id'], f'history:Z={z}: broken declaration join')
        require(t['duon_current_status']==t['sadar_flow_status']=='declared_not_executed_in_this_gate', f'history:Z={z}: transition status promoted')
        require(f['duon_current_flow_status']==f['sadar_temporal_flow_status']=='declared_not_executed', f'history:Z={z}: SADAR status promoted')
        for source in (o,t,f):
            require(source['target_value_read_status']=='not_read' and source['metric_report_status']=='closed' and source['score_status']=='no_score', f'history:Z={z}: target/metric status promoted')
        crosswalk.append({'declaration_id':row['declaration_id'],'z':z,'symbol':row['symbol'],
                          'v94_placement_comparison':'six_fields_match','r24_occurrence_declaration_id':o['occurrence_id'],
                          'r24_transition_declaration_id':t['transition_packet_id'],'r24_sadar_declaration_id':f['sadar_packet_id'],
                          'predecessor_transition_status':t['duon_current_status'],'predecessor_sadar_status':f['sadar_temporal_flow_status'],
                          'candidate_execution_status':row['execution_status']})
    require(len(matrix)==708, 'v94 observable inventory: expected 708 rows')
    seen=set(); coverage=[]
    for r in matrix:
        z=integer(r['AtomicNumber'],'v94 matrix Z'); lane=r['lane']
        require(1<=z<=118 and lane in ('E0','E1','E2','E3','E4','E5'), 'v94 observable inventory: unknown identity/lane')
        require((z,lane) not in seen, 'v94 observable inventory: duplicate pair');seen.add((z,lane))
        require(r['Symbol']==rows[z-1]['symbol'], f'v94 matrix:Z={z}: symbol mismatch')
        expected='active_registry' if lane=='E0' else 'declared_lane_not_scored_in_v94'
        require(r['row_status']==expected, f'v94 matrix:{z}:{lane}: status differs')
        coverage.append({'declaration_id':rows[z-1]['declaration_id'],'z':z,'symbol':r['Symbol'],'lane':lane,
                         'lane_name':r['lane_name'],'predecessor_status':r['row_status'],
                         'candidate_status':'reference_registry' if lane=='E0' else 'not_scored'})
    require(len(maps)==10 and len({r['value_map'] for r in maps})==10, 'value maps: expected ten unique records')
    value_status=[]
    for r in maps:
        require(r['status']=='deferred_not_attached','value map: predecessor status promoted')
        value_status.append({'value_map':r['value_map'],'predecessor_status':r['status'],'candidate_status':'deferred_not_attached','reason':r['reason']})
    artifacts={}
    for name,records in [('declaration_crosswalk.csv',crosswalk),('observable_coverage.csv',coverage),('value_map_status.csv',value_status)]:
        artifacts['data/m1/history/'+name]=csv_bytes(records,list(records[0]))
    return artifacts


def audit_report(rows):
    assigned = Counter(r['assigned_route_class'] for r in rows)
    disjoint=Counter(('named_anchor_' if r['is_named_anchor'] else '')+r['assigned_route_class'] for r in rows)
    c22=[r for r in rows if r['enclosure_l']==22]
    occupancy=sum(r['record_kind']=='element_reference' for r in c22)
    retained=sum(r['assigned_ttl']>=r['window_w'] for r in c22)
    return {'schema_version':2,'profile':'static_relational_reference','status':'PASS',
            'total_reference_slots':len(rows),'named_element_references':sum(r['record_kind']=='element_reference' for r in rows),
            'unfilled_reference_slots':sum(r['record_kind']=='unfilled_reference_slot' for r in rows),
            'labelled_reference_occupancy_fraction':str(Fraction(118,len(rows))),
            'c22_labelled_reference_occupancy_fraction':str(Fraction(occupancy,len(c22))),
            'c22_assigned_ttl_qualified_fraction':str(Fraction(retained,len(c22))),
            'assigned_class_counts':dict(sorted(assigned.items())),
            'disjoint_class_counts':dict(sorted(disjoint.items())),
            'independent_attributes':{'named_anchors':sum(r['is_named_anchor'] for r in rows),
                                      'named_anchors_with_assigned_surplus':sum(r['is_named_anchor'] and r['assigned_route_class']=='surplus' for r in rows)},
            'executed_checks':{'complete_unique_reference_slots':126,'exact_reference_relations':126,'preserved_numeric_baseline_rows':126,
                               'v94_placement_field_comparisons':708,'historical_observable_pairs':708,'r24_declaration_joins':118},
            'native_evidence_lanes':{lane:'not_executed' for lane in NATIVE_LANES},
            'observable_lanes':{'E0':'reference_registry',**{f'E{i}':'not_scored' for i in range(1,6)}},
            'interpretation':'PASS covers reference integrity and conditional arithmetic only; no admission, native duration, retention or empirical agreement is inferred.'}


def tex_table(rows):
    lines=[r'{\scriptsize',r'\setlength{\tabcolsep}{3.0pt}',r'\begin{longtable}{@{}rllccrrrrrrll@{}}',
           r'\caption{\textbf{Complete declared reference and conditional support ledger.} $Z=1\dots118$ names supplied elements; slots $119\dots126$ are unfilled reference positions. Pressure and route classes are assigned inputs; the support sum is a conditional expression, not an admitted native duration. Grouping follows \mainsection{subsec:coord-zero-support-enclosure-grouping}; the expression specializes \mainequation{eq:curling-support-model}.}\label{tab:matter1-full-ledger}\\',
           r'\toprule',r'$Z$ & Sym & Ref. $A$ & $\mathsf{C}_{2m}$ & Local $a{:}b{:}c$ & $u_-$ & $h$ & $u_+$ & $U$ & $P^{\mathrm{fix}}$ & $C^{\mathrm{fix}}$ & $S^{\mathrm{fix}},X^{\mathrm{fix}}$ & Assigned class\\',r'\midrule',r'\endfirsthead',
           r'\toprule',r'$Z$ & Sym & Ref. $A$ & $\mathsf{C}_{2m}$ & Local $a{:}b{:}c$ & $u_-$ & $h$ & $u_+$ & $U$ & $P^{\mathrm{fix}}$ & $C^{\mathrm{fix}}$ & $S^{\mathrm{fix}},X^{\mathrm{fix}}$ & Assigned class\\',r'\midrule',r'\endhead',r'\bottomrule',r'\endfoot']
    for r in rows:
        status=r['assigned_route_class'].capitalize()+(' + anchor' if r['is_named_anchor'] else '')
        if r['record_kind']=='unfilled_reference_slot':status='Unfilled fixture'
        values=[str(r['z']),r['symbol'],str(r['mass_a']),f"$\\mathsf{{C}}_{{{r['enclosure_l']}}}$",
                f"${r['a_tritrio']}:{r['b_tetratrio']}:{r['c_dimon']}$"]
        values.extend(str(r[k]) for k in ('pi_minus','h_mu','pi_plus','support_sum','assigned_pressure','c_close'))
        values.extend([f"${r['s_residual']},{r['x_shedding']}$",status])
        lines.append(' & '.join(values)+r'\\')
    lines.extend([r'\end{longtable}',r'}'])
    return ('\n'.join(lines)+'\n').encode()


def expected_artifacts(root, rows):
    history=history_artifacts(root,rows)
    summary=[]
    for m in range(3,12):
        group=[r for r in rows if r['m_order']==m];first,last=group[0],group[-1]
        summary.append({'m':m,'enclosure':f'C_{2*m}','seats_2m':2*m,'gamma_prev':first['gamma_prev'],'gamma_m':last['gamma_m'],
                        'z_range':f"{first['z']}..{last['z']}",'hinge_z':first['gamma_prev']+m,
                        'boundary_slot_z':last['z'],'boundary_slot_kind':last['record_kind'],'c_close':3*(2*m)})
    payloads={'matter1_elements_1_118_ledger.csv':csv_bytes(rows,FIELDS),
              'matter1_coord0_enclosure_summary.csv':csv_bytes(summary,list(summary[0])),
              'matter1_audit_report.json':json_bytes(audit_report(rows))}
    outputs={f'data/{sub}{name}':payload for sub in ('m1/','') for name,payload in payloads.items()}
    outputs.update(history);outputs['sections/generated_elements_longtable.tex']=tex_table(rows)
    return outputs


def verify(root):
    root=Path(root)
    refs,model,baseline=load_contract(root)
    expected=build_rows(refs,model)
    actual=typed_rows(root/'data/m1/matter1_elements_1_118_ledger.csv')
    verify_rows(actual,expected,baseline)
    for name,payload in expected_artifacts(root,expected).items():
        require(read_bytes(root/name)==payload, f'{name}: persisted content differs from declared inputs; not modified')
    return audit_report(actual)
