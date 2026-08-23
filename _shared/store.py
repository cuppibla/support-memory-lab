"""The Lumen & Co. world: customers, orders, products, batches, tickets, defects.

One SQLite file (_shared/lumen_world.db), built on first import. This is the
"company database" that exists BEFORE the agent — rung 5 teaches that the
institutional-memory graph is already sitting in tables like these.
"""

import pathlib
import sqlite3

WORLD_DB = pathlib.Path(__file__).parent / "lumen_world.db"


def _build() -> None:
    db = sqlite3.connect(WORLD_DB)
    db.executescript("""
    CREATE TABLE customers(id TEXT PRIMARY KEY, name TEXT);
    CREATE TABLE products(id TEXT PRIMARY KEY, name TEXT);
    CREATE TABLE batches(id TEXT PRIMARY KEY, product_id TEXT REFERENCES products);
    CREATE TABLE orders(id TEXT PRIMARY KEY, customer_id TEXT REFERENCES customers,
                        product_id TEXT REFERENCES products, batch_id TEXT REFERENCES batches);
    CREATE TABLE tickets(id TEXT PRIMARY KEY, order_id TEXT REFERENCES orders, text TEXT);
    CREATE TABLE defects(batch_id TEXT REFERENCES batches, title TEXT, fix TEXT);
    """)
    db.execute("INSERT INTO customers VALUES ('maya','Maya')")
    db.execute("INSERT INTO products VALUES ('lg2','LumenGlow v2'),"
               "('lg1','LumenGlow v1'),('halo','Halo Mini')")
    db.execute("INSERT INTO batches VALUES ('B7','lg2'),('B6','lg2'),('A2','lg1')")
    db.execute("INSERT INTO orders VALUES ('8841','maya','lg2','B7')")
    for i in range(37):
        db.execute("INSERT INTO customers VALUES (?,?)", (f"c{i}", f"Customer {i}"))
        db.execute("INSERT INTO orders VALUES (?,?,'lg2','B7')", (f"o{i}", f"c{i}"))
        db.execute("INSERT INTO tickets VALUES (?,?,?)",
                   (f"T{i}", f"o{i}", "flicker after firmware 2.0, base cracks near the seam"))
    # similar-SOUNDING but unconnected tickets (different product/batch) — the trap
    for pid, bid, i in [("lg1", "A2", 90), ("halo", None, 91), ("lg1", "A2", 92)]:
        db.execute("INSERT INTO customers VALUES (?,?)", (f"c{i}", f"Customer {i}"))
        db.execute("INSERT INTO orders VALUES (?,?,?,?)", (f"o{i}", f"c{i}", pid, bid))
        db.execute("INSERT INTO tickets VALUES (?,?,?)",
                   (f"T{i}", f"o{i}", "my lamp flickers sometimes in the evening"))
    db.execute("INSERT INTO defects VALUES "
               "('B7','Flicker + base crack (driver defect)','firmware 2.1')")
    db.commit()
    db.close()


def conn() -> sqlite3.Connection:
    if not WORLD_DB.exists():
        _build()
    return sqlite3.connect(WORLD_DB)
