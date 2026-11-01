"use strict";
(()=>{
const root=document.getElementById('matter1');
const layout=JSON.parse(document.getElementById('matter1-data').textContent);
const catalog=JSON.parse(document.getElementById('matter1-isotope-data').textContent);
const records=catalog.isotopes,byId=new Map(records.map(r=>[r.id,r]));
const sources=new Map(catalog.sources.map(s=>[s.id,s]));
const picker=document.getElementById('nuclide-picker'),evaluations=document.getElementById('evaluation-picker');
const view=document.getElementById('reference-view'),detail=document.getElementById('nuclide-detail'),decays=document.getElementById('decay-detail');
const selected=new Map(),selectedSources=new Map();
const number=value=>{if(value===null||value===undefined)return NaN;const p=String(value).split('/');return Number(p[0])/(p.length===2?Number(p[1]):1);};
const words=value=>String(value||'unspecified').replaceAll('_',' ');
const label=r=>`${r.symbol}-${r.A}${r.state==='ground'?'':' · '+words(r.state)}`;
const finite=(r,h=r.half_life)=>h?.quantity==='total_half_life'&&Number.isFinite(number(h?.value_seconds))&&number(h.value_seconds)>0&&!/unobserved|rejected/.test(r.empirical_status)&&!['unknown','observationally_stable','lower_limit','upper_limit'].includes(h.kind);
const option=(value,text,parent)=>{const o=document.createElement('option');o.value=value;o.textContent=text;parent.append(o);return o;};
function node(tag,text,parent=detail,cls){const e=document.createElement(tag);if(text!==null)e.textContent=text;if(cls)e.className=cls;parent.append(e);return e;}
function time(value){const x=number(value);if(!Number.isFinite(x))return 'not supplied';const units=[[31557600,'yr'],[86400,'d'],[3600,'h'],[60,'min'],[1,'s'],[1e-3,'ms'],[1e-6,'μs'],[1e-9,'ns']];const [scale,unit]=units.find(([s])=>x>=s)||units.at(-1);return `${Number((x/scale).toPrecision(6))} ${unit}`;}
function variants(r){return [{source_id:r.selection_source,half_life:r.half_life,role:'selected source record'},...(r.updates||[]).filter(u=>u.half_life&&u.source_id)];}
function chosenVariant(r){const list=variants(r);return list.find(v=>v.source_id===selectedSources.get(r.id))||list[0];}
function defaultId(z){const mark=layout.marks[z-1];return records.find(r=>r.Z===z&&r.A===mark.reference_a&&r.state==='ground'&&!/unobserved|rejected/.test(r.empirical_status))?.id||'';}
function chosen(z){if(!selected.has(z))selected.set(z,defaultId(z));return byId.get(selected.get(z));}
function halfLife(r,h=r.half_life){if(h.kind==='observationally_stable')return 'Observationally stable';if(h.kind==='unknown'||h.value_seconds===null)return 'Half-life not established';const prefix=h.kind==='lower_limit'?'> ':h.kind==='upper_limit'?'< ':'';return `${prefix}${time(h.value_seconds)}${h.uncertainty_plus_seconds!==null&&h.uncertainty_plus_seconds!==undefined?` (+${time(h.uncertainty_plus_seconds)} / −${time(h.uncertainty_minus_seconds)})`:''}`;}
function sourceLink(id,parent){const source=sources.get(id);if(!source){node('span',`Source ${id||'not supplied'}`,parent);return;}if(/^https?:\/\//.test(source.url)){const a=node('a',source.title||source.id,parent);a.href=source.url;a.target='_blank';a.rel='noopener noreferrer';}else node('span',source.id,parent);}
function paint(){
 root.dataset.view=view.value;
 document.getElementById('half-life-key').hidden=view.value!=='half-life';
 const eligible=records.flatMap(r=>variants(r).filter(v=>finite(r,v.half_life)).map(v=>number(v.half_life.value_seconds)));
 const min=Math.min(...eligible),max=Math.max(...eligible),span=Math.log10(max)-Math.log10(min)||1;
 document.getElementById('half-life-scale').textContent=`${time(min)} → ${time(max)} · color uses central values only; uncertainty and source qualification appear below.`;
 for(const element of root.querySelectorAll('[data-element]')){
  const z=+element.dataset.element,r=chosen(z),v=r?chosenVariant(r):null,h=v?.half_life;
  let fill='#e8ebed',dash='2 2',status='not covered',description='No sourced reference-A isotope selected';
  if(r){status=h.kind;description=`${label(r)}; ${halfLife(r,h)}; ${words(r.empirical_status)}; source ${v.source_id}`;
   if(finite(r,h)){const fraction=(Math.log10(number(h.value_seconds))-Math.log10(min))/span;const from=[245,237,225],to=[145,190,209];fill=`rgb(${from.map((x,i)=>Math.round(x+(to[i]-x)*fraction)).join(',')})`;dash=r.empirical_status==='evaluated_observed'?'none':'2 2';}
   else if(h.kind==='observationally_stable'){fill='#e1e9dc';dash='none';}
   else if(/limit/.test(h.kind)){fill='#eee5d7';dash='4 2';}
  }
  element.style.setProperty('--life-fill',fill);element.style.setProperty('--life-dash',dash);element.style.setProperty('--life-border',dash==='none'?'solid':'dashed');
  element.dataset.halfLifeKind=status;element.dataset.isotope=r?.id||'';
  if(!element.dataset.structuralLabel)element.dataset.structuralLabel=element.getAttribute('aria-label');
  element.setAttribute('aria-label',element.dataset.structuralLabel+(view.value==='half-life'?'; '+description:''));
  const text=element.namespaceURI==='http://www.w3.org/2000/svg'?element.querySelector('text'):element;
  if(text){if(!element.dataset.structuralText)element.dataset.structuralText=text.textContent;text.textContent=view.value==='half-life'&&r?`${r.symbol}${r.A}${r.state==='ground'?'':'m?'}`:element.dataset.structuralText;}
  const tip=view.value==='half-life'?description:element.dataset.structuralLabel;
  if(element.namespaceURI==='http://www.w3.org/2000/svg'){let title=element.querySelector('title');if(!title){title=document.createElementNS('http://www.w3.org/2000/svg','title');element.append(title);}title.textContent=tip;}else element.title=tip;
 }
}
function jump(id){const r=byId.get(id);if(!r)return;selected.set(r.Z,id);root.dispatchEvent(new CustomEvent('matter1:choose',{detail:{z:r.Z}}));}
function chain(r,parent,depth,visited){
 if(depth<0||visited.has(r.id))return;const seen=new Set([...visited,r.id]);
 for(const edge of r.decay_channels||[]){const li=node('li',`${label(r)} · ${edge.mode==='alpha'?'α':words(edge.mode)} · ${words(edge.status)}${edge.branching_original?' · '+edge.branching_original:''}`,parent);
  if(edge.daughter){const daughter=byId.get(edge.daughter.id);const text=`${edge.daughter.symbol}-${edge.daughter.A}`;
   if(daughter){node('span',' → ',li);const button=node('button',text,li);button.type='button';button.dataset.nuclide=daughter.id;button.addEventListener('click',()=>jump(daughter.id));node('span',` ${halfLife(daughter)}`,li);if(depth>0&&(daughter.decay_channels||[]).length)chain(daughter,node('ul',null,li),depth-1,seen);}
   else node('span',` → ${text} (endpoint record not supplied)`,li);
  }else node('span',' · no unique daughter assigned',li);
  node('span',' · source: ',li);sourceLink(edge.source_id,li);
 }
}
function render(){
 const z=+root.dataset.z,r=chosen(z);detail.replaceChildren();decays.replaceChildren();picker.replaceChildren();evaluations.replaceChildren();
 option('',records.some(x=>x.Z===z)?'Select an isotope / state':'No isotope records in this snapshot',picker);
 for(const candidate of records.filter(x=>x.Z===z).sort((a,b)=>a.A-b.A||a.state.localeCompare(b.state)))option(candidate.id,`${label(candidate)} · ${words(candidate.empirical_status)}`,picker);
 picker.value=r?.id||'';picker.disabled=picker.options.length===1;
 if(!r){option('','No source record selected',evaluations);evaluations.disabled=true;node('p','This element has no selected sourced reference-A state in this snapshot. It is not classified as stable or assigned a half-life.',detail,'scope');root.dataset.isotope='';paint();return;}
 const list=variants(r),v=chosenVariant(r),h=v.half_life;
 for(const item of list)option(item.source_id,`${item.source_id} · ${words(item.role||'literature update')}`,evaluations);
 evaluations.value=v.source_id;evaluations.disabled=list.length===1;
 root.dataset.isotope=r.id;root.dataset.isotopeSource=v.source_id;
 node('p',`${label(r)} · ${halfLife(r,h)}`,detail,'observation-status');
 node('p',`Z=${r.Z}, N=${r.N}; formal groups q=${r.support_coordinates.q}; residual p=${r.support_coordinates.r_p}, n=${r.support_coordinates.r_n}.`);
 node('p',`${words(r.empirical_status)}; ${words(r.state_assignment)}. Quantity: ${words(h.quantity||'total_half_life')}.`);
 node('p',`Source notation: ${h.original||'not supplied'}. Confidence convention: ${words(h.confidence)}.`,detail,'scope');
 const source=node('p',null);sourceLink(v.source_id,source);
 const locator=v.locator||(r.source_records||[]).find(x=>x.source_id===v.source_id)?.locator;if(locator)node('p',`Source locator: ${locator}.`,detail,'scope');
 if(v.overlap)node('p',v.overlap,detail,'scope');
 const src=sources.get(v.source_id);if(src)node('p',`Evaluation: ${src.evaluation_date||'not specified'}; literature cutoff: ${src.literature_cutoff||'not specified'}.`,detail,'scope');
 for(const note of r.notes||[])node('p',typeof note==='string'?note:JSON.stringify(note),detail,'scope');
 for(const limit of r.limits||[]){
  const lh=limit.measurement,p=node('p',`Separate ${words(limit.channel)} limit: ${words(lh.quantity)} ${halfLife(r,lh)}; ${words(limit.confidence)}. `,detail,'scope');sourceLink(limit.source_id,p);if(limit.locator)node('span',` · ${limit.locator}`,p);
 }
 for(const partial of v.channel_partial_half_lives||[]){
  const p=node('p',`Separate ${words(partial.channel)} partial half-life: ${halfLife(r,partial.measurement)}. Estimated branching fraction: ${partial.branching_estimate}${partial.alpha_energy?`; alpha energy ${partial.alpha_energy}`:''}. `,detail,'scope');
  node('p',partial.qualification,detail,'scope');sourceLink(partial.source_id,p);node('span',` · ${partial.locator}`,p);
 }
 for(const event of r.event_times||[])node('p',`Individual waiting time: ${time(event.value_seconds)}; ${event.locator}. This event time is not a half-life.`,detail,'scope');
 if(r.nubase_crosscheck)node('p',`NUBASE2020 cross-check: ${r.nubase_crosscheck.half_life_raw}; retained as comparison data, with no status promotion or averaging.`,detail,'scope');
 node('p',`Native admission: ${words(r.native_admission)}; empirical model agreement: ${words(r.empirical_agreement)}.`,detail,'scope');
 node('h3','Source-recorded decay routes',decays);
 const routeSource=node('p','Adopted/default route source: ',decays,'scope');sourceLink(r.selection_source,routeSource);
 if((r.decay_channels||[]).length)chain(r,node('ul',null,decays,'decay-path'),2,new Set());else node('p','No decay route supplied for this selected state.',decays,'scope');
 if(v.source_id!==r.selection_source){
  node('p','The selected literature update changes the displayed half-life. Routes above retain the separately identified adopted/default-source records.',decays,'scope');
  if((v.decay_channels||[]).length){node('h3','Selected experimental update routes',decays);const p=node('p',null,decays,'scope');sourceLink(v.source_id,p);chain({...r,decay_channels:v.decay_channels},node('ul',null,decays,'decay-path'),2,new Set());}
 }
 paint();
}
root.addEventListener('matter1:select',render);
picker.addEventListener('change',()=>{selected.set(+root.dataset.z,picker.value);render();});
evaluations.addEventListener('change',()=>{const r=chosen(+root.dataset.z);if(r)selectedSources.set(r.id,evaluations.value);render();});
view.addEventListener('change',paint);render();
})();
