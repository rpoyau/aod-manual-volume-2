"""Exact witnessed response/burden-to-retention fixture, with no isotope fit."""
from __future__ import annotations
import argparse
from copy import deepcopy
import csv
from dataclasses import asdict, replace
from fractions import Fraction as Q
import hashlib
from itertools import product
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
CODE_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
sys.path.insert(0,str(HERE/'upstream/manual/scripts'))
import aod_native_closure_wave as n

INNER='declared:retention-fixture:inner'
OUTER='declared:retention-fixture:outer'
PLUS=(0,8,9,1,0)
MINUS=(0,4,5,1,0)
EXIT=(0,2,10)


def require(condition,message):
    if not condition:raise ValueError(message)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode()


def digest(value):return hashlib.sha256(canonical(value)).hexdigest()


def verify_sources():
    record=json.loads((HERE/'source_bindings.json').read_text())
    for name,sha in record['sha256'].items():
        require(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==sha,'Changed bound source: '+name)
    return record


def default_contract():return json.loads((HERE/'contract.json').read_text())


class Clock:
    def __init__(self):self.cut=0;self.events=[]
    def event(self,kind,**data):
        self.cut+=1
        row={'cut':self.cut,'kind':kind,**data};self.events.append(row)
        return self.cut
    def walk(self,lineage,occurrence,vertices,turn,*,scope=INNER,scale=0,
             orientation=1,extra=0,ancestor=None,closed=True):
        require(type(orientation) is int and orientation in (-1,1),'Exact orientation required')
        require(type(extra) is int and extra>=0,'Exact reflection extent required')
        start=self.event('start',lineage=lineage,occurrence=occurrence)
        indices=[start]
        for j,(a,b) in enumerate(zip(vertices,vertices[1:]),1):
            if j==turn+1:
                self.event('hinge',lineage=lineage,occurrence=occurrence)
                for r in range(extra):self.event('reflection',lineage=lineage,occurrence=occurrence,index=r)
            require(n.hamming(a,b)==1,'Executed path is not H1')
            indices.append(self.event('edge',lineage=lineage,occurrence=occurrence,index=j,source=a,target=b))
        raw=n.trace(lineage,occurrence,vertices=vertices,scope=scope,scale=scale,
                    turn=turn,start_index=start,chirality=orientation)
        t=replace(raw,indices=tuple(indices),reflection=replace(raw.reflection,
                  committed_at=indices[-1],turnaround_committed_at=indices[turn]))
        if ancestor is not None:t=replace(t,ancestor=ancestor)
        n.validate_trace(t,require_closed=closed)
        return t


class Field:
    def __init__(self,name,clock,seed_count,background=False):
        require(type(seed_count) is int and seed_count>=2,'Recurring preparation required')
        self.name=name;self.lineage='retention:'+name;self.records=[];self.motifs=[]
        self.components=();self.construction=None;self.pending=None
        self.vertices=PLUS;self.turn=2
        if background:
            catalogue=tuple([('word',*word) for word in product(range(4),repeat=3)]+
                            [('shell',axis) for axis in range(4)])
            axes=tuple(x[-1] for x in catalogue)
            vertex=0;vertices=[0]
            for axis in axes+tuple(reversed(axes)):
                vertex ^=1<<axis;vertices.append(vertex)
            self.vertices=tuple(vertices);self.turn=len(axes)
            require(2*self.turn+1==n.rd(3,4),'Background support/RD mismatch')
            records=[]
            for axis in range(4):
                t=clock.walk(self.lineage,'unit:'+str(axis),(0,1<<axis,0),1)
                records.append((t,n.certify(t)))
            self.components=tuple(records)
            ids=tuple(cert.return_id for _,cert in self.components)
            self.construction=(tuple(ids for _ in range(3)),ids)
        for j in range(seed_count):self.advance(clock,'seed:'+str(j))
        self.identity=self.wave().identity

    def advance(self,clock,occurrence,orientation=1):
        require(self.pending is None,'Cannot complete a different return over a pending path')
        vertices=self.vertices if self.components or orientation==1 else MINUS
        t=clock.walk(self.lineage,occurrence,vertices,self.turn,orientation=orientation)
        cert=n.certify(t)
        registry={cert.certificate_digest:cert,**{c.certificate_digest:c for _,c in self.components}}
        if self.components:
            self.motifs.append(n.motif_witness('3:4',t,self.construction,self.components,registry,enclosure=6))
        self.records.append((t,cert,registry))
        return t

    def hold_pending(self,clock,occurrence):
        require(self.pending is None,'An unfinished return already exists')
        start=clock.event('start',lineage=self.lineage,occurrence=occurrence)
        a,b=self.vertices[:2];require(n.hamming(a,b)==1,'Invalid partial edge')
        cut=clock.event('edge',lineage=self.lineage,occurrence=occurrence,index=1,source=a,target=b)
        self.pending={'start':start,'last_cut':cut,'vertices':[a,b],'atomic_steps':1,
                      'status':'pending; no return certificate','occurrence':occurrence}

    def wave(self):return n.wave(self.records,tuple(self.motifs))
    def bip(self):return len(self.records)-1
    def prefix(self,cut):return n.wave_prefix(self.wave(),cut)


class Channel:
    def __init__(self,candidate,sender,clock):
        self.candidate=candidate;self.sender=sender
        self.lineage=candidate.identity+'|'+sender.identity
        self.events=[];self.reverse_traces=[];self.motifs=[];self.evidence=[]
        self.pivot_trace=clock.walk(self.lineage,'current-pivot',(0,1,0),1)
        self.pivot=n.certify(self.pivot_trace)
        self.current_construction=((1,-1),(self.pivot.certificate_digest,0),(-1,1))

    def contact(self,clock,occurrence,reverse_extra=0):
        a,b=self.candidate,self.sender
        emission=clock.event('tick',channel=self.lineage,occurrence=occurrence,
                             source_return=b.records[-1][0].return_id,
                             source_prefix=b.prefix(clock.cut),receiver_prefix=a.prefix(clock.cut))
        t=clock.walk(self.lineage,occurrence,b.vertices,b.turn)
        cert=n.certify(t)
        reverse=clock.walk(b.identity+'|'+a.identity,'reverse:'+occurrence,
                           b.vertices,b.turn,extra=reverse_extra)
        rd=len(t.vertices)-1+len(t.roles)-2
        forward_count=t.indices[-1]-t.indices[0]-rd
        reverse_count=reverse.indices[-1]-reverse.indices[0]-rd
        require(forward_count>=0 and reverse_count>=0,'Negative reflection count')
        event=n.Contact('contact:'+self.sender.name+':'+occurrence,a.identity,b.identity,
                        INNER,t.indices[-1],a.prefix(t.indices[-1]),b.prefix(t.indices[-1]),
                        (forward_count,reverse_count),t,cert)
        registry={cert.certificate_digest:cert,self.pivot.certificate_digest:self.pivot}
        motif=n.motif_witness('Duon',t,self.current_construction,
                              ((self.pivot_trace,self.pivot),),registry)
        self.events.append(event);self.reverse_traces.append(reverse);self.motifs.append(motif)
        click=clock.event('click',contact_id=event.identity,contact_committed=event.committed,
                          support_return=t.return_id,source_return=b.records[-1][0].return_id)
        evidence={'tick_cut':emission,'forward_return_cut':event.committed,'click_cut':click,
                  'contact':asdict(event),'reverse_trace':asdict(reverse),
                  'duon_witness_digest':motif.witness_digest,'source_return':b.records[-1][0].return_id}
        self.evidence.append(evidence)
        return event

    def comparison(self,cut,window_length,reverse=False):
        require(len(self.events)>=2,'Repeated contacts required')
        a,b=self.candidate.wave(),self.sender.wave()
        prior=(n.compare(a,b,tuple(self.events[-3:-1]),(0,self.events[-2].committed))['lag']
               if len(self.events)>2 else Q(0))
        result=n.compare(a,b,tuple(self.events[-2:]),(0,cut),reverse=reverse,prior_lag=prior)
        rho=n.participation(result['rcd'],window_length,result['rcd'].domain)
        return {**result,'rho':rho,'C3':1,'pressure':Q(rho),
                'candidate_bip':self.candidate.bip(),'sender_bip':self.sender.bip(),'prior_lag':prior}

    def validate(self):
        a,b=self.candidate.wave(),self.sender.wave()
        for event,reverse in zip(self.events,self.reverse_traces):
            require((event.left,event.right,event.scope)==(a.identity,b.identity,INNER),
                    'Contact belongs to a substituted wave pair')
            require(event.left_prefix==n.wave_prefix(a,event.committed) and
                    event.right_prefix==n.wave_prefix(b,event.committed),
                    'Contact does not bind its actual committed pair prefixes')
            n.admitted(event.support_trace,event.support_certificate,
                        {event.support_certificate.certificate_digest:event.support_certificate})
            n.validate_trace(reverse)
            rd=len(event.support_trace.vertices)-1+len(event.support_trace.roles)-2
            require(event.reflection==(event.support_trace.indices[-1]-event.support_trace.indices[0]-rd,
                                      reverse.indices[-1]-reverse.indices[0]-rd),
                    'Directional reflection differs from witnessed traces')
        wave=n.wave([(e.support_trace,e.support_certificate,
                      {e.support_certificate.certificate_digest:e.support_certificate}) for e in self.events],
                    tuple(self.motifs))
        n.validate_wave(wave)
        return wave


class Fixture:
    def __init__(self,contract,case,observer=True,candidate_seed_override=None):
        require(case in contract['cases'],'Undeclared fixture case')
        require(contract['physical_seconds'] is None and contract['isotope_state_assignment'] is None,
                'Physical identification is not a fixture input')
        require(contract['experimental_inputs']==[] and contract['fit_parameters']==[],
                'No experimental inputs or fitted parameters are permitted')
        self.contract=deepcopy(contract);self.case=case;self.observer=observer
        self.clock=Clock();self.prefix='';self.responses=[];self.observations=[]
        self.parent_records=[];self.parent_states=[];self.parent_folds=[]
        seeds=contract['formation_returns']
        self.candidate=Field('candidate',self.clock,seeds['candidate'] if candidate_seed_override is None else candidate_seed_override)
        self.reference=Field('reference',self.clock,seeds['reference'])
        self.background=Field('background',self.clock,seeds['background'],background=True)
        self.channels={name:Channel(self.candidate,field,self.clock)
                       for name,field in (('reference',self.reference),('background',self.background))}
        for name,ch in self.channels.items():
            for j in range(2):ch.contact(self.clock,'formation:'+str(j))
        span=contract['horizon']['allowed_cut_window'][1]-contract['horizon']['allowed_cut_window'][0]
        self.window_length=span
        reference_relation=self.channels['reference'].comparison(self.clock.cut,span)
        self.unit=reference_relation['rcd'].support
        self.capacity=n.Q(contract['capacity']['diagnostic_units'])*self.unit
        require(self.unit>0 and self.capacity>=0,'Positive normalization and nonnegative capacity required')
        self.initial_reference_bip=self.reference.bip()
        self.initial_candidate_bip=self.candidate.bip()
        self.current_state=replace(n.initial_state(self.candidate.wave()),
                                   committed=self.clock.event('preparation_state'),capacity=self.capacity)
        for j in range(seeds['outer_parent']):self.fold_parent('formation:'+str(j))
        self.measurement_origin=self.clock.cut
        self.formation_event_count=len(self.clock.events)
        self.pending_inputs=None;self.pending_decision=None

    def fold_parent(self,occurrence):
        inner=(self.candidate.wave(),)
        proposal=n.fold_proposal(inner,OUTER,1)
        t=self.clock.walk('retention:outer-parent',occurrence,PLUS,2,scope=OUTER,scale=1,
                           ancestor='fold:'+n.digest(proposal))
        cert=n.certify(t,'outer',inner=inner)
        record=(t,cert,{cert.certificate_digest:cert})
        folded=n.fold(inner,record)
        require(self.current_state.committed<t.indices[0],'Current state did not precede outer closure')
        self.parent_records.append(record);self.parent_folds.append(folded)
        self.parent_states.append(self.current_state)
        if len(self.parent_records)>=2:n.validate_wave(n.wave(self.parent_records))
        self.clock.event('outer_return',return_id=t.return_id,certificate=cert.certificate_digest,
                         inner_prefix=n.wave_prefix(inner[0],self.clock.cut))

    def measured_reference(self):return self.reference.bip()-self.initial_reference_bip
    def measured_candidate(self):return self.candidate.bip()-self.initial_candidate_bip
    def raw_signed(self):return sum((Q(r['raw_signed']) for r in self.responses),Q(0))
    def raw_burden(self):return sum((Q(r['raw_burden']) for r in self.responses),Q(0))

    def load_selection(self):
        active=list(self.responses)
        exclusion=[]
        if self.case=='net_memory':selected=abs(self.raw_signed())
        elif self.case=='burden_feedback_off' and len(active)>=2:
            selected=Q(0)
            exclusion=[{'response_id':x['id'],'reason':'next-decision input gate disabled; history retained'} for x in active]
            active=[]
        else:
            if self.case=='burden_latest_response_window' and len(active)>1:
                exclusion=[{'response_id':x['id'],'reason':'outside most-recent-response window; history retained'} for x in active[:-1]]
                active=active[-1:]
            selected=sum((Q(x['raw_burden']) for x in active),Q(0))
        return selected,[x['id'] for x in active],exclusion

    def prepare_next(self,reverse_extra=0):
        require(self.pending_inputs is None,'Previous comparison not yet consumed')
        require(self.measured_reference()<self.contract['horizon']['new_reference_returns'],
                'Reference horizon already reached')
        expected=self.measured_reference()+1
        self.reference.advance(self.clock,'new:'+self.prefix+':'+str(expected))
        require(self.measured_reference()==expected,'No actual reference return for this decision')
        contexts={}
        self.channels['reference'].contact(self.clock,'new:'+self.prefix+':'+str(expected),reverse_extra)
        contexts['reference']=self.channel_operands('reference')
        if self.case=='burden_background_pending' and expected==2:
            self.background.hold_pending(self.clock,'held:'+self.prefix)
        elif self.background.pending is None:
            self.background.advance(self.clock,'new:'+self.prefix+':'+str(expected))
        self.channels['background'].contact(self.clock,'new:'+self.prefix+':'+str(expected),reverse_extra)
        contexts['background']=self.channel_operands('background')
        # The current contacts are pending operands of a subsequent response.
        # Retention consumes only preceding, committed response records.
        selected,active,excluded=self.load_selection()
        excess=max(Q(0),selected-self.capacity)
        weights=(Q(1),Q(1),excess/self.unit);norm=sum(weights)
        kernel={name:weight/norm for name,weight in zip(('+','-','exit'),weights)}
        require(sum(kernel.values())==1 and all(p>=0 for p in kernel.values()),'Nonstochastic kernel')
        consumed_cut=max([self.measurement_origin]+[x['committed'] for x in self.responses])
        decision_cut=self.clock.event('retention_decision',prefix=self.prefix,reference_count=expected,
                                      selected_load=str(selected),capacity=str(self.capacity),
                                      weights=[str(w) for w in weights],
                                      response_ids=active,excluded=excluded)
        require(consumed_cut<decision_cut,'Same-step or future response consumed')
        self.pending_inputs=contexts
        self.pending_decision={'prefix':self.prefix,'reference_count':expected,'cut':decision_cut,
                               'consumed_through':consumed_cut,'selected_raw_load':str(selected),
                               'raw_signed':str(self.raw_signed()),'raw_burden':str(self.raw_burden()),
                               'active_response_ids':active,'exclusions':excluded,
                               'raw_capacity':str(self.capacity),'unit':self.unit,'raw_excess':str(excess),
                               'weights':[str(w) for w in weights],
                               'probabilities':{k:str(v) for k,v in kernel.items()},
                               'response_history_digest':digest(self.responses),
                               'parent_return_id':self.parent_records[-1][0].return_id,
                               'parent_certificate_digest':self.parent_records[-1][1].certificate_digest}
        return deepcopy(self.pending_decision)

    def channel_operands(self,name):
        ch=self.channels[name]
        relation=ch.comparison(self.clock.cut,self.window_length)
        return {'sender':name,'comparison_cut':self.clock.cut,
                'contact_ids':list(relation['rcd'].contact_ids),
                'contact_digests':[n.digest(asdict(e)) for e in ch.events[-2:]],
                'support_RD':relation['rcd'].support,'directional_RCD':relation['duration'],
                'rho':relation['rho'],'C3':relation['C3'],'pressure':str(relation['pressure']),
                'candidate_bip':relation['candidate_bip'],'sender_bip':relation['sender_bip'],
                'ratio':str(relation['ratio']),'phase_bias':str(relation['bias']),
                'lag':str(relation['lag']),'prior_lag':str(relation['prior_lag']),
                'drift':str(relation['drift'])}

    def retain(self,symbol):
        require(symbol in ('+','-') and self.pending_inputs is not None,'Missing return decision')
        decision=self.pending_decision
        probability=Q(decision['probabilities'][symbol])
        sign=1 if symbol=='+' else -1
        new_prefix=self.prefix+symbol
        t=self.candidate.advance(self.clock,'return:'+new_prefix,orientation=sign)
        orientation=t.roles[0]
        require(orientation==sign,'Response orientation not bound to the selected return')
        terms=[]
        for name,context in sorted(self.pending_inputs.items()):
            lag=Q(context['lag']);pressure=Q(context['pressure'])
            require(context['comparison_cut']<t.indices[0],'Response reads future comparison')
            terms.append({**context,'orientation':orientation,
                          'raw_signed':str(pressure*lag*orientation),
                          'raw_burden':str(pressure*abs(lag))})
        signed=sum((Q(x['raw_signed']) for x in terms),Q(0))
        burden=sum((Q(x['raw_burden']) for x in terms),Q(0))
        require(burden>=abs(signed),'Nonnegative burden lost an oriented contribution')
        committed=self.clock.event('response_committed',prefix=new_prefix,return_id=t.return_id,
                                    signed=str(signed),burden=str(burden),operand_digest=digest(terms))
        response={'id':'response:'+new_prefix,'committed':committed,'candidate_return_id':t.return_id,
                  'candidate_certificate_digest':self.candidate.records[-1][1].certificate_digest,
                  'terms':terms,'raw_signed':str(signed),'raw_burden':str(burden),
                  'paired_signed_response':[str(signed),str(-signed)],
                  'diagnostic_signed':str(signed/self.unit),'diagnostic_burden':str(burden/self.unit)}
        self.responses.append(response);self.prefix=new_prefix
        self.current_state=replace(n.initial_state(self.candidate.wave()),committed=committed,
                                    current=self.raw_signed(),capacity=self.capacity,
                                    pressure=sum((Q(x['pressure']) for x in terms),Q(0)),
                                    retained_rebalancing=tuple(digest(x) for x in self.responses))
        self.fold_parent('return:'+new_prefix)
        if self.observer:
            self.observations.append({'prefix':new_prefix,'signed':str(self.raw_signed()),
                                      'burden':str(self.raw_burden()),'cut':self.clock.cut})
        self.pending_inputs=None;self.pending_decision=None
        return probability

    def lose(self):
        decision=self.pending_decision
        require(decision is not None and Q(decision['probabilities']['exit'])>0,
                'An exit requires a positive computed weight')
        fold=self.parent_folds[-1];state=self.parent_states[-1]
        t=self.clock.walk('retention:outer-parent','exit:'+self.prefix,EXIT,1,
                           scope=OUTER,scale=1,ancestor=fold['outer'][0].ancestor,closed=False)
        require(t.vertices[-1]!=t.vertices[0],'Open exit became a parent closure')
        committed=self.clock.event('outer_retention_lost',prefix=self.prefix,
                                    prior_outer_return=fold['outer'][0].return_id)
        bridge=digest({'contract':self.contract,'case':self.case,'selection':decision})
        record=n.shedding(fold,state,Q(decision['selected_raw_load']),self.capacity,
                           source_event_digest=digest({'responses':self.responses,'decision':decision}),
                           model_bridge=bridge,committed=committed,route='exoshedding',
                           target_scope=INNER,target_scale=0)
        exposed=n.expose(fold,record)
        require(exposed==(self.candidate.wave(),),'Loss erased or substituted retained inner lineage')
        return {'probability':decision['probabilities']['exit'],'shedding':asdict(record),
                'open_path':asdict(t),'exposed_wave_identity':exposed[0].identity,
                'exposed_certificate_digests':[x.certificate_digest for x in exposed[0].certificates],
                'physical_decay':None,'daughter_identity':None}

    def validate(self):
        for field in (self.candidate,self.reference,self.background):n.validate_wave(field.wave())
        n.validate_wave(n.wave(self.parent_records))
        for ch in self.channels.values():ch.validate()
        returns={t.return_id:(t,cert) for t,cert,_ in self.candidate.records}
        require(len({r['candidate_return_id'] for r in self.responses})==len(self.responses),
                'A return was counted as more than one response')
        for response in self.responses:
            require(response['candidate_return_id'] in returns,'Response has no admitted return')
            trace,certificate=returns[response['candidate_return_id']]
            require(certificate.certificate_digest==response['candidate_certificate_digest'] and
                    trace.indices[-1]<response['committed'],'Response return binding is stale or future')
            for context in response['terms']:
                require(type(context['orientation']) is int and context['orientation']==trace.roles[0],
                        'Response sign is not the committed return orientation')
                require(type(context['C3']) is int and context['C3']==1,'Unsupported channel participation')
                ch=self.channels[context['sender']]
                by_id={e.identity:e for e in ch.events}
                require(all(k in by_id for k in context['contact_ids']),'Response lost contact evidence')
                events=tuple(by_id[k] for k in context['contact_ids'])
                eligible=[e for e in ch.events if e.committed<=context['comparison_cut']]
                require(tuple(eligible[-2:])==events,'Response did not consume its last two committed contacts')
                require(context['contact_digests']==[n.digest(asdict(e)) for e in events],
                        'Response contact evidence changed')
                prior=(n.compare(self.candidate.wave(),ch.sender.wave(),tuple(eligible[-3:-1]),
                                  (0,eligible[-2].committed))['lag'] if len(eligible)>2 else Q(0))
                relation=n.compare(self.candidate.wave(),ch.sender.wave(),events,
                                    (0,context['comparison_cut']),prior_lag=prior)
                rho=n.participation(relation['rcd'],self.window_length,relation['rcd'].domain)
                require(context['lag']==str(relation['lag']) and
                        context['ratio']==str(relation['ratio']) and
                        context['phase_bias']==str(relation['bias']) and
                        context['prior_lag']==str(prior) and context['drift']==str(relation['drift']) and
                        context['support_RD']==relation['rcd'].support and
                        context['directional_RCD']==relation['duration'] and
                        context['rho']==rho and Q(context['pressure'])==rho,
                        'Response operands do not regenerate from committed comparisons')
            require(all(t['comparison_cut']<response['committed'] for t in response['terms']),
                    'Response has uncommitted operands')
            require(Q(response['raw_signed'])==sum((Q(x['pressure'])*Q(x['lag'])*x['orientation'] for x in response['terms']),Q(0)),
                    'Signed response differs from its operands')
            require(Q(response['raw_burden'])==sum((Q(x['pressure'])*abs(Q(x['lag'])) for x in response['terms']),Q(0)),
                    'Burden differs from its nonnegative operands')
        require(self.clock.cut<=self.contract['horizon']['allowed_cut_window'][1],'Frozen cut window exceeded')
        return True

    def proofs(self):
        fields={}
        for field in (self.candidate,self.reference,self.background):
            fields[field.name]={'identity':field.identity,'returns':[asdict(t) for t,_,_ in field.records],
                                'certificate_digests':[x.certificate_digest for _,x,_ in field.records],
                                'component_traces':[asdict(t) for t,_ in field.components],
                                'motif_witness_digests':[x.witness_digest for x in field.motifs],
                                'pending':field.pending}
        return {'fields':fields,'channels':{name:{'pivot':asdict(ch.pivot_trace),'events':ch.evidence}
                                            for name,ch in self.channels.items()},
                'parent_returns':[{'trace':asdict(t),'certificate_digest':cert.certificate_digest,
                                   'inner_wave_identity':cert.inner_waves[0].identity,
                                   'inner_prefix_certificates':[x.certificate_digest for x in cert.inner_waves[0].certificates]}
                                  for t,cert,_ in self.parent_records],
                'response_history':self.responses,'events':self.clock.events,
                'measurement_origin':self.measurement_origin,'unit':self.unit,
                'raw_capacity':str(self.capacity)}


def prepare_prefix(contract,case,prefix,observer=True):
    require(len(prefix)==2 and all(x in '+-' for x in prefix),'Two committed response choices required')
    frame=Fixture(contract,case,observer=observer)
    mass=Q(1);earlier=[]
    for symbol in prefix:
        decision=frame.prepare_next();earlier.append(decision)
        require(Q(decision['probabilities']['exit'])==0,'This two-prefix enumeration requires no earlier loss')
        mass*=frame.retain(symbol)
    return frame,mass,earlier


def terminal_counts(frame,status):
    candidate_edges=sum(row['kind']=='edge' and row.get('lineage')==frame.candidate.lineage
                        and row['cut']>frame.measurement_origin for row in frame.clock.events)
    parent_edges=sum(row['kind']=='edge' and row.get('lineage')=='retention:outer-parent'
                     and row['cut']>frame.measurement_origin for row in frame.clock.events)
    new_outer=len(frame.parent_records)-frame.contract['formation_returns']['outer_parent']
    ref=frame.measured_reference()
    return {'status':status,'parent_reclosures':new_outer,'candidate_reclosures':frame.measured_candidate(),
            'reference_bips':ref,'parent_closures_per_reference_bip':str(Q(new_outer,ref)),
            'candidate_atomic_traversals':candidate_edges,'outer_atomic_traversals':parent_edges,
            'candidate_closures_per_atomic_traversal':str(Q(frame.measured_candidate(),candidate_edges)) if candidate_edges else None,
            'terminal_cut':frame.clock.cut,'background_bip':frame.background.bip(),
            'background_partial_return':frame.background.pending,
            'seconds':None,'physical_isotope_decay':None}


def run_case(contract,case,observer=True):
    prefixes=[];terminals=[];traces={};survival=Q(0);loss=Q(0)
    for symbols in product('+-',repeat=2):
        prefix=''.join(symbols)
        frame,mass,earlier=prepare_prefix(contract,case,prefix,observer)
        before_decision_digest=digest(frame.clock.events)
        third=frame.prepare_next()
        frame.validate()
        execution_digest=digest(frame.clock.events)
        context=frame.proofs()
        traces[prefix]=context
        row={'prefix':prefix,'incoming_probability':str(mass),
             'raw_signed':str(frame.raw_signed()),'raw_burden':str(frame.raw_burden()),
             'normalized_signed':str(frame.raw_signed()/frame.unit),
             'normalized_burden':str(frame.raw_burden()/frame.unit),
             'unit':frame.unit,'raw_capacity':str(frame.capacity),
             'reference_lags':[r['terms'][1]['lag'] if r['terms'][1]['sender']=='reference' else r['terms'][0]['lag'] for r in frame.responses],
             'background_lags':[next(t['lag'] for t in r['terms'] if t['sender']=='background') for r in frame.responses],
             'third_decision':third,'earlier_decisions':earlier,
             'committed_prefix_sha256':before_decision_digest,
             'context_sha256':digest(context),'execution_sha256':execution_digest}
        prefixes.append(row)
        for symbol in ('+','-','exit'):
            conditional=Q(third['probabilities'][symbol])
            if conditional==0:continue
            child=deepcopy(frame);start=len(child.clock.events)
            terminal={'prefix':prefix,'outcome':symbol,'probability_mass':str(mass*conditional),
                      'source_context_sha256':digest(context),'shedding':None,'exposed_inner':None}
            if symbol=='exit':
                exited=child.lose();loss+=mass*conditional
                terminal['shedding']=exited['shedding']
                terminal['open_exit_trace']=exited['open_path']
                terminal['exposed_inner']={'identity':exited['exposed_wave_identity'],
                                           'certificates':exited['exposed_certificate_digests']}
                status='absorbed by declared outer-exit predicate'
            else:
                child.retain(symbol);survival+=mass*conditional
                status='retained at the frozen horizon; right-censored within this fixture'
            child.validate()
            terminal.update(terminal_counts(child,status))
            terminal['event_suffix']=child.clock.events[start:]
            terminal['terminal_history_sha256']=digest(child.clock.events)
            terminal['candidate_return_ids']=[t.return_id for t,_,_ in child.candidate.records]
            terminal['outer_return_ids']=[t.return_id for t,_,_ in child.parent_records]
            terminals.append(terminal)
    require(sum(Q(p['incoming_probability']) for p in prefixes)==1,'Prefix probability mass lost')
    require(survival+loss==1 and sum(Q(t['probability_mass']) for t in terminals)==1,'Terminal probability mass lost')
    return {'case':case,'prefixes':prefixes,'traces':traces,'terminals':terminals,
            'survival_by_reference_return':['1','1','1',str(survival)],
            'loss_by_reference_return':['0','0','0',str(loss)],
            'S3':str(survival),'absorbed_probability':str(loss),
            'terminal_count':len(terminals),'exact_mass':'1',
            'execution_sha256':digest([p['execution_sha256'] for p in prefixes]),
            'physical_isotope_prediction':None,'seconds':None}


def generate(contract=None,observer=True):
    contract=default_contract() if contract is None else deepcopy(contract)
    require(canonical(contract)==canonical(default_contract()),'Unsupported alteration of the frozen fixture contract')
    verify_sources()
    result={'schema':'witnessed-retention-result-v1','classification':'exact finite fixture with declared load and loss map',
            'contract':contract,'contract_sha256':digest(contract),'implementation_sha256':CODE_SHA,
            'source_binding_sha256':hashlib.sha256((HERE/'source_bindings.json').read_bytes()).hexdigest(),
            'cases':{case:run_case(contract,case,observer) for case in contract['cases']},
            'physical_isotope_admission':False,'physical_loss_identification':False,
            'empirical_inputs_read':[],'physical_seconds':None}
    result['report_sha256']=digest(result)
    return result


def verify_report(report,*,original_contract):
    require(canonical(report)==canonical(generate(original_contract)),
            'Supplied artifact differs from full original-context replay')
    return True


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,default=str)+'\n')


def export(result,out):
    out.mkdir(parents=True,exist_ok=True)
    write_json(out/'prediction.json',result)
    summary=[];prefixes=[];terminal=[]
    for case,run in result['cases'].items():
        summary.append({'case':case,'S0':'1','S1':'1','S2':'1','S3':run['S3'],
                        'absorbed_probability':run['absorbed_probability'],'terminal_count':run['terminal_count'],
                        'exact_mass':run['exact_mass']})
        for row in run['prefixes']:
            prefixes.append({'case':case,'prefix':row['prefix'],'unit':row['unit'],
                             'raw_signed':row['raw_signed'],'raw_burden':row['raw_burden'],
                             'normalized_signed':row['normalized_signed'],'normalized_burden':row['normalized_burden'],
                             'selected_raw_load':row['third_decision']['selected_raw_load'],
                             'next_exit_probability':row['third_decision']['probabilities']['exit'],
                             'reference_lags':','.join(row['reference_lags']),'background_lags':','.join(row['background_lags']),
                             'response_ids':','.join(row['third_decision']['active_response_ids'])})
        for row in run['terminals']:
            terminal.append({'case':case,**{k:row[k] for k in
                              ('prefix','outcome','probability_mass','parent_reclosures','candidate_reclosures',
                               'reference_bips','parent_closures_per_reference_bip','candidate_atomic_traversals',
                               'outer_atomic_traversals','terminal_cut','status')}})
    for name,rows in [('survival.csv',summary),('two_history_comparison.csv',prefixes),('terminal_counts.csv',terminal)]:
        with (out/name).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    write_json(out/'sha256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(out.iterdir()) if p.is_file() and p.name!='sha256.json'})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=generate();export(result,args.out)
    print(json.dumps({case:{k:run[k] for k in ('S3','absorbed_probability','terminal_count','exact_mass')}
                      for case,run in result['cases'].items()},indent=2))


if __name__=='__main__':main()
