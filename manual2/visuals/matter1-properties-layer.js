"use strict";
(()=>{
const data=JSON.parse(document.getElementById('matter1-properties-data').textContent);
const root=document.getElementById('matter1'),picker=document.getElementById('property-state'),filter=document.getElementById('property-filter'),detail=document.getElementById('property-detail');
const entities=data.states.entities,records=data.catalog.properties,coverage=data.coverage.rows;
const sources=Array.isArray(data.sources.sources)?data.sources.sources:Object.values(data.sources.sources||{});
const definitions=data.definitions.properties||data.definitions.definitions||[];
const label=id=>(Array.isArray(definitions)?definitions:[]).find(d=>d.id===id)?.label||id.replaceAll('_',' ');
const words=s=>String(s??'not stated').replaceAll('_',' ');
function node(tag,text,parent,cls){const e=document.createElement(tag);if(text!==null)e.textContent=text;if(cls)e.className=cls;parent.append(e);return e;}
function field(dl,name,value){node('dt',name,dl);node('dd',words(value),dl);}
function sourceLink(record,parent){const source=sources.find(s=>s.id===record.source_id)||{};
 const url=source.url||source.source_url;
 if(url&&/^https:\/\//.test(url)){const a=node('a',source.title||source.citation||record.source_id,parent);a.href=url;a.rel='noopener noreferrer';a.target='_blank';}
 else node('span',record.source_id||'No adopted source',parent);
 if(record.locator)node('p',typeof record.locator==='string'?record.locator:JSON.stringify(record.locator),parent,'scope');
}
function render(){detail.replaceChildren();const entity=entities.find(e=>e.id===picker.value);if(!entity)return;
 root.dataset.propertyState=entity.id;
 const identity=[entity.label,words(entity.kind)];if(entity.a!=null)identity.push(`A = ${entity.a}`);else if(entity.kind!=='element')identity.push('isotope unspecified');if(entity.charge!=null)identity.push(`charge ${entity.charge}`);if(entity.nuclear_state)identity.push('nuclear '+words(entity.nuclear_state));if(entity.electronic_state)identity.push('electronic '+words(entity.electronic_state));node('p',identity.join(' · '),detail,'scope');
 const matches=r=>r.entity_id===entity.id&&(!filter.value||r.property===filter.value);
 const selected=records.filter(matches),covered=coverage.filter(matches);
 node('p',`${selected.length} property records; ${selected.filter(r=>r.value==null).length} without an adopted value.`,detail,'scope');
 for(const r of selected.filter(r=>r.value!=null||r.value_kind==='interval')){const card=node('article',null,detail,'property-card');card.dataset.property=r.property;card.dataset.record=r.id;
  node('h3',label(r.property),card);
  const value=r.value_kind==='interval'?`[${r.interval.lower}, ${r.interval.upper}]${r.unit?' '+r.unit:''}`:r.value==null?words(r.value_kind):`${['numeric','text'].includes(r.value_kind)?'':words(r.value_kind)+': '}${r.value}${r.unit?' '+r.unit:''}`;
  node('p',value,card,'property-value');const dl=node('dl',null,card);
  field(dl,'Method',r.method);field(dl,'Target exposure',r.exposure);field(dl,'Physical prediction',r.physical_prediction?'claimed':'not established');
  const u=r.uncertainty||{};field(dl,'Uncertainty',u.value==null?words(u.kind):`${u.value} ${r.unit||''}; ${words(u.kind)}`);
  if(u.coverage!=null)field(dl,'Coverage',u.coverage);if(u.distribution!=null)field(dl,'Distribution',u.distribution);
  if(r.conditions&&Object.keys(r.conditions).length)field(dl,'Conditions',typeof r.conditions==='string'?r.conditions:JSON.stringify(r.conditions));
  if(r.qualification)node('p',typeof r.qualification==='string'?r.qualification:JSON.stringify(r.qualification),card,'scope');sourceLink(r,card);
 }
 const gaps=[...selected.filter(r=>r.value==null&&r.value_kind!=='interval').map(r=>({property:r.property,status:r.value_kind,reason:r.qualification})),...covered.filter(c=>!selected.some(r=>r.property===c.property))];
 if(gaps.length){const list=node('ul',null,detail,'property-gaps');for(const c of gaps)node('li',`${label(c.property)} — ${words(c.status)}${c.reason?': '+c.reason:''}`,list);}
 if(!selected.length&&!gaps.length)node('p','No records in this selection.',detail);
 const model=data.model.rows.find(r=>r.entity_id===entity.id);
 if(model){const research=node('details',null,detail);node('summary','Native pilot and physical-model dependencies',research);
  node('p','Generic native history executed. A physical state correspondence and property observation law remain unestablished.',research);
  const dl=node('dl',null,research);for(const key of ['cadence_ratio','lag'])if(model.native_observation[key]!=null)field(dl,'Native '+words(key),model.native_observation[key]);
  node('p','These relational quantities have no identified conversion to this atom’s transition frequency or mass.',research,'scope');
  const list=node('ul',null,research);for(const d of data.model.dependencies)node('li',`${d.premise}: ${d.required_evidence}`,list);
 }
}
function choose(z){const previous=picker.value;picker.replaceChildren();for(const e of entities.filter(e=>e.z===z)){const option=node('option',`${e.label||e.id} · ${words(e.kind)}${e.charge!=null?' (charge '+e.charge+')':''}`,picker);option.value=e.id;}
 if([...picker.options].some(o=>o.value===previous))picker.value=previous;
 render();
}
const ids=[...new Set([...records,...coverage].map(r=>r.property))].sort();for(const id of ids){const o=node('option',label(id),filter);o.value=id;}
picker.addEventListener('change',render);filter.addEventListener('change',render);
root.addEventListener('matter1:select',e=>choose(e.detail.z));choose(Number(root.dataset.z||6));
})();
