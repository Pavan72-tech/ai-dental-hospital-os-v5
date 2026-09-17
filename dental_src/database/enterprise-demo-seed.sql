-- Optional demo data for CRM / operations. Run after schema + enterprise migration.
INSERT INTO doctors(user_id,specialization,registration_no,phone,chair)
SELECT u.id,'Prosthodontics','DEMO-MCI-001','9000000001','CHAIR-01' FROM users u WHERE u.email='doctor@demo.local'
ON CONFLICT (user_id) DO NOTHING;
INSERT INTO suppliers(name,contact_person,phone,email,gstin,address) VALUES
('DentalCare Supplies','Demo Vendor','9000000101','vendor1@demo.local','27DEMO0001X1Z1','Pune, Maharashtra'),
('OrthoMed Labs','Demo Contact','9000000102','vendor2@demo.local','27DEMO0002X1Z1','Mumbai, Maharashtra') ON CONFLICT DO NOTHING;
INSERT INTO partners(name,type,contact_person,phone,email,commission_percent) VALUES
('Smile Referral Network','Referral','Demo Partner','9000000201','partner@demo.local',5) ON CONFLICT DO NOTHING;
INSERT INTO enquiries(name,phone,email,source,interest,stage,assigned_to,next_followup,notes)
SELECT 'Neha Kulkarni','9000000301','neha@demo.local','Website','Implant Consultation','NEW',u.id,NOW()+INTERVAL '1 day','High intent web enquiry'
FROM users u WHERE u.email='reception@demo.local';
INSERT INTO enquiries(name,phone,email,source,interest,stage,assigned_to,next_followup,notes)
SELECT 'Arjun Deshmukh','9000000302','arjun@demo.local','Referral','Smile Design','CONTACTED',u.id,NOW()+INTERVAL '2 days','Asked for estimate'
FROM users u WHERE u.email='reception@demo.local';
INSERT INTO leads(enquiry_id,name,phone,source,stage,assigned_to,expected_value,next_followup,notes)
SELECT e.id,e.name,e.phone,e.source,'TREATMENT_PROPOSED',u.id,85000,NOW()+INTERVAL '1 day','Proposal sent'
FROM enquiries e CROSS JOIN users u WHERE e.name='Arjun Deshmukh' AND u.email='reception@demo.local';
INSERT INTO followups(patient_id,assigned_to,type,due_at,status,notes)
SELECT p.id,u.id,'Payment Follow-up',NOW()+INTERVAL '4 hours','PENDING','Outstanding balance reminder'
FROM patients p CROSS JOIN users u WHERE p.uhid='DENT-DEMO-0001' AND u.email='reception@demo.local';
INSERT INTO recalls(patient_id,type,due_at,status,notes)
SELECT p.id,'Dental Cleaning',CURRENT_DATE+7,'DUE','Routine 6-month cleaning recall'
FROM patients p WHERE p.uhid='DENT-DEMO-0002';
INSERT INTO complaints(patient_id,category,description,severity,status,assigned_to)
SELECT p.id,'Service','Demo complaint for workflow testing','MEDIUM','OPEN',u.id
FROM patients p CROSS JOIN users u WHERE p.uhid='DENT-DEMO-0001' AND u.email='reception@demo.local';
