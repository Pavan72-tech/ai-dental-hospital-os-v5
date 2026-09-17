INSERT INTO organizations(name) VALUES ('Demo Dental Hospital');
INSERT INTO branches(organization_id,name) VALUES (1,'Main Branch');
INSERT INTO users(branch_id,name,email,role,password_hash) VALUES
(1,'Demo Admin','admin@demo.local','SUPER_ADMIN','DEMO_ONLY'),
(1,'Dr. Sharma','doctor@demo.local','DOCTOR','DEMO_ONLY'),
(1,'Reception Desk','reception@demo.local','RECEPTION','DEMO_ONLY');
INSERT INTO patients(branch_id,uhid,name,phone,medical_history) VALUES
(1,'DENT-DEMO-0001','Rahul Sharma','98XXXXXX12','No recorded drug allergy. RCT initiated on tooth #36.'),
(1,'DENT-DEMO-0002','Priya Patil','97XXXXXX45','Routine follow-up patient.');
INSERT INTO treatment_plans(patient_id,title,amount,status) VALUES (1,'Implant + Zirconia Crown',85000,'PENDING_APPROVAL');
INSERT INTO invoices(patient_id,invoice_no,amount,paid,status) VALUES (1,'INV-DEMO-001',85000,5000,'PARTIALLY_PAID');
INSERT INTO inventory_items(branch_id,sku,name,quantity,reorder_level) VALUES (1,'COMP-001','Composite Resin',18,20),(1,'IMP-A','Implant System A',42,10);
