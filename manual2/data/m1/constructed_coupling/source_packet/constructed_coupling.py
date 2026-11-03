"""A declared isotope-indexed construction and coupled-count experiment.

This executes a finite folded field, not a physical nuclear decay law. The
native admission module is byte-preserved. Internal constituent histories are
retained formation inputs, not resolved evolving nucleons. No lifetime is read.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
import csv
from dataclasses import asdict, replace
from fractions import Fraction
from functools import cached_property, lru_cache
import gzip
import hashlib
import heapq
import io
from itertools import product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
IMPLEMENTATION_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
sys.path.insert(0, str(HERE / 'upstream/manual/scripts'))
import aod_native_closure_wave as n

INNER = 'declared:matter1-construction:inner'
OUTER = 'declared:matter1-coupling:outer'


class CountTrace(n.Trace):
    """Memoize the original accessor on this immutable native trace subclass.

    The source verifier and admission rules are unchanged. dataclasses.replace
    constructs a fresh object and therefore cannot inherit a stale digest.
    """
    @cached_property
    def trace_digest(self):
        return n.Trace.trace_digest.fget(self)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()


def digest(value):
    return hashlib.sha256(canon(value)).hexdigest()


def check_sources():
    binding = json.loads((HERE / 'source_bindings.json').read_text())
    for path, expected in binding['sha256'].items():
        require(hashlib.sha256((HERE/path).read_bytes()).hexdigest() == expected,
                'Bound input changed: '+path)
    return binding


def catalogue(p, q):
    require(type(p) is int and type(q) is int and p in (1, 3) and q in (2, 3, 4),
            'Unsupported exact support signature')
    return tuple([('word', *word) for word in product(range(q), repeat=p)] +
                 [('shell', axis) for axis in range(q)])


def vertices_from_axes(axes):
    value = 0
    vertices = [0]
    for axis in tuple(axes) + tuple(reversed(axes)):
        value ^= 1 << axis
        vertices.append(value)
    require(value == 0 and all(n.hamming(a,b) == 1 for a,b in zip(vertices,vertices[1:])),
            'Construction is not a closed H1 path')
    return tuple(vertices)


def indices_for(start, branch, extra=0):
    return tuple(start + j + (1+extra if j > branch else 0)
                 for j in range(2*branch+1))


def bound_trace(lineage, occurrence, vertices, indices, branch, scope, scale, ancestor=None):
    raw = n.trace(lineage, occurrence, vertices=vertices, scope=scope, scale=scale,
                  turn=branch, start_index=indices[0])
    t = CountTrace(**{key:getattr(raw,key) for key in n.Trace.__dataclass_fields__})
    t = replace(t, indices=tuple(indices),
                reflection=replace(t.reflection, committed_at=indices[-1],
                                   turnaround_committed_at=indices[branch]))
    if ancestor is not None:
        t = replace(t, ancestor=ancestor)
    n.validate_trace(t)
    return t


@lru_cache(maxsize=None)
def constituent(name, p, q):
    """Separate return IDs for every retained constituent; no count aliases."""
    cat = catalogue(p,q)
    vertices = vertices_from_axes(tuple(item[-1] for item in cat))
    lineage = 'constituent:'+name
    components = tuple(n.certified(n.trace(lineage, 'unit:'+str(j), scope=INNER,
                                           start_index=3*j)) for j in range(q))
    ids = tuple(c.return_id for _,c,_ in components)
    construction = (tuple(ids for _ in range(p)), ids)
    records, motifs = [], []
    registry = {c.certificate_digest:c for _,c,_ in components}
    rd = 2*len(cat)+1
    require(rd == n.rd(p,q), 'Enumerated component RD mismatch')
    for occurrence in range(2):
        start = 30+occurrence*(rd+3)
        t = bound_trace(lineage, 'seed:'+str(occurrence), vertices,
                        indices_for(start,len(cat)),len(cat),INNER,0)
        c = n.certify(t)
        registry[c.certificate_digest] = c
        m = n.motif_witness(f'{p}:{q}',t,construction,
                            tuple((x,y) for x,y,_ in components),registry,enclosure=6)
        records.append((t,c,dict(registry)));motifs.append(m)
    w = n.wave(records,tuple(motifs))
    n.validate_wave(w)
    return w,cat,components


def inventory(z, neutron_count):
    require(type(z) is int and type(neutron_count) is int and z>0 and neutron_count>=0,
            'Inventory requires positive integer Z and nonnegative integer N')
    return tuple([(f'p{j:03d}',3,3) for j in range(z)] +
                 [(f'n{j:03d}',3,4) for j in range(neutron_count)])


class FoldedField:
    def __init__(self, name, specs, start_cut):
        require(bool(specs) and len({s[0] for s in specs}) == len(specs),
                'Distinct actual constituent constructions required')
        self.name = name
        self.specs = tuple(specs)
        self.inner = tuple(constituent(*s)[0] for s in specs)
        self.proposal = n.fold_proposal(self.inner,OUTER,1)
        self.ancestor = 'fold:'+n.digest(self.proposal)
        self.occurrence_map = tuple((w.identity,position,item,item[-1])
                                    for spec,w in zip(specs,self.inner)
                                    for position,item in enumerate(constituent(*spec)[1]))
        self.axes = tuple(item[-1] for item in self.occurrence_map)
        self.vertices = vertices_from_axes(self.axes)
        self.branch = len(self.axes)
        self.rd = 2*self.branch+1
        self.lineage = 'folded:'+name
        self.records, self.returns, self.hashes, self.prefixes = [], [], [], []
        for occurrence in range(2):
            start = 1000+occurrence*(self.rd+3)
            self.add_return(indices_for(start,self.branch), 'seed:'+str(occurrence))
        self.identity = self.wave().identity
        self.action = -1
        self.occurrence = 2
        self.current_indices = []
        self.due = start_cut
        self.used_pressure = 1
        self.used_binding = digest([])
        self.atomic_steps = []
        self.actions = []

    def add_return(self, indices, occurrence):
        t = bound_trace(self.lineage,occurrence,self.vertices,indices,self.branch,
                        OUTER,1,self.ancestor)
        c = n.certify(t,'outer',inner=self.inner)
        record = (t,c,{c.certificate_digest:c})
        if not self.records:
            n.fold(self.inner,record)
        self.records.append(record)
        self.returns.append(t.indices[-1])
        self.hashes.append(t.trace_digest)
        self.prefixes.append(n.digest(tuple(self.hashes)))
        return t,c

    def wave(self):
        return n.wave(self.records)

    def prefix(self, cut):
        index = bisect_right(self.returns,cut)
        return self.prefixes[index-1] if index else n.digest(())

    def count(self, lo, hi):
        return sum(lo<k<=hi for k in self.returns[1:])

    def phase(self):
        return len(self.returns)-1


class Channel:
    def __init__(self, receiver, sender):
        self.receiver,self.sender = receiver,sender
        self.events,self.evidence,self.motifs = [],[],[]
        lineage = receiver.identity+'|'+sender.identity
        pivot = n.trace(lineage,'pivot',scope=OUTER,scale=1,start_index=1)
        self.pivot = (pivot,n.certify(pivot))
        self.construction = ((1,-1),(self.pivot[1].certificate_digest,0),(-1,1))

    def operative(self):
        if len(self.events)<2:
            return 0,None
        last = self.events[-2:]
        r = n.RCD(self.receiver.identity,self.sender.identity,OUTER,
                  tuple(e.identity for e in last),self.sender.rd,
                  tuple(e.reflection[0] for e in last))
        return r.duration(),r

    def accept(self, packet):
        a,b = self.receiver,self.sender
        t = bound_trace(a.identity+'|'+b.identity,packet['id'],b.vertices,
                        indices_for(packet['start'],b.branch,packet['reflection'][0]),
                        b.branch,OUTER,1)
        cut = t.indices[-1]
        require(cut==packet['arrives'], 'Contact arrival differs from its support trace')
        c = n.certify(t)
        event = n.Contact(packet['id'],a.identity,b.identity,OUTER,cut,
                          a.prefix(cut),b.prefix(cut),tuple(packet['reflection']),t,c)
        registry={c.certificate_digest:c,self.pivot[1].certificate_digest:self.pivot[1]}
        motif=n.motif_witness('Duon',t,self.construction,(self.pivot,),registry)
        self.events.append(event);self.evidence.append(dict(packet));self.motifs.append(motif)
        return event,motif

    def current_wave(self):
        return n.wave([(e.support_trace,e.support_certificate,
                        {e.support_certificate.certificate_digest:e.support_certificate})
                       for e in self.events],tuple(self.motifs))


class Engine:
    def __init__(self, contract, case, emit_files=True):
        require(case in contract['cases'], 'Undeclared execution case')
        require(type(contract['Z']) is int and type(contract['N']) is int and
                contract['Z']>0 and contract['N']>=1, 'Exact constituent integers required')
        require(all(type(contract[k]) is int for k in
                    ('engine_start_cut','intervention_cut','horizon_cut')) and
                contract['engine_start_cut']<contract['intervention_cut']<contract['horizon_cut'],
                'Strictly ordered integer execution cuts required')
        require(all(contract[k] is None for k in
                    ('parent_capacity','parent_loss_rule','decay_channel_or_daughter_map','physical_seconds')),
                'This experiment does not admit an invented decay or SI model')
        self.contract,self.case = contract,case
        count = contract['N']-(case=='one_fewer_346_constituent')
        start = contract['engine_start_cut']
        self.fields = {
            'P':FoldedField('P',inventory(contract['Z'],count),start),
            'R':FoldedField('R',(('reference',3,3),),start),
            'B0':FoldedField('B0',(('background0',3,4),),start),
            'B1':FoldedField('B1',(('background1',3,4),),start),
            'B2':FoldedField('B2',(('background2',3,4),),start),
        }
        self.base=('P','R','B0','B1')
        self.active=set();self.channels={};self.heap=[];self.serial=0;self.packet_serial=0
        self.pending={};self.packets=[];self.clicks=[];self.pressures=[];self.closures=[]
        self.actions=[];self.loads=[];self.last_response={};self.emit_files=emit_files
        self.prefix_hash=hashlib.sha256();self.trajectory_hash=hashlib.sha256()
        self.node_hash={name:hashlib.sha256() for name in self.fields}
        self.intervened=False
        for receiver in self.base:
            for sender in self.base:
                if receiver==sender:continue
                ch=self.activate(receiver,sender)
                for start_seed in (100000,200000):
                    packet={'id':f'seed:{receiver}:{sender}:{start_seed}',
                            'receiver':receiver,'sender':sender,'emitted':start_seed-1,
                            'start':start_seed,'arrives':start_seed+self.fields[sender].rd,
                            'reflection':[0,0],'lag_at_emission':0,'seed':True,
                            'source_prefix':self.fields[sender].prefix(start_seed-1),
                            'receiver_prefix':self.fields[receiver].prefix(start_seed-1),
                            'source_return':self.fields[sender].records[-1][0].return_id,
                            'source_phase':1,'receiver_phase':1}
                    event,motif=ch.accept(packet)
                    self.clicks.append(self.click_row(packet,event,motif,formation=True))
        require(max(e.committed for ch in self.channels.values() for e in ch.events)<start,
                'Execution begins before its admitted contact history')
        # B2 has the same committed one-way receiving history in every run.
        # The intervention adds its return influence on P, without introducing
        # a fast unconditioned ticker at a late cut.
        ch=self.activate('B2','P')
        for start_seed in (100000,200000):
            packet={'id':f'seed:B2:P:{start_seed}', 'receiver':'B2','sender':'P',
                    'emitted':start_seed-1,'start':start_seed,
                    'arrives':start_seed+self.fields['P'].rd,'reflection':[0,0],
                    'lag_at_emission':0,'seed':True,
                    'source_prefix':self.fields['P'].prefix(start_seed-1),
                    'receiver_prefix':self.fields['B2'].prefix(start_seed-1),
                    'source_return':self.fields['P'].records[-1][0].return_id,
                    'source_phase':1,'receiver_phase':1}
            event,motif=ch.accept(packet)
            self.clicks.append(self.click_row(packet,event,motif,formation=True))
        for name in self.fields:self.push(start,'node',name)
        self.push(contract['intervention_cut'],'intervention',None)

    def push(self,cut,kind,payload):
        self.serial+=1;heapq.heappush(self.heap,(cut,self.serial,kind,payload))

    def activate(self,receiver,sender):
        key=(receiver,sender)
        self.active.add(key)
        if key not in self.channels:
            self.channels[key]=Channel(self.fields[receiver],self.fields[sender])
        return self.channels[key]

    def pressure(self,name):
        total=self.fields[name].rd
        terms=[{'self_RD':total}]
        for key in sorted(self.active):
            if key[0]!=name:continue
            rho,rcd=self.channels[key].operative()
            if rcd is None:continue
            if self.case=='same_addition_feedback_disabled' and key==('P','B2'):continue
            total+=rho
            terms.append({'channel':list(key),'rho':rho,'contact_ids':list(rcd.contact_ids),
                          'support_RD':rcd.support,'reflection_counts':list(rcd.reflection_counts)})
        return total,terms

    def node_action(self,cut,name):
        node=self.fields[name]
        require(cut==node.due,'Stale action deadline')
        if node.action==-1:
            node.current_indices=[cut];node.action=0;kind='start';edge_index=0;before=after=0
        elif node.action==node.branch:
            node.action+=1;kind='hinge';edge_index=len(node.current_indices)-1
            before=after=node.vertices[edge_index]
        else:
            node.current_indices.append(cut);node.action+=1;kind='edge'
            edge_index=len(node.current_indices)-1
            before,after=node.vertices[edge_index-1:edge_index+1]
            require(n.hamming(before,after)==1,'Non-H1 executed edge')
            node.atomic_steps.append(cut)
        completed=node.action==node.rd
        row={'cut':cut,'field':name,'occurrence':node.occurrence,'kind':kind,
             'edge_index':edge_index,'from':before,'to':after,
             'pressure_used':node.used_pressure,'pressure_binding':node.used_binding}
        self.actions.append(row);node.actions.append(row)
        raw=canon(row)+b'\n';self.node_hash[name].update(raw)
        if name in self.base:
            self.trajectory_hash.update(raw)
            if cut<self.contract['intervention_cut']:self.prefix_hash.update(raw)
        if completed:
            t,c=node.add_return(node.current_indices,'run:'+str(node.occurrence))
            self.closures.append({'field':name,'cut':cut,'occurrence':node.occurrence,
                                  'return_id':t.return_id,'certificate_digest':c.certificate_digest,
                                  'trace_digest':t.trace_digest,'RD':node.rd,
                                  'atomic_traversals':2*node.branch,
                                  'previous_separation_cuts':node.returns[-1]-node.returns[-2]})
            node.occurrence+=1;node.action=-1
        return completed

    def emit(self,cut,sender):
        source=self.fields[sender]
        for receiver,src in sorted(self.active):
            if src!=sender:continue
            target=self.fields[receiver]
            lag=target.phase()-source.phase()
            self.packet_serial+=1
            packet={'id':f'packet:{sender}:{receiver}:{source.occurrence}', 'receiver':receiver,'sender':sender,
                    'emitted':cut,'start':cut+1,'arrives':cut+1+source.rd+max(0,lag),
                    'reflection':[max(0,lag),max(0,-lag)],'lag_at_emission':lag,'seed':False,
                    'source_prefix':source.prefix(cut),'receiver_prefix':target.prefix(cut),
                    'source_return':source.records[-1][0].return_id,
                    'source_phase':source.phase(),'receiver_phase':target.phase()}
            self.pending[packet['id']]=packet;self.packets.append(packet)
            self.push(packet['arrives'],'arrival',packet['id'])

    def click_row(self,packet,event,motif,formation=False):
        ch=self.channels[(packet['receiver'],packet['sender'])]
        rho,rcd=ch.operative()
        return {**packet,'committed':event.committed,'formation':formation,
                'contact_digest':n.digest(asdict(event)),
                'support_return_id':event.support_trace.return_id,
                'support_trace_digest':event.support_trace.trace_digest,
                'duon_witness_digest':motif.witness_digest,'operative_rho':rho,
                'rcd_contact_ids':list(rcd.contact_ids) if rcd else [],
                'left_prefix_at_click':event.left_prefix,'right_prefix_at_click':event.right_prefix}

    def arrive(self,cut,identity):
        packet=self.pending.pop(identity)
        require(packet['emitted']<packet['start']<cut,'Noncausal current arrival')
        ch=self.channels[(packet['receiver'],packet['sender'])]
        event,motif=ch.accept(packet)
        require(event.committed==cut,'Returned support is in the future')
        row=self.click_row(packet,event,motif)
        self.clicks.append(row)
        if packet['receiver']=='P':
            self.loads.append({'cut':cut,'contact_id':identity,'sender':packet['sender'],
                               'rho':row['operative_rho'],'abs_committed_lag':abs(packet['lag_at_emission']),
                               'nonnegative_term':row['operative_rho']*abs(packet['lag_at_emission']),
                               'operative_contacts':row['rcd_contact_ids']})

    def schedule(self,cut,name,completed):
        node=self.fields[name]
        pressure,terms=self.pressure(name)
        binding=digest(terms)
        if self.last_response.get(name)!=(pressure,binding):
            self.pressures.append({'cut':cut,'field':name,'pressure':pressure,'terms':terms,
                                   'binding':binding})
            self.last_response[name]=(pressure,binding)
        node.used_pressure=pressure;node.used_binding=binding
        node.due=cut+(1 if completed else pressure)
        self.push(node.due,'node',name)

    def run(self,end=None):
        end=self.contract['horizon_cut'] if end is None else end
        while self.heap and self.heap[0][0]<=end:
            cut=self.heap[0][0];batch=[]
            while self.heap and self.heap[0][0]==cut:batch.append(heapq.heappop(self.heap))
            for _,_,kind,payload in batch:
                if kind=='intervention':
                    self.intervened=True
                    if self.case in ('add_346_to_parent','same_addition_feedback_disabled'):
                        self.activate('P','B2')
            done=[]
            for _,_,kind,payload in batch:
                if kind=='node':done.append((payload,self.node_action(cut,payload)))
            for _,_,kind,payload in batch:
                if kind=='arrival':self.arrive(cut,payload)
            for name,completed in done:
                if completed:self.emit(cut,name)
            for name,completed in done:self.schedule(cut,name,completed)
        self.end=end
        return self

    def validate(self):
        waves={name:node.wave() for name,node in self.fields.items()}
        for w in waves.values():n.validate_wave(w)
        return_index={name:{t.return_id:t.indices[-1] for t,_,_ in node.records}
                      for name,node in self.fields.items()}
        returned={row['id']:row for row in self.clicks if not row['formation']}
        for packet in self.packets:
            source,target=self.fields[packet['sender']],self.fields[packet['receiver']]
            cut=packet['emitted']
            require(packet['source_prefix']==source.prefix(cut) and
                    packet['receiver_prefix']==target.prefix(cut),'Emission prefix changed')
            require(packet['source_phase']==source.count(-1,cut) and
                    packet['receiver_phase']==target.count(-1,cut),'Future phase used in emission')
            require(return_index[packet['sender']].get(packet['source_return'])==cut,
                    'Tick not caused by an actual reclosure')
            require((packet['id'] in returned)==(packet['arrives']<=self.end),
                    'Missing or prematurely counted click')
        current_states=[]
        for (receiver,sender),ch in self.channels.items():
            for event in ch.events:
                require(event.left_prefix==self.fields[receiver].prefix(event.committed) and
                        event.right_prefix==self.fields[sender].prefix(event.committed),
                        'Contact binds a substituted prefix')
            if len(ch.events)>=2:
                w=ch.current_wave();n.validate_wave(w)
                state=n.seat_duon(w,n.initial_state(w),True)
                require(state.identity==w.identity and state.closure_status=='seated',
                        'Seating changed Duon identity')
                current_states.append({'receiver':receiver,'sender':sender,
                                       'duon_identity':w.identity,'duad_identity':state.identity,
                                       'state':'seated','return_count':len(w.returns),
                                       'added_propagation_slowdown':None})
        native_comparisons=[]
        for receiver,sender in (('P','R'),('R','P')):
            ch=self.channels[(receiver,sender)]
            selected=[e for e in ch.events if self.fields['P'].returns[1]<e.committed<=self.end]
            lo=self.fields['P'].returns[1]
            if len(selected)>=2 and all(self.fields[k].count(lo,self.end)>0 for k in (receiver,sender)):
                comparison=n.compare(waves[receiver],waves[sender],tuple(selected[-2:]),(lo,self.end))
                require(comparison['duration']==ch.operative()[0], 'Native RCD reduction differs')
                native_comparisons.append({'receiver':receiver,'sender':sender,
                                           'ratio':str(comparison['ratio']),
                                           'operative_RCD':comparison['duration'],
                                           'lag':str(comparison['lag'])})
        return {'admitted_outer_waves':len(waves),
                'admitted_distinct_parent_constituents':len(self.fields['P'].inner),
                'admitted_returned_currents':current_states,
                'actual_tick_count':len(self.packets),'actual_click_count':len(returned),
                'pending_current_count':len(self.pending),'atomic_edges':sum(len(x.atomic_steps) for x in self.fields.values()),
                'counter_conservation':len(self.packets)==len(returned)+len(self.pending),
                'native_P_R_comparisons':native_comparisons,
                'physical_nuclear_admission':False,'physical_decay_prediction':False}


def ratio(numerator,denominator):
    return str(Fraction(numerator,denominator)) if denominator else None


def window_rows(engine):
    p,r=engine.fields['P'],engine.fields['R']
    formation=p.returns[1]
    endpoints=[k for k in engine.contract['window_endpoints'] if k<=engine.end]
    if not endpoints or endpoints[-1]!=engine.end:endpoints.append(engine.end)
    windows=[('cumulative',formation,k) for k in endpoints]
    windows += [('disjoint',a,b) for a,b in zip([formation]+endpoints,endpoints)]
    rows=[]
    for kind,lo,hi in windows:
        cp,cr=p.count(lo,hi),r.count(lo,hi)
        steps=sum(lo<k<=hi for k in p.atomic_steps)
        prior=p.count(-1,lo)-r.count(-1,lo)
        endlag=p.count(-1,hi)-r.count(-1,hi)
        arrivals=[row for row in engine.loads if lo<row['cut']<=hi]
        rows.append({'case':engine.case,'kind':kind,'lo_exclusive':lo,'hi_inclusive':hi,
                     'new_parent_closures':cp,'reference_bips':cr,'parent_atomic_traversals':steps,
                     'closures_per_reference_bip':ratio(cp,cr),
                     'closures_per_atomic_traversal':ratio(cp,steps),
                     'phase_bias':'0','unwrapped_lag_start':prior,'unwrapped_lag_end':endlag,
                     'lag_drift':endlag-prior,'parent_structural_RD':p.rd,
                     'reference_structural_RD':r.rd,
                     'parent_window_load':sum(row['nonnegative_term'] for row in arrivals),
                     'load_contact_count':len(arrivals),'parent_capacity':None,'parent_loss':None,
                     'seconds':None})
    return rows


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True,default=str)+'\n')


def pair_rows(engine):
    """Keep each actual direction; window RCD and operative RCD are distinct."""
    rows=[]
    for window in window_rows(engine):
        lo,hi=window['lo_exclusive'],window['hi_inclusive']
        for receiver,sender in sorted(engine.channels):
            if 'P' not in (receiver,sender):continue
            ch=engine.channels[(receiver,sender)]
            a,b=engine.fields[receiver],engine.fields[sender]
            selected=[e for e in ch.events if lo<e.committed<=hi]
            history=[e for e in ch.events if e.committed<=hi]
            na,nb=a.count(lo,hi),b.count(lo,hi)
            window_rcd=(b.rd+sum(e.reflection[0] for e in selected)) if len(selected)>=2 else None
            operative=(b.rd+sum(e.reflection[0] for e in history[-2:])) if len(history)>=2 else None
            rows.append({'case':engine.case,'window_kind':window['kind'],
                         'lo_exclusive':lo,'hi_inclusive':hi,'receiver':receiver,'sender':sender,
                         'receiver_reclosures':na,'sender_reclosures':nb,'count_ratio':ratio(na,nb),
                         'bias':'0','window_lag':na-nb,
                         'unwrapped_lag_end':a.count(-1,hi)-b.count(-1,hi),
                         'support_RD':b.rd,'window_contacts':len(selected),
                         'window_RCD':window_rcd,'last_two_contact_rho':operative,
                         'window_contact_ids':[e.identity for e in selected],
                         'native_full_comparison_admissible':len(selected)>=2 and na>0 and nb>0})
    return rows


def write_csv(path,rows):
    require(bool(rows),'Cannot write a schema-free empty table')
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader()
        writer.writerows({k:(canon(v).decode() if isinstance(v,(dict,list,tuple)) else v)
                          for k,v in row.items()} for row in rows)


def write_jsonl_gz(path,rows):
    with path.open('wb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as out:
            for row in rows:out.write(canon(row)+b'\n')


def construction_record(engine):
    result={'schema':'admitted-finite-construction-v1','physical_identification':False,
            'inner_resolution':'frozen formation histories; not dynamically resolved nuclear constituents',
            'fields':[]}
    for name,node in engine.fields.items():
        entries=[]
        for spec,w in zip(node.specs,node.inner):
            entries.append({'name':spec[0],'motif':f'{spec[1]}:{spec[2]}:6','identity':w.identity,
                            'scope':w.scope,'scale':w.scale,
                            'primitive_components':[asdict(t) for t,_,_ in constituent(*spec)[2]],
                            'returns':[asdict(t) for t in w.returns],
                            'certificate_digests':[c.certificate_digest for c in w.certificates],
                            'motif_witness_digests':[m.witness_digest for m in w.motif_witnesses]})
        result['fields'].append({'name':name,'identity':node.identity,'scope':OUTER,'scale':1,
                                 'initial_closure_cut':node.returns[0],
                                 'recurrence_admission_cut':node.returns[1],
                                 'branch_occurrences':node.branch,'RD':node.rd,
                                 'inner':entries,'fold_proposal':node.proposal,
                                 'scope_map_sha256':digest(node.occurrence_map),
                                 'scope_map':node.occurrence_map,
                                 'seed_return_ids':[t.return_id for t,_,_ in node.records[:2]]})
    return result


def export(engine,dest,checks):
    dest.mkdir(parents=True,exist_ok=True)
    rows=window_rows(engine)
    write_json(dest/'checks.json',checks)
    write_json(dest/'constructed_state.json',construction_record(engine))
    write_csv(dest/'closures.csv',engine.closures)
    write_csv(dest/'windowed_relations.csv',rows)
    write_csv(dest/'directional_rd_rcd.csv',pair_rows(engine))
    write_jsonl_gz(dest/'atomic_and_hinge_events.jsonl.gz',engine.actions)
    write_jsonl_gz(dest/'tick_events.jsonl.gz',engine.packets)
    write_jsonl_gz(dest/'click_and_rcd_events.jsonl.gz',engine.clicks)
    write_jsonl_gz(dest/'pressure_events.jsonl.gz',engine.pressures)
    write_jsonl_gz(dest/'nonnegative_load_terms.jsonl.gz',engine.loads)
    write_jsonl_gz(dest/'outer_return_witnesses.jsonl.gz',(
        {'field':name,'scope':OUTER,'scale':1,'lineage':t.lineage,
         'occurrence_start_id':t.event_ids[0],'indices':t.indices,
         'trace_digest':t.trace_digest,'certificate_digest':c.certificate_digest,
         'return_id':t.return_id,'ancestor':t.ancestor}
        for name,node in engine.fields.items() for t,c,_ in node.records))
    terminal=[]
    for name,node in engine.fields.items():
        terminal.append({'field':name,'cut':engine.end,'complete_returns_total':len(node.records),
                         'new_returns_since_parent_formation':node.count(engine.fields['P'].returns[1],engine.end),
                         'partial_return_atomic_traversals':max(0,len(node.current_indices)-1) if node.action>=0 else 0,
                         'next_action_cut':node.due,'next_action_kind_index':node.action,
                         'parent_decay_status':'not evaluated: retention and daughter rules absent',
                         'survival_probability':None,'seconds':None})
    write_csv(dest/'terminal_survival.csv',terminal)
    prediction={'schema':'counted-construction-v1','case':engine.case,
                'classification':'deterministic declared finite construction; not an isotope decay prediction',
                'contract_sha256':hashlib.sha256((HERE/'contract.json').read_bytes()).hexdigest(),
                'implementation_sha256':IMPLEMENTATION_SHA256,
                'source_binding_sha256':hashlib.sha256((HERE/'source_bindings.json').read_bytes()).hexdigest(),
                'effective_inventory':{'Z':engine.contract['Z'],'N':engine.contract['N']-(engine.case=='one_fewer_346_constituent')},
                'formation_cut':engine.fields['P'].returns[1],'horizon_cut':engine.end,
                'base_prefix_sha256':engine.prefix_hash.hexdigest(),
                'base_trajectory_sha256':engine.trajectory_hash.hexdigest(),
                'field_trajectory_sha256':{k:v.hexdigest() for k,v in engine.node_hash.items()},
                'final_counts':rows[len([r for r in rows if r['kind']=='cumulative'])-1],
                'physical_isotope_closures_until_decay':None,'half_life':None,'seconds':None,
                'unresolved':['physical nuclear identification','resolved inner nuclear evolution',
                              'parent closure capacity','loss/transformation and daughter witness'],
                'file_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.iterdir()) if p.is_file() and p.name!='prediction.json'}}
    prediction['prediction_sha256']=digest(prediction)
    write_json(dest/'prediction.json',prediction)
    return prediction


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--case',choices=json.loads((HERE/'contract.json').read_text())['cases'])
    args=parser.parse_args()
    check_sources()
    contract=json.loads((HERE/'contract.json').read_text())
    cases=[args.case] if args.case else contract['cases']
    for case in cases:
        print('executing '+case,flush=True)
        engine=Engine(contract,case).run()
        print('validating '+case,flush=True)
        checks=engine.validate()
        prediction=export(engine,args.out/case,checks)
        print(json.dumps({'case':case,'counts':prediction['final_counts'],
                          'prediction_sha256':prediction['prediction_sha256']}),flush=True)


if __name__=='__main__':
    main()
