"""Import the generator's Neo4j CSVs with neo4j-admin and verify the counts.

Usage (from repo root, container created with docker compose):
    python databases/neo4j/load.py --size s

neo4j-admin import needs the database offline, so the script stops the container, runs the
import in a one-off container on the same volume, starts Neo4j again, creates the id
uniqueness constraints and sets Product.stock (see README), then compares counts with the CSVs.
"""

import argparse
import csv
import os
import subprocess
import time
from pathlib import Path

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ["docker", "compose", "-f", str(Path(__file__).with_name("docker-compose.yml")),
           "--env-file", str(ROOT / ".env")]

NODES = {"Customer": "customers", "Order": "orders", "Product": "products", "Category": "categories",
         "Brand": "brands"}
RELATIONSHIPS = {"PLACED": "placed", "CONTAINS": "contains", "BELONGS_TO": "belongs_to",
                 "MADE_BY": "made_by", "COMPATIBLE_WITH": "compatible_with"}
ID_PROPERTIES = {"Customer": "customerId", "Order": "orderId", "Product": "productId",
                 "Category": "categoryId", "Brand": "brandId"}


def env():
    values = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    values.update({k: v for k, v in os.environ.items() if k.startswith("NEO4J_")})
    return values


def connect():
    e = env()
    uri = f"bolt://{e.get('NEO4J_HOST', '127.0.0.1')}:{e.get('NEO4J_BOLT_PORT', 7687)}"
    return GraphDatabase.driver(uri, auth=(e.get("NEO4J_USER", "neo4j"), e["NEO4J_PASSWORD"]))


def wait_until_ready(driver, timeout=180):
    deadline = time.monotonic() + timeout
    while True:
        try:
            driver.verify_connectivity()
            driver.execute_query("RETURN 1")
            return
        except ServiceUnavailable:
            if time.monotonic() > deadline:
                raise
            time.sleep(1)


def import_command(size):
    base = f"/import/{size}/neo4j"
    # Integer ids so lookups like {orderId: 1} match; the default stores :ID values as strings.
    args = ["neo4j-admin", "database", "import", "full", "neo4j", "--overwrite-destination", "--id-type=INTEGER"]
    for label, name in NODES.items():
        # Products carry their labels (Product;CPU, ...) in the :LABEL column.
        prefix = "" if label == "Product" else f"{label}="
        args.append(f"--nodes={prefix}{base}/{name}_header.csv,{base}/{name}.csv")
    for rel_type, name in RELATIONSHIPS.items():
        args.append(f"--relationships={rel_type}={base}/{name}_header.csv,{base}/{name}.csv")
    return args


def lines(path):
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def lowest_supplier_stock(path):
    """Stock of each product at its lowest-id supplier, the row U4 decrements in SQL."""
    stock = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            product, supplier = int(row["product_id"]), int(row["supplier_id"])
            if product not in stock or supplier < stock[product][0]:
                stock[product] = (supplier, int(row["quantity"]))
    return [{"id": p, "stock": q} for p, (_, q) in stock.items()]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--size", default="s", help="dataset size, reads data/<size>/neo4j")
    args = parser.parse_args()
    data = ROOT / "data" / args.size

    subprocess.run(COMPOSE + ["stop", "neo4j"], check=True, capture_output=True)
    start = time.perf_counter()
    result = subprocess.run(COMPOSE + ["run", "--rm", "--no-deps", "neo4j", *import_command(args.size)],
                            capture_output=True, text=True)
    import_seconds = time.perf_counter() - start
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    print(next((line for line in result.stdout.splitlines() if line.startswith("IMPORT DONE")), "import finished"))

    start = time.perf_counter()
    subprocess.run(COMPOSE + ["up", "-d", "neo4j"], check=True, capture_output=True)
    driver = connect()
    wait_until_ready(driver)
    startup_seconds = time.perf_counter() - start

    start = time.perf_counter()
    for label, prop in ID_PROPERTIES.items():
        driver.execute_query(f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS "
                             f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE")
    driver.execute_query("CALL db.awaitIndexes(300)")
    constraint_seconds = time.perf_counter() - start

    start = time.perf_counter()
    rows = lowest_supplier_stock(data / "relational" / "inventory.csv")
    for i in range(0, len(rows), 10_000):
        driver.execute_query("UNWIND $rows AS r MATCH (p:Product {productId: r.id}) SET p.stock = r.stock",
                             rows=rows[i:i + 10_000])
    stock_seconds = time.perf_counter() - start

    ok = True
    print(f"{'element':<18}{'count':>12}{'expected':>12}")
    for label, name in NODES.items():
        count = driver.execute_query(f"MATCH (n:{label}) RETURN count(n) AS c").records[0]["c"]
        expected = lines(data / "neo4j" / f"{name}.csv")
        ok &= count == expected
        print(f"{':' + label:<18}{count:>12,}{expected:>12,}{'' if count == expected else '  MISMATCH'}")
    for rel_type, name in RELATIONSHIPS.items():
        count = driver.execute_query(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS c").records[0]["c"]
        expected = lines(data / "neo4j" / f"{name}.csv")
        ok &= count == expected
        print(f"{'[:' + rel_type + ']':<18}{count:>12,}{expected:>12,}{'' if count == expected else '  MISMATCH'}")
    driver.close()

    print(f"neo4j-admin import: {import_seconds:6.2f}s")
    print(f"startup:            {startup_seconds:6.2f}s")
    print(f"constraints:        {constraint_seconds:6.2f}s")
    print(f"product stock:      {stock_seconds:6.2f}s")
    print(f"total:              {import_seconds + startup_seconds + constraint_seconds + stock_seconds:6.2f}s")
    if not ok:
        raise SystemExit("Counts do not match the generator output")


if __name__ == "__main__":
    main()
