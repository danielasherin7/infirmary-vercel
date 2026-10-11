"""The website page (HTML, CSS, JavaScript) as one Python string.
Edit the page here, between the triple quotes. It lives in a .py file so Vercel always
ships it together with app.py."""

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Infirmary Emergency Desk</title>
<style>
:root{--bg:#eef3f1;--card:#fff;--tx:#14201b;--mu:#62736b;--bd:#dbe5e0;--ac:#0b7a5a;--ac2:#0f9d73;--c4:#d32f2f;--c3:#ef6c00;--c2:#b28704;--c1:#2e7d32;--sh:0 6px 24px rgba(16,60,45,.08)}
@media(prefers-color-scheme:dark){:root{--bg:#0f1513;--card:#18201d;--tx:#e8f0ec;--mu:#93a69c;--bd:#27332e;--ac:#2fb68a;--ac2:#3fd0a0;--c4:#ff6b6b;--c3:#ffa94d;--c2:#e0c050;--c1:#69c36d;--sh:none}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.55 "Segoe UI",system-ui,sans-serif}
.hero{background:linear-gradient(135deg,#0b7a5a,#0f9d73);color:#fff;padding:26px 16px 70px}
.wrap{max-width:780px;margin:0 auto}.hero h1{margin:0;font-size:1.6rem}.hero p{margin:4px 0 0;opacity:.9}
.nav{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
main{max-width:780px;margin:-48px auto 40px;padding:0 16px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:16px;padding:20px;margin-bottom:16px;box-shadow:var(--sh)}
h2{font-size:1.1rem;margin:0 0 12px}.mu{color:var(--mu);font-size:.88rem}
label{display:block;font-size:.84rem;font-weight:600;margin:12px 0 5px;color:var(--mu)}
input,select,textarea{width:100%;padding:11px 12px;border:1.5px solid var(--bd);border-radius:10px;background:var(--bg);color:var(--tx);font:inherit;transition:.15s}
input:focus,select:focus,textarea:focus{outline:0;border-color:var(--ac);box-shadow:0 0 0 3px rgba(15,157,115,.18)}
textarea{min-height:90px;resize:vertical}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:560px){.row{grid-template-columns:1fr}}
button{padding:11px 18px;border:0;border-radius:10px;background:var(--ac);color:#fff;font:inherit;font-weight:600;cursor:pointer;transition:.15s}
button:hover{filter:brightness(1.08)}button:disabled{opacity:.45;cursor:not-allowed}
button.g{background:transparent;color:var(--tx);border:1.5px solid var(--bd)}button.d{background:var(--c4)}button.w{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.4)}
.tabs{display:flex;gap:4px;background:var(--bg);padding:4px;border-radius:12px;margin-bottom:8px}.tabs button{flex:1;background:transparent;color:var(--mu)}.tabs button.on{background:var(--card);color:var(--ac);box-shadow:var(--sh)}
.item{border:1px solid var(--bd);border-left:6px solid var(--bd);border-radius:12px;padding:14px;margin-bottom:12px}
.s4{border-left-color:var(--c4)}.s3{border-left-color:var(--c3)}.s2{border-left-color:var(--c2)}.s1{border-left-color:var(--c1)}
.badge{display:inline-block;padding:1px 10px;border-radius:99px;font-size:.76rem;font-weight:700;border:1.5px solid currentColor}
.b4{color:var(--c4)}.b3{color:var(--c3)}.b2{color:var(--c2)}.b1{color:var(--c1)}
audio{width:100%;margin-top:8px}.msg{min-height:1.3em;margin-top:10px;font-size:.92rem}.bad{color:var(--c4)}.ok{color:var(--c1)}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}.stats div{background:var(--card);border:1px solid var(--bd);border-radius:14px;text-align:center;padding:12px;box-shadow:var(--sh)}.stats b{display:block;font-size:1.8rem;color:var(--ac)}
a.btn{display:inline-block;padding:11px 18px;border-radius:10px;background:var(--ac);color:#fff;font-weight:600;text-decoration:none;margin:4px 8px 4px 0}a.btn.red{background:var(--c4)}.call{border-left:6px solid var(--c4)}
.mono{font-family:ui-monospace,Consolas,monospace;font-size:.82rem;word-break:break-all}.rec{display:flex;gap:8px;flex-wrap:wrap}
</style></head><body>
<div class="hero"><div class="wrap nav"><div><h1>🏥 Infirmary Emergency Desk</h1><p>Fast help, ranked by how urgent it is.</p></div><div id="who"></div></div></div>
<main id="app"></main>
<script>
const $=s=>document.querySelector(s),app=$('#app');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const SEV={4:['Critical','unconscious, not breathing, severe bleeding, chest pain'],3:['High','fracture, asthma attack, high fever, severe pain'],2:['Medium','injury, vomiting, dizziness'],1:['Low','minor cut, headache, first aid']};
async function api(url,opt={}){const r=await fetch(url,opt);const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.error||'Something went wrong');return d}
const jpost=(u,b)=>api(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})});
const msg=(t,ok)=>{const m=$('#m');if(m){m.className='msg '+(ok?'ok':'bad');m.textContent=t}};
const ago=t=>{const m=Math.floor((Date.now()/1000-t)/60);return m<1?'just now':m+' min ago'};
let tab='login',me={},cfg={phone:'',staffCode:false},poll,audioBlob=null,rec=null;

async function start(){clearInterval(poll);try{cfg=await api('/api/config')}catch(e){}try{me=await api('/api/me')}catch(e){me={}}
  $('#who').innerHTML=me.role?`<span>${esc(me.name)}${me.designation?' · '+esc(me.designation):''}</span> <button class="w" id="lo">Log out</button>`:'';
  if($('#lo'))$('#lo').onclick=async()=>{await jpost('/api/logout');start()};
  me.role==='staff'?staffView():me.role==='student'?studentView():authView()}

const callCard=()=>`<div class="card call"><h2>📞 Can't type, or no internet? Call us</h2>
  <p>Call the infirmary and explain the emergency in your own words. You don't need to log in or type anything.</p>
  <p><a class="btn" href="tel:${esc(cfg.phone.replace(/[^+\d]/g,''))}">Call Infirmary: ${esc(cfg.phone)}</a><a class="btn red" href="tel:112">Emergency: 112</a></p>
  <p class="mu">When you call, say <b>who</b> needs help, <b>where</b> they are, <b>what</b> happened, and whether the person is awake and breathing. Stay on the line and stay where you are. If someone else is hurt, stay with them and ask a person nearby to make the call.</p></div>`;

function authView(){
  const T=[['login','Student login'],['register','Student register'],['staff','Staff login'],['sregister','Staff register']];
  app.innerHTML=`<div class="card"><div class="tabs" style="flex-wrap:wrap">${T.map(([k,l])=>`<button data-t="${k}" class="${tab==k?'on':''}">${l}</button>`).join('')}</div><div id="f"></div><div class="msg" id="m"></div></div>${callCard()}
  <p class="mu" style="text-align:center">First time? Register once with your college email, then log in.</p>`;
  app.querySelectorAll('[data-t]').forEach(b=>b.onclick=()=>{tab=b.dataset.t;authView()});
  const f=$('#f');
  if(tab=='register'){f.innerHTML=`<label>Full name</label><input id="n"><label>College email</label><input id="e" type="email" placeholder="name@college.ac.in">
  <div class="row"><div><label>Register number (username)</label><input id="r"></div><div><label>Date of birth (default password)</label><input id="d" type="date"></div></div>
  <label>Own password (optional)</label><input id="p" type="password"><p><button id="go">Create account</button></p>`;
   $('#go').onclick=async()=>{try{await jpost('/api/register',{name:$('#n').value,email:$('#e').value,regno:$('#r').value,dob:$('#d').value,password:$('#p').value});tab='login';authView();msg('Registered! Log in with your register number.',1)}catch(e){msg(e.message)}}}
  else if(tab=='sregister'){f.innerHTML=`<label>Full name</label><input id="n"><label>College email</label><input id="e" type="email" placeholder="name@college.ac.in">
  <div class="row"><div><label>Designation</label><input id="g" list="dl" placeholder="e.g. Nurse"><datalist id="dl"><option>Doctor</option><option>Nurse</option><option>Medical Officer</option><option>Pharmacist</option><option>Attender</option></datalist></div>
  <div><label>Password (min 6 characters)</label><input id="p" type="password"></div></div>
  ${cfg.staffCode?'<label>Staff registration code (ask the infirmary in-charge)</label><input id="c" type="password">':''}
  <p><button id="go">Register as staff</button></p>`;
   $('#go').onclick=async()=>{try{await jpost('/api/staff/register',{name:$('#n').value,email:$('#e').value,designation:$('#g').value,password:$('#p').value,code:$('#c')?$('#c').value:''});tab='staff';authView();msg('Registered! Log in with your email.',1)}catch(e){msg(e.message)}}}
  else{const st=tab=='staff';f.innerHTML=`<label>${st?'College email':'Register number'}</label><input id="u"><label>${st?'Password':'Password (your own, or DOB as YYYY-MM-DD)'}</label><input id="p" type="password"><p><button id="go">Log in</button></p>`;
   $('#go').onclick=async()=>{try{await jpost('/api/login',{role:st?'staff':'student',username:$('#u').value,password:$('#p').value});start()}catch(e){msg(e.message)}}}
}

function studentView(){
  const age=me.dob?Math.max(0,Math.floor((Date.now()-new Date(me.dob))/31557600000)):'';
  app.innerHTML=`<div class="card"><h2>🚨 Send an emergency request</h2>
  <label>Who needs help?</label><select id="w"><option value="0">Myself</option><option value="1">Someone else (I am reporting for them)</option></select>
  <div class="row"><div><label id="nl">Your name</label><input id="n" value="${esc(me.name)}"></div><div><label id="rl">Your register number</label><input id="r" value="${esc(me.id)}" readonly></div></div>
  <div class="row"><div><label id="al">Your age</label><input id="a" type="number" min="1" max="99" value="${age}"></div><div><label>Where are they / you now?</label><input id="l" placeholder="e.g. Library, 2nd floor"></div></div>
  <label>How serious is it?</label><select id="s">${[4,3,2,1].map(k=>`<option value="${k}">${SEV[k][0]} — ${SEV[k][1]}</option>`).join('')}</select>
  <label>What happened?</label><textarea id="ds" placeholder="Type here, or record a voice message"></textarea>
  <label>Voice message (optional, max 30 s)</label><div class="rec"><button class="g" id="rs">🎤 Record</button><button class="g" id="rx" disabled>■ Stop</button><button class="g" id="rc" disabled>Delete</button></div><div id="pv"></div>
  <div class="msg" id="m"></div><p><button class="d" id="go">Send emergency request</button></p></div>
  ${callCard()}
  <div class="card"><h2>My requests</h2><div id="mine"></div></div>`;
  audioBlob=null;
  $('#w').onchange=()=>{const o=$('#w').value=='1';
   $('#nl').textContent=o?"Patient's name":'Your name';$('#n').value=o?'':me.name;
   $('#rl').textContent=o?"Patient's register number (if you know it)":'Your register number';$('#r').readOnly=!o;$('#r').value=o?'':me.id;
   $('#al').textContent=o?"Patient's age (guess if unsure)":'Your age';$('#a').value=o?'':age};
  $('#rs').onclick=async()=>{try{const st=await navigator.mediaDevices.getUserMedia({audio:true}),ch=[];rec=new MediaRecorder(st);
   rec.ondataavailable=e=>ch.push(e.data);
   rec.onstop=()=>{st.getTracks().forEach(t=>t.stop());audioBlob=new Blob(ch,{type:rec.mimeType});$('#pv').innerHTML=`<audio controls src="${URL.createObjectURL(audioBlob)}"></audio>`;$('#rc').disabled=false;$('#rs').disabled=false;$('#rx').disabled=true};
   rec.start();$('#rs').disabled=true;$('#rx').disabled=false;setTimeout(()=>rec.state==='recording'&&rec.stop(),30000)}catch(e){msg('Microphone not available. Please type, or call the infirmary below.')}};
  $('#rx').onclick=()=>rec&&rec.state==='recording'&&rec.stop();
  $('#rc').onclick=()=>{audioBlob=null;$('#pv').innerHTML='';$('#rc').disabled=true};
  $('#go').onclick=async()=>{const o=$('#w').value;const fd=new FormData();fd.append('name',$('#n').value);fd.append('age',$('#a').value);fd.append('location',$('#l').value);fd.append('sev',$('#s').value);fd.append('description',$('#ds').value);
   fd.append('for_other',o);fd.append('patient_regno',o=='1'?$('#r').value:'');
   if(audioBlob)fd.append('audio',audioBlob,'voice.webm');
   try{await api('/api/requests',{method:'POST',body:fd});$('#ds').value='';audioBlob=null;$('#pv').innerHTML='';msg('Request sent. Stay where you are — help is coming. No internet? Call the infirmary below.',1);mine()}catch(e){msg(e.message+' — if this keeps failing, call the infirmary below.')}};
  mine();poll=setInterval(mine,2500);
}
async function mine(){const el=$('#mine');if(!el)return;try{const l=await api('/api/my-requests');
  el.innerHTML=l.length?l.map(r=>`<div class="item s${r.sev}"><span class="badge b${r.sev}">${r.level}</span> <span class="mu">${ago(r.created)} · ${esc(r.location)}${r.forOther?' · for '+esc(r.name):''}</span><div>${r.status=='waiting'?`⏳ Waiting — position <b>${r.position}</b> of ${r.total}`:r.status=='accepted'?`🚑 <b>${esc(r.by)}</b> is on the way`:'✅ Resolved'}</div></div>`).join(''):'<p class="mu">No requests yet.</p>'}catch(e){}}

function staffView(){
  app.innerHTML=`<div class="stats"><div><b id="c1">0</b><span class="mu">waiting</span></div><div><b id="c2">0</b><span class="mu">on the way</span></div></div>
  <div class="card"><h2>Emergency queue — highest priority first</h2><div id="q"></div><details><summary class="mu">Max-heap array (DSA view)</summary><p class="mono" id="hp"></p></details></div>
  <div class="card"><h2>My active cases</h2><div id="ot"></div></div><div class="msg bad" id="m"></div>`;
  refresh();poll=setInterval(refresh,2500);
}
const audioTag=r=>r.hasAudio?`<audio controls preload="none" src="/api/audio/${r.id}"></audio>`:'';
const card=(r,x='')=>`<div class="item s${r.sev}"><span class="badge b${r.sev}">${r.level}</span> <b>${esc(r.name)}</b> <span class="mu">· ${esc(r.forOther?(r.patientRegno||'reg no unknown'):r.regno)} · age ${esc(r.age)} · ${ago(r.created)}</span>${r.forOther?`<div class="mu">👥 Reported by ${esc(r.reporter)} (${esc(r.regno)}) for someone else</div>`:''}<div>📍 ${esc(r.location)}</div>${r.description?`<div>${esc(r.description)}</div>`:''}${audioTag(r)}${x}</div>`;
async function refresh(){if(!$('#q')||document.activeElement?.tagName==='AUDIO')return;
  if([...document.querySelectorAll('audio')].some(a=>!a.paused))return;
  try{const d=await api('/api/queue');$('#c1').textContent=d.queue.length;$('#c2').textContent=d.inProgress.length;
   $('#q').innerHTML=d.queue.length?d.queue.map((r,i)=>card(r,i==0?`<p><button id="acc">Respond to this emergency</button></p>`:`<div class="mu">#${i+1} in queue</div>`)).join(''):'<p class="mu">No emergencies waiting.</p>';
   $('#hp').textContent='['+d.heap.join(', ')+']  (severity@arrival)';
   $('#ot').innerHTML=d.inProgress.length?d.inProgress.map(r=>card(r,`<p><button class="g" data-done="${r.id}">Mark resolved</button></p>`)).join(''):'<p class="mu">Nothing in progress.</p>';
   if($('#acc'))$('#acc').onclick=async()=>{try{await jpost('/api/queue/accept');refresh()}catch(e){msg(e.message)}};
   document.querySelectorAll('[data-done]').forEach(b=>b.onclick=async()=>{await jpost(`/api/requests/${b.dataset.done}/resolve`);refresh()})}catch(e){}}
start();
</script></body></html>
"""
