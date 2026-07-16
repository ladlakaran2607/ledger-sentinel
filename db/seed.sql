-- Seed data for the Ledger Sentinel mock ERP.
-- Dumped from the live Supabase project on 2026-07-15; rerun after `truncate` to rebuild the world.

insert into vendors (id, name, payment_terms) values
    ('VEND-001', 'AgriBean Traders', 'NET-30'),
    ('VEND-002', 'FlexiPack Industries', 'NET-30'),
    ('VEND-003', 'Brennan Mechanical Services', 'NET-15'),
    ('VEND-004', 'Meridian Facility Services', 'NET-15');

insert into gl_accounts (code, name) values
    ('6210', 'Raw Materials'),
    ('6220', 'Packaging Supplies'),
    ('6350', 'Equipment Maintenance'),
    ('6410', 'Facilities and Cleaning');

insert into purchase_orders (id, vendor_id, order_date, status) values
    ('PO-118', 'VEND-001', '2026-07-01', 'open'),
    ('PO-121', 'VEND-002', '2026-07-03', 'open'),
    ('PO-125', 'VEND-003', '2026-06-02', 'open'),
    ('PO-127', 'VEND-002', '2026-07-05', 'open'),
    ('PO-130', 'VEND-001', '2026-07-06', 'open'),
    ('PO-140', 'VEND-001', '2026-07-08', 'open'),
    ('PO-142', 'VEND-001', '2026-07-10', 'open'),
    ('PO-143', 'VEND-001', '2026-07-11', 'open'),
    ('PO-144', 'VEND-001', '2026-07-12', 'open');

insert into po_lines (po_id, line_no, description, quantity, unit_price, gl_code, match_type) values
    ('PO-118', 1, 'Arabica beans grade A, kg', '500', '4.00', '6210', '3-way'),
    ('PO-121', 1, 'Coffee bag film roll', '1000', '0.80', '6220', '3-way'),
    ('PO-125', 1, 'Roastery AC quarterly service', '1', '48200.00', '6350', '2-way'),
    ('PO-127', 1, 'Kraft label sheet', '200', '1.50', '6220', '3-way'),
    ('PO-130', 1, 'Robusta beans grade B, kg', '300', '3.20', '6210', '3-way'),
    ('PO-140', 1, 'Arabica beans grade A, kg', '400', '4.00', '6210', '3-way'),
    ('PO-140', 2, 'Robusta beans grade B, kg', '200', '3.20', '6210', '3-way'),
    ('PO-140', 3, 'Jute sack, 25kg', '50', '1.10', '6220', '3-way'),
    ('PO-142', 1, 'Arabica beans grade A, kg', '300', '4.00', '6210', '3-way'),
    ('PO-143', 1, 'Robusta beans grade B, kg', '320', '3.20', '6210', '3-way'),
    ('PO-144', 1, 'Arabica beans grade A, kg', '250', '4.00', '6210', '3-way');

insert into goods_receipts (id, po_id, received_date) values
    ('GR-501', 'PO-118', '2026-07-08'),
    ('GR-509', 'PO-121', '2026-07-10'),
    ('GR-512', 'PO-127', '2026-07-09'),
    ('GR-515', 'PO-130', '2026-07-11'),
    ('GR-520', 'PO-140', '2026-07-12'),
    ('GR-522', 'PO-142', '2026-07-13'),
    ('GR-523', 'PO-143', '2026-07-14'),
    ('GR-524', 'PO-144', '2026-07-14');

insert into receipt_lines (receipt_id, po_line_no, qty_received) values
    ('GR-501', 1, '500'),
    ('GR-509', 1, '620'),
    ('GR-512', 1, '200'),
    ('GR-515', 1, '300'),
    ('GR-520', 1, '400'),
    ('GR-520', 2, '200'),
    ('GR-520', 3, '50'),
    ('GR-522', 1, '300'),
    ('GR-523', 1, '320'),
    ('GR-524', 1, '250');

insert into invoices (id, invoice_number, vendor_id, po_id, invoice_date, subtotal, tax_rate, tax_amount, total, gl_code, status, paid_date) values
    ('INV-1040', 'BMS-2201', 'VEND-003', 'PO-125', '2026-06-20', '48200.00', '0.00', '0.00', '48200.00', '6350', 'paid', '2026-06-28'),
    ('INV-1051', 'AGB-991', 'VEND-001', 'PO-118', '2026-07-09', '2080.00', '0.08', '166.40', '2246.40', '6210', 'received', null),
    ('INV-1052', 'FPX-3307', 'VEND-002', 'PO-121', '2026-07-10', '800.00', '0.08', '64.00', '864.00', '6220', 'received', null),
    ('INV-1053', 'BMS-2201-A', 'VEND-003', 'PO-125', '2026-07-11', '48200.00', '0.00', '0.00', '48200.00', '6350', 'received', null),
    ('INV-1054', 'FPX-3341', 'VEND-002', 'PO-127', '2026-07-11', '300.00', '0.18', '54.00', '354.00', '6220', 'received', null),
    ('INV-1055', 'MFS-88', 'VEND-004', null, '2026-07-12', '450.00', '0.08', '36.00', '486.00', null, 'received', null),
    ('INV-1056', 'AGB-1005', 'VEND-001', 'PO-130', '2026-07-12', '960.00', '0.08', '76.80', '1036.80', '6210', 'received', null),
    ('INV-1057', 'AGB-1019', 'VEND-001', 'PO-140', '2026-07-13', '2375.00', '0.08', '190.00', '2565.00', '6210', 'received', null),
    ('INV-1058', 'AGB-1027', 'VEND-001', 'PO-142', '2026-07-14', '1236.00', '0.08', '98.88', '1334.88', '6210', 'received', null),
    ('INV-1059', 'AGB-1031', 'VEND-001', 'PO-143', '2026-07-14', '1049.60', '0.08', '83.97', '1133.57', '6210', 'received', null),
    ('INV-1060', 'AGB-1042', 'VEND-001', 'PO-144', '2026-07-15', '1040.00', '0.08', '83.20', '1123.20', '6210', 'received', null);

insert into invoice_lines (invoice_id, line_no, po_line_no, description, quantity, unit_price, amount) values
    ('INV-1040', 1, 1, 'Roastery AC quarterly service', '1', '48200.00', '48200.00'),
    ('INV-1051', 1, 1, 'Arabica beans grade A, kg', '500', '4.16', '2080.00'),
    ('INV-1052', 1, 1, 'Coffee bag film roll', '1000', '0.80', '800.00'),
    ('INV-1053', 1, 1, 'Roastery AC quarterly service', '1', '48200.00', '48200.00'),
    ('INV-1054', 1, 1, 'Kraft label sheet', '200', '1.50', '300.00'),
    ('INV-1055', 1, null, 'Deep cleaning, roastery floor, July', '1', '450.00', '450.00'),
    ('INV-1056', 1, 1, 'Robusta beans grade B, kg', '300', '3.20', '960.00'),
    ('INV-1057', 1, 1, 'Arabica beans grade A, kg', '400', '4.00', '1600.00'),
    ('INV-1057', 2, 2, 'Robusta beans grade B, kg', '200', '3.60', '720.00'),
    ('INV-1057', 3, 3, 'Jute sack, 25kg', '50', '1.10', '55.00'),
    ('INV-1058', 1, 1, 'Arabica beans grade A, kg', '300', '4.12', '1236.00'),
    ('INV-1059', 1, 1, 'Robusta beans grade B, kg', '320', '3.28', '1049.60'),
    ('INV-1060', 1, 1, 'Arabica beans grade A, kg', '250', '4.16', '1040.00');

insert into contracts (id, vendor_id, valid_from, valid_to) values
    ('CON-001', 'VEND-001', '2026-01-01', '2026-12-31'),
    ('CON-002', 'VEND-002', '2026-03-01', '2027-02-28');

insert into contract_clauses (contract_id, clause_ref, clause_text) values
    ('CON-001', '2.1', 'Supplier shall deliver the full ordered quantity in a single shipment unless Buyer agrees to partial delivery in writing.'),
    ('CON-001', '4.2', 'Given commodity market variability, Supplier may adjust unit prices up to five percent (5%) above the purchase order price without prior written approval from Buyer.'),
    ('CON-002', '3.4', 'Supplier shall invoice only for quantities actually delivered and accepted at Buyer''s dock. Invoicing ahead of delivery is not permitted.'),
    ('CON-002', '5.1', 'Applicable sales tax for packaging materials under this agreement is eight percent (8%) as per resale exemption filing.');
