"""Rung 6 tools — the same two ways of reading, now against the company warehouse.

Both queries are FIXED and parameterized. The agent never writes SQL — it calls
a governed tool and quotes what comes back. Same principle as rung 5, real scale.
"""

import os

from google.cloud import bigquery

_client = None


def _bq() -> bigquery.Client:
    global _client
    if _client is None:
        _client = bigquery.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    return _client


def warehouse_search(text: str) -> dict:
    """Semantic search over ALL support tickets in the company warehouse.

    Args:
        text: What to look for — meaning, not keywords.

    Returns:
        dict with the closest tickets and their distance scores.
    """
    query = """
    SELECT base.id, base.content, ROUND(distance, 3) AS distance
    FROM VECTOR_SEARCH(
      TABLE lumen.ticket_embeddings, 'embedding',
      (SELECT ml_generate_embedding_result FROM ML.GENERATE_EMBEDDING(
         MODEL lumen.embedder, (SELECT @q AS content))),
      top_k => 5)
    ORDER BY distance
    """
    job = _bq().query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("q", "STRING", text)]))
    rows = [{"ticket": r.id, "text": r.content, "distance": r.distance} for r in job]
    return {"status": "success", "matches": rows,
            "note": "semantic match — meaning, not keywords; still says nothing about connection"}


def warehouse_known_issue(order_number: str) -> dict:
    """Checks whether an order's product batch has a known issue — the governed
    traversal, in the warehouse: orders -> products -> batches -> tickets -> defects.

    Args:
        order_number: The customer's order number (e.g. 8841).

    Returns:
        dict with the traversal path, any known defect, and the fix.
    """
    query = """
    SELECT c.name, o.id AS order_id, p.name AS product, b.id AS batch,
           d.title, d.fix,
           (SELECT COUNT(*) FROM lumen.tickets t
            JOIN lumen.orders oo ON t.order_id = oo.id
            WHERE oo.batch_id = b.id) AS connected_tickets
    FROM lumen.orders o
    JOIN lumen.customers c ON o.customer_id = c.id
    JOIN lumen.products p ON o.product_id = p.id
    LEFT JOIN lumen.batches b ON o.batch_id = b.id
    LEFT JOIN lumen.defects d ON d.batch_id = b.id
    WHERE o.id = @order_number
    """
    job = _bq().query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("order_number", "STRING", order_number)]))
    rows = list(job)
    if not rows:
        return {"status": "not_found", "order_number": order_number}
    r = rows[0]
    path = (f"{r.name} -> order #{r.order_id} -> {r.product} -> batch {r.batch} "
            f"-> {r.connected_tickets} tickets -> {r.title or 'no known defect'}")
    return {"status": "success", "path": path, "known_issue": r.title,
            "fix": r.fix, "connected_tickets": r.connected_tickets}
