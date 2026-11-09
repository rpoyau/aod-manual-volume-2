"use strict";
(()=>{
const root=document.getElementById('matter1');
const data=JSON.parse(document.getElementById('matter1-campaign-data').textContent);
const records=data.records,byId=new Map(records.map(r=>[r.id,r]));
const view=document.getElementById('reference-view'),picker=document.getElementById('campaign-picker');
const detail=document.getElementById('campaign-detail'),panel=document.getElementById('campaign-panel');
const selected=new Map();
const words=value=>String(value??'not supplied').replaceAll('_',' ');
const number=value=>{if(value===null||value===undefined)return NaN;const parts=String(value).split('/');return parts.length<=2?Number(parts[0])/(parts.length===2?Number(parts[1]):1):NaN;};
const label=r=>`${r.symbol}-${r.a} · ${words(r.state)}`;
const metric=()=>view.value.replace('campaign-','');
const active=()=>view.value.startsWith('campaign-');
const titles={cadence:'Bounded return ratio',lag:'Return-count lag',survival:'Survival probability'};
function node(tag,text,parent=detail,cls){const element=document.createElement(tag);if(text!==null)element.textContent=text;if(cls)element.className=cls;parent.append(element);return element;}
function chosen(z){if(!selected.has(z)){const first=records.find(r=>r.z===z);if(first)selected.set(z,first.id);}return byId.get(selected.get(z));}
function value(r,key=metric()){if(!r)return null;return key==='cadence'?r.cadence_ratio:key==='lag'?r.lag:r.survival;}
function valueText(r,key=metric()){const v=value(r,key);return v===null||v===undefined?'Unavailable':String(v);}
function scopeText(r,key=metric()){
 if(key==='survival'&&(r?.survival===null||r?.survival===undefined))return 'Loss observation map not established; no survival probability or half-life assigned.';
 return key==='cadence'?'Completed candidate returns / independent reference returns in this configuration’s bounded window. These windows do not identify a cross-element frequency ratio.':key==='lag'?'Candidate minus reference complete-return count in this configuration’s window; no conversion to seconds.':'Declared model survival; physical isotope identification is separate.';
}
function paint(){
 const enabled=active(),key=metric();panel.hidden=!enabled;document.getElementById('campaign-key').hidden=!enabled;
 if(!enabled)return;
 const available=Array.from({length:118},(_,i)=>chosen(i+1)).filter(r=>Number.isFinite(number(value(r))));
 const sorted=[...available].sort((a,b)=>number(value(a))-number(value(b)));
 const low=sorted[0],high=sorted.at(-1),min=number(value(low)),max=number(value(high)),span=max-min||1;
 document.getElementById('campaign-scale-label').textContent=low?`${titles[key]}: ${valueText(low)} → ${valueText(high)} · linear display scale; exact values in configuration-specific windows, not a cross-element frequency comparison.`:`${titles[key]}: unavailable for the selected configurations.`;
 for(const element of root.querySelectorAll('[data-element]')){
  const r=chosen(+element.dataset.element),v=value(r),numeric=number(v),valid=Number.isFinite(numeric);
  const fraction=valid?(numeric-min)/span:0,from=[244,241,230],to=[173,213,226];
  const fill=valid?`rgb(${from.map((x,i)=>Math.round(x+(to[i]-x)*fraction)).join(',')})`:'#e8ebed';
  element.style.setProperty('--campaign-fill',fill);element.style.setProperty('--campaign-dash',valid?'none':'2 2');element.style.setProperty('--campaign-border',valid?'solid':'dashed');
  element.dataset.campaignId=r?.id||'';element.dataset.campaignValue=valid?String(v):'';element.dataset.campaignKind=valid?'declared_model_value':'unavailable';
  const description=r?`${label(r)}; ${titles[key]} ${valueText(r)}; ${scopeText(r)}; execution ${words(r.execution_status)}`:'No campaign configuration';
  element.setAttribute('aria-label',`${element.dataset.structuralLabel}; ${description}`);
  if(element.namespaceURI==='http://www.w3.org/2000/svg'){let title=element.querySelector('title');if(!title){title=document.createElementNS('http://www.w3.org/2000/svg','title');element.append(title);}title.textContent=description;}else element.title=description;
 }
}
function render(){
 picker.replaceChildren();detail.replaceChildren();const z=+root.dataset.z,r=chosen(z);
 for(const candidate of records.filter(x=>x.z===z)){const option=document.createElement('option');option.value=candidate.id;option.textContent=`${label(candidate)} · ${words(candidate.provenance_kind||candidate.id)}`;picker.append(option);}
 picker.value=r?.id||'';picker.disabled=picker.options.length<=1;
 if(r){
  root.dataset.campaignId=r.id;root.dataset.campaignConfiguration=r.configuration_id;
  node('p',`${label(r)} · ${titles[metric()]||'Declared model'} ${valueText(r)}`,detail,'observation-status');
  const fields=node('dl',null);
  for(const [name,text] of [['Generic fold',words(r.construction_status)],['Execution',words(r.execution_status)],['Bounded return ratio',valueText(r,'cadence')],['Return-count lag',valueText(r,'lag')],['Survival probability',valueText(r,'survival')],['Physical prediction',words(r.physical_prediction_status||'not established')]]){node('dt',name,fields);node('dd',text,fields);}
  if(Array.isArray(r.reference_window))node('p',`Reference window: (${r.reference_window.join(', ')}]; reference ${r.reference_identity}.`,detail,'scope');
  if(r.window_policy)node('p',r.window_policy,detail,'scope');
  node('p','The independent reference is a declared 3:3:6 support. Its mapping to a realized atomic clock is unresolved.',detail,'scope');
  node('p',scopeText(r),detail,'scope');
  node('p','State labels retain source distinctions. A shared constituent inventory does not establish a distinct atomic or isomer preparation.',detail,'scope');
  node('p',`Source assignment: ${words(r.state_assignment)}; selection ${words(r.selection_policy)}; source ${r.selection_source}.`,detail,'scope');
  if(r.dependencies?.length){node('h3','Dependencies');const list=node('ul',null,detail,'campaign-dependencies');for(const dependency of r.dependencies)node('li',words(typeof dependency==='string'?dependency:dependency.id||dependency.description),list);}
  node('p',`Configuration ${r.configuration_id}; source record ${r.id}.`,detail,'scope');
 }
 paint();
}
root.addEventListener('matter1:select',render);
picker.addEventListener('change',()=>{selected.set(+root.dataset.z,picker.value);render();});
view.addEventListener('change',render);
document.getElementById('nuclide-picker').addEventListener('change',paint);
document.getElementById('evaluation-picker').addEventListener('change',paint);
// Source selectors remain independent: choosing a measurement never changes the
// model's configuration or its frozen prediction.
render();
})();
