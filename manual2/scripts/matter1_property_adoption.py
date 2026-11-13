"""Offline adoption adapters for separately acquired and reviewed source bytes.

No network acquisition occurs here. A new adoption requires retained raw bytes,
an input-manifest hash update and scientific review of identity/units/selection.
Synthetic parser fixtures establish parser behavior, not acquired data coverage.
"""
import csv
import io
import re
from decimal import Decimal


def clean(value):
    value=value.strip()
    if value.startswith('="') and value.endswith('"'):value=value[2:-1]
    return value.strip()


def asd_ionization(text, columns, source_id):
    if __package__:
        from .matter1_properties import record, uncertainty, number, require
    else:
        from matter1_properties import record, uncertainty, number, require
    table=list(csv.DictReader(io.StringIO(text)))
    needed={'z','charge','configuration','term','energy','uncertainty'}
    require(set(columns)>=needed,'ASD adoption requires explicit source-header mapping')
    require(table and all(v in table[0] for v in columns.values()),'ASD source columns absent')
    result=[];identities=set()
    for index,row in enumerate(table,2):
        ztext,qtext=clean(row[columns['z']]),clean(row[columns['charge']])
        if not ztext and not qtext:continue
        require(ztext.isdigit() and qtext.isdigit(),'ASD Z/charge is not integer')
        z,q=int(ztext),int(qtext)
        require(1<=z<=118 and q in (0,1) and q<z,'ASD row outside acquired atom scope')
        require((z,q) not in identities,'Duplicate ASD spectrum');identities.add((z,q))
        entity=f'atom:Z{z:03d}:q{q}:ground';locator=f'CSV row {index}; mapped source columns'
        bibliographic=clean(row[columns['reference']]) if columns.get('reference') else None
        for field,prop in [('configuration','ground_configuration'),('term','ground_term')]:
            val=clean(row[columns[field]])
            if val:result.append(record(f'{prop}:{entity}:asd',entity,prop,val,'text',source_id,locator,'evaluated',
               reason='Source ground-state designation, isotope unspecified; source theoretical qualifiers retained verbatim.',source_reference=bibliographic))
        raw=clean(row[columns['energy']]);raw_unc=clean(row[columns['uncertainty']])
        if not raw:continue
        method='evaluated';value=raw
        if raw.startswith('[') and raw.endswith(']'):method='semiempirical';value=raw[1:-1]
        elif raw.startswith('(') and raw.endswith(')'):method='theoretical';value=raw[1:-1]
        value=re.sub(r'\s+','',value);number(value)
        unc=re.sub(r'\s+','',raw_unc).strip('[]()') or None
        if unc is not None:number(unc)
        result.append(record(f'ionization_energy:{entity}:asd',entity,'ionization_energy',value,'numeric',source_id,locator,method,
          reason='ASD supplied eV column; source conversion/uncertainty retained. Brackets distinguish semiempirical and theoretical data.',
          unc=uncertainty(unc,'source_reported_magnitude_convention_not_reconstructed'),source_value_notation=raw,source_reference=bibliographic))
    return result


def curated_records(text, adoption, source_id):
    if __package__:
        from .matter1_properties import require
    else:
        from matter1_properties import require
    rows=[]
    for entry in adoption['records']:
        require(type(entry['source_match']) is str and entry['source_match'] in text,'Curated source passage no longer matches')
        row=dict(entry['record'])
        require(row['source_id']==source_id,'Curated record source mismatch')
        require(row['locator'],'Curated record needs a precise locator')
        rows.append(row)
    return rows


def adopt(text, adoption):
    parser=adoption['parser'];source_id=adoption['source_id']
    if parser=='nist_asd_ionization_csv_v1':
        if adoption.get('energy_unit')!='eV':raise ValueError('ASD ionization adoption requires an actual eV source column')
        return asd_ionization(text,adoption['columns'],source_id)
    if parser=='curated_property_records_v1':return curated_records(text,adoption,source_id)
    raise ValueError('Unsupported property adoption parser: '+parser)
