
/* AI Dental Hospital OS — Enterprise CRM & Operations layer.
   Keeps the legacy modules and adds a 360-degree patient/operations workspace. */
(() => {
  const legacyLoad = window.load;
  const legacyGo = window.go;
  let active = 'Executive Dashboard';
  const legacyModules = [
    'Patients & EMR','Appointments & Queue','Clinical Records','Odontogram','Periodontal Chart',
    'Treatment Plans','Prescriptions','Billing & Payments',
    'Inventory & Procurement','Dental Laboratory','AI Dental Copilot','Analytics & Reports','Administration & Security'
  ];
  const groups = [
    {title:'WORKSPACE',items:['Executive Dashboard','Patient 360','Enquiries & Leads','Appointments & Queue','Clinical Records','Treatment & Care','Prescriptions','Dental Imaging']},
    {title:'OPERATIONS',items:['Billing & Payments','Inventory & Procurement','Dental Laboratory','Suppliers & Partners','Follow-ups & Recalls','Complaints & Escalations']},
    {title:'GROWTH & CRM+',items:['Growth & Loyalty','Reviews & Reputation','Campaigns']},
    {title:'INTELLIGENCE',items:['MIS & Dashboards','AI Clinical Copilot','AI+ Advanced Suite','Odontogram','Periodontal Chart']},
    {title:'SYSTEM',items:['Administration & Security']}
  ];
  const getUser=()=>JSON.parse(localStorage.getItem('dental_user')||'null');
  const money=n=>'₹'+Number(n||0).toLocaleString('en-IN',{maximumFractionDigits:0});
  const safe=s=>window.esc?esc(s):String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const api=window.api;
  const app=document.getElementById('app');

  function shell(content='',subtitle='Operations command center'){
    const u=getUser();
    app.innerHTML=`<div class="enterprise">
      <aside class="eside">
        <div class="elogo"><span class="logoMark">✦</span><div><b>AI Dental</b><small>Hospital OS</small></div></div>
        <div class="clinicTag">CLINIC OPERATING SYSTEM</div>
        <div class="enav">${groups.map(g=>`<div class="navGroup"><div class="navTitle">${g.title}</div>${g.items.map(i=>`<button class="${i===active?'eactive':''}" onclick="window.eGo('${i.replace(/'/g,"\\'")}')"><span>${icon(i)}</span>${i}</button>`).join('')}</div>`).join('')}</div>
        <div class="esideBottom"><div class="onlineDot"></div><span>System online</span><button onclick="window.eLogout()">Sign out</button></div>
      </aside>
      <main class="emain">
        <header class="etop"><div><div class="eyebrow">AI DENTAL HOSPITAL OS</div><h1>${safe(active)}</h1><p>${subtitle}</p></div>
        <div class="etopRight"><div class="statusPill">● Live</div><div class="userCard"><div class="avatar">${safe((u?.name||'A')[0])}</div><div><b>${safe(u?.name||'User')}</b><small>${safe(u?.role||'')}</small></div></div></div></header>
        <section id="enterpriseContent">${content||'<div class="loadingCard">Loading workspace…</div>'}</section>
      </main>
    </div>`;
  }
  function icon(x){
    const m={'Executive Dashboard':'⌂','Patient 360':'◉','Enquiries & Leads':'◎','Appointments & Queue':'◷','Clinical Records':'✚','Treatment & Care':'◇','Prescriptions':'Rx','Dental Imaging':'▣','Billing & Payments':'₹','Inventory & Procurement':'▤','Dental Laboratory':'◈','Suppliers & Partners':'⇄','Follow-ups & Recalls':'↻','Complaints & Escalations':'!','Growth & Loyalty':'★','Reviews & Reputation':'☆','Campaigns':'▶','MIS & Dashboards':'▥','AI Clinical Copilot':'✦','AI+ Advanced Suite':'⚡','Odontogram':'◌','Periodontal Chart':'⌁','Administration & Security':'⚙'};return m[x]||'•';
  }
  function card(label,value,trend='',cls=''){
    return `<div class="metric ${cls}"><div class="metricTop"><span>${label}</span><i>↗</i></div><strong>${value}</strong>${trend?`<small>${trend}</small>`:''}</div>`;
  }
  function table(head,rows){
    if(!rows.length)return `<div class="empty">No records yet. Use the action above to create the first record.</div>`;
    return `<div class="tableWrap"><table><thead><tr>${head.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }
  function modal(title,body){
    const m=document.createElement('div');m.className='eModal';m.innerHTML=`<div class="eModalBox"><div class="eModalHead"><div><span>WORKFLOW</span><h2>${title}</h2></div><button onclick="this.closest('.eModal').remove()">×</button></div><div class="eModalBody">${body}</div></div>`;document.body.appendChild(m);return m;
  }
  async function dashboard(){
    const [d,s,rev]=await Promise.all([api('/crm/dashboard'),api('/reports/summary'),api('/crm/revenue')]);
    const max=Math.max(1,...rev.map(x=>Number(x.revenue||0)));
    shell(`<div class="heroGrid">
      <div class="heroPanel"><div class="heroKicker">TODAY AT A GLANCE</div><h2>One command center for your entire dental practice.</h2><p>Track patients, chair utilization, treatment conversion, collections and recalls without switching systems.</p>
      <div class="heroActions"><button class="primary" onclick="window.eGo('Patient 360')">Open Patient 360</button><button class="ghost" onclick="window.newPatient()">+ New patient</button></div></div>
      <div class="focusPanel"><div class="focusTitle">Attention today</div><div class="attention"><b>${d.followups_due}</b><span>follow-ups due</span></div><div class="attention"><b>${d.recalls_due}</b><span>recalls due</span></div><div class="attention"><b>${d.pending_payments}</b><span>pending payments</span></div><div class="attention"><b>${d.complaints_open}</b><span>open complaints</span></div></div>
    </div>
    <div class="metrics">${card('Total patients',d.patients,'Master patient database')}${card('New enquiries',d.new_enquiries,'Today')}${card('Appointments',d.appointments_today,'Today')}${card('Revenue',money(d.revenue_month),'This month')}${card('Outstanding',money(d.outstanding),'Collections')}${card('Active treatments',d.treatments_active,'In progress')}</div>
    <div class="twoCol">
      <div class="panel"><div class="panelHead"><div><span class="eyebrow">REVENUE</span><h3>Last 30 days</h3></div><span class="badge green">${money(d.revenue_today)} today</span></div>
        <div class="bars">${rev.slice(-14).map(x=>`<div class="barCol"><div class="bar" style="height:${Math.max(6,Number(x.revenue||0)/max*130)}px"></div><small>${String(x.day).slice(8)}</small></div>`).join('')}</div>
      </div>
      <div class="panel"><div class="panelHead"><div><span class="eyebrow">OPERATIONS</span><h3>Live control board</h3></div></div>
      <div class="controlList"><div><span>Low stock</span><b>${d.low_stock}</b></div><div><span>Completed today</span><b>${d.completed_today}</b></div><div><span>Open leads</span><b>${d.open_leads}</b></div><div><span>Recall queue</span><b>${d.recalls_due}</b></div></div></div>
    </div>
    <div class="mediaHero"><div><span class="eyebrow">CLINIC EXPERIENCE</span><h3>Modern chairside + management workspace</h3><p>Designed around the workflows seen across leading dental PMS platforms: scheduling, patient 360, charting, treatment, billing, recall, communication and management reporting.</p></div><video autoplay muted loop playsinline poster="assets/dental-operatory.svg"><source src="assets/dental-loop.mp4" type="video/mp4"></video></div><div class="visualStrip"><div><img src="assets/patient-360.svg" alt="Patient 360"><span>Patient 360 workspace</span></div><div><img src="assets/ai-clinical.svg" alt="AI clinical copilot"><span>AI clinical intelligence</span></div><div><img src="assets/dental-operatory.svg" alt="Dental operatory"><span>Connected chairside operations</span></div></div><div class="quickGrid"><button onclick="window.eGo('Enquiries & Leads')"><b>Lead pipeline</b><span>Enquiry → assignment → conversion</span></button><button onclick="window.eGo('Follow-ups & Recalls')"><b>Recall engine</b><span>Cleaning, follow-up & maintenance</span></button><button onclick="window.eGo('MIS & Dashboards')"><b>Management MIS</b><span>Daily, weekly & monthly</span></button><button onclick="window.eGo('AI Clinical Copilot')"><b>AI Copilot</b><span>Voice, SOAP, lead scoring & recall AI</span></button><button onclick="window.eGo('Dental Imaging')"><b>Imaging & MRI AI</b><span>X-ray, OPG, CBCT & MRI screening</span></button><button onclick="window.eGo('Growth & Loyalty')"><b>Growth & Loyalty</b><span>Points, tiers & referral rewards</span></button><button onclick="window.eGo('Reviews & Reputation')"><b>Reviews</b><span>Requests, NPS & response queue</span></button><button onclick="window.eGo('AI+ Advanced Suite')"><b>AI+ Suite</b><span>No-show risk, sentiment & receptionist</span></button></div>`, 'Real-time clinic, CRM, finance and patient-care visibility');
  }
  async function patient360(){
    const ps=await api('/patients');
    shell(`<div class="toolbar"><input id="patientSearch" placeholder="Search patient by name, UHID or phone"><button class="primary" onclick="window.loadPatientList()">Search</button><button class="ghost" onclick="window.newPatient()">+ Register patient</button></div><div id="patientList">${patientCards(ps)}</div>`, 'Master patient database with 360° longitudinal records');
  }
  function patientCards(rows){return `<div class="patientGrid">${rows.map(p=>`<button class="patientCard" onclick="window.openP360(${p.id})"><div class="pAvatar">${safe((p.name||'P')[0])}</div><div><b>${safe(p.name)}</b><span>${safe(p.uhid)}</span><span>${safe(p.phone||'No phone')}</span></div><em>View 360 →</em></button>`).join('')}</div>`}
  window.loadPatientList=async()=>{const s=document.getElementById('patientSearch').value;const ps=await api('/patients?search='+encodeURIComponent(s));document.getElementById('patientList').innerHTML=patientCards(ps)};
  window.openP360=async id=>{
    const d=await api('/crm/patient-360/'+id),p=d.patient;
    shell(`<div class="profileHero"><div class="pAvatar big">${safe((p.name||'P')[0])}</div><div><span class="eyebrow">PATIENT 360</span><h2>${safe(p.name)}</h2><p>${safe(p.uhid)} · ${safe(p.phone||'No phone')} · ${safe(p.email||'No email')}</p></div><div class="profileActions"><button class="primary" onclick="window.openP360(${id})">Refresh</button><button class="ghost" onclick="window.statusForm(${id})">Update status</button><button class="ghost" onclick="window.mediaForm(${id})">Upload media</button></div></div>
      <div class="tabs"><span class="tab active">Overview</span><span class="tab">Clinical</span><span class="tab">Treatment</span><span class="tab">Finance</span><span class="tab">Communication</span></div>
      <div class="twoCol"><div class="panel"><div class="panelHead"><h3>Clinical history</h3></div>${table(['Date','Doctor','Complaint','Diagnosis'],d.visits.slice(0,8).map(v=>[safe(String(v.visit_date||'').slice(0,16)),safe(v.doctor_name||'—'),safe(v.chief_complaint||'—'),safe(v.diagnosis||'—')]))}</div>
      <div class="panel"><div class="panelHead"><h3>Care & treatment</h3><button class="miniBtn" onclick="window.followupForm(${id})">+ Follow-up</button></div>${table(['Treatment','Amount','Status'],d.treatments.map(t=>[safe(t.title||'Treatment'),money(t.amount),`<span class="status">${safe(t.status)}</span>`]))}</div></div>
      <div class="twoCol"><div class="panel"><div class="panelHead"><h3>Payments</h3></div>${table(['Invoice','Amount','Paid','Status'],d.invoices.map(i=>[safe(i.invoice_no),money(i.amount),money(i.paid),safe(i.status)]))}</div>
      <div class="panel"><div class="panelHead"><h3>Recall & follow-up</h3></div>${table(['Type','Due','Status'],[...d.recalls.map(r=>[safe(r.type),safe(r.due_at),safe(r.status)]),...d.followups.map(f=>[safe(f.type),safe(String(f.due_at||'').slice(0,10)),safe(f.status)])])}</div></div>
      <div class="panel"><div class="panelHead"><h3>Documents & media</h3><button class="miniBtn" onclick="window.mediaForm(${id})">+ Upload</button></div><div class="mediaGrid">${d.documents.length?d.documents.map(x=>mediaCard(x)).join(''):'<div class="empty">No documents or media uploaded.</div>'}</div></div>
      <div class="panel"><div class="panelHead"><h3>Document checklist</h3></div>${table(['Document','Required','Status'],d.checklist.map(x=>[safe(x.document_type),x.required?'Yes':'No',safe(x.status)]))}</div>`, 'Longitudinal patient history, clinical, financial and engagement data');
  };
  function mediaCard(x){const url='/uploads/'+encodeURIComponent(x.storage_path);const isImg=/image|png|jpg|jpeg|webp|gif/i.test(x.content_type||x.filename);const isVid=/video|mp4|mov|webm/i.test(x.content_type||x.filename);return `<div class="mediaCard">${isImg?`<img src="${url}" alt="">`:isVid?`<video src="${url}" controls></video>`:`<div class="docIcon">DOC</div>`}<div><b>${safe(x.filename)}</b><small>${safe(x.content_type||'file')}</small></div></div>`}
  window.mediaForm=id=>{const m=modal('Patient documents & media',`<form id="mediaF"><input id="mediaFile" type="file" accept=".pdf,.jpg,.jpeg,.png,.webp,.gif,.mp4,.mov,.webm,.doc,.docx" required><p class="formHint">Images and clinical videos can be stored against the patient record. AI analysis should only be enabled with a validated clinical imaging provider.</p><button class="primary">Upload</button></form>`);document.getElementById('mediaF').onsubmit=async e=>{e.preventDefault();const fd=new FormData();fd.append('file',document.getElementById('mediaFile').files[0]);await api('/documents/'+id,{method:'POST',body:fd});m.remove();window.openP360(id)}};
  window.statusForm=id=>{const m=modal('Patient status',`<select id="st"><option>ACTIVE</option><option>NEW</option><option>IN_TREATMENT</option><option>TREATMENT_COMPLETED</option><option>RECALL_DUE</option><option>INACTIVE</option></select><textarea id="sn" placeholder="Notes"></textarea><button class="primary" onclick="window.saveStatus(${id})">Save status</button>`);};
  window.saveStatus=async id=>{await api('/crm/patient-status/'+id,{method:'PATCH',body:JSON.stringify({status:st.value,notes:sn.value})});document.querySelector('.eModal').remove();window.openP360(id)};
  window.newPatient=()=>{const m=modal('Register new patient',`<input id="pn" placeholder="Full name"><input id="pp" placeholder="Phone"><input id="pe" placeholder="Email"><textarea id="ph" placeholder="Medical history"></textarea><button class="primary" onclick="window.saveNewPatient()">Create patient</button>`);};
  window.saveNewPatient=async()=>{const r=await api('/patients',{method:'POST',body:JSON.stringify({name:pn.value,phone:pp.value||null,email:pe.value||null,medical_history:ph.value||null})});document.querySelector('.eModal').remove();window.openP360(r.id)};
  async function crmPage(){
    const [e,l]=await Promise.all([api('/crm/enquiries'),api('/crm/leads')]);
    shell(`<div class="crmTop"><div class="pipeline">${['NEW','CONTACTED','CONSULTATION','TREATMENT_PROPOSED','WON','LOST'].map(stage=>`<div><span>${stage.replaceAll('_',' ')}</span><b>${l.filter(x=>x.stage===stage).length}</b></div>`).join('')}</div><div class="heroActions"><button class="primary" onclick="window.enquiryForm()">+ New enquiry</button><button class="ghost" onclick="window.leadForm()">+ New lead</button></div></div>
    <div class="twoCol"><div class="panel"><div class="panelHead"><div><span class="eyebrow">NEW ENQUIRIES</span><h3>Lead capture & assignment</h3></div></div>${table(['Name','Source','Interest','Stage','Assigned'],e.map(x=>[safe(x.name),safe(x.source||'—'),safe(x.interest||'—'),`<span class="status">${safe(x.stage)}</span>`,safe(x.assigned_name||'Unassigned')]))}</div>
    <div class="panel"><div class="panelHead"><div><span class="eyebrow">PIPELINE</span><h3>Patient conversion</h3></div></div>${table(['Lead','Stage','Value','Assigned'],l.map(x=>[safe(x.name),`<select onchange="window.updateLead(${x.id},this.value)">${['NEW','CONTACTED','CONSULTATION','TREATMENT_PROPOSED','WON','LOST'].map(s=>`<option ${s===x.stage?'selected':''}>${s}</option>`).join('')}</select>`,money(x.expected_value),safe(x.assigned_name||'Unassigned')]))}</div></div>`, 'Enquiries, lead assignment, conversion and patient acquisition');
  }
  window.enquiryForm=()=>{const m=modal('New enquiry',`<input id="en" placeholder="Name"><input id="ep" placeholder="Phone"><input id="ee" placeholder="Email"><input id="es" placeholder="Source (Google, referral, walk-in)"><input id="ei" placeholder="Treatment interest"><select id="eg"><option>NEW</option><option>CONTACTED</option><option>CONSULTATION</option></select><button class="primary" onclick="window.saveEnquiry()">Create enquiry</button>`);};
  window.saveEnquiry=async()=>{await api('/crm/enquiries',{method:'POST',body:JSON.stringify({name:en.value,phone:ep.value,email:ee.value,source:es.value,interest:ei.value,stage:eg.value})});document.querySelector('.eModal').remove();window.eGo('Enquiries & Leads')};
  window.leadForm=()=>{const m=modal('New lead',`<input id="ln" placeholder="Lead / patient name"><input id="lp" placeholder="Phone"><input id="ls" placeholder="Source"><input id="lv" type="number" placeholder="Expected treatment value"><select id="lg"><option>NEW</option><option>CONTACTED</option><option>CONSULTATION</option><option>TREATMENT_PROPOSED</option></select><button class="primary" onclick="window.saveLead()">Create lead</button>`);};
  window.saveLead=async()=>{await api('/crm/leads',{method:'POST',body:JSON.stringify({name:ln.value,phone:lp.value,source:ls.value,expected_value:Number(lv.value||0),stage:lg.value})});document.querySelector('.eModal').remove();window.eGo('Enquiries & Leads')};
  window.updateLead=async(id,stage)=>{await api('/crm/leads/'+id,{method:'PATCH',body:JSON.stringify({stage})})};
  async function operations(kind){
    const configs={
      'Suppliers & Partners':[['suppliers','Suppliers','Name','Contact','Phone','GSTIN'],['partners','Partners','Name','Type','Contact','Commission']],
      'Follow-ups & Recalls':[['followups','Follow-ups','Patient','Type','Due','Status'],['recalls','Recalls','Patient','Type','Due','Status']],
      'Complaints & Escalations':[['complaints','Complaints','Patient','Category','Severity','Status']]
    };
    const cfg=configs[kind];let blocks='';
    for(const c of cfg){const rows=await api('/crm/'+c[0]);blocks+=`<div class="panel"><div class="panelHead"><div><span class="eyebrow">${c[1]}</span><h3>${kind}</h3></div><button class="primary" onclick="window.simpleForm('${c[0]}')">+ Add</button></div>${table(c.slice(2),rows.map(x=>c[0]==='suppliers'?[safe(x.name),safe(x.contact_person||'—'),safe(x.phone||'—'),safe(x.gstin||'—')]:c[0]==='partners'?[safe(x.name),safe(x.type||'—'),safe(x.contact_person||'—'),safe(x.commission_percent)+'%']:c[0]==='followups'?[safe(x.patient_name),safe(x.type),safe(String(x.due_at||'').slice(0,16)),safe(x.status)]:c[0]==='recalls'?[safe(x.patient_name),safe(x.type),safe(x.due_at),safe(x.status)]:[safe(x.patient_name||'—'),safe(x.category||'—'),safe(x.severity),safe(x.status)]))}</div>`}
    shell(blocks, 'Suppliers, partners, follow-up queues, recalls and complaint escalation');
  }
  window.simpleForm=type=>{let body='',title='';if(type==='suppliers'){title='Supplier';body=`<input id="snm" placeholder="Supplier name"><input id="scp" placeholder="Contact person"><input id="sph" placeholder="Phone"><input id="sem" placeholder="Email"><input id="sgs" placeholder="GSTIN"><textarea id="sad" placeholder="Address"></textarea><button class="primary" onclick="window.saveSimple('suppliers')">Save</button>`}else if(type==='partners'){title='Partner';body=`<input id="pnm" placeholder="Partner name"><input id="pty" placeholder="Type"><input id="pcp" placeholder="Contact person"><input id="pph" placeholder="Phone"><input id="pco" type="number" placeholder="Commission %"><button class="primary" onclick="window.saveSimple('partners')">Save</button>`}else if(type==='followups'){title='Follow-up';body=`<input id="fpi" type="number" placeholder="Patient ID"><input id="fty" placeholder="Type (consultation / payment / treatment)"><input id="fdu" type="datetime-local"><textarea id="fno" placeholder="Notes"></textarea><button class="primary" onclick="window.saveSimple('followups')">Save</button>`}else if(type==='recalls'){title='Recall';body=`<input id="rpi" type="number" placeholder="Patient ID"><select id="rty"><option>Dental Cleaning</option><option>Follow-up Recall</option><option>Treatment Maintenance</option><option>Treatment Renewal</option></select><input id="rdu" type="date"><textarea id="rno" placeholder="Notes"></textarea><button class="primary" onclick="window.saveSimple('recalls')">Save</button>`}else{title='Complaint';body=`<input id="cpi" type="number" placeholder="Patient ID"><input id="ccat" placeholder="Category"><select id="csev"><option>LOW</option><option selected>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select><textarea id="cdesc" placeholder="Complaint description"></textarea><button class="primary" onclick="window.saveSimple('complaints')">Save</button>`}modal(title,body)};
  window.saveSimple=async type=>{let b={};if(type==='suppliers')b={name:snm.value,contact_person:scp.value,phone:sph.value,email:sem.value,gstin:sgs.value,address:sad.value};if(type==='partners')b={name:pnm.value,type:pty.value,contact_person:pcp.value,phone:pph.value,commission_percent:Number(pco.value||0)};if(type==='followups')b={patient_id:Number(fpi.value),type:fty.value,due_at:fdu.value,notes:fno.value};if(type==='recalls')b={patient_id:Number(rpi.value),type:rty.value,due_at:rdu.value,notes:rno.value};if(type==='complaints')b={patient_id:Number(cpi.value)||null,category:ccat.value,severity:csev.value,description:cdesc.value};await api('/crm/'+type,{method:'POST',body:JSON.stringify(b)});document.querySelector('.eModal').remove();window.eGo(type==='suppliers'||type==='partners'?'Suppliers & Partners':type==='followups'||type==='recalls'?'Follow-ups & Recalls':'Complaints & Escalations')};
  async function mis(){
    const [d,w,m,c]=await Promise.all([api('/crm/mis?period=daily'),api('/crm/mis?period=weekly'),api('/crm/mis?period=monthly'),api('/crm/conversion')]);
    shell(`<div class="metrics">${card('Daily revenue',money(d.revenue),'Today')}${card('Weekly revenue',money(w.revenue),'7 days')}${card('Monthly revenue',money(m.revenue),'Month')}${card('Conversion',c.conversion_rate+'%','Lead → WON')}</div>
      <div class="threeCol">${misCard('DAILY MIS',d)}${misCard('WEEKLY DASHBOARD',w)}${misCard('MONTHLY DASHBOARD',m)}</div>
      <div class="panel"><div class="panelHead"><div><span class="eyebrow">PATIENT CONVERSION</span><h3>Lead funnel</h3></div></div><div class="funnel">${c.stages.map(x=>`<div><span>${safe(x.stage)}</span><b>${x.count}</b><em>${money(x.value)}</em></div>`).join('')}</div></div>`, 'Daily MIS, weekly and monthly management dashboards, conversion and revenue');
  }
  function misCard(title,d){return `<div class="panel"><span class="eyebrow">${title}</span><h3>${money(d.revenue)}</h3><div class="miniStats"><span>Patients <b>${d.new_patients}</b></span><span>Appointments <b>${d.appointments}</b></span><span>Completed <b>${d.completed}</b></span><span>Enquiries <b>${d.new_enquiries}</b></span><span>Follow-ups <b>${d.followups_completed}</b></span></div></div>`}
  async function aiPage(){
    const h=await api('/ai/health');
    shell(`<div class="aiHero"><div><span class="eyebrow">AI CLINICAL COPILOT</span><h2>AI that assists the team — never replaces the dentist.</h2><p>Use voice dictation, SOAP drafting, patient-reply drafts and treatment summaries. Every clinical output is a draft and must be reviewed.</p></div><div class="aiStatus"><b>${safe(h.status)}</b><span>${safe(h.provider)}</span><span>Voice: ${safe(h.voice)}</span></div></div>
    <div class="twoCol"><div class="panel"><div class="panelHead"><h3>Ambient voice → SOAP</h3><button class="miniBtn" id="voiceBtn">🎙 Start dictation</button></div><textarea id="aiDict" class="bigText" placeholder="Speak or type the consultation here…"></textarea><button class="primary" onclick="window.aiSoap()">Generate SOAP draft</button><pre id="aiOut"></pre></div>
    <div class="panel"><div class="panelHead"><h3>Patient communication</h3></div><textarea id="aiMsg" placeholder="Paste patient message / WhatsApp enquiry…"></textarea><button class="primary" onclick="window.aiReply()">Draft reply</button><pre id="aiReplyOut"></pre><div class="formHint">AI reply is a draft. Staff must review before sending.</div></div></div>
    <div class="panel"><div class="panelHead"><h3>Clinical copilot</h3></div><textarea id="aiPrompt" class="bigText" placeholder="Ask for a structured summary, checklist or workflow draft…"></textarea><button class="primary" onclick="window.aiGeneral()">Generate</button><pre id="aiGenOut"></pre></div><div class="threeCol"><div class="panel"><div class="panelHead"><h3>AI Lead Score</h3></div><input id="aiLeadValue" type="number" placeholder="Expected treatment value"><select id="aiLeadStage"><option>NEW</option><option>CONTACTED</option><option>CONSULTATION</option><option>TREATMENT_PROPOSED</option></select><input id="aiLeadSource" placeholder="Source e.g. referral"><button class="primary" onclick="window.aiLeadScore()">Score lead</button><pre id="aiLeadOut"></pre></div><div class="panel"><div class="panelHead"><h3>AI Follow-up Plan</h3></div><input id="aiFollowType" placeholder="Type e.g. payment follow-up"><textarea id="aiFollowNotes" placeholder="Context"></textarea><button class="primary" onclick="window.aiFollowPlan()">Create plan</button><pre id="aiFollowOut"></pre></div><div class="panel"><div class="panelHead"><h3>AI Recall Priority</h3></div><input id="aiRecallType" placeholder="Recall type" value="Dental Cleaning"><input id="aiRecallDays" type="number" placeholder="Days overdue"><button class="primary" onclick="window.aiRecallPriority()">Prioritize</button><pre id="aiRecallOut"></pre></div></div>`, 'AI-powered documentation and workflow assistance with mandatory human review');
    const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(SR){const r=new SR();r.continuous=true;r.interimResults=true;r.lang='en-IN';let final='';r.onresult=e=>{let interim='';for(let i=e.resultIndex;i<e.results.length;i++){const t=e.results[i][0].transcript;if(e.results[i].isFinal)final+=t+' ';else interim+=t;}document.getElementById('aiDict').value=final+interim};document.getElementById('voiceBtn').onclick=()=>{r.start();document.getElementById('voiceBtn').textContent='⏹ Stop dictation';document.getElementById('voiceBtn').onclick=()=>{r.stop();document.getElementById('voiceBtn').textContent='🎙 Start dictation'}}}else document.getElementById('voiceBtn').disabled=true;
  }
  window.aiSoap=async()=>{const r=await api('/ai/soap',{method:'POST',body:JSON.stringify({dictation:document.getElementById('aiDict').value})});document.getElementById('aiOut').textContent=r.draft};
  window.aiReply=async()=>{const r=await api('/ai/reply',{method:'POST',body:JSON.stringify({message:document.getElementById('aiMsg').value})});document.getElementById('aiReplyOut').textContent=r.draft};
  window.aiGeneral=async()=>{const r=await api('/ai/draft',{method:'POST',body:JSON.stringify({prompt:document.getElementById('aiPrompt').value})});document.getElementById('aiGenOut').textContent=r.draft};
  window.aiLeadScore=async()=>{const r=await api('/ai/lead-score',{method:'POST',body:JSON.stringify({expected_value:Number(document.getElementById('aiLeadValue').value||0),stage:document.getElementById('aiLeadStage').value,source:document.getElementById('aiLeadSource').value})});document.getElementById('aiLeadOut').textContent=JSON.stringify(r,null,2)};
  window.aiFollowPlan=async()=>{const r=await api('/ai/followup-plan',{method:'POST',body:JSON.stringify({type:document.getElementById('aiFollowType').value,notes:document.getElementById('aiFollowNotes').value})});document.getElementById('aiFollowOut').textContent=JSON.stringify(r,null,2)};
  window.aiRecallPriority=async()=>{const r=await api('/ai/recall-priority',{method:'POST',body:JSON.stringify({type:document.getElementById('aiRecallType').value,days_overdue:Number(document.getElementById('aiRecallDays').value||0)})});document.getElementById('aiRecallOut').textContent=JSON.stringify(r,null,2)};
  const STUDY_TYPES={XRAY_IOPA:'Intraoral X-ray (IOPA)',XRAY_BITEWING:'Bitewing X-ray',OPG:'Panoramic (OPG)',CBCT:'Cone-Beam CT (3D)',MRI:'MRI (TMJ / soft tissue / sinus)',IOS_SCAN:'Intraoral 3D scan',CLINICAL_PHOTO:'Clinical photograph'};
  function severityBadge(sev){const cls={HIGH:'badge red',MODERATE:'badge amber',LOW:'badge blue',NONE:'badge green'}[sev]||'badge';return `<span class="${cls}">${safe(sev||'—')}</span>`}
  async function imagingPage(){
    const rows=await api('/imaging/studies');
    shell(`<div class="aiHero"><div><span class="eyebrow">DENTAL IMAGING + MRI AI</span><h2>Upload X-ray, OPG, CBCT or MRI — get an instant AI screening draft.</h2><p>Covers intraoral X-ray/OPG caries &amp; bone-loss screening, CBCT implant-site analysis and the new <b>MRI module</b> for TMJ disc position, joint effusion and sinus/soft-tissue flags. Every AI finding requires clinician sign-off before it becomes part of the chart.</p></div>
      <div class="aiStatus"><b>Imaging AI</b><span>Local-demo + pluggable vision provider</span><span>MRI · CBCT · OPG · X-ray</span></div></div>
      <div class="panel"><div class="panelHead"><h3>Upload a study</h3></div>
        <form id="imgUploadForm" class="uploadForm">
          <input id="imgPatientId" type="number" placeholder="Patient ID" required>
          <select id="imgStudyType">${Object.entries(STUDY_TYPES).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select>
          <input id="imgTooth" placeholder="Tooth # (optional)">
          <input id="imgFile" type="file" accept=".jpg,.jpeg,.png,.webp,.dcm,.dicom" required>
          <textarea id="imgNotes" placeholder="Clinical notes (optional)"></textarea>
          <button class="primary" type="submit">Upload &amp; queue</button>
        </form>
        <div class="formHint">MRI studies unlock TMJ disc-position, joint-effusion and sinus screening. CBCT unlocks bone-density and implant-site checks. X-ray/OPG unlock caries and bone-loss screening.</div>
      </div>
      <div class="panel"><div class="panelHead"><h3>Studies</h3><button class="miniBtn" onclick="window.eGo('Dental Imaging')">Refresh</button></div><div id="imgStudyList">${imagingRows(rows)}</div></div>`,
      'AI-assisted radiograph, CBCT and MRI screening with mandatory clinician review');
    document.getElementById('imgUploadForm').onsubmit=async e=>{
      e.preventDefault();
      const fd=new FormData();
      fd.append('patient_id',document.getElementById('imgPatientId').value);
      fd.append('study_type',document.getElementById('imgStudyType').value);
      fd.append('tooth_number',document.getElementById('imgTooth').value||'');
      fd.append('notes',document.getElementById('imgNotes').value||'');
      fd.append('file',document.getElementById('imgFile').files[0]);
      await api('/imaging/upload',{method:'POST',body:fd});
      window.eGo('Dental Imaging');
    };
  }
  function imagingRows(rows){
    if(!rows.length)return '<div class="empty">No studies uploaded yet.</div>';
    return `<div class="imgGrid">${rows.map(r=>`<div class="imgCard">
      <div class="imgCardHead"><b>${safe(STUDY_TYPES[r.study_type]||r.study_type)}</b><span class="status">${safe(r.status)}</span></div>
      <img src="${r.storage_path?('/uploads/'+r.storage_path):''}" onerror="this.style.display='none'" alt="study">
      <div class="imgCardMeta"><span>Patient #${r.patient_id}</span>${r.tooth_number?`<span>Tooth ${safe(r.tooth_number)}</span>`:''}</div>
      <div class="imgCardActions"><button class="miniBtn" onclick="window.analyzeStudy(${r.id})">Run AI analysis</button>${r.study_type==='MRI'?`<button class="miniBtn" onclick="window.mriReport(${r.id})">MRI report</button>`:''}</div>
      <pre class="aiFindings" id="find-${r.id}">${r.ai_result?renderFindings(JSON.parse(r.ai_result)):''}</pre>
    </div>`).join('')}</div>`;
  }
  function renderFindings(res){
    const lines=(res.findings||[]).map(f=>`${severityBadge(f.severity)} ${safe(f.label)} — ${safe(f.region)} (${Math.round((f.confidence||0)*100)}% confidence)`).join('\n');
    return `${lines}\n\n${safe(res.disclaimer||'')}`;
  }
  window.analyzeStudy=async id=>{
    const el=document.getElementById('find-'+id);el.textContent='Analyzing…';
    const r=await api('/imaging/studies/'+id+'/analyze',{method:'POST'});
    el.innerHTML=renderFindings(r);
  };
  window.mriReport=async id=>{
    const r=await api('/imaging/mri/tmj-report/'+id);
    modal('MRI TMJ report',`<p>${safe(r.summary)}</p><p class="formHint">Status: ${safe(r.status)} ${r.requires_review?'— pending clinician review':''}</p>`);
  };

  async function growthPage(){
    const pid=Number(localStorage.getItem('lastGrowthPatient')||0)||'';
    shell(`<div class="panel"><div class="panelHead"><h3>Loyalty & referrals</h3></div>
      <div class="toolbar"><input id="loyPid" type="number" placeholder="Patient ID" value="${pid}"><button class="primary" onclick="window.loadLoyalty()">Load</button></div>
      <div id="loyBox" class="empty">Enter a patient ID to view their loyalty balance and referral rewards.</div>
      <div class="threeCol"><div class="panel"><h3>Add points</h3><input id="loyEarnPts" type="number" placeholder="Points (or leave blank + amount)"><input id="loyEarnAmt" type="number" placeholder="Amount spent (auto-converts)"><button class="primary" onclick="window.earnLoyalty()">Add</button></div>
      <div class="panel"><h3>Redeem</h3><input id="loyRedeemPts" type="number" placeholder="Points to redeem"><button class="primary" onclick="window.redeemLoyalty()">Redeem</button></div>
      <div class="panel"><h3>New referral</h3><input id="refName" placeholder="Referred person's name"><input id="refPhone" placeholder="Phone"><button class="primary" onclick="window.createReferral()">Log referral</button></div></div></div>
      <div class="panel"><div class="panelHead"><h3>Referral pipeline</h3></div><div id="refList">Loading…</div></div>`,
      'Loyalty points, tiers and patient-referral rewards');
    const refs=await api('/crm-plus/referrals');
    document.getElementById('refList').innerHTML=table(['Referred name','Phone','Status','Reward pts'],refs.map(r=>[safe(r.referred_name),safe(r.referred_phone||'—'),`<span class="status">${safe(r.status)}</span> ${r.status==='PENDING'?`<button class="miniBtn" onclick="window.convertReferral(${r.id})">Mark converted</button>`:''}`,r.reward_points]));
    if(pid)window.loadLoyalty();
  }
  window.loadLoyalty=async()=>{
    const pid=Number(document.getElementById('loyPid').value);if(!pid)return;
    localStorage.setItem('lastGrowthPatient',pid);
    const r=await api('/crm-plus/loyalty/'+pid);
    document.getElementById('loyBox').innerHTML=`<div class="metrics"><div class="metric"><div class="metricTop"><span>Points</span></div><strong>${r.points}</strong></div><div class="metric"><div class="metricTop"><span>Tier</span></div><strong>${safe(r.tier)}</strong></div></div>${table(['Type','Points','Reason'],r.history.map(h=>[safe(h.type),h.points,safe(h.reason||'—')]))}`;
  };
  window.earnLoyalty=async()=>{const pid=Number(document.getElementById('loyPid').value);if(!pid)return alert('Enter patient ID first');const pts=Number(document.getElementById('loyEarnPts').value||0);const amt=Number(document.getElementById('loyEarnAmt').value||0);await api('/crm-plus/loyalty/'+pid+'/earn',{method:'POST',body:JSON.stringify(pts?{points:pts}:{amount_spent:amt})});window.loadLoyalty()};
  window.redeemLoyalty=async()=>{const pid=Number(document.getElementById('loyPid').value);if(!pid)return alert('Enter patient ID first');const pts=Number(document.getElementById('loyRedeemPts').value||0);await api('/crm-plus/loyalty/'+pid+'/redeem',{method:'POST',body:JSON.stringify({points:pts})});window.loadLoyalty()};
  window.createReferral=async()=>{const pid=Number(document.getElementById('loyPid').value)||null;await api('/crm-plus/referrals',{method:'POST',body:JSON.stringify({referrer_patient_id:pid,referred_name:document.getElementById('refName').value,referred_phone:document.getElementById('refPhone').value})});window.eGo('Growth & Loyalty')};
  window.convertReferral=async id=>{await api('/crm-plus/referrals/'+id+'/convert',{method:'PATCH'});window.eGo('Growth & Loyalty')};

  async function reviewsPage(){
    const [revs,nps]=await Promise.all([api('/crm-plus/reviews'),api('/crm-plus/nps/summary').catch(()=>({nps:0,total_responses:0}))]);
    shell(`<div class="metrics">${card('NPS score',nps.nps,nps.total_responses+' responses')}${card('Reviews',revs.length,'All channels')}${card('Needing response',revs.filter(r=>r.status==='NEEDS_RESPONSE').length,'Rating ≤ 3')}</div>
      <div class="panel"><div class="panelHead"><h3>Request a review after a great visit</h3></div><div class="toolbar"><input id="revPid" type="number" placeholder="Patient ID"><button class="primary" onclick="window.requestReview()">Send review request</button></div><div class="formHint">Only send after a positive visit/NPS — avoids inviting negative public reviews.</div></div>
      <div class="panel"><div class="panelHead"><h3>All reviews</h3></div>${table(['Patient','Rating','Comment','Status'],revs.map(r=>[r.patient_id||'—','★'.repeat(r.rating),safe(r.comment||'—'),`<span class="status">${safe(r.status)}</span>`]))}</div>`,
      'Reputation management, review requests and NPS tracking');
  }
  window.requestReview=async()=>{const pid=Number(document.getElementById('revPid').value);if(!pid)return alert('Enter patient ID');await api('/crm-plus/reviews/request',{method:'POST',body:JSON.stringify({patient_id:pid})});alert('Review request queued')};

  async function campaignsPage(){
    const rows=await api('/crm-plus/campaigns');
    shell(`<div class="panel"><div class="panelHead"><h3>New campaign</h3></div>
      <input id="campName" placeholder="Campaign name (e.g. Diwali whitening offer)">
      <select id="campChannel"><option>WHATSAPP</option><option>SMS</option><option>EMAIL</option></select>
      <select id="campSegment"><option value="ALL_ACTIVE">All active patients</option><option value="OVERDUE_RECALL">Overdue recall</option><option value="HIGH_VALUE">High-value patients</option></select>
      <textarea id="campMsg" placeholder="Message template"></textarea>
      <button class="primary" onclick="window.saveCampaign()">Create draft</button></div>
      <div class="panel"><div class="panelHead"><h3>Campaigns</h3></div>${table(['Name','Channel','Segment','Status','Action'],rows.map(c=>[safe(c.name),safe(c.channel),safe(c.segment),`<span class="status">${safe(c.status)}</span>`,c.status==='DRAFT'?`<button class="miniBtn" onclick="window.launchCampaign(${c.id})">Launch</button>`:'—']))}</div>`,
      'Multi-channel WhatsApp/SMS/Email campaign automation');
  }
  window.saveCampaign=async()=>{await api('/crm-plus/campaigns',{method:'POST',body:JSON.stringify({name:document.getElementById('campName').value,channel:document.getElementById('campChannel').value,segment:document.getElementById('campSegment').value,message_template:document.getElementById('campMsg').value})});window.eGo('Campaigns')};
  window.launchCampaign=async id=>{await api('/crm-plus/campaigns/'+id+'/launch',{method:'POST'});window.eGo('Campaigns')};

  async function aiPlusPage(){
    shell(`<div class="aiHero"><div><span class="eyebrow">AI+ ADVANCED SUITE</span><h2>The newer AI layer: predictive, conversational and revenue-protecting tools.</h2><p>No-show prediction, an AI treatment-sequence recommender, message/review sentiment analysis, a WhatsApp/website virtual receptionist and perio risk scoring — on top of the existing AI Clinical Copilot.</p></div></div>
    <div class="threeCol">
      <div class="panel"><div class="panelHead"><h3>No-show risk</h3></div><input id="nsPast" type="number" placeholder="Past no-shows"><input id="nsTotal" type="number" placeholder="Total past appointments"><input id="nsLead" type="number" placeholder="Lead time (days)"><label class="checkline"><input id="nsNew" type="checkbox"> New patient</label><button class="primary" onclick="window.aiNoShow()">Predict</button><pre id="nsOut"></pre></div>
      <div class="panel"><div class="panelHead"><h3>Treatment recommender</h3></div><textarea id="trFindings" placeholder="One finding per line, e.g. caries, periapical radiolucency"></textarea><button class="primary" onclick="window.aiTreatmentRec()">Suggest plan</button><pre id="trOut"></pre></div>
      <div class="panel"><div class="panelHead"><h3>Sentiment analysis</h3></div><textarea id="senText" placeholder="Paste a review or patient message"></textarea><button class="primary" onclick="window.aiSentiment()">Analyze</button><pre id="senOut"></pre></div>
    </div>
    <div class="threeCol">
      <div class="panel"><div class="panelHead"><h3>Virtual receptionist</h3></div><textarea id="vrMsg" placeholder="Incoming WhatsApp/website message"></textarea><button class="primary" onclick="window.aiReceptionist()">Draft reply</button><pre id="vrOut"></pre></div>
      <div class="panel"><div class="panelHead"><h3>Perio risk score</h3></div><input id="prAge" type="number" placeholder="Age"><input id="prPocket" type="number" step="0.1" placeholder="Avg pocket depth (mm)"><input id="prBleed" type="number" placeholder="Bleeding on probing %"><label class="checkline"><input id="prSmoker" type="checkbox"> Smoker</label><label class="checkline"><input id="prDiabetic" type="checkbox"> Diabetic</label><button class="primary" onclick="window.aiPerioRisk()">Score</button><pre id="prOut"></pre></div>
      <div class="panel"><div class="panelHead"><h3>Insurance claim assist</h3></div><input id="icProc" placeholder="Procedure"><input id="icAmt" type="number" placeholder="Amount"><button class="primary" onclick="window.aiClaimAssist()">Check readiness</button><pre id="icOut"></pre></div>
    </div>`, 'Predictive and conversational AI features that extend the clinical copilot');
  }
  window.aiNoShow=async()=>{const r=await api('/ai-plus/no-show-risk',{method:'POST',body:JSON.stringify({past_no_shows:Number(document.getElementById('nsPast').value||0),total_past_appointments:Number(document.getElementById('nsTotal').value||1),lead_time_days:Number(document.getElementById('nsLead').value||1),is_new_patient:document.getElementById('nsNew').checked})});document.getElementById('nsOut').textContent=JSON.stringify(r,null,2)};
  window.aiTreatmentRec=async()=>{const r=await api('/ai-plus/treatment-recommender',{method:'POST',body:JSON.stringify({findings:document.getElementById('trFindings').value.split('\n').filter(Boolean)})});document.getElementById('trOut').textContent=JSON.stringify(r,null,2)};
  window.aiSentiment=async()=>{const r=await api('/ai-plus/sentiment',{method:'POST',body:JSON.stringify({text:document.getElementById('senText').value})});document.getElementById('senOut').textContent=JSON.stringify(r,null,2)};
  window.aiReceptionist=async()=>{const r=await api('/ai-plus/virtual-receptionist',{method:'POST',body:JSON.stringify({message:document.getElementById('vrMsg').value})});document.getElementById('vrOut').textContent=JSON.stringify(r,null,2)};
  window.aiPerioRisk=async()=>{const r=await api('/ai-plus/perio-risk-score',{method:'POST',body:JSON.stringify({age:Number(document.getElementById('prAge').value||30),avg_pocket_depth_mm:Number(document.getElementById('prPocket').value||2.5),bleeding_on_probing_pct:Number(document.getElementById('prBleed').value||10),smoker:document.getElementById('prSmoker').checked,diabetic:document.getElementById('prDiabetic').checked})});document.getElementById('prOut').textContent=JSON.stringify(r,null,2)};
  window.aiClaimAssist=async()=>{const r=await api('/ai-plus/insurance-claim-assist',{method:'POST',body:JSON.stringify({procedure:document.getElementById('icProc').value,amount:Number(document.getElementById('icAmt').value||0)})});document.getElementById('icOut').textContent=JSON.stringify(r,null,2)};

  async function legacy(name){
    shell('<div class="loadingCard">Loading legacy module…</div>','Existing clinical module retained from the original build');
    try{active=name;await legacyLoad(name)}catch(e){document.getElementById('enterpriseContent').innerHTML=`<div class="panel error"><b>${safe(e.message)}</b></div>`}
  }
  window.eGo=async x=>{
    active=x;
    if(x==='Executive Dashboard')return dashboard();
    if(x==='Patient 360')return patient360();
    if(x==='Enquiries & Leads')return crmPage();
    if(['Suppliers & Partners','Follow-ups & Recalls','Complaints & Escalations'].includes(x))return operations(x);
    if(x==='MIS & Dashboards')return mis();
    if(x==='AI Clinical Copilot')return aiPage();
    if(x==='AI+ Advanced Suite')return aiPlusPage();
    if(x==='Dental Imaging')return imagingPage();
    if(x==='Growth & Loyalty')return growthPage();
    if(x==='Reviews & Reputation')return reviewsPage();
    if(x==='Campaigns')return campaignsPage();
    if(x==='Treatment & Care')return legacy('Treatment Plans');
    if(legacyModules.includes(x))return legacy(x);
  };
  window.eLogout=()=>{localStorage.removeItem('dental_token');localStorage.removeItem('dental_user');location.reload()};
  window.eRender=()=>window.eGo('Executive Dashboard');
  if(localStorage.getItem('dental_token')&&getUser()) window.eRender();
})();
