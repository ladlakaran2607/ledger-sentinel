-- Ledger Sentinel mock ERP schema.
-- Run once in a fresh Supabase project, then load db/seed.sql.
-- The LangGraph checkpointer creates its own tables separately via checkpointer.setup().

create table vendors (
    id            text primary key,
    name          text not null,
    payment_terms text not null
);

create table gl_accounts (
    code text primary key,
    name text not null
);

create table purchase_orders (
    id         text primary key,
    vendor_id  text not null references vendors(id),
    order_date date not null,
    status     text not null default 'open'
);

create table po_lines (
    po_id       text not null references purchase_orders(id),
    line_no     int  not null,
    description text not null,
    quantity    numeric not null,
    unit_price  numeric not null,
    gl_code     text references gl_accounts(code),
    match_type  text not null default '3-way',
    primary key (po_id, line_no)
);

create table goods_receipts (
    id            text primary key,
    po_id         text not null references purchase_orders(id),
    received_date date not null
);

create table receipt_lines (
    receipt_id   text not null references goods_receipts(id),
    po_line_no   int  not null,
    qty_received numeric not null,
    primary key (receipt_id, po_line_no)
);

create table invoices (
    id             text primary key,
    invoice_number text not null,
    vendor_id      text not null references vendors(id),
    po_id          text references purchase_orders(id),
    invoice_date   date not null,
    subtotal       numeric not null,
    tax_rate       numeric not null,
    tax_amount     numeric not null,
    total          numeric not null,
    gl_code        text references gl_accounts(code),
    status         text not null default 'received',
    paid_date      date
);

create table invoice_lines (
    invoice_id  text not null references invoices(id),
    line_no     int  not null,
    po_line_no  int,
    description text not null,
    quantity    numeric not null,
    unit_price  numeric not null,
    amount      numeric not null,
    primary key (invoice_id, line_no)
);

create table contracts (
    id         text primary key,
    vendor_id  text not null references vendors(id),
    valid_from date not null,
    valid_to   date not null
);

create table contract_clauses (
    contract_id text not null references contracts(id),
    clause_ref  text not null,
    clause_text text not null,
    primary key (contract_id, clause_ref)
);

create index idx_invoices_vendor_total on invoices (vendor_id, total);

alter table vendors          enable row level security;
alter table gl_accounts      enable row level security;
alter table purchase_orders  enable row level security;
alter table po_lines         enable row level security;
alter table goods_receipts   enable row level security;
alter table receipt_lines    enable row level security;
alter table invoices         enable row level security;
alter table invoice_lines    enable row level security;
alter table contracts        enable row level security;
alter table contract_clauses enable row level security;
