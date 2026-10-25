#!/usr/bin/env node
/* Read-only companion checks. Screenshots are optional explicit outputs. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright');
const options={};for(let i=2;i<process.argv.length;i+=2){const key=process.argv[i];if(!['--visual-dir','--screenshots-dir'].includes(key)||!process.argv[i+1])throw new Error('Unknown or incomplete option: '+key);options[key]=process.argv[i+1];}
const dir=options['--visual-dir']||path.resolve(__dirname,'../visuals');
const html=path.join(dir,'matter1-reference.html'),layoutPath=path.join(dir,'matter1-layout.json');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const before=[hash(html),hash(layoutPath)];
const data=JSON.parse(fs.readFileSync(layoutPath,'utf8'));
async function capture(page,name){if(options['--screenshots-dir']){fs.mkdirSync(options['--screenshots-dir'],{recursive:true});await page.locator('main').screenshot({path:path.join(options['--screenshots-dir'],name+'.png')});}}
async function checkDesktop(page){return page.evaluate(()=>{
 const marks=[...document.querySelectorAll('#chart [data-slot]')].map(e=>{const r=e.querySelector('rect').getBoundingClientRect(),t=e.querySelector('text').getBoundingClientRect();return{z:+e.dataset.slot,label:e.querySelector('text').textContent,r:{left:r.left,right:r.right,top:r.top,bottom:r.bottom},t:{left:t.left,right:t.right,top:t.top,bottom:t.bottom},role:e.classList[0],edge:!!e.querySelector('path.edge')};});
 const overlaps=[],clipped=[];for(let i=0;i<marks.length;i++){const a=marks[i];if(a.t.left<a.r.left||a.t.right>a.r.right||a.t.top<a.r.top||a.t.bottom>a.r.bottom)clipped.push(a.z);for(let j=i+1;j<marks.length;j++){const b=marks[j];if(Math.min(a.r.right,b.r.right)>Math.max(a.r.left,b.r.left)+.1&&Math.min(a.r.bottom,b.r.bottom)>Math.max(a.r.top,b.r.top)+.1)overlaps.push([a.z,b.z]);}}
 return{marks,overlaps,clipped,scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth};
 });}
(async()=>{
 const executablePath=process.env.CHROMIUM_EXECUTABLE||(fs.existsSync('/opt/google/chrome/chrome')?'/opt/google/chrome/chrome':undefined);
 const browser=await chromium.launch({headless:true,...(executablePath?{executablePath}:{})});
 try{
 const page=await browser.newPage({viewport:{width:736,height:1050},colorScheme:'light'}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(html).href);await page.locator('#chart [data-element="1"]').waitFor();
 const desktop=await checkDesktop(page);assert.equal(desktop.marks.length,126);assert.deepEqual(desktop.marks.map(x=>x.label),data.marks.map(x=>x.label));assert.deepEqual(desktop.overlaps,[]);assert.deepEqual(desktop.clipped,[]);assert(desktop.marks.every(x=>x.edge));assert(desktop.scroll<=desktop.client+1);
 await capture(page,'desktop-light');
 await page.locator('#chart [data-element="8"]').click();assert.equal(await page.locator('#matter1').getAttribute('data-z'),'8');
 await page.locator('#isotopes summary').click();await page.locator('#mass-a').fill('17');assert.equal(await page.locator('#matter1').getAttribute('data-support-sum'),'861');assert.equal(await page.locator('#matter1').getAttribute('data-m'),'4');assert.equal(await page.locator('#matter1').getAttribute('data-seat'),'2');assert.equal(await page.locator('#matter1').getAttribute('data-local'),'1:1:0');
 for(const value of ['7','17.5','','1000001']){await page.locator('#mass-a').fill(value);assert(await page.locator('#error').isVisible());assert.equal(await page.locator('#mass-a').getAttribute('aria-invalid'),'true');assert.equal(await page.locator('#matter1').getAttribute('data-a'),'17');}
 await page.locator('#chart [data-element="6"]').focus();await page.keyboard.press('Enter');assert.equal(await page.locator('#matter1').getAttribute('data-z'),'6');assert.equal(await page.locator('#mass-a').inputValue(),'12');assert(await page.locator('#error').isHidden());
 for(const [a,sum]of[[12,613],[13,681],[14,749]]){await page.locator('#mass-a').fill(String(a));assert.equal(await page.locator('#matter1').getAttribute('data-support-sum'),String(sum));assert.equal(await page.locator('#matter1').getAttribute('data-seat'),'6');}
 await page.locator('#chart [data-element="14"]').focus();await page.keyboard.press('Space');assert.equal(await page.locator('#matter1').getAttribute('data-z'),'14');assert.equal(await page.locator('#mass-a').inputValue(),String(data.marks[13].reference_a));
 await page.locator('#isotopes summary').click();assert(await page.locator('#mass-a').isHidden());
 await page.emulateMedia({colorScheme:'dark'});const dark=await checkDesktop(page);assert.deepEqual(dark.overlaps,[]);assert.deepEqual(dark.clipped,[]);await capture(page,'desktop-dark');
 const responsive=[];
 for(const width of [360,320]){await page.setViewportSize({width,height:1500});await page.emulateMedia({colorScheme:'light'});await page.locator('#strips').waitFor({state:'visible'});assert(await page.locator('#chart').isHidden());
 const narrow=await page.evaluate(()=>({labels:[...document.querySelectorAll('#strips [data-slot]')].map(e=>({z:+e.dataset.slot,label:e.textContent,role:['alpha','hinge','omega','boundary'].find(x=>e.classList.contains(x)),after:getComputedStyle(e,'::after').backgroundColor,overflow:e.scrollWidth>e.clientWidth,rect:e.getBoundingClientRect().toJSON()})),scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth}));
 assert.equal(narrow.labels.length,126);assert.deepEqual(narrow.labels.map(x=>x.label),data.marks.map(x=>x.label));assert(narrow.labels.every((x,i)=>x.role===data.marks[i].role&&x.after!=='rgba(0, 0, 0, 0)'&&!x.overflow));assert(narrow.scroll<=narrow.client+1);
 for(let i=0;i<narrow.labels.length;i++)for(let j=i+1;j<narrow.labels.length;j++){const a=narrow.labels[i].rect,b=narrow.labels[j].rect;assert(!(Math.min(a.right,b.right)>Math.max(a.left,b.left)+.1&&Math.min(a.bottom,b.bottom)>Math.max(a.top,b.top)+.1));}
 await page.locator('#strips button[data-element="118"]').click();assert.equal(await page.locator('#matter1').getAttribute('data-z'),'118');await page.locator('#strips button[data-element="1"]').focus();await page.keyboard.press('Enter');assert.equal(await page.locator('#matter1').getAttribute('data-z'),'1');
 responsive.push({width,marks:126,visible_z_symbols:118,visible_roles:true,horizontal_overflow:false});await capture(page,'narrow-'+width);
 }
 assert.deepEqual(errors,[]);assert.deepEqual([hash(html),hash(layoutPath)],before);
 console.log(JSON.stringify({status:'PASS',desktop:{marks:126,named_labels:118,unfilled_slots:8,overlaps:[],clipped_text:[]},responsive,conditional_count_checks:'O16→17=861; C12/13/14=613/681/749; placement fixed',invalid_inputs_rejected:4,keyboard_and_pointer:true,light_and_dark:true,page_errors:errors,inputs_unchanged:true},null,2));
 }finally{await browser.close();}
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
