#!/usr/bin/env node
/* Guided local compositor. Uses host-provided sharp; no generation, install or network. */
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const json = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const save = (file, value) => fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n', {flag: 'wx'});
let sharp;
function dependency() {
  try { sharp = require('sharp'); }
  catch (_) { throw Error('tool-blocked: host-provided Node sharp unavailable; do not install or generate as fallback'); }
}
function inside(x, y, polygon) {
  let result = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const a = polygon[i], b = polygon[j];
    if ((a[1] > y) !== (b[1] > y) && x < (b[0]-a[0]) * (y-a[1]) / (b[1]-a[1]) + a[0]) result = !result;
  }
  return result;
}
function polygonCheck(p, w, h) {
  if (!Array.isArray(p) || p.length < 3 || p.some(v => !Array.isArray(v) || v.length !== 2 || v.some(x => !Number.isFinite(x)) || v[0] < 0 || v[0] > w || v[1] < 0 || v[1] > h)) throw Error('Invalid garment polygon');
}
function rectangleCheck(r, w, h) {
  if (!Array.isArray(r) || r.length !== 4 || r.some(v => !Number.isInteger(v)) || r[0] < 0 || r[1] < 0 || r[2] > w || r[3] > h || r[0] >= r[2] || r[1] >= r[3]) throw Error('Invalid protected rectangle');
}
async function rgb(file, size) {
  const meta = await sharp(file).metadata();
  if (meta.orientation && meta.orientation !== 1) throw Error('qa-retry: use an upright mother/donor; no silent EXIF rotation');
  if (meta.hasAlpha && (await sharp(file).stats()).channels[3]?.min !== 255) throw Error('qa-retry: mother and donor must be opaque');
  const {data, info} = await sharp(file).toColourspace('srgb').removeAlpha().raw().toBuffer({resolveWithObject:true});
  if (info.channels !== 3 || info.width !== size[0] || info.height !== size[1]) throw Error('qa-retry: canvas mismatch; no resize, warp or crop');
  return data;
}
async function alphaFor(polygon, guard, size) {
  const [w,h] = size, region = Buffer.alloc(w*h);
  polygonCheck(polygon,w,h);
  for (let y=0;y<h;y++) for(let x=0;x<w;x++) if(inside(x,y,polygon)) region[y*w+x]=255;
  const smoothed = await sharp(region,{raw:{width:w,height:h,channels:1}}).blur(4).toColourspace('b-w').raw().toBuffer();
  const a = Buffer.from(smoothed);
  for(let i=0;i<a.length;i++) a[i]=guard[i]?0:Math.round(255*Math.max(0,Math.min(1,(a[i]-8)/239)));
  if(!a.some(v=>v)) throw Error('Empty clothing region after protection');
  return a;
}
function guardFor(spec) {
  const [w,h]=spec.size;
  rectangleCheck(spec.face_rectangle,w,h);
  if(!Array.isArray(spec.protected_rectangles)||!spec.protected_rectangles.length) throw Error('Freeze head/face protection before generation');
  const g=Buffer.alloc(w*h);
  for(const r of spec.protected_rectangles) {
    rectangleCheck(r,w,h);
    for(let y=r[1];y<r[3];y++) g.fill(255,y*w+r[0],y*w+r[2]);
  }
  const r=spec.face_rectangle;
  for(let y=r[1];y<r[3];y++) for(let x=r[0];x<r[2];x++) if(!g[y*w+x]) throw Error('Head protection must cover the whole declared face rectangle');
  return g;
}
async function prepare(specFile, output) {
  const spec=json(specFile);
  const fields=['base_path','base_sha256','garment_paths','garment_conditions','size','garment_polygon','protected_rectangles','face_rectangle','protection_review'];
  if(Object.keys(spec).sort().join()!==fields.sort().join()) throw Error('Unsupported preparation fields');
  if(!Array.isArray(spec.size)||spec.size.length!==2||spec.size.some(v=>!Number.isInteger(v)||v<=0||v>8192)) throw Error('Declare positive exact canvas dimensions');
  if(!Array.isArray(spec.garment_paths)||!spec.garment_paths.length||spec.garment_paths.length>4) throw Error('Attach mother plus one to four current garment sources');
  for(const key of ['garment_conditions','protection_review']) if(typeof spec[key]!=='string'||!spec[key].trim()) throw Error('Describe garment truth and pre-call visual protection review');
  const basePath=path.resolve(spec.base_path), baseFile=fs.readFileSync(basePath);
  if(hash(baseFile)!==spec.base_sha256) throw Error('Changed mother image');
  const inputs=spec.garment_paths.map(p=>({path:path.resolve(p),bytes:fs.readFileSync(p)}));
  const allowed = new Set(['.png','.jpg','.jpeg','.webp']);
  if (!allowed.has(path.extname(basePath).toLowerCase()) || inputs.some(r=>!allowed.has(path.extname(r.path).toLowerCase()))) throw Error('Use supported raster image references');
  const baseName='base'+path.extname(basePath).toLowerCase();
  const base=await rgb(basePath,spec.size),g=guardFor(spec),a=await alphaFor(spec.garment_polygon,g,spec.size);
  if(fs.existsSync(output)) throw Error('Use a new private run directory; never overwrite a frozen run');
  fs.mkdirSync(output,{recursive:true});
  try {
    fs.writeFileSync(path.join(output,baseName),baseFile,{flag:'wx'});
    fs.writeFileSync(path.join(output,'head-guard.bin'),g,{flag:'wx'});
    fs.writeFileSync(path.join(output,'edit-alpha.bin'),a,{flag:'wx'});
    fs.mkdirSync(path.join(output,'garments'));
    const garments=inputs.map((r,i)=>{
      const file=path.join(path.resolve(output),'garments',String(i+1).padStart(2,'0')+path.extname(r.path).toLowerCase());
      fs.writeFileSync(file,r.bytes,{flag:'wx'});
      return {source:r.path,path:file,sha256:hash(r.bytes)};
    });
    const prompt='Edit Image 1 directly as ONE opaque '+spec.size.join('x')+' image. Keep the same pixel alignment, crop, camera, fixed body pose, face, expression, head tilt and scene. Change only the declared garment components, using Images 2 onward as the current garment truth. '+spec.garment_conditions+' Do not transfer other items or screenshot borders from garment sources. Do not move or beautify the person, add jewelry or text, create another pose, or relight the whole frame. Keep existing hair, hands and straps naturally in front of the edited garment. This is an existing-pose wardrobe edit, not creation of a new identity.';
    const contract={schema_version:1,created_at:new Date().toISOString(),spec,base_file:baseName,base_sha256:hash(baseFile),base_rgb_sha256:hash(base),guard_sha256:hash(g),alpha_sha256:hash(a),garments,provider_mask:false,tool_parameters:{prompt,referenced_image_paths:[path.join(path.resolve(output),baseName),...garments.map(r=>r.path)],transparent_background:false},scope:'own-mother head/face protection; original-real-person fidelity and product QA remain separate; no generation authority'};
    save(path.join(output,'contract.json'),contract);
    console.log(JSON.stringify({prepared:path.resolve(output),generation_calls:0,provider_mask:false}));
  } catch(error) {fs.rmSync(output,{recursive:true,force:true});throw error;}
}
async function load(run) {
  const c=json(path.join(run,'contract.json'));
  const baseFile=fs.readFileSync(path.join(run,c.base_file)),g=fs.readFileSync(path.join(run,'head-guard.bin')),a=fs.readFileSync(path.join(run,'edit-alpha.bin'));
  if(hash(baseFile)!==c.base_sha256||hash(g)!==c.guard_sha256||hash(a)!==c.alpha_sha256) throw Error('Frozen base/protection changed');
  const base=await rgb(path.join(run,c.base_file),c.spec.size);
  if(hash(base)!==c.base_rgb_sha256||!g.equals(guardFor(c.spec))) throw Error('Frozen contract/protection inconsistent');
  for(const r of c.garments) if(hash(fs.readFileSync(r.path))!==r.sha256) throw Error('Current garment reference changed');
  return {c,base,g,a};
}
function versionCheck(v) {if(!/^[1-9][0-9]*$/.test(v)) throw Error('Version must be a positive integer');}
async function apply(run, donorFile, version, regionFile) {
  versionCheck(version);const {c,base,g,a:frozen}=await load(run);
  const file=path.join(run,'candidate-v'+version+'.png');
  if(fs.existsSync(file)||fs.existsSync(path.join(run,'result-v'+version+'.json'))) throw Error('Never overwrite a result version');
  const donor=await rgb(donorFile,c.spec.size),[w,h]=c.spec.size;
  const region=regionFile?json(regionFile):null;
  if(region&&(Object.keys(region).sort().join()!==['garment_polygon','reason'].sort().join()||typeof region.reason!=='string'||!region.reason.trim())) throw Error('Local refinement requires garment_polygon and reason; protection cannot change');
  const a=region?await alphaFor(region.garment_polygon,g,c.spec.size):frozen,out=Buffer.from(base);
  for(let i=0;i<a.length;i++) for(let k=0;k<3;k++) out[i*3+k]=Math.round((base[i*3+k]*(255-a[i])+donor[i*3+k]*a[i])/255);
  const donorCopy=path.join(run,'donor-v'+version+'.png');
  if(fs.existsSync(donorCopy)||fs.existsSync(path.join(run,'alpha-v'+version+'.bin'))) throw Error('Version artifacts already exist');
  fs.copyFileSync(donorFile,donorCopy,fs.constants.COPYFILE_EXCL);
  fs.writeFileSync(path.join(run,'alpha-v'+version+'.bin'),a,{flag:'wx'});
  await sharp(out,{raw:{width:w,height:h,channels:3}}).png().toFile(file);
  save(path.join(run,'result-v'+version+'.json'),{output_sha256:hash(fs.readFileSync(file)),donor_sha256:hash(fs.readFileSync(donorCopy)),alpha_sha256:hash(a),guard_sha256:hash(g),region,additional_generation_calls:0,visual_qa:'pending',scope:c.scope});
  return verify(run,version);
}
async function verify(run,version) {
  versionCheck(version);const {c,base,g}=await load(run),[w,h]=c.spec.size;
  const r=json(path.join(run,'result-v'+version+'.json')),file=path.join(run,'candidate-v'+version+'.png'),donorFile=path.join(run,'donor-v'+version+'.png'),a=fs.readFileSync(path.join(run,'alpha-v'+version+'.bin'));
  if(hash(fs.readFileSync(file))!==r.output_sha256||hash(fs.readFileSync(donorFile))!==r.donor_sha256||hash(a)!==r.alpha_sha256||r.guard_sha256!==c.guard_sha256||a.length!==w*h) throw Error('Result artifacts changed');
  const out=await rgb(file,c.spec.size),donor=await rgb(donorFile,c.spec.size);let changed=0,head=0,face=0,outside=0,equation=0;
  const f=c.spec.face_rectangle;
  for(let i=0;i<a.length;i++) {
    let diff=false;
    for(let k=0;k<3;k++) {if(out[i*3+k]!==base[i*3+k])diff=true;if(out[i*3+k]!==Math.round((base[i*3+k]*(255-a[i])+donor[i*3+k]*a[i])/255))equation++;}
    if(diff) {changed++;if(g[i])head++;if(!a[i])outside++;const x=i%w,y=Math.floor(i/w);if(x>=f[0]&&x<f[2]&&y>=f[1]&&y<f[3])face++;}
  }
  const report={pass:head===0&&face===0&&outside===0&&equation===0&&changed>0,changed_pixels:changed,head_changed_pixels:head,face_changed_pixels:face,outside_alpha_changed_pixels:outside,blend_mismatch_channels:equation,visual_qa:'pending',original_fidelity:'not_measured',generation_calls:0};
  console.log(JSON.stringify(report));if(!report.pass)throw Error('qa-retry: deterministic protection failed');return report;
}
(async()=>{
  const [command,...args]=process.argv.slice(2);
  if(command==='--help'||command==='help') {console.log('Local only; host sharp required. prepare <spec.json> <new-private-run> | apply <run> <donor> <version> [region-refinement.json] | verify <run> <version>. No generation/installation/visual QA.');return;}
  dependency();
  if(command==='prepare'&&args.length===2)await prepare(...args);
  else if(command==='apply'&&(args.length===3||args.length===4))await apply(...args);
  else if(command==='verify'&&args.length===2)await verify(...args);
  else throw Error('Invalid command; use --help');
})().catch(error=>{console.error(error.message);process.exitCode=1;});
