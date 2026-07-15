import os
import sys

import psycopg
from dotenv import load_dotenv

load_dotenv()


def _connect():
    return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=20)


def three_way_match(invoice_id: str) -> dict:
    with _connect() as conn:
        invoice = conn.execute(
            """select po_id, subtotal, tax_rate, tax_amount, total
               from invoices where id = %s""",
            (invoice_id,),
        ).fetchone()

        if invoice is None:
            return {"invoice_id": invoice_id, "verdict": "not_found", "discrepancies": []}

        po_id, subtotal, tax_rate, tax_amount, total = invoice

        if po_id is None:
            return {"invoice_id": invoice_id, "verdict": "no_po", "discrepancies": []}

        discrepancies = []

        lines = conn.execute(
            """select il.line_no, il.po_line_no, il.quantity, il.unit_price, il.amount,
                      pl.unit_price, pl.match_type
               from invoice_lines il
               join po_lines pl on pl.po_id = %s and pl.line_no = il.po_line_no
               where il.invoice_id = %s
               order by il.line_no""",
            (po_id, invoice_id),
        ).fetchall()

        line_amount_sum = 0
        for line_no, po_line_no, billed_qty, billed_price, amount, agreed_price, match_type in lines:
            line_amount_sum += amount

            if billed_price != agreed_price:
                discrepancies.append({
                    "line_no": line_no,
                    "field": "unit_price",
                    "expected": float(agreed_price),
                    "found": float(billed_price),
                })

            if match_type == "3-way":
                received = conn.execute(
                    """select coalesce(sum(rl.qty_received), 0)
                       from goods_receipts gr
                       join receipt_lines rl on rl.receipt_id = gr.id
                       where gr.po_id = %s and rl.po_line_no = %s""",
                    (po_id, po_line_no),
                ).fetchone()[0]

                if billed_qty != received:
                    discrepancies.append({
                        "line_no": line_no,
                        "field": "quantity",
                        "expected": float(received),
                        "found": float(billed_qty),
                    })

        if subtotal != line_amount_sum:
            discrepancies.append({
                "line_no": None,
                "field": "subtotal",
                "expected": float(line_amount_sum),
                "found": float(subtotal),
            })

        if tax_amount != round(subtotal * tax_rate, 2):
            discrepancies.append({
                "line_no": None,
                "field": "tax_amount",
                "expected": float(round(subtotal * tax_rate, 2)),
                "found": float(tax_amount),
            })

        verdict = "mismatch" if discrepancies else "clean"
        return {"invoice_id": invoice_id, "verdict": verdict, "discrepancies": discrepancies}

def fetch_po(po_id: str) -> dict:
    with _connect() as conn:
        header = conn.execute(
            """select id, vendor_id, order_date, status
               from purchase_orders where id = %s""",
            (po_id,),
        ).fetchone()

        if header is None:
            return {"po_id": po_id, "found": False}

        lines = conn.execute(
            """select line_no, description, quantity, unit_price, gl_code, match_type
               from po_lines where po_id = %s order by line_no""",
            (po_id,),
        ).fetchall()

        return {
            "po_id": header[0],
            "found": True,
            "vendor_id": header[1],
            "order_date": str(header[2]),
            "status": header[3],
            "lines": [
                {
                    "line_no": l[0],
                    "description": l[1],
                    "quantity": float(l[2]),
                    "unit_price": float(l[3]),
                    "gl_code": l[4],
                    "match_type": l[5],
                }
                for l in lines
            ],
        }


def fetch_goods_receipts(po_id: str) -> dict:
    with _connect() as conn:
        rows = conn.execute(
            """select gr.id, gr.received_date, rl.po_line_no, rl.qty_received
               from goods_receipts gr
               join receipt_lines rl on rl.receipt_id = gr.id
               where gr.po_id = %s
               order by gr.received_date, gr.id, rl.po_line_no""",
            (po_id,),
        ).fetchall()

        receipts = {}
        for receipt_id, received_date, po_line_no, qty in rows:
            receipts.setdefault(
                receipt_id, {"receipt_id": receipt_id, "received_date": str(received_date), "lines": []}
            )["lines"].append({"po_line_no": po_line_no, "qty_received": float(qty)})

        return {"po_id": po_id, "receipts": list(receipts.values())}


def read_contract_clauses(vendor_id: str) -> dict:
    with _connect() as conn:
        rows = conn.execute(
            """select c.id, c.valid_from, c.valid_to, cc.clause_ref, cc.clause_text
               from contracts c
               join contract_clauses cc on cc.contract_id = c.id
               where c.vendor_id = %s
               order by c.id, cc.clause_ref""",
            (vendor_id,),
        ).fetchall()

        contracts = {}
        for contract_id, valid_from, valid_to, clause_ref, clause_text in rows:
            contracts.setdefault(
                contract_id,
                {
                    "contract_id": contract_id,
                    "valid_from": str(valid_from),
                    "valid_to": str(valid_to),
                    "clauses": [],
                },
            )["clauses"].append({"ref": clause_ref, "text": clause_text})

        return {"vendor_id": vendor_id, "contracts": list(contracts.values())}


def search_vendor_history(vendor_id: str, total: float, exclude_invoice_id: str) -> dict:
    with _connect() as conn:
        rows = conn.execute(
            """select id, invoice_number, invoice_date, total, status, paid_date
               from invoices
               where vendor_id = %s and total = %s and id <> %s
               order by invoice_date""",
            (vendor_id, total, exclude_invoice_id),
        ).fetchall()

        return {
            "vendor_id": vendor_id,
            "total_searched": float(total),
            "matches": [
                {
                    "invoice_id": r[0],
                    "invoice_number": r[1],
                    "invoice_date": str(r[2]),
                    "total": float(r[3]),
                    "status": r[4],
                    "paid_date": str(r[5]) if r[5] else None,
                }
                for r in rows
            ],
        }


def fetch_invoice(invoice_id: str) -> dict:
    with _connect() as conn:
        row = conn.execute(
            """select id, invoice_number, vendor_id, po_id, invoice_date,
                      subtotal, tax_rate, tax_amount, total, gl_code, status, paid_date
               from invoices where id = %s""",
            (invoice_id,),
        ).fetchone()

        if row is None:
            return {"invoice_id": invoice_id, "found": False}

        lines = conn.execute(
            """select line_no, po_line_no, description, quantity, unit_price, amount
               from invoice_lines where invoice_id = %s order by line_no""",
            (invoice_id,),
        ).fetchall()

        return {
            "invoice_id": row[0],
            "found": True,
            "invoice_number": row[1],
            "vendor_id": row[2],
            "po_id": row[3],
            "invoice_date": str(row[4]),
            "subtotal": float(row[5]),
            "tax_rate": float(row[6]),
            "tax_amount": float(row[7]),
            "total": float(row[8]),
            "gl_code": row[9],
            "status": row[10],
            "paid_date": str(row[11]) if row[11] else None,
            "lines": [
                {
                    "line_no": l[0],
                    "po_line_no": l[1],
                    "description": l[2],
                    "quantity": float(l[3]),
                    "unit_price": float(l[4]),
                    "amount": float(l[5]),
                }
                for l in lines
            ],
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(three_way_match(sys.argv[1]))
    else:
        for inv in ["INV-1040", "INV-1051", "INV-1052", "INV-1053",
                    "INV-1054", "INV-1055", "INV-1056", "INV-1057"]:
            print(three_way_match(inv))
        print()
        print(fetch_po("PO-121"))
        print(fetch_goods_receipts("PO-121"))
        print(read_contract_clauses("VEND-002"))
        print(search_vendor_history("VEND-003", 48200.00, "INV-1053"))