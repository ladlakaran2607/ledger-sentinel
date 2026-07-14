import os

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


if __name__ == "__main__":
    for inv in ["INV-1040", "INV-1051", "INV-1052", "INV-1053",
                "INV-1054", "INV-1055", "INV-1056", "INV-1057"]:
        print(three_way_match(inv))