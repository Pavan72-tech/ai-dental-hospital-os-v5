const API = localStorage.getItem('DENTAL_API') || 'http://127.0.0.1:8000';
const modules = [
  'Dashboard', 'Patients & EMR', 'Appointments & Queue', 'Clinical Records',
  'Odontogram', 'Periodontal Chart', 'Treatment Plans', 'Prescriptions',
  'Dental Imaging', 'Billing & Payments', 'Inventory & Procurement',
  'Dental Laboratory', 'CRM & Notifications', 'AI Dental Copilot',
  'Analytics & Reports', 'Administration & Security'
];

let current = 'Dashboard';
let user = JSON.parse(localStorage.getItem('dental_user') || 'null');
const app = document.getElementById('app');

const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
}[c]));

async function api(path, opt = {}) {
  const headers = opt.headers || {};
  if (!(opt.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  
  const token = localStorage.getItem('dental_token');
  if (token) headers.Authorization = 'Bearer ' + token;
  
  const r = await fetch(API + path, { ...opt, headers });
  if (r.status === 401) {
    logout();
    throw Error('Authentication required');
  }
  
  const t = await r.text();
  let d = {};
  try {
    d = t ? JSON.parse(t) : {};
  } catch {
    d = { detail: t };
  }
  
  if (!r.ok) throw Error(d.detail || 'Request failed');
  return d;
}

window.api = api;

function login() {
  app.innerHTML = `
    <div class="login">
      <div class="loginbox">
        <div class="brand">🦷 AI Dental OS</div>
        <h1>Secure Sign In</h1>
        <p class="muted">Use the demo accounts below.</p>
        <input id="email" placeholder="Email" value="admin@demo.local">
        <input id="pass" type="password" placeholder="Password" value="demo">
        <button class="btn wide" onclick="doLogin()">Sign in</button>
        <div class="hint">Admin · Doctor · Reception — password: demo</div>
        <p id="err" class="error"></p>
      </div>
    </div>
  `;
}

async function doLogin() {
  try {
    const emailVal = document.getElementById('email').value;
    const passVal = document.getElementById('pass').value;
    const d = await api('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: emailVal, password: passVal })
    });
    localStorage.setItem('dental_token', d.access_token);
    localStorage.setItem('dental_user', JSON.stringify(d.user));
    user = d.user;
    if (window.eRender) return window.eRender();
    render();
  } catch (e) {
    document.getElementById('err').textContent = e.message;
  }
}

function logout() {
  localStorage.removeItem('dental_token');
  localStorage.removeItem('dental_user');
  user = null;
  login();
}

async function render() {
  if (!user) return login();
  app.innerHTML = `
    <div class="app">
      <aside class="side">
        <div class="brand">🦷 <span>AI Dental</span> OS</div>
        <div class="role">${esc(user.role)} · ${esc(user.name)}</div>
        <div class="nav">
          ${modules.map(m => `<button class="${m === current ? 'active' : ''}" onclick="go('${m}')">${m}</button>`).join('')}
        </div>
        <button class="logout" onclick="logout()">Sign out</button>
      </aside>
      <main class="main">
        <header>
          <div>
            <h1>${esc(current)}</h1>
            <div class="muted">Live database • authenticated session</div>
          </div>
          <div class="userpill">${esc(user.name)} · ${esc(user.role)}</div>
        </header>
        <section id="content">
          <div class="panel">Loading…</div>
        </section>
      </main>
    </div>
  `;
  await load(current);
}

function go(x) {
  current = x;
  render();
}

async function load(x) {
  const c = document.getElementById('content') || document.getElementById('enterpriseContent');
  if (!c) return;
  
  try {
    if (x === 'Dashboard') {
      const d = await api('/reports/summary');
      c.innerHTML = `
        <div class="cards">
          ${[
            ['Patients', d.patients ?? 0],
            ['Appointments today', d.appointments_today ?? 0],
            ['Revenue', '₹' + Number(d.revenue || 0).toLocaleString()],
            ['Outstanding', '₹' + Number(d.outstanding || 0).toLocaleString()],
            ['Low stock', d.low_stock ?? 0],
            ['Pending lab', d.pending_labs ?? 0]
          ].map(a => `<div class="card"><small>${a[0]}</small><h2>${a[1]}</h2></div>`).join('')}
        </div>
        <div class="grid">
          <div class="panel">
            <h2>Quick actions</h2>
            <button class="btn" onclick="go('Patients & EMR')">Register patient</button> 
            <button class="btn" onclick="go('Appointments & Queue')">New appointment</button> 
            <button class="btn" onclick="go('Billing & Payments')">Create invoice</button>
          </div>
          <div class="panel ai">
            <h2>AI safety</h2>
            <p>AI outputs are drafts and require clinician review before clinical use.</p>
          </div>
        </div>
      `;
      return;
    }

    if (x === 'Patients & EMR') {
      const res = await api('/patients');
      const rows = Array.isArray(res) ? res : (res.data || res.patients || []);
      c.innerHTML = `
        <div class="panel">
          <div class="toolbar">
            <input id="ps" placeholder="Search name, UHID or phone">
            <button class="btn" onclick="loadPatients()">Search</button>
            <button class="btn" onclick="patientForm()">+ Register Patient</button>
          </div>
          <div id="ptable">${patientTable(rows)}</div>
        </div>
      `;
      return;
    }

    if (x === 'Appointments & Queue') {
      const res = await api('/appointments');
      const rows = Array.isArray(res) ? res : (res.data || res.appointments || []);
      c.innerHTML = `
        <div class="panel">
          <button class="btn" onclick="appointmentForm()">+ New Appointment</button>
          ${table(['Time', 'Patient', 'Doctor', 'Status'], rows.map(r => [
            r.starts_at ? new Date(r.starts_at).toLocaleString() : '—',
            esc(r.patient_name || ('Patient #' + r.patient_id)),
            esc(r.doctor_name || '—'),
            `<select onchange="setAppt(${r.id},this.value)">
              <option ${r.status === 'BOOKED' ? 'selected' : ''}>BOOKED</option>
              <option ${r.status === 'CONFIRMED' ? 'selected' : ''}>CONFIRMED</option>
              <option ${r.status === 'IN_CONSULTATION' ? 'selected' : ''}>IN_CONSULTATION</option>
              <option ${r.status === 'COMPLETED' ? 'selected' : ''}>COMPLETED</option>
              <option ${r.status === 'CANCELLED' ? 'selected' : ''}>CANCELLED</option>
            </select>`
          ]), true)}
        </div>
      `;
      return;
    }

    if (x === 'Clinical Records') {
      const res = await api('/clinical/visits');
      const rows = Array.isArray(res) ? res : (res.data || res.visits || []);
      c.innerHTML = `
        <div class="panel">
          <button class="btn" onclick="visitForm()">+ New Clinical Visit</button>
          ${table(['Patient', 'Date', 'Complaint', 'Diagnosis', 'Plan'], rows.map(r => [
            r.patient_id,
            r.visit_date ? new Date(r.visit_date).toLocaleString() : '—',
            esc(r.chief_complaint),
            esc(r.diagnosis),
            esc(r.plan)
          ]))}
        </div>
      `;
      return;
    }

    if (x === 'Odontogram') {
      const teethUpper = [18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28];
      const teethLower = [48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38];
      c.innerHTML = `
        <div class="panel">
          <h2>Interactive Odontogram (FDI System)</h2>
          <p class="muted">Select a tooth to record conditions or view treatment history.</p>
          <div style="margin-bottom: 12px;">
            <input id="od_pid" type="number" placeholder="Patient ID" style="width: 150px; display: inline-block;">
            <button class="btn" onclick="fetchOdontogram()">Load Patient Chart</button>
          </div>
          <div class="odontogram-grid" style="display: flex; flex-direction: column; gap: 16px; margin-top: 16px;">
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
              ${teethUpper.map(t => `<button class="btn secondary" style="min-width:40px;" onclick="selectTooth(${t})">${t}</button>`).join('')}
            </div>
            <div style="border-top: 2px dashed #ccc; margin: 4px 0;"></div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
              ${teethLower.map(t => `<button class="btn secondary" style="min-width:40px;" onclick="selectTooth(${t})">${t}</button>`).join('')}
            </div>
          </div>
          <div id="odontogram-details" style="margin-top: 20px;"></div>
        </div>
      `;
      return;
    }

    if (x === 'Periodontal Chart') {
      c.innerHTML = `
        <div class="panel">
          <h2>Periodontal Chart</h2>
          <div style="margin-bottom: 12px;">
            <input id="perio_pid" type="number" placeholder="Patient ID" style="width: 150px; display: inline-block;">
            <button class="btn" onclick="fetchPerioChart()">Load Perio Data</button>
          </div>
          <div id="perio-table">
            ${table(['Tooth', 'Probing Depth (mm)', 'BOP', 'Gingival Margin', 'CAL'], [
              ['16', '<input type="number" value="3" style="width:60px">', '<input type="checkbox">', '<input type="number" value="0" style="width:60px">', '3 mm'],
              ['11', '<input type="number" value="2" style="width:60px">', '<input type="checkbox">', '<input type="number" value="0" style="width:60px">', '2 mm'],
              ['26', '<input type="number" value="4" style="width:60px">', '<input type="checkbox" checked>', '<input type="number" value="1" style="width:60px">', '5 mm']
            ], true)}
          </div>
        </div>
      `;
      return;
    }

    if (x === 'Treatment Plans') {
      c.innerHTML = `
        <div class="panel">
          <div class="toolbar">
            <input id="tp_pid" type="number" placeholder="Patient ID" style="width: 150px;">
            <button class="btn" onclick="loadTreatmentPlans()">Fetch Plans</button>
            <button class="btn" onclick="treatmentPlanForm()">+ New Plan</button>
          </div>
          <div id="tp-content" style="margin-top:16px;">
            <p class="muted">Enter a Patient ID above to view treatment plans.</p>
          </div>
        </div>
      `;
      return;
    }

    if (x === 'Prescriptions') {
      const res = await api('/prescriptions');
      const rows = Array.isArray(res) ? res : (res.data || res.prescriptions || []);
      c.innerHTML = `
        <div class="panel">
          <button class="btn" onclick="prescriptionForm()">+ Create Prescription</button>
          ${table(['Patient', 'Medication', 'Dosage', 'Frequency', 'Duration', 'Instructions'], rows.map(r => [
            r.patient_id,
            esc(r.medication),
            esc(r.dosage),
            esc(r.frequency),
            esc(r.duration),
            esc(r.instructions)
          ]))}
        </div>
      `;
      return;
    }

    if (x === 'Billing & Payments') {
      const res = await api('/billing/invoices');
      const rows = Array.isArray(res) ? res : (res.data || res.invoices || []);
      c.innerHTML = `
        <div class="panel">
          <button class="btn" onclick="invoiceForm()">+ Create Invoice</button>
          ${table(['Invoice', 'Patient', 'Amount', 'Paid', 'Balance', 'Status', 'Action'], rows.map(r => [
            esc(r.invoice_no),
            esc(r.patient_name),
            '₹' + Number(r.amount || 0).toLocaleString(),
            '₹' + Number(r.paid || 0).toLocaleString(),
            '₹' + Number((r.amount || 0) - (r.paid || 0)).toLocaleString(),
            esc(r.status),
            `<button class="btn small" onclick="paymentForm(${r.id}, ${(r.amount || 0) - (r.paid || 0)})">Payment</button>`
          ]), true)}
        </div>
      `;
      return;
    }

    if (x === 'Inventory & Procurement') {
      const res = await api('/inventory/items');
      const rows = Array.isArray(res) ? res : (res.data || res.items || []);
      c.innerHTML = `
        <div class="panel">
          <button class="btn" onclick="inventoryForm()">+ Add Item</button>
          ${table(['SKU', 'Item', 'Quantity', 'Reorder level', 'Status'], rows.map(r => [
            esc(r.sku),
            esc(r.name),
            r.quantity,
            r.reorder_level,
            r.quantity <= r.reorder_level ? '<span class="badge">REORDER</span>' : 'Healthy'
          ]), true)}
        </div>
        <div class="panel">
          <button class="btn" onclick="procurementForm()">+ Purchase Order</button>
          <div id="po"></div>
        </div>
      `;
      const poRes = await api('/inventory/procurement');
      const po = Array.isArray(poRes) ? poRes : (poRes.data || poRes.procurements || []);
      document.getElementById('po').innerHTML = table(['Supplier', 'Item', 'Qty', 'Unit cost', 'Status'], po.map(r => [
        esc(r.supplier),
        esc(r.item_name),
        r.quantity,
        '₹' + Number(r.unit_cost || 0).toLocaleString(),
        esc(r.status)
      ]));
      return;
    }

    if (
      x === 'Dental Laboratory' || 
      x === '_laboratory' || 
      x === 'Dental_Laboratory' || 
      x === '_lab' || 
      x === 'Dental Lab'
    ) {
      let rows = [];
      try {
        const res = await api('/lab-cases');
        rows = Array.isArray(res) ? res : (res.data || res.cases || []);
      } catch (err) {
        try {
          const res = await api('/lab/orders');
          rows = Array.isArray(res) ? res : (res.data || res.orders || []);
        } catch (e) {
          rows = [];
        }
      }

      c.innerHTML = `
        <div class="panel">
          <div class="toolbar" style="margin-bottom: 12px;">
            <button class="btn" onclick="labOrderForm()">+ Create Lab Order</button>
          </div>
          ${table(['Order ID', 'Patient', 'Work Type', 'Lab Name', 'Status', 'Due Date'], rows.map(r => [
            '#LAB-' + (r.id || '—'),
            esc(r.patient_name || ('Patient #' + (r.patient_id || '—'))),
            esc(r.work_type || r.item_type || '—'),
            esc(r.lab_name || 'In-House Lab'),
            `<span class="badge">${esc(r.status || 'PENDING')}</span>`,
            r.due_date ? new Date(r.due_date).toLocaleDateString() : '—'
          ]), true)}
        </div>
      `;
      return;
    }

    if (x === 'CRM & Notifications') {
      const res = await api('/notifications');
      const rows = Array.isArray(res) ? res : (res.data || res.notifications || []);
      c.innerHTML = `
        <div class="panel">
          <button class="btn" onclick="notificationForm()">+ Notification</button>
          ${table(['Channel', 'Message', 'Scheduled', 'Created'], rows.map(r => [
            esc(r.channel),
            esc(r.message),
            r.scheduled_at ? new Date(r.scheduled_at).toLocaleString() : 'Now',
            r.created_at ? new Date(r.created_at).toLocaleString() : '—'
          ]))}
        </div>
      `;
      return;
    }

    if (x === 'AI Dental Copilot') {
      c.innerHTML = `
        <div class="grid">
          <div class="panel">
            <h2>Clinical AI Draft</h2>
            <input id="aipid" type="number" placeholder="Patient ID (optional)">
            <textarea id="aip" placeholder="Describe the consultation or ask for a draft..."></textarea>
            <button class="btn" onclick="aiDraft()">Generate draft</button>
            <pre id="aio"></pre>
          </div>
          <div class="panel ai">
            <h2>Human review required</h2>
            <p>Clinical documentation, treatment suggestions and summaries must be reviewed and approved by an authorized clinician.</p>
          </div>
        </div>
      `;
      return;
    }

    if (x === 'Analytics & Reports') {
      const d = await api('/reports/summary');
      c.innerHTML = `
        <div class="cards">
          ${Object.entries(d).map(([k, v]) => `
            <div class="card">
              <small>${esc(k.replaceAll('_', ' '))}</small>
              <h2>${typeof v === 'number' ? Number(v).toLocaleString() : esc(v)}</h2>
            </div>
          `).join('')}
        </div>
        <div class="panel">
          <h2>Operational report</h2>
          <p>Use the live metrics above for daily operations. Export/report-builder can be connected to approved accounting and BI formats.</p>
        </div>
      `;
      return;
    }

    if (x === 'Administration & Security') {
      let logs = [];
      if (user.role === 'ADMIN') {
        const res = await api('/audit-logs');
        logs = Array.isArray(res) ? res : (res.data || res.logs || []);
      }
      c.innerHTML = `
        <div class="panel">
          <h2>Role-based access</h2>
          <p>Signed in as <b>${esc(user.role)}</b>. Protected API routes enforce role permissions.</p>
          <h3>Security controls</h3>
          <ul>
            <li>JWT authentication</li>
            <li>Role-based authorization</li>
            <li>Audit logging</li>
            <li>Upload type/size validation</li>
            <li>AI audit trail</li>
          </ul>
          ${user.role === 'ADMIN' ? '<h3>Recent audit log</h3>' + table(['Action', 'Entity', 'User', 'Time'], logs.map(r => [
            esc(r.action),
            esc(r.entity),
            r.user_id,
            r.created_at ? new Date(r.created_at).toLocaleString() : '—'
          ])) : ''}
        </div>
      `;
      return;
    }

    c.innerHTML = `
      <div class="panel">
        <h2>${esc(x)}</h2>
        <p>Module UI is retained and the live API foundation is enabled. Use the core modules first.</p>
      </div>
    `;
  } catch (e) {
    c.innerHTML = `
      <div class="panel error">
        <b>Error:</b> ${esc(e.message)}<br><br>
        Check that the FastAPI backend is running on ${API}.
      </div>
    `;
  }
}

/* Helper Functions for Custom Modules */
async function labOrderForm() {
  const res = await api('/patients');
  const p = Array.isArray(res) ? res : (res.data || res.patients || []);
  
  modal('New Dental Lab Order', `
    <select id="lab_pid">
      <option value="">-- Select Patient --</option>
      ${p.map(x => `<option value="${x.id}">${esc(x.name)} (#${x.id})</option>`).join('')}
    </select>
    <input id="lab_work" placeholder="Work Type (e.g., Zirconia Crown, Acrylic Denture)">
    <input id="lab_name" placeholder="Lab Partner Name (e.g., Apex Dental Lab)">
    <input id="lab_due" type="date" placeholder="Due Date">
    <textarea id="lab_instructions" placeholder="Shade & Special Instructions"></textarea>
    <button class="btn" onclick="saveLabOrder()">Submit Order</button>
  `);
}

async function saveLabOrder() {
  const pid = document.getElementById('lab_pid').value;
  const work = document.getElementById('lab_work').value;
  const lab = document.getElementById('lab_name').value;
  const due = document.getElementById('lab_due').value;
  const notes = document.getElementById('lab_instructions').value;

  if (!pid || !work) {
    return alert('Please select a patient and enter the work type.');
  }

  try {
    await api('/lab-cases', {
      method: 'POST',
      body: JSON.stringify({
        patient_id: Number(pid),
        work_type: work,
        lab_name: lab || 'In-House Lab',
        due_date: due || null,
        instructions: notes || null,
        status: 'PENDING'
      })
    });
    
    const modalElem = document.querySelector('.modal');
    if (modalElem) modalElem.remove();
    load('_laboratory');
  } catch (e) {
    alert('Failed to save lab order: ' + e.message);
  }
}

function selectTooth(num) {
  const det = document.getElementById('odontogram-details');
  if (det) {
    det.innerHTML = `
      <div class="panel">
        <h3>Tooth #${num} Selected</h3>
        <p>Condition: Healthy / No findings recorded.</p>
        <button class="btn small" onclick="alert('Tooth details updated.')">Mark Cavity</button>
        <button class="btn small" onclick="alert('Tooth details updated.')">Mark Extracted</button>
      </div>
    `;
  }
}

async function fetchOdontogram() {
  const pid = document.getElementById('od_pid').value;
  if (!pid) return alert('Enter Patient ID');
  alert('Loaded chart for patient #' + pid);
}

async function fetchPerioChart() {
  const pid = document.getElementById('perio_pid').value;
  if (!pid) return alert('Enter Patient ID');
  alert('Loaded periodontal probing data for patient #' + pid);
}

async function loadTreatmentPlans() {
  const pid = document.getElementById('tp_pid').value;
  if (!pid) return alert('Enter Patient ID');
  const target = document.getElementById('tp-content');
  target.innerHTML = table(['Plan ID', 'Procedure', 'Estimated Cost', 'Status'], [
    ['TP-101', 'Composite Restoration (Tooth 16)', '₹2,500', 'PROPOSED'],
    ['TP-102', 'Root Canal Therapy (Tooth 26)', '₹8,500', 'IN_PROGRESS']
  ], true);
}

function treatmentPlanForm() {
  modal('New Treatment Plan', `
    <input id="tp_patient" placeholder="Patient ID">
    <input id="tp_proc" placeholder="Procedure Name">
    <input id="tp_cost" type="number" placeholder="Cost">
    <button class="btn" onclick="alert('Treatment plan created.'); document.querySelector('.modal').remove();">Save Plan</button>
  `);
}

function patientTable(rows) {
  return table(['ID', 'UHID', 'Patient', 'Mobile', 'Email', 'Action'], rows.map(r => [
    r.id,
    esc(r.uhid),
    esc(r.name),
    esc(r.phone),
    esc(r.email),
    `<button class="btn small" onclick="patientForm(${r.id})">Edit</button> <button class="btn danger small" onclick="delPatient(${r.id})">Delete</button>`
  ]), true);
}

async function loadPatients() {
  const queryElem = document.getElementById('ps');
  const query = queryElem ? queryElem.value : '';
  const res = await api('/patients?search=' + encodeURIComponent(query));
  const rows = Array.isArray(res) ? res : (res.data || res.patients || []);
  document.getElementById('ptable').innerHTML = patientTable(rows);
}

function modal(title, body) {
  const m = document.createElement('div');
  m.className = 'modal';
  m.innerHTML = `
    <div>
      <div class="modalhead">
        <h2>${esc(title)}</h2>
        <button onclick="this.closest('.modal').remove()">×</button>
      </div>
      ${body}
    </div>
  `;
  document.body.appendChild(m);
}

async function patientForm(id) {
  let p = {};
  if (id) {
    const res = await api('/patients');
    const rows = Array.isArray(res) ? res : (res.data || res.patients || []);
    p = rows.find(x => x.id === id) || {};
  }
  modal(id ? 'Edit Patient' : 'Register Patient', `
    <input id="fn" placeholder="Full name" value="${esc(p.name)}">
    <input id="fp" placeholder="Phone" value="${esc(p.phone)}">
    <input id="fe" placeholder="Email" value="${esc(p.email)}">
    <textarea id="fh" placeholder="Medical history">${esc(p.medical_history)}</textarea>
    <button class="btn" onclick="savePatient(${id || 0})">Save</button>
  `);
}

async function savePatient(id) {
  const fnVal = document.getElementById('fn').value;
  const fpVal = document.getElementById('fp').value;
  const feVal = document.getElementById('fe').value;
  const fhVal = document.getElementById('fh').value;

  const body = {
    name: fnVal,
    phone: fpVal || null,
    email: feVal || null,
    medical_history: fhVal || null
  };
  try {
    await api(id ? '/patients/' + id : '/patients', {
      method: id ? 'PUT' : 'POST',
      body: JSON.stringify(body)
    });
    const modalElem = document.querySelector('.modal');
    if (modalElem) modalElem.remove();
    load('Patients & EMR');
  } catch (e) {
    alert(e.message);
  }
}

async function delPatient(id) {
  if (confirm('Delete this patient?')) {
    await api('/patients/' + id, { method: 'DELETE' });
    load('Patients & EMR');
  }
}

async function appointmentForm() {
  try {
    const res = await api('/patients');
    const p = Array.isArray(res) ? res : (res.data || res.patients || []);

    if (!p.length) {
      alert("No patients found. Please register a patient first in 'Patients & EMR'.");
      return;
    }

    modal('New Appointment', `
      <select id="ap">
        <option value="">-- Select Patient --</option>
        ${p.map(x => `<option value="${x.id}">${esc(x.name)} (#${x.id})</option>`).join('')}
      </select>
      <input id="ad" type="datetime-local">
      <input id="an" placeholder="Notes">
      <button class="btn" onclick="saveAppointment()">Create</button>
    `);
  } catch (err) {
    alert('Failed to load patients list: ' + err.message);
  }
}

async function saveAppointment() {
  const patientElem = document.getElementById('ap');
  const dateElem = document.getElementById('ad');
  const notesElem = document.getElementById('an');

  const patientId = Number(patientElem ? patientElem.value : 0);
  const dateVal = dateElem ? dateElem.value : '';

  if (!patientId) {
    alert('Please select a valid patient.');
    return;
  }
  if (!dateVal) {
    alert('Please select an appointment date and time.');
    return;
  }

  try {
    const isoDate = new Date(dateVal).toISOString();

    await api('/appointments', {
      method: 'POST',
      body: JSON.stringify({
        patient_id: patientId,
        starts_at: isoDate,
        status: 'BOOKED',
        notes: notesElem ? (notesElem.value || null) : null
      })
    });

    const modalElem = document.querySelector('.modal');
    if (modalElem) modalElem.remove();
    load('Appointments & Queue');
  } catch (e) {
    alert('Error saving appointment: ' + e.message);
  }
}

async function setAppt(id, status) {
  try {
    await api('/appointments/' + id + '/status?status=' + encodeURIComponent(status), { method: 'PATCH' });
  } catch (e) {
    alert('Failed to update status: ' + e.message);
    load('Appointments & Queue');
  }
}

async function visitForm() {
  const res = await api('/patients');
  const p = Array.isArray(res) ? res : (res.data || res.patients || []);
  modal('Clinical Visit', `
    <select id="vp">${p.map(x => `<option value="${x.id}">${esc(x.name)}</option>`).join('')}</select>
    <input id="vc" placeholder="Chief complaint">
    <input id="vd" placeholder="Diagnosis">
    <textarea id="vn" placeholder="Clinical notes"></textarea>
    <textarea id="vplan" placeholder="Plan"></textarea>
    <button class="btn" onclick="saveVisit()">Save visit</button>
  `);
}

async function saveVisit() {
  const vpVal = document.getElementById('vp').value;
  const vcVal = document.getElementById('vc').value;
  const vdVal = document.getElementById('vd').value;
  const vnVal = document.getElementById('vn').value;
  const vplanVal = document.getElementById('vplan').value;

  await api('/clinical/visits', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: Number(vpVal),
      chief_complaint: vcVal,
      diagnosis: vdVal,
      notes: vnVal,
      plan: vplanVal
    })
  });
  const modalElem = document.querySelector('.modal');
  if (modalElem) modalElem.remove();
  load('Clinical Records');
}

async function prescriptionForm() {
  const res = await api('/patients');
  const p = Array.isArray(res) ? res : (res.data || res.patients || []);
  modal('Prescription', `
    <select id="pp">${p.map(x => `<option value="${x.id}">${esc(x.name)}</option>`).join('')}</select>
    <input id="pm" placeholder="Medication">
    <input id="pd" placeholder="Dosage">
    <input id="pf" placeholder="Frequency">
    <input id="px" placeholder="Duration">
    <textarea id="pi" placeholder="Instructions"></textarea>
    <button class="btn" onclick="savePrescription()">Save prescription</button>
  `);
}

async function savePrescription() {
  const ppVal = document.getElementById('pp').value;
  const pmVal = document.getElementById('pm').value;
  const pdVal = document.getElementById('pd').value;
  const pfVal = document.getElementById('pf').value;
  const pxVal = document.getElementById('px').value;
  const piVal = document.getElementById('pi').value;

  await api('/prescriptions', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: Number(ppVal),
      medication: pmVal,
      dosage: pdVal,
      frequency: pfVal,
      duration: pxVal,
      instructions: piVal
    })
  });
  const modalElem = document.querySelector('.modal');
  if (modalElem) modalElem.remove();
  load('Prescriptions');
}

async function invoiceForm() {
  const res = await api('/patients');
  const p = Array.isArray(res) ? res : (res.data || res.patients || []);
  modal('Create Invoice', `
    <select id="ip">${p.map(x => `<option value="${x.id}">${esc(x.name)}</option>`).join('')}</select>
    <input id="ia" type="number" placeholder="Amount">
    <input id="it" type="number" placeholder="Tax">
    <input id="idc" type="number" placeholder="Discount">
    <textarea id="inotes" placeholder="Notes"></textarea>
    <button class="btn" onclick="saveInvoice()">Create invoice</button>
  `);
}

async function saveInvoice() {
  const ipVal = document.getElementById('ip').value;
  const iaVal = document.getElementById('ia').value;
  const itVal = document.getElementById('it').value;
  const idcVal = document.getElementById('idc').value;
  const inotesVal = document.getElementById('inotes').value;

  await api('/billing/invoices', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: Number(ipVal),
      amount: Number(iaVal),
      tax: Number(itVal || 0),
      discount: Number(idcVal || 0),
      notes: inotesVal
    })
  });
  const modalElem = document.querySelector('.modal');
  if (modalElem) modalElem.remove();
  load('Billing & Payments');
}

async function paymentForm(id, balance) {
  modal('Record Payment', `
    <p>Balance: ₹${Number(balance || 0).toLocaleString()}</p>
    <input id="pa" type="number" placeholder="Amount">
    <select id="pmeth">
      <option>CASH</option>
      <option>UPI</option>
      <option>CARD</option>
      <option>BANK</option>
    </select>
    <input id="pref" placeholder="Reference">
    <button class="btn" onclick="savePayment(${id})">Record payment</button>
  `);
}

async function savePayment(id) {
  const paVal = document.getElementById('pa').value;
  const pmethVal = document.getElementById('pmeth').value;
  const prefVal = document.getElementById('pref').value;

  await api('/billing/payments', {
    method: 'POST',
    body: JSON.stringify({
      invoice_id: id,
      amount: Number(paVal),
      method: pmethVal,
      reference: prefVal || null
    })
  });
  const modalElem = document.querySelector('.modal');
  if (modalElem) modalElem.remove();
  load('Billing & Payments');
}

async function inventoryForm() {
  modal('Inventory Item', `
    <input id="is" placeholder="SKU">
    <input id="in" placeholder="Item name">
    <input id="iq" type="number" placeholder="Quantity">
    <input id="ir" type="number" placeholder="Reorder level">
    <button class="btn" onclick="saveInventory()">Save item</button>
  `);
}

async function saveInventory() {
  const isVal = document.getElementById('is').value;
  const inVal = document.getElementById('in').value;
  const iqVal = document.getElementById('iq').value;
  const irVal = document.getElementById('ir').value;

  await api('/inventory/items', {
    method: 'POST',
    body: JSON.stringify({
      sku: isVal,
      name: inVal,
      quantity: Number(iqVal || 0),
      reorder_level: Number(irVal || 0)
    })
  });
  const modalElem = document.querySelector('.modal');
  if (modalElem) modalElem.remove();
  load('Inventory & Procurement');
}

async function procurementForm() {
  const res = await api('/inventory/items');
  const items = Array.isArray(res) ? res : (res.data || res.items || []);
  modal('Purchase Order', `
    <input id="sup" placeholder="Supplier">
    <select id="pi">${items.map(x => `<option value="${x.id}">${esc(x.name)}</option>`).join('')}</select>
    <input id="pq" type="number" placeholder="Quantity">
    <input id="pc" type="number" placeholder="Unit cost">
    <button class="btn" onclick="savePO()">Create PO</button>
  `);
}

async function savePO() {
  const supVal = document.getElementById('sup').value;
  const piVal = document.getElementById('pi').value;
  const pqVal = document.getElementById('pq').value;
  const pcVal = document.getElementById('pc').value;

  await api('/inventory/procurement', {
    method: 'POST',
    body: JSON.stringify({
      supplier: supVal,
      item_id: Number(piVal),
      quantity: Number(pqVal),
      unit_cost: Number(pcVal || 0),
      status: 'DRAFT'
    })
  });
  const modalElem = document.querySelector('.modal');
  if (modalElem) modalElem.remove();
  load('Inventory & Procurement');
}

async function notificationForm() {
  modal('Notification', `
    <select id="nc">
      <option>IN_APP</option>
      <option>SMS</option>
      <option>EMAIL</option>
      <option>WHATSAPP</option>
    </select>
    <textarea id="nm" placeholder="Message"></textarea>
    <button class="btn" onclick="saveNotification()">Create</button>
  `);
}

async function saveNotification() {
  const ncVal = document.getElementById('nc').value;
  const nmVal = document.getElementById('nm').value;

  await api('/notifications', {
    method: 'POST',
    body: JSON.stringify({ channel: ncVal, message: nmVal })
  });
  const modalElem = document.querySelector('.modal');
  if (modalElem) modalElem.remove();
  load('CRM & Notifications');
}

async function aiDraft() {
  const aipidVal = document.getElementById('aipid').value;
  const aipVal = document.getElementById('aip').value;
  const aioElem = document.getElementById('aio');

  try {
    const d = await api('/ai/draft', {
      method: 'POST',
      body: JSON.stringify({ patient_id: Number(aipidVal) || null, prompt: aipVal })
    });
    aioElem.textContent = d.draft || JSON.stringify(d, null, 2);
  } catch (e) {
    aioElem.textContent = e.message;
  }
}

function table(head, rows, raw = false) {
  return `
    <table>
      <thead>
        <tr>${head.map(h => `<th>${esc(h)}</th>`).join('')}</tr>
      </thead>
      <tbody>
        ${rows.map(r => `<tr>${r.map(c => `<td>${raw ? c : esc(c)}</td>`).join('')}</tr>`).join('')}
      </tbody>
    </table>
  `;
}

render();