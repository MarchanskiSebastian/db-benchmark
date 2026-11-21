"""The 24 CRUD scenarios of docs/scenarios.md for Neo4j (Cypher, official driver).

Every scenario is Scenario(name, run, setup, cleanup, params); run(driver, params) is the
timed part, with the same IDs and parameters as the SQL engines. Each Cypher statement runs
in its own auto-committed transaction. Smoke test (from repo root, data imported):
    python databases/neo4j/scenarios.py [--only C1,R4]
"""

import argparse
import sys
import time
from collections import namedtuple

from load import connect

TEMP = 900_000_000
NOW = "2026-06-30T12:00:00"

Scenario = namedtuple("Scenario", "name run setup cleanup params", defaults=(None, None, {}))

COUNTERS = ("nodes_created", "nodes_deleted", "relationships_created", "relationships_deleted", "properties_set")


def read(driver, query, **params):
    return driver.execute_query(query, params).records


def write(driver, query, **params):
    """Run a write and return the number of affected nodes, relationships and properties."""
    counters = driver.execute_query(query, params).summary.counters
    return sum(getattr(counters, name) for name in COUNTERS)


def purge_temp(driver, params=None):
    for label, prop in (("Order", "orderId"), ("Customer", "customerId"), ("Product", "productId")):
        write(driver, f"MATCH (n:{label}) WHERE n.{prop} >= $temp DETACH DELETE n", temp=TEMP)
    write(driver, "MATCH (a:Address) DETACH DELETE a")


def create_customers(driver, first_id, count, last_name="User", created_at=NOW, tag="c"):
    return write(driver, "UNWIND range($first, $first + $count - 1) AS id "
                         "CREATE (:Customer {customerId: id, first_name: 'Bench', last_name: $last_name, "
                         "email: 'bench.' + $tag + '.' + toString(id - $first) + '@example.com', "
                         "phone: '+1-555-000-0000', created_at: datetime($created_at)})",
                 first=first_id, count=count, last_name=last_name, created_at=created_at, tag=tag)


def create_orders(driver, first_id, count, customer_id, product_ids, created_at, shipped_at=None):
    """Orders with one CONTAINS per product (quantity 1, current price) and payment properties."""
    return write(driver, "MATCH (c:Customer {customerId: $customer_id}) "
                         "MATCH (p:Product) WHERE p.productId IN $product_ids "
                         "WITH c, collect(p) AS products, sum(p.price) AS total "
                         "UNWIND range($first, $first + $count - 1) AS id "
                         "CREATE (c)-[:PLACED]->(o:Order {orderId: id, total_amount: total, "
                         "  status: CASE WHEN $shipped_at IS NULL THEN 'paid' ELSE 'shipped' END, "
                         "  created_at: datetime($created_at), payment_method: 'credit_card', "
                         "  payment_status: 'completed', paid_at: datetime($created_at), "
                         "  carrier: CASE WHEN $shipped_at IS NULL THEN null ELSE 'UPS' END, "
                         "  shipped_at: datetime($shipped_at)}) "
                         "WITH o, products UNWIND products AS p "
                         "CREATE (o)-[:CONTAINS {quantity: 1, unit_price: p.price}]->(p)",
                 first=first_id, count=count, customer_id=customer_id, product_ids=product_ids,
                 created_at=created_at, shipped_at=shipped_at)


def create_product(driver, product_id, category, brand, specs, stock=None):
    # Category doubles as a label (Product:GPU), as in the import.
    return write(driver, "MATCH (c:Category {name: $category}), (b:Brand {name: $brand}) "
                         f"CREATE (p:Product:{category} {{productId: $id, sku: 'BENCH-' + toString($id), "
                         "  name: $brand + ' Benchmark ' + $category, price: 699.99, release_date: date('2026-06-01'), "
                         "  stock: $stock}) "
                         "SET p += $specs "
                         "CREATE (p)-[:BELONGS_TO]->(c), (p)-[:MADE_BY]->(b)",
                 id=product_id, category=category, brand=brand, specs=specs, stock=stock)


GPU_SPECS = {"chipset": "GeForce RTX 5070 Ti", "gpu_vendor": "NVIDIA", "vram_gb": 16,
             "memory_type": "GDDR7", "tdp_w": 300, "length_mm": 305}


# Create

def c1(driver, p):
    return create_customers(driver, p["id"], 1, tag="c1")


def c2(driver, p):
    return create_customers(driver, p["first_id"], p["count"], tag="c2")


def c3(driver, p):
    return create_orders(driver, p["order_id"], 1, p["customer_id"], p["product_ids"], p["created_at"])


def c4(driver, p):
    return create_product(driver, p["id"], p["category"], p["brand"], p["specs"])


def c5(driver, p):
    return create_orders(driver, p["first_id"], p["count"], p["customer_id"], p["product_ids"], p["created_at"])


def c6(driver, p):
    return write(driver, "CREATE (c:Customer {customerId: $id, first_name: 'Bench', last_name: 'User', "
                         "  email: 'bench.c6.0@example.com', phone: '+1-555-000-0000', created_at: datetime($now)}) "
                         "WITH c UNWIND range(0, 1) AS n "
                         "CREATE (c)-[:HAS_ADDRESS]->(:Address {addressId: $address_id + n, "
                         "  street: toString(n + 1) + ' Benchmark Street', city: 'Springfield', "
                         "  postal_code: '12345', country: 'US', is_default: n = 0})",
                 id=p["customer_id"], address_id=p["address_id"], now=NOW)


# Read

def r1(driver, p):
    return read(driver, "MATCH (c:Category)<-[:BELONGS_TO]-(p:Product {productId: $id})-[:MADE_BY]->(b:Brand) "
                        "RETURN p.productId, p.sku, p.name, p.price, c.name, b.name", id=p["product_id"])


def r2(driver, p):
    return read(driver, "MATCH (c:Customer) WHERE c.last_name = $last_name "
                        "RETURN c.customerId, c.first_name, c.last_name, c.email", last_name=p["last_name"])


def r3(driver, p):
    return read(driver, "MATCH (p:Product)-[:BELONGS_TO]->(:Category {name: $category}) "
                        "WHERE $min_price <= p.price <= $max_price "
                        "RETURN p.productId AS id, p.name, p.price ORDER BY p.price, id LIMIT $limit", **p)


def r4(driver, p):
    return read(driver, "MATCH (o:Order)-[c:CONTAINS]->(p:Product) "
                        "WHERE datetime($from) <= o.created_at < datetime($to) AND o.status <> 'cancelled' "
                        "RETURN p.productId AS id, p.name AS name, sum(c.quantity) AS sold "
                        "ORDER BY sold DESC, id LIMIT $limit", **p)


def r5(driver, p):
    return read(driver, "MATCH (:Customer {customerId: $customer_id})-[:PLACED]->(o:Order)-[c:CONTAINS]->(p:Product) "
                        "RETURN o.orderId AS id, o.created_at AS created_at, o.status, o.total_amount, "
                        "p.productId, p.name, c.quantity, c.unit_price ORDER BY created_at DESC, id, p.productId",
                **p)


def r6(driver, p):
    return read(driver, "MATCH (:CPU {productId: $cpu_id})-[:COMPATIBLE_WITH {via: 'socket'}]->(m:Motherboard) "
                        "RETURN m.productId AS id, m.name, m.price ORDER BY m.price, id", **p)


# Update

def u1_setup(driver, p):
    old = read(driver, "MATCH (p:Product {productId: $id}) RETURN p.price AS price", id=p["product_id"])[0]["price"]
    return {**p, "old": old}


def u1(driver, p):
    return write(driver, "MATCH (p:Product {productId: $id}) SET p.price = $price", id=p["product_id"], price=p["price"])


def u1_cleanup(driver, p):
    write(driver, "MATCH (p:Product {productId: $id}) SET p.price = $price", id=p["product_id"], price=p["old"])


BRAND_CATEGORY = "MATCH (p:Product)-[:MADE_BY]->(:Brand {name: $brand}), (p)-[:BELONGS_TO]->(:Category {name: $category}) "


def u2_setup(driver, p):
    rows = read(driver, BRAND_CATEGORY + "RETURN p.productId AS id, p.price AS price", **p)
    return {**p, "old": [dict(r) for r in rows]}


def u2(driver, p):
    return write(driver, BRAND_CATEGORY + "SET p.price = round(p.price * $factor, 2)",
                 brand=p["brand"], category=p["category"], factor=p["factor"])


def u2_cleanup(driver, p):
    write(driver, "UNWIND $rows AS r MATCH (p:Product {productId: r.id}) SET p.price = r.price", rows=p["old"])


def u3_setup(driver, p):
    old = read(driver, f"MATCH (p:Product {{productId: $id}}) RETURN p.{p['name']} AS value", id=p["product_id"])
    return {**p, "old": old[0]["value"]}


def u3(driver, p):
    # Specs are plain node properties, so the attribute update is a property SET.
    return write(driver, f"MATCH (p:Product {{productId: $id}}) SET p.{p['name']} = $value",
                 id=p["product_id"], value=p["value"])


def u3_cleanup(driver, p):
    write(driver, f"MATCH (p:Product {{productId: $id}}) SET p.{p['name']} = $value", id=p["product_id"], value=p["old"])


def u4_setup(driver, p):
    rows = read(driver, "MATCH (:Order {orderId: $order_id})-[:CONTAINS]->(p:Product) "
                        "RETURN p.productId AS id, p.stock AS stock", **p)
    return {**p, "old": [dict(r) for r in rows]}


def u4(driver, p):
    return write(driver, "MATCH (:Order {orderId: $order_id})-[c:CONTAINS]->(p:Product) "
                         "SET p.stock = CASE WHEN p.stock > c.quantity THEN p.stock - c.quantity ELSE 0 END", **p)


def u4_cleanup(driver, p):
    write(driver, "UNWIND $rows AS r MATCH (p:Product {productId: r.id}) SET p.stock = r.stock", rows=p["old"])


def u5_setup(driver, p):
    return {**p, "order_id": read(driver, "MATCH (o:Order {status: 'paid'}) RETURN min(o.orderId) AS id")[0]["id"]}


def u5(driver, p):
    return write(driver, "MATCH (o:Order {orderId: $order_id}) SET o.status = 'shipped', o.carrier = $carrier, "
                         "o.tracking_number = 'BENCH' + toString($order_id), o.shipped_at = datetime($shipped_at)", **p)


def u5_cleanup(driver, p):
    write(driver, "MATCH (o:Order {orderId: $order_id}) SET o.status = 'paid' "
                  "REMOVE o.carrier, o.tracking_number, o.shipped_at", order_id=p["order_id"])


def u6_setup(driver, p):
    rows = read(driver, "MATCH (o:Order {status: 'pending'}) WHERE o.created_at < datetime($before) "
                        "RETURN collect(o.orderId) AS ids", **p)
    return {**p, "old": rows[0]["ids"]}


def u6(driver, p):
    return write(driver, "MATCH (o:Order {status: 'pending'}) WHERE o.created_at < datetime($before) "
                         "SET o.status = 'cancelled', o.payment_status = 'refunded'", before=p["before"])


def u6_cleanup(driver, p):
    write(driver, "UNWIND $ids AS id MATCH (o:Order {orderId: id}) "
                  "SET o.status = 'pending', o.payment_status = 'pending'", ids=p["old"])


# Delete: setup creates the victims in the reserved id range, cleanup purges leftovers.

def d1_setup(driver, p):
    create_customers(driver, p["customer_id"], 1, tag="d1")
    return p


def d1(driver, p):
    return write(driver, "MATCH (c:Customer {customerId: $customer_id}) DETACH DELETE c", **p)


def d2_setup(driver, p):
    create_customers(driver, TEMP, p["count"], last_name=p["last_name"], created_at="2019-06-01T00:00:00", tag="d2")
    return p


def d2(driver, p):
    return write(driver, "MATCH (c:Customer) WHERE c.last_name = $last_name AND c.created_at < datetime($before) "
                         "DETACH DELETE c", last_name=p["last_name"], before=p["before"])


def d3_setup(driver, p):
    c6(driver, {"customer_id": p["customer_id"], "address_id": TEMP})
    create_orders(driver, TEMP, 5, p["customer_id"], [1, 2, 3], NOW, shipped_at="2026-06-30T18:00:00")
    return p


def d3(driver, p):
    # No FK cascade in a graph: the customer's orders and addresses are deleted explicitly.
    return write(driver, "MATCH (c:Customer {customerId: $customer_id}) "
                         "OPTIONAL MATCH (c)-[:PLACED|HAS_ADDRESS]->(n) DETACH DELETE c, n", **p)


def d4_setup(driver, p):
    create_product(driver, p["product_id"], "GPU", "MSI", GPU_SPECS, stock=20)
    return p


def d4(driver, p):
    return write(driver, "MATCH (p:Product {productId: $product_id}) DETACH DELETE p", **p)


def d5_setup(driver, p):
    create_orders(driver, TEMP, p["count"], 1, [1, 2], "2019-06-01T00:00:00")
    return p


def d5(driver, p):
    return write(driver, "MATCH (o:Order) WHERE o.created_at < datetime($before) DETACH DELETE o", before=p["before"])


def d6_setup(driver, p):
    create_orders(driver, p["order_id"], 1, 1, [1, 2, 3], NOW, shipped_at="2026-06-30T18:00:00")
    return p


def d6(driver, p):
    return write(driver, "MATCH (o:Order {orderId: $order_id}) DETACH DELETE o", **p)


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
    "R4": Scenario("Aggregation", r4, params={"from": "2026-05-31T00:00:00", "to": "2026-06-30T00:00:00", "limit": 10}),
    "R5": Scenario("Join / lookup", r5, params={"customer_id": 1}),
    "R6": Scenario("Compatible parts lookup", r6, params={"cpu_id": 1}),
    "U1": Scenario("Update one record", u1, u1_setup, u1_cleanup, {"product_id": 42, "price": 199.99}),
    "U2": Scenario("Bulk update by condition", u2, u2_setup, u2_cleanup,
                   {"brand": "MSI", "category": "GPU", "factor": 1.10}),
    "U3": Scenario("Update nested / attribute field", u3, u3_setup, u3_cleanup,
                   {"product_id": 1, "name": "boost_clock_ghz", "value": 6.2}),
    "U4": Scenario("Update stock after order", u4, u4_setup, u4_cleanup, {"order_id": 1}),
    "U5": Scenario("Ship an order", u5, u5_setup, u5_cleanup, {"carrier": "UPS", "shipped_at": NOW}),
    "U6": Scenario("Bulk status change", u6, u6_setup, u6_cleanup, {"before": "2025-01-01T00:00:00"}),
    "D1": Scenario("Delete one", d1, d1_setup, purge_temp, {"customer_id": TEMP}),
    "D2": Scenario("Delete by condition", d2, d2_setup, purge_temp,
                   {"count": 1000, "last_name": "Tempbench", "before": "2020-01-01T00:00:00"}),
    "D3": Scenario("Cascading delete", d3, d3_setup, purge_temp, {"customer_id": TEMP}),
    "D4": Scenario("Delete product with specs", d4, d4_setup, purge_temp, {"product_id": TEMP}),
    "D5": Scenario("Delete old records", d5, d5_setup, purge_temp, {"count": 500, "before": "2020-01-01T00:00:00"}),
    "D6": Scenario("Delete one order", d6, d6_setup, purge_temp, {"order_id": TEMP}),
}


def fingerprint(driver):
    """Counts and value sums that every scenario's run + cleanup must leave unchanged."""
    labels = read(driver, "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS n ORDER BY label")
    rels = read(driver, "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS n, sum(r.unit_price) AS value "
                        "ORDER BY type")
    products = read(driver, "MATCH (p:Product) RETURN sum(p.price) AS price, sum(p.stock) AS stock, "
                            "sum(p.boost_clock_ghz) AS boost, count(p.chipset) AS chipsets")
    orders = read(driver, "MATCH (o:Order) RETURN o.status AS status, o.payment_status AS payment, count(*) AS n, "
                          "count(o.carrier) AS carriers, count(o.shipped_at) AS shipped, "
                          "count(o.tracking_number) AS tracking ORDER BY status, payment")
    return [tuple(map(tuple, (r.values() for r in rows))) for rows in (labels, rels, products, orders)]


def summary(result):
    return f"{len(result)} rows" if isinstance(result, list) else f"{result} affected"


def smoke(driver, ids):
    before = fingerprint(driver)
    failures = []
    for sid in ids:
        s = SCENARIOS[sid]
        params = s.setup(driver, dict(s.params)) if s.setup else dict(s.params)
        start = time.perf_counter()
        try:
            result = s.run(driver, params)
        except Exception as exc:
            result = exc
        elapsed = (time.perf_counter() - start) * 1000
        if s.cleanup:
            s.cleanup(driver, params)
        changed = fingerprint(driver) != before
        ok = not isinstance(result, Exception) and not changed
        if not ok:
            failures.append(sid)
        detail = result if isinstance(result, Exception) else summary(result)
        print(f"{'OK  ' if ok else 'FAIL'} {sid} {s.name:<32} {elapsed:9.1f} ms  {detail}"
              f"{'  state changed' if changed else ''}")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", help="comma-separated scenario ids (default: all)")
    args = parser.parse_args()
    ids = args.only.split(",") if args.only else list(SCENARIOS)
    with connect() as driver:
        failures = smoke(driver, ids)
    print(f"{len(ids) - len(failures)}/{len(ids)} scenarios passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
