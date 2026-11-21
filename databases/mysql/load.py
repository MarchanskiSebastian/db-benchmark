"""Bulk-load the generator's relational CSVs into MySQL.

Usage (from repo root, container running):
    python databases/mysql/load.py --size s
"""

import argparse
import os
import time
from pathlib import Path

import mysql.connector

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = Path(__file__).with_name("schema.sql")

# Parents before children, so the order also works if FK checks were left on.
TABLES = {
    "customers": ["id", "first_name", "last_name", "email", "phone", "created_at"],
    "addresses": ["id", "customer_id", "street", "city", "postal_code", "country", "is_default"],
    "categories": ["id", "name"],
    "brands": ["id", "name", "country"],
    "suppliers": ["id", "name", "email", "country"],
    "products": ["id", "sku", "name", "category_id", "brand_id", "price", "release_date"],
    "product_attributes": ["product_id", "name", "value"],
    "inventory": ["product_id", "supplier_id", "warehouse", "quantity", "updated_at"],
    "orders": ["id", "customer_id", "address_id", "status", "total_amount", "created_at"],
    "order_items": ["id", "order_id", "product_id", "quantity", "unit_price"],
    "payments": ["id", "order_id", "method", "status", "amount", "paid_at"],
    "shipments": ["id", "order_id", "carrier", "tracking_number", "shipped_at", "delivered_at"],
}
# The generator writes NULL as an empty field; LOAD DATA would read it as '' or a zero date.
NULLABLE = {"payments": {"paid_at"}, "shipments": {"delivered_at"}}


def env():
    values = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    values.update({k: v for k, v in os.environ.items() if k.startswith("MYSQL_")})
    return values


def connect(**kwargs):
    e = env()
    return mysql.connector.connect(
        host=e.get("MYSQL_HOST", "127.0.0.1"), port=int(e.get("MYSQL_PORT", 3306)),
        user=e["MYSQL_USER"], password=e["MYSQL_PASSWORD"], database=e["MYSQL_DATABASE"],
        **kwargs,
    )


def load_statement(table, path):
    nullable = NULLABLE.get(table, set())
    columns = ", ".join(f"@{c}" if c in nullable else c for c in TABLES[table])
    sets = ", ".join(f"{c} = NULLIF(@{c}, '')" for c in sorted(nullable))
    return (
        f"LOAD DATA LOCAL INFILE '{path.as_posix()}' INTO TABLE {table} CHARACTER SET utf8mb4 "
        "FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' ESCAPED BY '' "
        "LINES TERMINATED BY '\\r\\n' IGNORE 1 LINES "
        f"({columns})" + (f" SET {sets}" if sets else "")
    )


def csv_rows(path):
    with open(path, "rb") as f:
        return sum(1 for _ in f) - 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--size", default="s", help="dataset size, reads data/<size>/relational")
    parser.add_argument("--data", type=Path, help="CSV directory (overrides --size)")
    args = parser.parse_args()
    data = args.data or ROOT / "data" / args.size / "relational"

    conn = connect(allow_local_infile=True, allow_local_infile_in_path=str(data))
    cur = conn.cursor()
    sql = "\n".join(line for line in SCHEMA.read_text().splitlines() if not line.lstrip().startswith("--"))
    for statement in filter(str.strip, sql.split(";")):
        cur.execute(statement)

    print(f"Loading {data}")
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    cur.execute("SET UNIQUE_CHECKS = 0")
    total = time.perf_counter()
    timings = {}
    for table in TABLES:
        start = time.perf_counter()
        cur.execute(load_statement(table, data / f"{table}.csv"))
        conn.commit()
        timings[table] = time.perf_counter() - start
    cur.execute("SET UNIQUE_CHECKS = 1")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    total = time.perf_counter() - total

    ok = True
    print(f"{'table':<20}{'rows':>12}{'expected':>12}{'seconds':>10}")
    for table, seconds in timings.items():
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        rows = cur.fetchone()[0]
        expected = csv_rows(data / f"{table}.csv")
        ok &= rows == expected
        print(f"{table:<20}{rows:>12,}{expected:>12,}{seconds:>10.2f}{'' if rows == expected else '  MISMATCH'}")
    print(f"{'total':<44}{total:>10.2f}")

    start = time.perf_counter()
    cur.execute("ANALYZE TABLE " + ", ".join(TABLES))
    cur.fetchall()
    print(f"ANALYZE TABLE: {time.perf_counter() - start:.2f}s")
    conn.close()
    if not ok:
        raise SystemExit("Row counts do not match the generator output")


if __name__ == "__main__":
    main()
