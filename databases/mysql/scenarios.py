"""The 24 CRUD scenarios of docs/scenarios.md for MySQL.

Every scenario is Scenario(name, run, setup, cleanup, params); run(conn, params) is the timed
part. The connection runs in autocommit mode, multi-statement scenarios open an explicit
transaction. Smoke test (from repo root, data loaded):
    python databases/mysql/scenarios.py [--only C1,R4]
"""

import argparse
import sys
import time
from collections import namedtuple
from decimal import Decimal

from load import TABLES, connect

TEMP = 900_000_000

Scenario = namedtuple("Scenario", "name run setup cleanup params", defaults=(None, None, {}))


def execute(conn, sql, args=()):
    cur = conn.cursor()
    cur.execute(sql, args)
    rows = cur.fetchall() if cur.with_rows else cur.rowcount
    cur.close()
    return rows


def executemany(conn, sql, rows):
    cur = conn.cursor()
    cur.executemany(sql, rows)
    count = cur.rowcount
    cur.close()
    return count


def purge_temp(conn, params=None):
    """Remove every row in the reserved id range; FK cascades take the children."""
    conn.start_transaction()
    execute(conn, "DELETE FROM orders WHERE id >= %s", (TEMP,))
    execute(conn, "DELETE FROM customers WHERE id >= %s", (TEMP,))
    execute(conn, "DELETE FROM products WHERE id >= %s", (TEMP,))
    conn.commit()


def insert_customers(conn, first_id, count, last_name="User", created_at="2026-06-30 12:00:00", tag="c"):
    rows = [(first_id + n, "Bench", last_name, f"bench.{tag}.{n}@example.com", "+1-555-000-0000", created_at)
            for n in range(count)]
    return executemany(conn, "INSERT INTO customers (id, first_name, last_name, email, phone, created_at) "
                             "VALUES (%s, %s, %s, %s, %s, %s)", rows)


def insert_addresses(conn, customer_id, first_id, count):
    rows = [(first_id + n, customer_id, f"{n + 1} Benchmark Street", "Springfield", "12345", "US", n == 0)
            for n in range(count)]
    return executemany(conn, "INSERT INTO addresses (id, customer_id, street, city, postal_code, country, is_default) "
                             "VALUES (%s, %s, %s, %s, %s, %s, %s)", rows)


def insert_orders(conn, first_id, count, customer_id, address_id, product_ids, created_at, shipped_at=None):
    """Insert orders with one item per product (quantity 1, current price) and a payment each."""
    placeholders = ", ".join(["%s"] * len(product_ids))
    prices = dict(execute(conn, f"SELECT id, price FROM products WHERE id IN ({placeholders})", product_ids))
    total = sum(prices[p] for p in product_ids)
    order_ids = range(first_id, first_id + count)
    status = "shipped" if shipped_at else "paid"
    executemany(conn, "INSERT INTO orders (id, customer_id, address_id, status, total_amount, created_at) "
                      "VALUES (%s, %s, %s, %s, %s, %s)",
                [(o, customer_id, address_id, status, total, created_at) for o in order_ids])
    items = [(TEMP + (o - TEMP) * len(product_ids) + n, o, p, 1, prices[p])
             for o in order_ids for n, p in enumerate(product_ids)]
    executemany(conn, "INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) "
                      "VALUES (%s, %s, %s, %s, %s)", items)
    executemany(conn, "INSERT INTO payments (id, order_id, method, status, amount, paid_at) "
                      "VALUES (%s, %s, 'credit_card', 'completed', %s, %s)",
                [(o, o, total, created_at) for o in order_ids])
    if shipped_at:
        executemany(conn, "INSERT INTO shipments (id, order_id, carrier, tracking_number, shipped_at, delivered_at) "
                          "VALUES (%s, %s, 'UPS', %s, %s, NULL)",
                    [(o, o, f"BENCH{o}", shipped_at) for o in order_ids])
    return len(items)


def insert_product(conn, product_id, category, brand, specs):
    execute(conn, "INSERT INTO products (id, sku, name, category_id, brand_id, price, release_date) "
                  "SELECT %s, %s, %s, c.id, b.id, %s, %s FROM categories c, brands b WHERE c.name = %s AND b.name = %s",
            (product_id, f"BENCH-{product_id}", f"{brand} Benchmark {category}", Decimal("699.99"), "2026-06-01",
             category, brand))
    return executemany(conn, "INSERT INTO product_attributes (product_id, name, value) VALUES (%s, %s, %s)",
                       [(product_id, k, str(v)) for k, v in specs.items()])


GPU_SPECS = {"chipset": "GeForce RTX 5070 Ti", "gpu_vendor": "NVIDIA", "vram_gb": 16,
             "memory_type": "GDDR7", "tdp_w": 300, "length_mm": 305}


# Create

def c1(conn, p):
    return insert_customers(conn, p["id"], 1, tag="c1")


def c2(conn, p):
    conn.start_transaction()
    count = insert_customers(conn, p["first_id"], p["count"], tag="c2")
    conn.commit()
    return count


def c3(conn, p):
    conn.start_transaction()
    count = insert_orders(conn, p["order_id"], 1, p["customer_id"], p["address_id"], p["product_ids"],
                          p["created_at"])
    conn.commit()
    return count


def c4(conn, p):
    conn.start_transaction()
    count = insert_product(conn, p["id"], p["category"], p["brand"], p["specs"])
    conn.commit()
    return count


def c5(conn, p):
    conn.start_transaction()
    count = insert_orders(conn, p["first_id"], p["count"], p["customer_id"], p["address_id"], p["product_ids"],
                          p["created_at"])
    conn.commit()
    return count


def c6(conn, p):
    conn.start_transaction()
    insert_customers(conn, p["customer_id"], 1, tag="c6")
    count = insert_addresses(conn, p["customer_id"], p["address_id"], 2)
    conn.commit()
    return count


# Read

def r1(conn, p):
    return execute(conn, "SELECT p.id, p.sku, p.name, p.price, c.name, b.name FROM products p "
                         "JOIN categories c ON c.id = p.category_id JOIN brands b ON b.id = p.brand_id "
                         "WHERE p.id = %s", (p["product_id"],))


def r2(conn, p):
    return execute(conn, "SELECT id, first_name, last_name, email FROM customers WHERE last_name = %s",
                   (p["last_name"],))


def r3(conn, p):
    return execute(conn, "SELECT p.id, p.name, p.price FROM products p JOIN categories c ON c.id = p.category_id "
                         "WHERE c.name = %s AND p.price BETWEEN %s AND %s ORDER BY p.price, p.id LIMIT %s",
                   (p["category"], p["min_price"], p["max_price"], p["limit"]))


def r4(conn, p):
    return execute(conn, "SELECT p.id, p.name, SUM(oi.quantity) AS sold FROM order_items oi "
                         "JOIN orders o ON o.id = oi.order_id JOIN products p ON p.id = oi.product_id "
                         "WHERE o.created_at >= %s AND o.created_at < %s AND o.status <> 'cancelled' "
                         "GROUP BY p.id, p.name ORDER BY sold DESC, p.id LIMIT %s",
                   (p["from"], p["to"], p["limit"]))


def r5(conn, p):
    return execute(conn, "SELECT o.id, o.created_at, o.status, o.total_amount, oi.product_id, pr.name, "
                         "oi.quantity, oi.unit_price FROM orders o "
                         "JOIN order_items oi ON oi.order_id = o.id JOIN products pr ON pr.id = oi.product_id "
                         "WHERE o.customer_id = %s ORDER BY o.created_at DESC, o.id, oi.id", (p["customer_id"],))


def r6(conn, p):
    return execute(conn, "SELECT m.id, m.name, m.price FROM product_attributes cpu "
                         "JOIN product_attributes board ON board.name = 'socket' AND board.value = cpu.value "
                         "JOIN products m ON m.id = board.product_id "
                         "JOIN categories c ON c.id = m.category_id AND c.name = 'Motherboard' "
                         "WHERE cpu.product_id = %s AND cpu.name = 'socket' ORDER BY m.price, m.id", (p["cpu_id"],))


# Update

def u1_setup(conn, p):
    return {**p, "old": execute(conn, "SELECT price FROM products WHERE id = %s", (p["product_id"],))[0][0]}


def u1(conn, p):
    return execute(conn, "UPDATE products SET price = %s WHERE id = %s", (p["price"], p["product_id"]))


def u1_cleanup(conn, p):
    execute(conn, "UPDATE products SET price = %s WHERE id = %s", (p["old"], p["product_id"]))


def u2_setup(conn, p):
    rows = execute(conn, "SELECT p.price, p.id FROM products p JOIN brands b ON b.id = p.brand_id "
                         "JOIN categories c ON c.id = p.category_id WHERE b.name = %s AND c.name = %s",
                   (p["brand"], p["category"]))
    return {**p, "old": rows}


def u2(conn, p):
    return execute(conn, "UPDATE products p JOIN brands b ON b.id = p.brand_id "
                         "JOIN categories c ON c.id = p.category_id SET p.price = ROUND(p.price * %s, 2) "
                         "WHERE b.name = %s AND c.name = %s", (p["factor"], p["brand"], p["category"]))


def u2_cleanup(conn, p):
    executemany(conn, "UPDATE products SET price = %s WHERE id = %s", p["old"])


def u3_setup(conn, p):
    old = execute(conn, "SELECT value FROM product_attributes WHERE product_id = %s AND name = %s",
                  (p["product_id"], p["name"]))[0][0]
    return {**p, "old": old}


def u3(conn, p):
    return execute(conn, "UPDATE product_attributes SET value = %s WHERE product_id = %s AND name = %s",
                   (str(p["value"]), p["product_id"], p["name"]))


def u3_cleanup(conn, p):
    execute(conn, "UPDATE product_attributes SET value = %s WHERE product_id = %s AND name = %s",
            (p["old"], p["product_id"], p["name"]))


def u4_setup(conn, p):
    rows = execute(conn, "SELECT inv.quantity, inv.product_id, inv.supplier_id FROM inventory inv "
                         "JOIN order_items oi ON oi.product_id = inv.product_id WHERE oi.order_id = %s",
                   (p["order_id"],))
    return {**p, "old": rows}


def u4(conn, p):
    conn.start_transaction()
    count = execute(conn, "UPDATE inventory inv "
                          "JOIN order_items oi ON oi.product_id = inv.product_id AND oi.order_id = %s "
                          "JOIN (SELECT i.product_id, MIN(i.supplier_id) AS supplier_id FROM inventory i "
                          "      JOIN order_items x ON x.product_id = i.product_id AND x.order_id = %s "
                          "      GROUP BY i.product_id) first ON first.product_id = inv.product_id "
                          "      AND first.supplier_id = inv.supplier_id "
                          "SET inv.quantity = GREATEST(inv.quantity - oi.quantity, 0)",
                    (p["order_id"], p["order_id"]))
    conn.commit()
    return count


def u4_cleanup(conn, p):
    executemany(conn, "UPDATE inventory SET quantity = %s WHERE product_id = %s AND supplier_id = %s", p["old"])


def u5_setup(conn, p):
    return {**p, "order_id": execute(conn, "SELECT MIN(id) FROM orders WHERE status = 'paid'")[0][0]}


def u5(conn, p):
    conn.start_transaction()
    execute(conn, "UPDATE orders SET status = 'shipped' WHERE id = %s", (p["order_id"],))
    count = execute(conn, "INSERT INTO shipments (id, order_id, carrier, tracking_number, shipped_at, delivered_at) "
                          "VALUES (%s, %s, %s, %s, %s, NULL)",
                    (TEMP, p["order_id"], p["carrier"], f"BENCH{p['order_id']}", p["shipped_at"]))
    conn.commit()
    return count


def u5_cleanup(conn, p):
    conn.start_transaction()
    execute(conn, "DELETE FROM shipments WHERE id = %s", (TEMP,))
    execute(conn, "UPDATE orders SET status = 'paid' WHERE id = %s", (p["order_id"],))
    conn.commit()


def u6_setup(conn, p):
    ids = execute(conn, "SELECT id FROM orders WHERE status = 'pending' AND created_at < %s", (p["before"],))
    return {**p, "old": ids}


def u6(conn, p):
    return execute(conn, "UPDATE orders o JOIN payments pay ON pay.order_id = o.id "
                         "SET o.status = 'cancelled', pay.status = 'refunded' "
                         "WHERE o.status = 'pending' AND o.created_at < %s", (p["before"],))


def u6_cleanup(conn, p):
    conn.start_transaction()
    executemany(conn, "UPDATE orders SET status = 'pending' WHERE id = %s", p["old"])
    executemany(conn, "UPDATE payments SET status = 'pending' WHERE order_id = %s", p["old"])
    conn.commit()


# Delete: setup creates the victims in the reserved id range, cleanup purges leftovers.

def d1_setup(conn, p):
    insert_customers(conn, p["customer_id"], 1, tag="d1")
    return p


def d1(conn, p):
    return execute(conn, "DELETE FROM customers WHERE id = %s", (p["customer_id"],))


def d2_setup(conn, p):
    conn.start_transaction()
    insert_customers(conn, TEMP, p["count"], last_name=p["last_name"], created_at="2019-06-01 00:00:00", tag="d2")
    conn.commit()
    return p


def d2(conn, p):
    return execute(conn, "DELETE FROM customers WHERE last_name = %s AND created_at < %s",
                   (p["last_name"], p["before"]))


def d3_setup(conn, p):
    conn.start_transaction()
    insert_customers(conn, p["customer_id"], 1, tag="d3")
    insert_addresses(conn, p["customer_id"], TEMP, 2)
    insert_orders(conn, TEMP, 5, p["customer_id"], TEMP, [1, 2, 3], "2026-06-30 12:00:00",
                  shipped_at="2026-06-30 18:00:00")
    conn.commit()
    return p


def d3(conn, p):
    # InnoDB checks FKs row by row inside a cascade, so deleting the customer first would hit
    # orders -> addresses before the orders are gone; orders go first, both cascade further.
    conn.start_transaction()
    orders = execute(conn, "DELETE FROM orders WHERE customer_id = %s", (p["customer_id"],))
    customers = execute(conn, "DELETE FROM customers WHERE id = %s", (p["customer_id"],))
    conn.commit()
    return orders + customers


def d4_setup(conn, p):
    conn.start_transaction()
    insert_product(conn, p["product_id"], "GPU", "MSI", GPU_SPECS)
    executemany(conn, "INSERT INTO inventory (product_id, supplier_id, warehouse, quantity, updated_at) "
                      "VALUES (%s, %s, 'Reno NV', 10, '2026-06-30 12:00:00')",
                [(p["product_id"], 1), (p["product_id"], 2)])
    conn.commit()
    return p


def d4(conn, p):
    return execute(conn, "DELETE FROM products WHERE id = %s", (p["product_id"],))


def d5_setup(conn, p):
    conn.start_transaction()
    insert_orders(conn, TEMP, p["count"], 1, 1, [1, 2], "2019-06-01 00:00:00")
    conn.commit()
    return p


def d5(conn, p):
    return execute(conn, "DELETE FROM orders WHERE created_at < %s", (p["before"],))


def d6_setup(conn, p):
    conn.start_transaction()
    insert_orders(conn, p["order_id"], 1, 1, 1, [1, 2, 3], "2026-06-30 12:00:00", shipped_at="2026-06-30 18:00:00")
    conn.commit()
    return p


def d6(conn, p):
    return execute(conn, "DELETE FROM orders WHERE id = %s", (p["order_id"],))


NOW = "2026-06-30 12:00:00"

SCENARIOS = {
    "C1": Scenario("Single insert", c1, None, purge_temp, {"id": TEMP}),
    "C2": Scenario("Batch insert 1000", c2, None, purge_temp, {"first_id": TEMP, "count": 1000}),
    "C3": Scenario("Insert order with items", c3, None, purge_temp,
                   {"order_id": TEMP, "customer_id": 1, "address_id": 1, "product_ids": [1, 2, 3], "created_at": NOW}),
    "C4": Scenario("Insert product with specs", c4, None, purge_temp,
                   {"id": TEMP, "category": "GPU", "brand": "MSI", "specs": GPU_SPECS}),
    "C5": Scenario("Batch insert orders", c5, None, purge_temp,
                   {"first_id": TEMP, "count": 1000, "customer_id": 1, "address_id": 1, "product_ids": [1, 2],
                    "created_at": NOW}),
    "C6": Scenario("Insert customer with addresses", c6, None, purge_temp,
                   {"customer_id": TEMP, "address_id": TEMP}),
    "R1": Scenario("Read by primary key", r1, params={"product_id": 42}),
    "R2": Scenario("Read by non-indexed field", r2, params={"last_name": "Smith"}),
    "R3": Scenario("Range query + sort + limit", r3,
                   params={"category": "GPU", "min_price": 300, "max_price": 800, "limit": 20}),
    "R4": Scenario("Aggregation", r4, params={"from": "2026-05-31 00:00:00", "to": "2026-06-30 00:00:00", "limit": 10}),
    "R5": Scenario("Join / lookup", r5, params={"customer_id": 1}),
    "R6": Scenario("Compatible parts lookup", r6, params={"cpu_id": 1}),
    "U1": Scenario("Update one record", u1, u1_setup, u1_cleanup, {"product_id": 42, "price": Decimal("199.99")}),
    "U2": Scenario("Bulk update by condition", u2, u2_setup, u2_cleanup,
                   {"brand": "MSI", "category": "GPU", "factor": Decimal("1.10")}),
    "U3": Scenario("Update nested / attribute field", u3, u3_setup, u3_cleanup,
                   {"product_id": 1, "name": "boost_clock_ghz", "value": 6.2}),
    "U4": Scenario("Update stock after order", u4, u4_setup, u4_cleanup, {"order_id": 1}),
    "U5": Scenario("Ship an order", u5, u5_setup, u5_cleanup, {"carrier": "UPS", "shipped_at": NOW}),
    "U6": Scenario("Bulk status change", u6, u6_setup, u6_cleanup, {"before": "2025-01-01 00:00:00"}),
    "D1": Scenario("Delete one", d1, d1_setup, purge_temp, {"customer_id": TEMP}),
    "D2": Scenario("Delete by condition", d2, d2_setup, purge_temp,
                   {"count": 1000, "last_name": "Tempbench", "before": "2020-01-01 00:00:00"}),
    "D3": Scenario("Cascading delete", d3, d3_setup, purge_temp, {"customer_id": TEMP}),
    "D4": Scenario("Delete product with specs", d4, d4_setup, purge_temp, {"product_id": TEMP}),
    "D5": Scenario("Delete old records", d5, d5_setup, purge_temp, {"count": 500, "before": "2020-01-01 00:00:00"}),
    "D6": Scenario("Delete one order", d6, d6_setup, purge_temp, {"order_id": TEMP}),
}


def fingerprint(conn):
    rows = execute(conn, "CHECKSUM TABLE " + ", ".join(TABLES))
    return {table: checksum for table, checksum in rows}


def summary(result):
    return f"{len(result)} rows" if isinstance(result, list) else f"{result} affected"


def smoke(conn, ids):
    before = fingerprint(conn)
    failures = []
    for sid in ids:
        s = SCENARIOS[sid]
        params = s.setup(conn, dict(s.params)) if s.setup else dict(s.params)
        start = time.perf_counter()
        try:
            result = s.run(conn, params)
        except Exception as exc:
            conn.rollback()
            result = exc
        elapsed = (time.perf_counter() - start) * 1000
        if s.cleanup:
            s.cleanup(conn, params)
        changed = [t for t, c in fingerprint(conn).items() if c != before[t]]
        ok = not isinstance(result, Exception) and not changed
        if not ok:
            failures.append(sid)
        detail = result if isinstance(result, Exception) else summary(result)
        state = f"  state changed: {', '.join(changed)}" if changed else ""
        print(f"{'OK  ' if ok else 'FAIL'} {sid} {s.name:<32} {elapsed:9.1f} ms  {detail}{state}")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", help="comma-separated scenario ids (default: all)")
    args = parser.parse_args()
    ids = args.only.split(",") if args.only else list(SCENARIOS)
    conn = connect(autocommit=True)
    failures = smoke(conn, ids)
    conn.close()
    print(f"{len(ids) - len(failures)}/{len(ids)} scenarios passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
