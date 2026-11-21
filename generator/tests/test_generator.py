import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from generator.__main__ import build_writers
from generator.generate import SIZES, counts_for, generate
from generator.writers import TABLES

SEED = 42


def run(out):
    generate(SIZES["s"], SEED, build_writers(out))
    return out


def read(out, table):
    with open(out / "relational" / f"{table}.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cents(value):
    whole, frac = value.split(".")
    return int(whole) * 100 + int(frac)


@pytest.fixture(scope="module")
def out(tmp_path_factory):
    return run(tmp_path_factory.mktemp("s"))


@pytest.fixture(scope="module")
def db(out):
    return {table: read(out, table) for table in TABLES}


def by_id(rows):
    return {r["id"]: r for r in rows}


def test_schema_sql_matches_written_tables():
    ddl = (Path(__file__).parents[1] / "schema.sql").read_text()
    tables = dict(re.findall(r"CREATE TABLE (\w+) \((.*?)\n\);", ddl, re.S))
    assert list(tables) == list(TABLES)
    for table, body in tables.items():
        columns = [line.split()[0] for line in body.strip().splitlines()
                   if not line.strip().startswith(("PRIMARY", "UNIQUE", "CHECK", "--"))
                   and not line.startswith("    " * 4)]
        assert columns == TABLES[table], table


def test_row_counts(db):
    expected = counts_for(SIZES["s"])
    for table in ("order_items", "orders", "customers", "products", "suppliers"):
        assert len(db[table]) == expected[table], table
    assert len(db["categories"]) == 14
    assert len(db["payments"]) == len(db["orders"])
    shipped = sum(o["status"] in ("shipped", "delivered") for o in db["orders"])
    assert len(db["shipments"]) == shipped


@pytest.mark.parametrize("table, column, target", [
    ("addresses", "customer_id", "customers"),
    ("products", "category_id", "categories"),
    ("products", "brand_id", "brands"),
    ("product_attributes", "product_id", "products"),
    ("inventory", "product_id", "products"),
    ("inventory", "supplier_id", "suppliers"),
    ("orders", "customer_id", "customers"),
    ("orders", "address_id", "addresses"),
    ("order_items", "order_id", "orders"),
    ("order_items", "product_id", "products"),
    ("payments", "order_id", "orders"),
    ("shipments", "order_id", "orders"),
])
def test_foreign_keys(db, table, column, target):
    ids = {r["id"] for r in db[target]}
    assert {r[column] for r in db[table]} <= ids


def test_unique_keys(db):
    for table in ("customers", "products", "orders", "order_items", "payments", "shipments"):
        assert len(by_id(db[table])) == len(db[table]), table
    assert len({c["email"] for c in db["customers"]}) == len(db["customers"])
    assert len({p["sku"] for p in db["products"]}) == len(db["products"])
    assert len({(i["order_id"], i["product_id"]) for i in db["order_items"]}) == len(db["order_items"])
    assert len({(a["product_id"], a["name"]) for a in db["product_attributes"]}) == len(db["product_attributes"])


def test_order_address_belongs_to_customer(db):
    addresses = by_id(db["addresses"])
    assert all(addresses[o["address_id"]]["customer_id"] == o["customer_id"] for o in db["orders"])


def test_totals_match_items_and_payments(db):
    totals = Counter()
    for i in db["order_items"]:
        totals[i["order_id"]] += int(i["quantity"]) * cents(i["unit_price"])
    payments = {p["order_id"]: p for p in db["payments"]}
    for o in db["orders"]:
        assert cents(o["total_amount"]) == totals[o["id"]]
        assert cents(payments[o["id"]]["amount"]) == totals[o["id"]]


def test_dates_are_consistent(db):
    customers = by_id(db["customers"])
    payments = {p["order_id"]: p for p in db["payments"]}
    shipments = {s["order_id"]: s for s in db["shipments"]}
    for o in db["orders"]:
        assert customers[o["customer_id"]]["created_at"] <= o["created_at"]
        payment = payments[o["id"]]
        assert (payment["paid_at"] == "") == (o["status"] == "pending")
        assert payment["status"] == {"pending": "pending", "cancelled": "refunded"}.get(o["status"], "completed")
        if payment["paid_at"]:
            assert o["created_at"] <= payment["paid_at"]
        shipment = shipments.get(o["id"])
        assert (shipment is not None) == (o["status"] in ("shipped", "delivered"))
        if shipment:
            assert payment["paid_at"] <= shipment["shipped_at"]
            assert (shipment["delivered_at"] != "") == (o["status"] == "delivered")
            if shipment["delivered_at"]:
                assert shipment["shipped_at"] <= shipment["delivered_at"]


def specs_by_category(db):
    categories = {c["id"]: c["name"] for c in db["categories"]}
    attrs = defaultdict(dict)
    for a in db["product_attributes"]:
        attrs[a["product_id"]][a["name"]] = a["value"]
    result = defaultdict(dict)
    for p in db["products"]:
        result[categories[p["category_id"]]][p["id"]] = attrs[p["id"]]
    return result


def test_every_cpu_and_ram_has_a_compatible_motherboard(db):
    specs = specs_by_category(db)
    boards = specs["Motherboard"].values()
    sockets = {b["socket"] for b in boards}
    memory = {b["memory_type"] for b in boards}
    assert all(c["socket"] in sockets for c in specs["CPU"].values())
    assert all(r["memory_type"] in memory for r in specs["RAM"].values())
    socket_memory = {"AM4": {"DDR4"}, "AM5": {"DDR5"}, "LGA1200": {"DDR4"},
                     "LGA1700": {"DDR4", "DDR5"}, "LGA1851": {"DDR5"}}
    assert all(b["memory_type"] in socket_memory[b["socket"]] for b in boards)


def test_neo4j_compatibility_relationships(db, out):
    specs = specs_by_category(db)
    cpus, rams, boards = specs["CPU"], specs["RAM"], specs["Motherboard"]
    expected = {(c, b, "socket") for c in cpus for b in boards if cpus[c]["socket"] == boards[b]["socket"]}
    expected |= {(r, b, "memory_type") for r in rams for b in boards
                 if rams[r]["memory_type"] == boards[b]["memory_type"]}
    with open(out / "neo4j" / "compatible_with.csv", newline="") as f:
        actual = {tuple(row) for row in csv.reader(f)}
    assert expected and actual == expected


def test_formats_are_consistent(db, out):
    def lines(path):
        with open(path, encoding="utf-8") as f:
            return sum(1 for _ in f)

    neo = out / "neo4j"
    assert lines(neo / "orders.csv") == lines(neo / "placed.csv") == len(db["orders"])
    assert lines(neo / "contains.csv") == len(db["order_items"])
    assert lines(neo / "products.csv") == lines(neo / "belongs_to.csv") == len(db["products"])
    with open(neo / "products_header.csv") as f:
        header_columns = len(next(csv.reader(f)))
    with open(neo / "products.csv", newline="", encoding="utf-8") as f:
        assert all(len(row) == header_columns for row in csv.reader(f))

    with open(out / "mongo" / "orders.ndjson", encoding="utf-8") as f:
        orders = [json.loads(line) for line in f]
    assert len(orders) == len(db["orders"])
    assert sum(len(o["items"]) for o in orders) == len(db["order_items"])
    totals = {o["id"]: cents(o["total_amount"]) for o in db["orders"]}
    assert all(round(o["total_amount"] * 100) == totals[str(o["_id"])] for o in orders)
    with open(out / "mongo" / "products.ndjson", encoding="utf-8") as f:
        assert all(json.loads(line)["specs"] for line in f)


def digest(directory):
    h = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            h.update(str(path.relative_to(directory)).encode())
            h.update(path.read_bytes())
    return h.hexdigest()


def test_same_seed_gives_identical_output(out, tmp_path):
    assert digest(run(tmp_path / "again")) == digest(out)


def test_different_seed_changes_output(out, tmp_path):
    generate(SIZES["s"], SEED + 1, build_writers(tmp_path))
    assert digest(tmp_path) != digest(out)
