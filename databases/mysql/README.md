# MySQL 8

All commands run from the repo root with the virtualenv active (`pip install -r requirements.txt`)
and a `.env` copied from `.env.example`.

## Start

```bash
docker compose -f databases/mysql/docker-compose.yml --env-file .env up -d
docker inspect -f '{{.State.Health.Status}}' bench-mysql   # wait for "healthy"
```

The container gets the shared limits from `.env` (`DB_CPUS`, `DB_MEMORY`), `--local-infile=1`
for the loader and a 2 GB InnoDB buffer pool (the 128 MB default would make every query disk-bound).

## Load

```bash
python -m generator --size s --out data/s --seed 42    # if data/s does not exist yet
python databases/mysql/load.py --size s
```

`load.py` recreates the schema from [`schema.sql`](schema.sql), loads every CSV from
`data/<size>/relational/` with `LOAD DATA LOCAL INFILE` (FK and unique checks off during the load,
back on afterwards), prints the time per table and in total, compares row counts with the CSV
files (exits non-zero on a mismatch) and runs `ANALYZE TABLE`.

### Schema notes

- [`schema.sql`](schema.sql) is the MySQL version of [`generator/schema.sql`](../../generator/schema.sql):
  InnoDB, `utf8mb4`, `DATETIME` for timestamps, `DECIMAL` for money, CHECK constraints enforced.
- Only primary keys, unique keys and foreign keys. Secondary indexes come in `perf/indexes-explain`.
  InnoDB automatically indexes every foreign key column (e.g. `orders.customer_id`), so the
  "before" state here already has those indexes, unlike PostgreSQL.
- Specs live in `product_attributes` (key/value rows). There is no JSON column, because the generator
  doesn't produce one.

### Measured import times

On a 4-vCPU cloud container with `DB_CPUS=2`, `DB_MEMORY=4g`, MySQL 8.4. Time covers `LOAD DATA` for
all 12 tables (`ANALYZE TABLE` excluded, < 0.1 s).

| Size | order_items | Rows total | Import time |
|------|-------------|------------|-------------|
| S | 10,000 | 26,403 | 0.3 s |
| M | 500,000 | 1,142,307 | 10.1 s |

Largest tables at M: `order_items` 4.2 s, `orders` 2.2 s, `payments` 1.5 s, `shipments` 1.4 s.

## Scenarios

[`scenarios.py`](scenarios.py) implements the 24 scenarios of
[`docs/scenarios.md`](../../docs/scenarios.md). `SCENARIOS` maps each ID (`C1`…`D6`) to
`Scenario(name, run, setup, cleanup, params)`, where `run(conn, params)` is the part to time.

Smoke test, which runs every scenario once and checks the database is unchanged afterwards
(`CHECKSUM TABLE` on all tables before and after each scenario):

```bash
python databases/mysql/scenarios.py            # all 24
python databases/mysql/scenarios.py --only R4,U6
```

MySQL-specific notes:
- **D3** deletes the customer's orders and then the customer in one transaction, and both cascade
  further. A single `DELETE FROM customers` fails in InnoDB, which checks `orders.address_id → addresses`
  row by row inside the cascade, while PostgreSQL checks at the end of the statement.
- **R6** matches sockets by self-joining `product_attributes` (`name = 'socket'`).
- **U3** updates the `value` of the `boost_clock_ghz` row in `product_attributes`.
